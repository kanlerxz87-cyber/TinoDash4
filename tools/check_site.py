"""Pre-publish checks for the root Pages dashboard and repository privacy boundary.

Default mode is strict: it requires the ignored local private/raw_inputs.json inventory and
compares redacted patterns from that file with the current repository text/PDF tree. If the
inventory is absent or unreadable, strict mode fails closed after running the public-surface
checks. Matched values and source text are never printed.

--public-only skips exact private-input comparison so CI and clean checkouts can run without
household inputs. It still checks restricted-token hashes across repository text and direct-
identifier patterns on root Pages artifacts, but it is not a privacy release clearance. Neither
mode proves that rounded, derived outputs
are anonymous or cannot be linked to public records.

Usage:
  python3 tools/check_site.py
  python3 tools/check_site.py --public-only
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PRIVATE = os.path.join(ROOT, "private", "raw_inputs.json")
CONFIG = os.path.join(ROOT, "_config.yml")
SCAN_EXT = (".html", ".css", ".js", ".json", ".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".pdf", ".svg")
SKIP_DIRS = {".git", "private", "node_modules", "__pycache__", ".venv"}
PUBLIC_DIRS = {"assets", "data"}
PUBLIC_PAGE_SUFFIXES = {".html", ".pdf"}
ALLOW_PUBLIC_NUMBERS = {
    # Public, sourced figures that can legitimately overlap with local household inputs.
    15000000, 15480000, 19000, 20000, 194000, 201000, 250000, 500000, 1000000,
    1044590, 1044586, 400000, 129, 177000000, 10000000, 2026, 2027,
}
# Hyper-local identifiers are held as truncated SHA-256 hashes, not literal tokens.
FORBIDDEN_HASHES = {
    "f6f9c5f004b4e5b5": "restricted identifier pattern #1",
    "0829103205fbe796": "restricted identifier pattern #2",
    "2478d903d7c875f0": "restricted identifier pattern #3",
    "43086d953bcc428c": "restricted identifier pattern #4",
    "576ba7c2e4abb718": "restricted identifier pattern #5",
}
PUBLIC_IDENTIFIER_PATTERNS = (
    ("e-mail address pattern", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("labelled postal-code pattern", re.compile(r"\b(?:ZIP|postal)(?:\s+code)?\s*[:#]?\s*\d{5}(?:-\d{4})?\b|\b\d{5}-\d{4}\b", re.I)),
    ("street-address pattern", re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,3}\s+(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Court|Ct|Boulevard|Blvd|Way|Terrace|Ter|Place|Pl)\b", re.I)),
    ("parcel-number pattern", re.compile(r"\b(?:APN|assessor(?:'s|’s)?\s+parcel\s+(?:number|no\.))\s*[:#]?\s*(?=[A-Z0-9-]{5,}\b)(?=[A-Z0-9-]*\d)[A-Z0-9-]{5,}\b", re.I)),
)
REQUIRED_JEKYLL_EXCLUDES = {
    ".github", "COORDINATION.md", "DECISION_RULES.md", "README.md",
    "decision-model", "decision-workspace", "model", "research", "site", "tools",
    "private", "*.py", "*.md",
}
SELF = os.path.normpath(os.path.abspath(__file__))
LOG = []
FAIL = []


def ok(message):
    LOG.append("PASS  " + message)


def note(message):
    LOG.append("NOTE  " + message)


def bad(message):
    FAIL.append("FAIL  " + message)
    LOG.append("FAIL  " + message)


def walk_numbers(value, out):
    if isinstance(value, dict):
        for child in value.values():
            walk_numbers(child, out)
    elif isinstance(value, list):
        for child in value:
            walk_numbers(child, out)
    elif isinstance(value, bool):
        return
    elif isinstance(value, (int, float)):
        out.append(value)


def walk_strings(value, out):
    if isinstance(value, dict):
        for child in value.values():
            walk_strings(child, out)
    elif isinstance(value, list):
        for child in value:
            walk_strings(child, out)
    elif isinstance(value, str):
        out.append(value)


def repository_files():
    """Yield current working-tree text/PDF files, excluding Git and local private inputs."""
    for directory, subdirs, filenames in os.walk(ROOT):
        subdirs[:] = [name for name in subdirs if name not in SKIP_DIRS]
        for filename in filenames:
            full_path = os.path.normpath(os.path.abspath(os.path.join(directory, filename)))
            if filename.lower().endswith(SCAN_EXT) and full_path != SELF:
                yield full_path


def public_files():
    """Yield root Pages documents plus the public assets/ and data/ trees."""
    for entry in sorted(os.scandir(ROOT), key=lambda item: item.name):
        if entry.name.startswith(".") or entry.name == "_config.yml":
            continue
        if entry.is_file(follow_symlinks=False):
            if os.path.splitext(entry.name)[1].lower() in PUBLIC_PAGE_SUFFIXES:
                yield entry.path
        elif entry.is_dir(follow_symlinks=False) and entry.name in PUBLIC_DIRS:
            for directory, subdirs, filenames in os.walk(entry.path):
                subdirs[:] = [name for name in subdirs if not name.startswith(".")]
                for filename in sorted(filenames):
                    if filename.startswith("."):
                        continue
                    full_path = os.path.join(directory, filename)
                    if os.path.splitext(filename)[1].lower() in SCAN_EXT:
                        yield full_path


def pdf_streams(data):
    """Decode PDF streams (ASCII85 and/or Flate) so drawn text is included in scans."""
    decoded = []
    for match in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        body = match.group(1).strip()
        try:
            if body.endswith(b"~>"):
                body = base64.a85decode(body[:-2].strip(), adobe=False)
            try:
                body = zlib.decompress(body)
            except zlib.error:
                pass
            decoded.append(body.decode("latin-1"))
        except Exception:
            decoded.append(match.group(1).decode("latin-1", "replace"))
    return decoded


def read_text(path):
    raw_bytes = open(path, "rb").read()
    if path.lower().endswith(".pdf"):
        return raw_bytes.decode("latin-1") + "\n" + "\n".join(pdf_streams(raw_bytes))
    return raw_bytes.decode("utf-8", "replace")


def private_patterns(raw):
    """Build exact-value regexes without ever returning or logging the private values."""
    patterns = []
    numbers = []
    walk_numbers(raw, numbers)
    # Published monetary outputs are rounded to $10. Compare unrounded source values only;
    # this is not a test for re-identification from rounded or otherwise derived outputs.
    unique_numbers = set()
    for value in numbers:
        try:
            number = int(value)
        except (OverflowError, ValueError):
            continue
        if number >= 1000 and number % 10 != 0 and not 1900 <= number <= 2100:
            unique_numbers.add(number)
    unique_numbers = sorted(unique_numbers)

    collisions = len(set(unique_numbers) & ALLOW_PUBLIC_NUMBERS)
    if collisions:
        bad(f"private numeric inputs overlap the public-number allowlist ({collisions} item(s)); review locally")
    for index, number in enumerate(unique_numbers, start=1):
        label = f"private numeric input #{index}"
        comma_value = f"{number:,}"
        patterns.append((label, re.compile(r"(?<![0-9.,])" + re.escape(comma_value) + r"(?![0-9])")))
        if number >= 10000:
            patterns.append((label, re.compile(r"(?<![0-9.,])" + re.escape(str(number)) + r"(?![0-9])")))

    strings = []
    walk_strings(raw, strings)
    ignored_placeholders = {"property", "property a", "property b", "estimate", "held internally"}
    for index, value in enumerate(strings, start=1):
        if len(value.strip()) >= 6 and value.strip().casefold() not in ignored_placeholders:
            patterns.append((f"private text input #{index}", re.compile(re.escape(value.strip()), re.I)))

    zip_values = raw.get("zip_codes_internal_only", [])
    if isinstance(zip_values, list):
        for index, value in enumerate(zip_values, start=1):
            patterns.append((f"private location-code input #{index}",
                             re.compile(r"(?<![0-9])" + re.escape(str(value)) + r"(?![0-9])")))
    return patterns


def check_repository_privacy(private_raw=None):
    """Scan current repository text for high-risk identifiers and, in strict mode, private inputs."""
    files = list(repository_files())
    if not files:
        bad("no repository text/PDF files found for privacy checks")
        return

    failures_before_patterns = len(FAIL)
    patterns = private_patterns(private_raw) if private_raw is not None else []
    if private_raw is not None and not patterns:
        bad("private inventory produced no comparison patterns; review its schema locally")
    private_matches = 0
    restricted_matches = 0

    for path in files:
        text = read_text(path)
        relative_path = os.path.relpath(path, ROOT)
        for label, regex in patterns:
            if regex.search(text):
                private_matches += 1
                bad(f"private-input pattern {label} found in {relative_path}; matching value withheld")

        tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            if digest in FORBIDDEN_HASHES:
                restricted_matches += 1
                bad(f"restricted identifier pattern found in {relative_path}; matching token withheld")

    if private_raw is None:
        note("exact private-value comparison skipped; no private values were read")
    elif patterns and private_matches == 0 and len(FAIL) == failures_before_patterns:
        ok(f"exact private-value comparison scanned {len(files)} repository text/PDF files using {len(patterns)} redacted patterns")
    else:
        note("exact private-value comparison completed; review the failure lines above (matched values withheld)")
    if restricted_matches == 0:
        ok(f"repository restricted-token scan of {len(files)} text/PDF files; matching tokens withheld")


def check_public_identifiers():
    """Scan the actual root Pages surface for common direct-identifier patterns."""
    files = list(public_files())
    if not files:
        bad("no public Pages files found for identifier checks")
        return
    failures = 0
    for path in files:
        text = read_text(path)
        relative_path = os.path.relpath(path, ROOT)
        for label, regex in PUBLIC_IDENTIFIER_PATTERNS:
            if regex.search(text):
                failures += 1
                bad(f"possible {label} in {relative_path}; matching text withheld")
    if not failures:
        ok(f"public identifier-pattern scan of {len(files)} Pages files; matching text withheld")


def check_jekyll_boundary():
    if not os.path.isfile(CONFIG):
        bad("_config.yml missing: Pages exclusion boundary cannot be checked")
        return
    exclusions = set()
    in_exclude = False
    with open(CONFIG, encoding="utf-8") as handle:
        for line in handle:
            if re.match(r"^exclude:\s*$", line):
                in_exclude = True
                continue
            if in_exclude and line.strip() and not line[:1].isspace():
                in_exclude = False
            if in_exclude:
                match = re.match(r"^\s*-\s*(.*?)\s*(?:#.*)?$", line)
                if match:
                    exclusions.add(match.group(1).strip("\"'"))

    missing = sorted(REQUIRED_JEKYLL_EXCLUDES - exclusions)
    if missing:
        bad("_config.yml is missing required Pages exclusions: " + ", ".join(missing))
    elif os.path.exists(os.path.join(ROOT, ".nojekyll")):
        bad(".nojekyll bypasses Jekyll, so configured Pages exclusions may not be applied")
    else:
        ok("Jekyll Pages exclusions are present and .nojekyll does not bypass them")


def check_rounding():
    data_path = os.path.join(ROOT, "data", "model_outputs.json")
    if not os.path.isfile(data_path):
        bad("data/model_outputs.json missing")
        return
    try:
        with open(data_path, encoding="utf-8") as handle:
            data = json.load(handle)
        money_values = list(data["base_results_real_2026"].values())
        money_values += [value for row in data["grid"] for value in row["results"].values()]
        money_values += [value for summary in data["monte_carlo"]["summary"].values()
                         for value in summary.values()
                         if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 1000]
        money_values += [value for row in data["projection_base"] for key, value in row.items() if key != "year"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        bad("data/model_outputs.json could not be parsed using the expected public schema")
        return

    invalid_count = sum(1 for value in money_values
                        if not isinstance(value, (int, float)) or isinstance(value, bool) or round(value) % 10 != 0)
    if invalid_count:
        bad(f"{invalid_count} monetary output(s) are not rounded to the nearest $10; values are withheld")
    else:
        ok(f"rounding: {len(money_values)} model-output monetary values are multiples of $10")


def check_pdf_export():
    path = os.path.join(ROOT, "brief.pdf")
    if not os.path.isfile(path):
        bad("brief.pdf missing")
        return
    raw = open(path, "rb").read()
    page_count = len(re.findall(rb"/Type\s*/Page\b", raw))
    link_count = len(re.findall(rb"/URI\s*\(", raw))
    if page_count != 1:
        bad("brief.pdf is not a one-page export")
    else:
        ok("brief.pdf is one page")
    if link_count < 8:
        bad("brief.pdf is missing clickable source links for fact rows")
    else:
        ok(f"brief.pdf contains {link_count} clickable source-link annotations")
    if "not guaranteed anonymous" not in read_text(path).lower():
        bad("brief.pdf is missing the privacy caveat")


def check_html():
    pages = sorted(path for path in public_files() if path.lower().endswith(".html"))
    if not any(os.path.basename(path) == "index.html" for path in pages):
        bad("index.html missing")

    row_total = 0
    row_fail = 0
    for path in pages:
        with open(path, encoding="utf-8", errors="replace") as handle:
            html = handle.read()
        page_name = os.path.relpath(path, ROOT)
        for tbody in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
            for row in re.findall(r"<tr>(.*?)</tr>", tbody, re.S):
                row_total += 1
                if "href=" not in row:
                    row_fail += 1
                    bad(f"table row #{row_total} has no source link in {page_name}")
        for href in re.findall(r'(?:href|src)="([^"]+)"', html):
            if href.startswith(("http://", "https://", "//", "#", "mailto:", "tel:")):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if target and not os.path.exists(os.path.join(ROOT, target)):
                bad(f"broken internal link in {page_name}; target value withheld")
    if row_total:
        ok(f"source links: {row_total - row_fail} of {row_total} public table rows link to a source")
    else:
        bad("no public table rows found for source-link validation")


def check_required_content():
    index_path = os.path.join(ROOT, "index.html")
    if not os.path.isfile(index_path):
        return
    with open(index_path, encoding="utf-8", errors="replace") as handle:
        index = handle.read()
    for phrase in ("What would change the answer", "Reinvestment risk", "Executive summary", "Privacy: partial"):
        if phrase not in index:
            bad(f"required dashboard content missing from index.html")

    required_pages = {
        "flagged.html": "Flagged for Review",
        "brief.html": "Attorney &amp; CPA Briefing Sheet",
        "glossary.html": "Terms",
        "suggestions.html": "Suggestions",
        "questions.html": "Questions and information gaps",
        "estate-tax.html": "Estate tax",
        "income-basis.html": "Income-tax basis",
        "property-tax.html": "Property-tax assessment",
        "blackswan.html": "Black swan",
        "timeline.html": "Deadlines timeline",
        "sources.html": "Sources",
    }
    for filename, phrase in required_pages.items():
        path = os.path.join(ROOT, filename)
        if not os.path.isfile(path):
            bad(f"required page missing: {filename}")
        else:
            with open(path, encoding="utf-8", errors="replace") as handle:
                if phrase not in handle.read():
                    bad(f"required dashboard content missing from {filename}")

    flagged_path = os.path.join(ROOT, "flagged.html")
    if os.path.isfile(flagged_path):
        with open(flagged_path, encoding="utf-8", errors="replace") as handle:
            if "Pages containment does not purge Git history" not in handle.read():
                bad("privacy/history limitation is missing from flagged.html")

    irregularities_path = os.path.join(ROOT, "data", "irregularities.json")
    if not os.path.isfile(irregularities_path):
        bad("data/irregularities.json missing")
    else:
        try:
            with open(irregularities_path, encoding="utf-8") as handle:
                count = len(json.load(handle))
            ok(f"irregularities register present ({count} items)")
        except (OSError, json.JSONDecodeError, TypeError):
            bad("data/irregularities.json could not be parsed")


def check_public_surface():
    files = list(public_files())
    if not files:
        bad("no public Pages files found in the root output surface")
        return
    check_public_identifiers()
    check_jekyll_boundary()
    check_rounding()
    check_pdf_export()
    check_html()
    check_required_content()


def finish(public_only, exact_comparison_ran):
    for line in LOG:
        print(line)
    if FAIL:
        print(f"\n{len(FAIL)} check(s) failed. "
              + ("Public-only verification failed." if public_only else "Strict mode failed closed."))
        return 1
    if public_only:
        print("\nPublic-only checks passed. Exact private-value comparison was skipped; this is not privacy clearance.")
    elif exact_comparison_ran:
        print("\nStrict checks passed. No exact private-value patterns were found; this does not prove anonymity.")
    else:
        print("\nStrict checks did not run the required private comparison; the result is not release-cleared.")
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the public dashboard and repository privacy boundary.")
    parser.add_argument(
        "--public-only", action="store_true",
        help="skip exact private-input comparison; run non-private repository and public Pages checks",
    )
    args = parser.parse_args(argv)

    private_raw = None
    exact_comparison_ran = False
    if not args.public_only:
        if not os.path.isfile(PRIVATE):
            bad("private/raw_inputs.json is absent; strict household-data comparison cannot run (keep this file local and ignored)")
        else:
            try:
                with open(PRIVATE, encoding="utf-8") as handle:
                    private_raw = json.load(handle)
                if not isinstance(private_raw, dict):
                    raise ValueError("invalid inventory shape")
                exact_comparison_ran = True
            except (OSError, json.JSONDecodeError, ValueError) as error:
                # Do not include exception text or parser context; either could contain private content.
                bad(f"private input file could not be read or validated ({type(error).__name__}); strict comparison is incomplete")
                private_raw = None

    check_repository_privacy(private_raw)
    check_public_surface()
    return finish(args.public_only, exact_comparison_ran)


if __name__ == "__main__":
    sys.exit(main())
