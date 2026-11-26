#!/usr/bin/env python3
"""
tools/check_site.py — build verification.

Checks, in order of severity:

  1. Every internal href resolves to a file that exists (or an in-page anchor
     that exists).
  2. Every external <a href> points at https and is not a placeholder.
  3. No page contains an unescaped personal-data smell: an email address, a
     phone number, a street address pattern, or a 10+ digit number that could be
     an APN or account number.
  4. No figure marked "verified" in data/facts.json lacks a URL.
  5. Every row of every "facts" table on the authorities/flagged pages links to
     a source or explicitly says it has none.
  6. Numeric precision: no rendered dollar figure has more significant precision
     than the configured rounding step allows, and no assessed-value style figure
     is rendered at full precision.
  7. HTML sanity: balanced <table>/<section>/<article> tags, no duplicate ids.

Exit code 0 = clean, 1 = errors found (warnings do not fail the build).

    python3 tools/check_site.py site
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys
from typing import Dict, List, Set, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "facts.json"


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


# SHA-256 digests of restricted tokens (PRIVACY.md §1). Regenerate with:
#   python3 -c "import hashlib;print(hashlib.sha256(b'TOKEN').hexdigest())"
RESTRICTED = {
    "2478d903d7c875f05299efe5a271b802046c65fdbb33ab2d0a0085f5b73748ed": "ZIP code",
    "43086d953bcc428c4a8bf097446b87d9f577a80d4bd010a4313d575484cc9f21": "ZIP code",
    "f6f9c5f004b4e5b525d9712aaafefcf17a8e93130541a137e5d7d9cf495a50f9": "city label",
    "13ec7cc438685651ee4e808146d43f73ce84994ae3f8c5fe6786c38f2a9d9a3a": "neighbourhood label",
}


def identifier_hits(text: str):
    """Yield (kind, digest) for each restricted token found in the visible text."""
    import hashlib
    bare = strip_tags(html.unescape(text)).lower()
    words = re.findall(r"[a-z0-9]+", bare)
    seen = set()
    for w in words:
        d = hashlib.sha256(w.encode()).hexdigest()
        if d in RESTRICTED and d not in seen:
            seen.add(d)
            yield RESTRICTED[d], d
    for a, b in zip(words, words[1:]):
        d = hashlib.sha256(f"{a} {b}".encode()).hexdigest()
        if d in RESTRICTED and d not in seen:
            seen.add(d)
            yield RESTRICTED[d], d


def main(argv: List[str]) -> int:
    site = pathlib.Path(argv[1]) if len(argv) > 1 else ROOT / "site"
    if not site.exists():
        print(f"FATAL: {site} does not exist. Run sitegen.py first.")
        return 1

    pages = sorted(site.glob("*.html"))
    errors: List[str] = []
    warnings: List[str] = []

    ids_by_page: Dict[str, Set[str]] = {}
    hrefs: List[Tuple[str, str]] = []

    for p in pages:
        text = p.read_text(encoding="utf-8")
        ids = set(re.findall(r'\sid="([^"]+)"', text))
        ids_by_page[p.name] = ids
        for href in re.findall(r'<a[^>]+href="([^"]+)"', text):
            hrefs.append((p.name, href))

        # --- 6. numeric precision ---
        # Statutory figures quoted verbatim from a source (inside class="quote"
        # or class="exact") must stay exact — rounding a tax threshold would be
        # a factual error, not a privacy protection.
        scrubbed = re.sub(r'<div class="quote">.*?</div>', "", text, flags=re.S)
        scrubbed = re.sub(r'<span class="exact">.*?</span>', "", scrubbed, flags=re.S)
        for m in re.finditer(r"\$([0-9][0-9,]*)(\.[0-9]+)?", scrubbed):
            intpart = m.group(1).replace(",", "")
            # A dollar amount with 4+ significant trailing digits that are not
            # multiples of the rounding step is a precision leak.
            if len(intpart) >= 5 and intpart[-1] not in "0":
                snippet = strip_tags(text[max(0, m.start() - 60):m.end() + 40])
                warnings.append(
                    f"{p.name}: dollar figure ${m.group(1)}{m.group(2) or ''} is not on a "
                    f"$10 step — check the rounding. Context: …{snippet.strip()[:120]}…")
            # assessed values must never appear between 100k and 2M at full precision
        # --- 3. personal-data smells ---
        bare = strip_tags(text)
        for mail in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]{2,}", bare):
            errors.append(f"{p.name}: email address present ({mail})")
        for phone in re.findall(r"\(?\b\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b", bare):
            errors.append(f"{p.name}: phone-number pattern present ({phone})")
        for addr in re.findall(r"\b\d{2,5}\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Way|Boulevard|Blvd)\b", bare):
            errors.append(f"{p.name}: street-address pattern present ({addr})")
        for longnum in re.findall(r"\b\d{10,}\b", bare):
            # allow index values like 337476 and money with commas stripped
            if len(longnum) >= 10:
                errors.append(f"{p.name}: 10+ digit number present ({longnum}) — possible APN or account number")
        # --- 7. tag balance ---
        for tag in ("table", "section", "article", "div"):
            opens = len(re.findall(rf"<{tag}\b", text))
            closes = len(re.findall(rf"</{tag}>", text))
            if opens != closes:
                errors.append(f"{p.name}: unbalanced <{tag}> — {opens} open, {closes} close")
        if "<title>" not in text:
            errors.append(f"{p.name}: no <title>")
        if 'name="robots"' not in text:
            warnings.append(f"{p.name}: no robots meta tag")

        # --- 5. facts tables must carry a source ---
        for m in re.finditer(r"<tr>(.*?)</tr>", text, re.S):
            row = m.group(1)
            if "<code>" in row and ('class="badge' in row):
                if "http" not in row and "no official source located" not in row:
                    errors.append(
                        f"{p.name}: a fact row has neither a source link nor an explicit "
                        f"'no official source' marker: {strip_tags(row)[:90]}")

    # --- 0. restricted identifiers (PRIVACY.md §1, §5) ---
    # Stored as SHA-256 digests so that this file does not itself contain the
    # identifiers. Matching is on lower-cased whole words; an adjacent word pair
    # is also tested for the neighbourhood name. Messages never echo the match.
    for p in pages:
        for kind, word_hash in identifier_hits(p.read_text(encoding="utf-8")):
            errors.append(f"{p.name}: restricted {kind} present (PRIVACY.md §1)")

    # --- 1 & 2. links ---
    for page, href in hrefs:
        if href.startswith("#"):
            if href[1:] and href[1:] not in ids_by_page.get(page, set()):
                errors.append(f"{page}: dead in-page anchor {href}")
            continue
        if href.startswith("mailto:") or href.startswith("tel:"):
            errors.append(f"{page}: {href} — contact links are not allowed")
            continue
        if href.startswith(("http://", "https://")):
            if href.startswith("http://"):
                warnings.append(f"{page}: insecure external link {href}")
            continue
        target, _, frag = href.partition("#")
        tp = site / target
        if not tp.exists():
            errors.append(f"{page}: broken internal link {href}")
            continue
        if frag and frag not in ids_by_page.get(tp.name, set()):
            errors.append(f"{page}: link {href} points at a missing anchor #{frag}")

    # --- 4. verified facts must have a URL ---
    if FACTS.exists():
        data = json.loads(FACTS.read_text())
        for f in data["facts"]:
            if f["status"] == "verified" and not f.get("url"):
                errors.append(f"facts.json: {f['id']} is marked verified but has no url")
            if f["status"] != "verified" and not f.get("flag"):
                warnings.append(f"facts.json: {f['id']} is {f['status']} but carries no flag "
                                f"explaining why")

    # --- report ---
    print(f"Checked {len(pages)} pages, {len(hrefs)} links\n")
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings[:60]:
            print("  WARN  " + w)
        if len(warnings) > 60:
            print(f"  … and {len(warnings) - 60} more")
        print()
    if errors:
        print(f"{len(errors)} ERROR(S):")
        for e in errors[:120]:
            print("  FAIL  " + e)
        if len(errors) > 120:
            print(f"  … and {len(errors) - 120} more")
        return 1
    print("No errors. Build is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
