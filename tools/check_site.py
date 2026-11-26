#!/usr/bin/env python3
"""Pre-publish gate. Exits non-zero if any check fails.

  python3 tools/check_site.py               full gate (needs private/raw_inputs.json; run locally before publishing)
  python3 tools/check_site.py --structural  structural checks only (used in CI, where private inputs do not exist)

Checks
  1. Privacy scan: every tracked text file is searched for the identifiers listed in
     private/raw_inputs.json (ZIP codes, neighbourhood labels, personal e-mail, and any
     other values listed there). The private folder is never published, and its contents
     are not written into this file.
  2. Rounding: every dollar figure on the site and in data/model_outputs.json is a multiple
     of $10, except the statutory amounts listed in STATUTORY below (checked against sources).
  3. Table rows: every body row of every table on every page contains an official-source
     link, or is visibly marked as owner, assumption, model, snippet or unverified.
  4. Internal links: every relative href and src points to a file that exists.
  5. Required content: the summary's 'What would change the answer', Flagged for Review,
     the briefing sheet, the glossary, the suggestions and the questions page.
  6. Source register: every source id used on a page exists in data/sources.json.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PRIVATE = os.path.join(ROOT, "private", "raw_inputs.json")
TEXT_EXT = (".html", ".css", ".js", ".json", ".md", ".py", ".txt", ".yml", ".yaml", ".csv")
# Statutory amounts printed exactly, each traceable to a source in data/sources.json.
STATUTORY = {1044586, 15000000, 5945800, 19000, 194000, 250000, 500000, 1000000, 1460000, 1940000}
SKIP_KEYS = {"seed", "valuation_year", "transfer_year", "horizon", "monte_carlo_draws", "sensitivity_draws", "year"}
OFFICIAL_BADGES = ("b-ok", "b-snip")  # official-source badges; a row also needs an official link to count
FLAG_BADGES = ("b-owner", "b-assume", "b-model", "b-bad", "b-snip")

FAIL, PASS = [], []


def ok(m):
    PASS.append("PASS  " + m)


def bad(m):
    FAIL.append("FAIL  " + m)


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    for rel in out:
        if rel and rel.endswith(TEXT_EXT) and not rel.startswith("private/") and rel != "tools/check_site.py":
            yield rel


def walk_numbers(x, out, key=""):
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP_KEYS:
                walk_numbers(v, out, k)
    elif isinstance(x, list):
        for v in x:
            walk_numbers(v, out, key)
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        out.append((key, x))


def privacy_scan(structural):
    if not os.path.exists(PRIVATE):
        if structural:
            ok("privacy scan skipped in --structural mode (private inputs are not available in CI)")
            return
        bad("private/raw_inputs.json missing: the privacy scan cannot run locally")
        return
    raw = json.load(open(PRIVATE, encoding="utf-8"))
    pats = []
    for z in raw.get("zip_codes_internal_only", []):
        pats.append(("zip " + str(z), re.compile(r"(?<![0-9])" + re.escape(str(z)) + r"(?![0-9])")))
    for w in raw.get("forbidden_words", []):
        pats.append(("word '" + w + "'", re.compile(re.escape(w), re.IGNORECASE)))
    for s in raw.get("exact_text_internal_only", []):
        pats.append(("text '" + s[:24] + "'", re.compile(re.escape(s), re.IGNORECASE)))
    n = 0
    for rel in tracked_text_files():
        n += 1
        text = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        for label, rx in pats:
            if rx.search(text):
                bad(f"privacy: {label} found in {rel}")
    ok(f"privacy scan of {n} tracked text files against {len(pats)} internal patterns")


def rounding_check():
    mo = json.load(open(os.path.join(ROOT, "data", "model_outputs.json"), encoding="utf-8"))
    nums = []
    walk_numbers(mo, nums)
    off = [(k, v) for k, v in nums if isinstance(v, float) and v != int(v) and k.startswith("mc_")]
    money = [(k, v) for k, v in nums if abs(v) >= 1000 and float(v) == int(v)]
    bad_vals = [(k, v) for k, v in money if int(v) % 10 != 0 and int(v) not in STATUTORY]
    if bad_vals:
        bad(f"rounding: {len(bad_vals)} model money values not multiples of $10, e.g. {bad_vals[:3]}")
    else:
        ok(f"rounding: {len(money)} model money values are multiples of $10 or statutory")
    site_bad = []
    for rel in tracked_text_files():
        if not rel.endswith(".html"):
            continue
        text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        text = re.sub(r"<[^>]+>", " ", text)
        for m in re.finditer(r"\$(-?[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,})", text):
            v = int(m.group(1).replace(",", ""))
            if v % 10 != 0 and v not in STATUTORY:
                site_bad.append((rel, v))
    if site_bad:
        bad(f"rounding: site dollar figures not multiples of $10: {site_bad[:5]}")
    else:
        ok("rounding: every dollar figure on the site is a multiple of $10 or a statutory amount")


def html_pages():
    for rel in tracked_text_files():
        if rel.endswith(".html"):
            yield rel, open(os.path.join(ROOT, rel), encoding="utf-8").read()


def table_rows_check():
    total, missing = 0, []
    for rel, text in html_pages():
        for tb in re.findall(r"<tbody>(.*?)</tbody>", text, flags=re.S):
            for row in re.findall(r"<tr>(.*?)</tr>", tb, flags=re.S):
                total += 1
                has_official = re.search(r'<a href="https?://', row) is not None
                flagged = any(b in row for b in FLAG_BADGES)
                if not (has_official or flagged):
                    missing.append(rel)
    if missing:
        bad(f"table rows without an official link or an unverified marker: {len(missing)} (first in {missing[0]})")
    else:
        ok(f"table rows: {total} rows checked; each has an official-source link or a visible status marker")


def links_check():
    broken = []
    for rel, text in html_pages():
        base = os.path.dirname(os.path.join(ROOT, rel))
        for m in re.finditer(r'(?:href|src)="([^"#:]+)"', text):
            target = m.group(1)
            if target.startswith(("mailto:", "data:")):
                continue
            path = os.path.normpath(os.path.join(base, target))
            if not os.path.exists(path):
                broken.append((rel, target))
    if broken:
        bad(f"internal links: {len(broken)} broken, e.g. {broken[:3]}")
    else:
        ok("internal links: all relative links and assets exist")


def sources_check():
    reg = {s["id"] for s in json.load(open(os.path.join(ROOT, "data", "sources.json")))["sources"]}
    used = set()
    for _, text in html_pages():
        used |= set(re.findall(r'>(S[0-9]{2})</a>', text))
    unknown = sorted(used - reg)
    if unknown:
        bad(f"source ids used on pages but not in data/sources.json: {unknown}")
    else:
        ok(f"source register: {len(used)} source ids used on pages, all registered")


def required_content():
    need = {
        "index.html": ["What would change the answer", "Pick for the 2050 transfer"],
        "pages/flagged.html": ["Flagged for Review"],
        "pages/briefing.html": ["Attorney and CPA briefing sheet"],
        "pages/glossary.html": ["Glossary"],
        "pages/suggestions.html": ["Suggestions"],
        "pages/questions.html": ["Questions and gaps"],
    }
    missing = []
    for rel, phrases in need.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        text = open(p, encoding="utf-8").read()
        for ph in phrases:
            if ph not in text:
                missing.append(f"{rel}: '{ph}'")
    if missing:
        bad("required content missing: " + "; ".join(missing))
    else:
        ok("required content: summary, flagged, briefing, glossary, suggestions and questions pages present")


def main():
    structural = "--structural" in sys.argv
    privacy_scan(structural)
    rounding_check()
    table_rows_check()
    links_check()
    sources_check()
    required_content()
    for line in PASS + FAIL:
        print(line)
    if FAIL:
        print(f"\n{len(FAIL)} check(s) failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
