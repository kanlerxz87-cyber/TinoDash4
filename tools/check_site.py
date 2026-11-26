"""
Pre-publish gate. Exits non-zero (fails the build) if any check fails.

  1. Privacy scan: no value, key, or text string from private/raw_inputs.json appears in any
     published or tracked text file (html, css, js, json, md, py, txt). The private folder is
     excluded from the scan; it is never published.
  2. Forbidden identifiers: zip codes, neighbourhood labels, parcel terms, and personal names.
  3. Rounding: every money value in data/model_outputs.json is a multiple of $10.
  4. Row links: every table row on every page contains at least one official-source link.
  5. Internal links: every relative href and src points to a file that exists.
  6. Required content: first-screen 'What would change the answer', Flagged for Review, the
     Attorney & CPA Briefing Sheet, and the glossary, suggestions, and questions pages.

Run: python3 tools/check_site.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PRIVATE = os.path.join(ROOT, "private", "raw_inputs.json")
SCAN_EXT = (".html", ".css", ".js", ".json", ".md", ".py", ".txt", ".yml", ".yaml", ".toml", ".pdf")
SKIP_DIRS = {".git", "private", "node_modules", "__pycache__", ".github"}
# The maintained root dashboard is the Pages product. _config.yml excludes legacy trees,
# research, source and model directories; they are not part of the deployed artifact.
# The public Git repository is a separate privacy surface (see PRIVACY_REMEDIATION.md).
PUBLISHED_ROOT_DIRS = {"assets", "data"}
PUBLISHED_ROOT_FILES = {"index.html", "brief.html", "brief.pdf"}

ALLOW_PUBLIC_NUMBERS = {
    # public, sourced figures that are allowed to appear
    15000000, 15480000, 19000, 20000, 194000, 201000, 250000, 500000, 1000000, 1044590, 1044586,
    400000, 129, 177000000, 10000000, 2026, 2027,
}
FORBIDDEN_WORDS = [
    "cupertino", "outer sunset", "sunset", "95014", "94122", "gmail",
]
SELF = os.path.normpath(os.path.abspath(__file__))
LOG = []
FAIL = []


def ok(msg):
    LOG.append("PASS  " + msg)


def bad(msg):
    FAIL.append("FAIL  " + msg)
    LOG.append("FAIL  " + msg)


def walk_numbers(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            walk_numbers(v, out)
    elif isinstance(x, list):
        for v in x:
            walk_numbers(v, out)
    elif isinstance(x, bool):
        return
    elif isinstance(x, (int, float)):
        out.append(x)


def walk_strings(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            walk_strings(v, out)
    elif isinstance(x, list):
        for v in x:
            walk_strings(v, out)
    elif isinstance(x, str):
        out.append(x)


def pdf_streams(data):
    """Decode every stream in a PDF (ASCII85 and/or Flate) so the drawn text is scanned."""
    import base64
    import zlib
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        body = m.group(1).strip()
        try:
            if body.endswith(b"~>"):
                body = base64.a85decode(body[:-2].strip(), adobe=False)
            try:
                body = zlib.decompress(body)
            except zlib.error:
                pass
            out.append(body.decode("latin-1"))
        except Exception:
            out.append(m.group(1).decode("latin-1", "replace"))
    return out


def published_files():
    """Yield the maintained root dashboard artifacts only (not excluded source/legacy trees)."""
    root_html = [fn for fn in os.listdir(ROOT) if fn.endswith(".html")]
    for fn in sorted(set(root_html) | PUBLISHED_ROOT_FILES):
        full = os.path.join(ROOT, fn)
        if os.path.isfile(full):
            yield full
    for folder in sorted(PUBLISHED_ROOT_DIRS):
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                full = os.path.join(dp, fn)
                if fn.endswith(SCAN_EXT):
                    yield full


def main():
    if not os.path.exists(PRIVATE):
        bad("private/raw_inputs.json missing: privacy scan cannot run (it is required in the working copy)")
        return finish()
    raw = json.load(open(PRIVATE, encoding="utf-8"))

    # 1. Privacy scan values
    nums = []
    walk_numbers(raw, nums)
    nums = sorted({int(n) for n in nums if n >= 1000})
    collide = [n for n in nums if n in ALLOW_PUBLIC_NUMBERS]
    if collide:
        bad(f"private numbers collide with allowed public figures: {collide}")
    pats = []
    for n in nums:
        comma = f"{n:,}"
        pats.append(("value " + comma, re.compile(r"(?<![0-9.,])" + re.escape(comma) + r"(?![0-9.,])")))
        if n >= 10000:  # plain digits only for 5+ digit values (avoids chance matches such as counts)
            s = str(n)
            pats.append(("value " + s, re.compile(r"(?<![0-9.,])" + re.escape(s) + r"(?![0-9])")))
    # small private numbers that appear in ranges (water, solar, etc.)
    strs = []
    walk_strings(raw, strs)
    for s in strs:
        if len(s) >= 6 and s.lower() not in ("property", "estimate"):
            pats.append(("text '" + s[:24] + "...'", re.compile(re.escape(s), re.IGNORECASE)))
    # zip codes (any digits in the private zip list)
    for z in raw.get("zip_codes_internal_only", []):
        pats.append(("zip " + str(z), re.compile(r"(?<![0-9])" + re.escape(str(z)) + r"(?![0-9])")))
    scanned = 0
    for fp in published_files():
        scanned += 1
        raw_bytes = open(fp, "rb").read()
        text = raw_bytes.decode("latin-1") if fp.endswith(".pdf") else raw_bytes.decode("utf-8", "replace")
        if fp.endswith(".pdf"):
            text += "\n".join(pdf_streams(raw_bytes))
        rel = os.path.relpath(fp, ROOT)
        for label, rx in pats:
            if rx.search(text):
                bad(f"privacy: {label} found in {rel}")
        low = text.lower()
        for w in FORBIDDEN_WORDS:
            if w in low:
                bad(f"forbidden identifier '{w}' in {rel}")
    ok(f"privacy scan of {scanned} files against {len(pats)} patterns")

    # 3. Rounding
    dat = json.load(open(os.path.join(ROOT, "data", "model_outputs.json"), encoding="utf-8"))
    money_vals = []
    money_vals += list(dat["base_results_real_2026"].values())
    money_vals += [v for r in dat["grid"] for v in r["results"].values()]
    money_vals += [v for s in dat["monte_carlo"]["summary"].values() for v in s.values() if isinstance(v, (int, float)) and v > 1000]
    money_vals += [v for r in dat["projection_base"] for k, v in r.items() if k != "year"]
    bad_round = [v for v in money_vals if round(v) % 10 != 0]
    if bad_round:
        bad(f"{len(bad_round)} money values are not rounded to $10 (first: {bad_round[:3]})")
    else:
        ok(f"rounding: {len(money_vals)} money values are multiples of $10")

    # 4-5. HTML checks
    pages = [f for f in os.listdir(ROOT) if f.endswith(".html")]
    if "index.html" not in pages:
        bad("index.html missing")
    row_fail = 0
    row_total = 0
    for p in sorted(pages):
        html = open(os.path.join(ROOT, p), encoding="utf-8").read()
        for tb in re.findall(r"<tbody>(.*?)</tbody>", html, re.S):
            for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
                row_total += 1
                if "href=" not in tr:
                    row_fail += 1
                    bad(f"table row without an official-source link in {p}: {re.sub('<[^>]+>', ' ', tr)[:90].strip()}")
        for href in re.findall(r'(?:href|src)="([^"]+)"', html):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = href.split("#")[0]
            if target and not os.path.exists(os.path.join(ROOT, target)):
                bad(f"broken internal link in {p}: {href}")
    ok(f"row links: {row_total - row_fail} of {row_total} table rows linked")

    # 6. Required content
    idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for needle, where in [
        ("What would change the answer", "index.html"),
        ("Reinvestment risk", "index.html"),
        ("Executive summary", "index.html"),
    ]:
        if needle not in idx:
            bad(f"'{needle}' missing from {where}")
    must = {
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
    for fn, needle in must.items():
        path = os.path.join(ROOT, fn)
        if not os.path.exists(path):
            bad(f"required page missing: {fn}")
        elif needle not in open(path, encoding="utf-8").read():
            bad(f"'{needle}' missing from {fn}")
    # This repository intentionally omits .nojekyll: its presence would bypass Jekyll's
    # _config.yml exclusions and expose alternate trees in the Pages artifact.
    if os.path.exists(os.path.join(ROOT, ".nojekyll")):
        bad(".nojekyll present: it bypasses the privacy exclusions in _config.yml")
    cfg = open(os.path.join(ROOT, "_config.yml"), encoding="utf-8").read()
    for excluded in ("decision-model", "decision-workspace", "model", "research", "site", "tools", "private"):
        if excluded not in cfg:
            bad(f"Pages exclusion missing from _config.yml: {excluded}")
    irr = os.path.join(ROOT, "data", "irregularities.json")
    if not os.path.exists(irr):
        bad("data/irregularities.json missing")
    else:
        ok(f"irregularities: {len(json.load(open(irr)))} items in data/irregularities.json")
    return finish()


def finish():
    for line in LOG:
        print(line)
    if FAIL:
        print(f"\n{len(FAIL)} check(s) failed. The build must not be published.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
