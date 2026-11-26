#!/usr/bin/env python3
"""Builds the static decision site served by GitHub Pages from the repository root.

Reads (all public, all figures rounded to the nearest $10 or statutory), under dashboard/:
    private/dashboard_inputs.json  owner-supplied property figures (rounded to $10; gitignored)
    data/sources.json         source register (S01-S23) with status
    data/model_outputs.json   results from tools/model.py
Writes:
    dashboard/index.html, dashboard/pages/*.html, dashboard/assets/site.css, dashboard/assets/site.js

Run:  python3 tools/dashboard_model.py  then  python3 tools/dashboard_build.py  then  python3 tools/dashboard_check.py --structural
Every table row is built from these files; no figure is typed in by hand except
statutory amounts, which are checked against the source register.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
INP = json.loads((ROOT / "private/dashboard_inputs.json").read_text())  # owner figures: private, never published
SRC_LIST = json.loads((DASH / "data/sources.json").read_text())["sources"]
SRC = {s["id"]: s for s in SRC_LIST}
MO = json.loads((DASH / "data/model_outputs.json").read_text())
ACCESSED = "2026-11-26"
PICK_KEYS = ["2040_10", "2040_20", "2050_10", "2050_20"]
PATH_ORDER = ["LIVE", "RENT", "SELL_LUMP", "SELL_P24", "SELL_P36", "LIVE3_SELL", "RENT3_SELL", "LIVE3_RENT"]
PATH_SHORT = {
    "LIVE": "Live in A", "RENT": "Rent A", "SELL_LUMP": "Sell, lump sum",
    "SELL_P24": "Sell, park 24 months, phase in over 12", "SELL_P36": "Sell, park 36 months, phase in over 12",
    "LIVE3_SELL": "Mixed: live 3 years, then sell", "RENT3_SELL": "Mixed: rent 3 years, then sell",
    "LIVE3_RENT": "Mixed: live 3 years, then rent",
}
GROUPS = [
    ("Start", [("Home and decision summary", "index.html")]),
    ("Decision", [("Paths compared", "pages/paths.html"), ("Rules and pick", "pages/decision.html"),
                  ("What-if and sensitivity", "pages/what-if.html"), ("Decision log", "pages/decision-log.html")]),
    ("Money", [("Projections", "pages/projections.html"), ("Black-swan scenarios", "pages/black-swan.html"),
               ("Phased investing and reinvestment", "pages/phased-investing.html")]),
    ("Properties", [("Property A (inherited)", "pages/property-a.html"), ("Property B (owned)", "pages/property-b.html"),
                    ("Estate inventory (structure)", "pages/inventory.html")]),
    ("Tax and law", [("Federal, state and local rules", "pages/tax-law.html"),
                     ("Legislation: enacted vs proposed", "pages/legislation.html"),
                     ("Inheritance steps and timeline", "pages/process-timeline.html")]),
    ("Review", [("Questions and gaps", "pages/questions.html"), ("Suggestions", "pages/suggestions.html"),
                ("Flagged for Review", "pages/flagged.html"), ("Sources", "pages/sources.html"),
                ("Glossary", "pages/glossary.html"), ("Method and privacy", "pages/method.html")]),
    ("Attorney and CPA", [("One-page briefing sheet", "pages/briefing.html")]),
]


def e(x):
    return html.escape("" if x is None else str(x))


def usd(v):
    if v is None:
        return "not verified"
    return ("-$" if v < 0 else "$") + f"{abs(v):,.0f}"


def pct(x, dp=2):
    return "not reached" if x is None else f"{x:.{dp}f}%"


STATUS = {
    "fetched": ("b-ok", "Official, read in full"),
    "statute": ("b-ok", "Enacted law (official source)"),
    "partial": ("b-snip", "Official, partly read"),
    "snippet": ("b-snip", "Official, snippet only"),
    "academic": ("b-snip", "Academic dataset"),
    "owner": ("b-owner", "Owner record, not verified"),
    "assumption": ("b-assume", "Assumption"),
    "model": ("b-model", "Model output"),
    "unverified": ("b-bad", "Unverified"),
    "internal": ("b-model", "Decision item (no figure)"),
}


def badge(status):
    cls, label = STATUS[status]
    return f'<span class="badge {cls}">{e(label)}</span>'


def srcl(ids):
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a href="{e(s["url"])}" title="{e(s["publisher"])}: {e(s["title"])}">{e(i)}</a>')
    return " ".join(out)


FIG_RE = re.compile(r"[$%]\s*\d|\d\s*%|\$\d")
LABEL_WORDS = ("assumption", "owner", "stress", "model output", "placeholder")


def _is_figure(text):
    return bool(FIG_RE.search(text)) and len(text) <= 40


def table(headers, rows, cls="", marker="internal"):
    """Every row must be sourced (official link) or labelled (owner record, assumption, model output).
    A row with neither gets an 'Unverified' badge, and any figure in it is blanked (never inferred).
    Text-only rows without a link keep their text with a neutral 'Decision item' badge."""
    h = "".join(f"<th>{e(x)}</th>" for x in headers)
    fixed = []
    for r in rows:
        r = list(r)
        joined = " ".join(str(c) for c in r)
        has_link = '<a href="http' in joined
        has_badge = any(b in joined for b in ("b-owner", "b-assume", "b-bad", "b-model", "b-snip"))
        labelled = any(w in joined.lower() for w in LABEL_WORDS)
        if has_link or has_badge:
            fixed.append(r)
            continue
        if labelled:
            low = joined.lower()
            if "placeholder" in low:
                kind = "unverified"
            elif "owner" in low:
                kind = "owner"
            elif "model output" in low:
                kind = "model"
            else:
                kind = "assumption"
            r[0] = badge(kind) + " " + str(r[0])
            fixed.append(r)
            continue
        figs = [i for i, c in enumerate(r) if i > 0 and _is_figure(re.sub(r"<[^>]+>", "", str(c)).strip())]
        if figs:
            for i in figs:
                r[i] = "<em>blank: not verified</em>"
            r[0] = badge("unverified") + " " + str(r[0])
        else:
            r[0] = badge(marker) + " " + str(r[0])
        fixed.append(r)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in fixed)
    return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{h}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def page(path, title, body, desc="", print_mode=False):
    prefix = "../" * path.count("/")
    nav = []
    for gname, items in GROUPS:
        links = []
        for label, target in items:
            cur = ' aria-current="page"' if target == path else ""
            links.append(f'<a href="{prefix}{target}"{cur}>{e(label)}</a>')
        nav.append(f'<div class="navgroup"><div class="navhead">{e(gname)}</div>{"".join(links)}</div>')
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{e(title)} | Inherited-home decision dashboard</title>"
            f'<meta name="description" content="{e(desc)}">'
            f'<link rel="stylesheet" href="{prefix}assets/site.css"></head>')
    if print_mode:
        doc = f'{head}<body class="print"><main class="sheetwrap">{body}</main></body></html>'
    else:
        doc = (f'{head}<body><header class="top"><a class="brand" href="{prefix}index.html">'
               f'Inherited-home decision dashboard</a><span class="privacy">No addresses, ZIP codes or '
               f'account numbers. Dollar figures rounded to $10.</span></header>'
               f'<div class="layout"><nav class="side" aria-label="Site menu">{"".join(nav)}</nav>'
               f'<main class="content">{body}<footer>Not legal or tax advice. Results depend on owner '
               f'estimates and the stated assumptions. Built {ACCESSED}.</footer></main></div>'
               f'<script src="{prefix}assets/site.js"></script></body></html>')
    out = DASH / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")


# ---------- numbers used on several pages (all computed) ----------

R50 = MO["results"]["2050_20"]["paths"]
PICK50 = MO["picks"]["2050_20"]["choice"]
BE = MO["breakeven"]["2050_20"]
A_HIST = INP["property_a"]["history"]
B_HIST = INP["property_b"]["history"]
A_RATE = A_HIST[1]["tax"] / A_HIST[1]["assessed"] * 100
B_RATE = B_HIST[0]["tax"] / B_HIST[0]["assessed"] * 100
STAT_B = 1.18162182
REF_A = 1.04120   # FY 2024-25 total for a published reference rate area (S11 snippet); parcel's own area unknown
PROP19 = 1044586  # BOE LTA 2025/009 (S03), statutory, printed exactly
SAVE = sum(r["a_tax_full_reassessment"] - r["a_tax_live_prop19"] for r in MO["projections"] if 2040 <= r["year"] <= 2060)
CHG = lambda a, b: (a - b) / b * 100


def picks_table():
    rows = []
    for k in PICK_KEYS:
        T, H = k.split("_")
        p = MO["picks"][k]
        rows.append([f"Transfer {T}, {H} years", f"<strong>{e(PATH_SHORT[p['choice']])}</strong>",
                     usd(MO["results"][k]["paths"][p["choice"]]["mc_fin"]["median"]),
                     e(PATH_SHORT[p["unconstrained_leader"]]),
                     "No" if not MO["sensitivity"]["moved_variants"] else "Yes (see What-if)",
                     srcl(["S03", "S17", "S23"])])
    return table(["Case", "Pick under the written rules", "Median, real, of the pick",
                  "Highest median with no rules applied", "Pick changes in any sensitivity?", "Sources"], rows)


def p_index():
    pk = R50[PICK50]
    p24 = R50["SELL_P24"]
    body = f"""
<h1>Inherited-home decision dashboard</h1>
<p class="lede">Property A is a single-family house in Santa Clara County that the heir expects to inherit through a trust, around 2040 to 2050. Property B is a three-unit building in San Francisco County that the heir already owns. This site compares eight paths for Property A at identical transfer years and horizons, with taxes, debt, occupancy, capital costs, liquidity and reinvestment risk.</p>

<section class="card first" aria-label="Summary">
<h2>What would change the answer</h2>
<ol class="changes">
<li><strong>A written commitment by the heir to live in A within 12 months.</strong> Until it exists, Rule 3 removes the living paths. Even with it, living matches a lump-sum sale only if the imputed rent yield is about {pct(BE['live_rent_yield']*100,1)} of value a year (base assumption 3.75%) or if home values grow about {pct(BE['live_hpa']*100,1)} a year (base 2.3%).</li>
<li><strong>Three verified rental comparables for A.</strong> Until they exist, Rule 4 keeps the rent paths as a floor only. A rent path matches a lump-sum sale only at a gross yield of about {pct(MO['breakeven']['2050_10']['rent_rent_yield']*100,1)} in the 10-year cases, and not within 20% in the 20-year cases (outside the range tested).</li>
<li><strong>Tax-rate area and bills for A.</strong> The owner's billed rate is {pct(A_RATE,2)} of assessed value; the reference rate area used here is {pct(REF_A,2)} (FY 2024-25). The parcel's own rate area is unknown. The model uses the billed rate. When the reference rate is used instead, the pick does not change (see What-if).</li>
<li><strong>Equity returns.</strong> If equities return 5% a year instead of the historical {MO['assumptions']['equity_geo_mean_1928_2025_pct']:.2f}%, the pick does not change in any of the four cases (see What-if).</li>
<li><strong>The Proposition 19 allowance.</strong> The statutory amount of {usd(PROP19)} applies to transfers up to 15 February 2027. The next adjustment is due 16 February 2027 (BOE LTA 2025/009). A change would re-open the living case.</li>
<li><strong>Other estate assets above the federal exclusion.</strong> Known real estate is about {usd(MO['estate']['known_real_estate_owner_estimates'])} (owner estimates). The federal basic exclusion is $15,000,000 for 2026, so estate tax is not modelled unless the total estate is verified above that amount (Rule 7).</li>
</ol>
</section>

<section class="card" aria-label="Headline">
<h2>Pick for the 2050 transfer, 20-year horizon</h2>
<p><strong>Pick under the rules written on 25 November 2026, before any output existed: {e(PATH_SHORT[PICK50])}.</strong>
Median real financial position at the horizon: <strong>{usd(pk['mc_fin']['median'])}</strong> (10th percentile {usd(pk['mc_fin']['p10'])}, 90th percentile {usd(pk['mc_fin']['p90'])}).
The phased path (park 24 months, then phase in) has a median of {usd(p24['mc_fin']['median'])}, which is {pct(abs(CHG(p24['mc_fin']['median'], pk['mc_fin']['median'])),1)} below the pick, outside the 5% band in Rule 5. Under a repeat of the 1929-type crash, the pick gives {usd(pk['bs1929'])} and the 24-month phased path gives {usd(p24['bs1929'])}; see <a href="pages/phased-investing.html">phased investing</a>.</p>
<p class="small">This is a comparison of stated assumptions. It is not a forecast and not advice.</p>
</section>

<section class="card" aria-label="Picks by case">
<h2>Pick by case</h2>
{picks_table()}
<p class="small">In every case the lump-sum sale is both the pick under the rules and the highest median with no rules applied. Both phased paths fail the Rule 5 median test in all four cases. The three living paths are removed by Rule 3, and the two rent-based paths by Rule 4, until the household supplies a commitment and comparables.</p>
</section>

<section class="card" aria-label="Start here">
<h2>Start here</h2>
<div class="grid3">
<a class="tile" href="pages/paths.html"><strong>Paths compared</strong><span>Eight paths at the same transfer years and horizons.</span></a>
<a class="tile" href="pages/decision.html"><strong>Rules and pick</strong><span>The written criteria and how each path was tested.</span></a>
<a class="tile" href="pages/property-a.html"><strong>Property A</strong><span>Assessment, tax history, Proposition 19 and costs.</span></a>
<a class="tile" href="pages/property-b.html"><strong>Property B</strong><span>Rent, costs, tax history and depreciation.</span></a>
<a class="tile" href="pages/process-timeline.html"><strong>Steps and deadlines</strong><span>The inheritance steps and the timeline.</span></a>
<a class="tile" href="pages/flagged.html"><strong>Flagged for Review</strong><span>Everything that is unverified, corrected or unreconciled.</span></a>
<a class="tile" href="pages/questions.html"><strong>Questions and gaps</strong><span>What is known, what is missing, and how to find out.</span></a>
<a class="tile" href="pages/suggestions.html"><strong>Suggestions</strong><span>Proposed changes, to review before any is made.</span></a>
<a class="tile" href="pages/briefing.html"><strong>Briefing sheet</strong><span>One page for the attorney and the tax adviser.</span></a>
</div></section>
"""
    page("index.html", "Home", body, "Inherited-home decision dashboard: paths, rules, sources and flags.")


def result_rows(k):
    R = MO["results"][k]["paths"]
    rows = []
    for pid in PATH_ORDER:
        r = R[pid]
        elig = "Eligible" if pid in MO["picks"][k]["eligible"] else "Removed by rule (value shown for reference)"
        imp = usd(r["imputed_real_base"]) if pid.startswith("LIVE") else "not applicable"
        rows.append([
            f"<strong>{e(PATH_SHORT[pid])}</strong><br><span class='small'>{'Pure' if r['pure'] else 'Mixed or phased'}</span>",
            usd(r["mc_fin"]["median"]), usd(r["mc_fin"]["p10"]), usd(r["mc_fin"]["p90"]),
            usd(r["bs1929"]), usd(r["bs2008"]), usd(r["bs1973"]), usd(r["bs2000"]),
            usd(r["stress_eq5"]), usd(r["reinvest_shock"]), imp, elig, srcl(["S03", "S17", "S23"]),
        ])
    return rows


def p_paths():
    hdr = ["Path", "Median (real)", "10th pct", "90th pct", "1929-type crash", "2008-type crash",
           "1973-type stagflation", "2000-type decline", "Equity at 5% a year", "Bills 1% from year 4",
           "Imputed rent (living, not cash)", "Rule status", "Sources"]
    parts = [f"<h3>Transfer {k.split('_')[0]}, horizon {k.split('_')[1]} years</h3>"
             + table(hdr, result_rows(k), cls="wide") for k in PICK_KEYS]
    body = f"""
<h1>Paths compared</h1>
<p>Eight paths for Property A, compared at the same transfer years (2040 and 2050) and horizons (10 and 20 years). Values are the financial position at the end of the horizon, in real dollars (deflated by the 2.3% inflation assumption), rounded to $10. A property still held at the end is valued as if sold then, after selling costs and tax, so the paths are comparable. Property B is held in every path and is left out. Median and percentiles come from {MO['_meta']['monte_carlo_draws']:,} simulated paths (seed {MO['_meta']['seed']}); crash columns replay the historical sequence from that year.</p>
<p class="small">Imputed rent (the rent a living owner does not pay) is not cash, so it is excluded from the financial position used by the rules and shown separately. Mixed and phased paths are listed beside the pure choices.</p>
{''.join(parts)}
<h2>How to read the columns</h2>
<ul>
<li><strong>Bills 1% from year 4:</strong> the same path if T-bill yields fall to 1% from year 4. It shows how much a path depends on the rate earned while cash waits.</li>
<li><strong>Taxes:</strong> property tax on the Proposition 19 or reassessed value, capital-gain tax at sale (basis is the value at death), depreciation recapture for rented paths, and tax on net rental income.</li>
<li><strong>Rule status:</strong> the rules are on the <a href="decision.html">rules page</a>.</li>
</ul>
<p class="small">Sources: {srcl(['S03','S17','S23'])}. Assumptions: <a href="method.html">Method and privacy</a>.</p>
"""
    page("pages/paths.html", "Paths compared", body, "Eight paths for Property A at identical dates and horizons.")


def _rules_section2():
    """Verbatim choice criteria from DECISION_RULES.md section 2 (bold markers removed)."""
    text = (ROOT / "DECISION_RULES.md").read_text(encoding="utf-8")
    sec = text.split("## 2.", 1)[1].split("## 3.", 1)[0]
    out = {}
    for line in sec.splitlines():
        m = re.match(r"^(\d)\. (.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).replace("**", "")
    assert sorted(out) == [str(i) for i in range(1, 9)], "DECISION_RULES.md section 2 must hold rules 1 to 8"
    return out


def p_decision():
    quotes = _rules_section2()
    effect = {
        "1": "Applied to every path.",
        "2": "Applied to the phased paths.",
        "3": "No commitment on file: living paths removed.",
        "4": "None on file: rent paths removed; shown as a floor.",
        "5": "Applied to the phased paths.",
        "6": "No mixed path eligible.",
        "7": "Other estate assets unknown; every result is conditional.",
        "8": "Applied to the phased paths.",
    }
    rules = [[k, quotes[k], effect[k]] for k in sorted(quotes)]
    rr = []
    for k in PICK_KEYS:
        ck = MO["picks"][k]["checks"]
        for pid in ("SELL_P24", "SELL_P36"):
            c = ck[pid]
            rr.append([e(k.replace("_", " / ") + " years"), e(PATH_SHORT[pid]),
                       "pass" if c["guard_rule2"] else "fail", "pass" if c["phase_rule5"] else "fail",
                       "yes" if c["beats_by_more_than_2pct"] else "no", usd(c["median"]),
                       usd(c["worst_black_swan"]), srcl(["S03", "S17"])])
    removed = "".join(f"<li><strong>{e(PATH_SHORT[p])}</strong>: {e(v)}</li>"
                      for p, v in MO["picks"]["2050_20"]["removed"].items())
    body = f"""
<h1>Rules and pick</h1>
<p>The choice rules are those written in the repository file <code>DECISION_RULES.md</code> on 25 November 2026, before any model output was generated. The model applies them mechanically and does not set them. A change must be dated, justified and logged in the <a href="decision-log.html">decision log</a>.</p>
<h2>Rules</h2>
{table(["#", "Rule (as written)", "Status for this household"], rules)}
<h2>Phased paths against the lump-sum sale</h2>
{table(["Case", "Path", "Rule 2 guard", "Rule 5 test", "Beats lump sum by more than 2%?", "Median (real)", "Worst black-swan (real)", "Sources"], rr)}
<h2>Pick and eligibility by case</h2>
{picks_table()}
<h2>Removed by rule (2050 transfer, 20-year horizon)</h2>
<ul>{removed}</ul>
<p class="small">Sources for the rule tests: {srcl(['S03','S17'])}. The rules are the household's own criteria; they are not sourced to any statute.</p>
"""
    page("pages/decision.html", "Rules and pick", body, "Pre-committed choice rules, eligibility and the resulting pick.")


def p_whatif():
    sens = []
    for g in MO["sensitivity"]["grid"]:
        p = g["picks"]["2050_20"]
        sens.append([e(g["label"]), "No" if not g["moved"] else "Yes: " + e(", ".join(g["moved_in"])),
                     e(PATH_SHORT[p["choice"]]), usd(p["median_choice"]), srcl(["S03", "S17", "S23"])])
    data = json.dumps({"rent_yields": MO["whatif"]["rent_yields"], "hpa": MO["whatif"]["hpa"],
                       "cells": MO["whatif"]["cells"]})
    body = f"""
<h1>What-if and sensitivity</h1>
<p>Two views. The first table shows whether the pick moves when one assumption changes. The second is an interactive table of real financial position for the 2050 transfer and 20-year horizon, for a chosen gross rent yield and home-value growth rate. Both are deterministic apart from the historical return draws.</p>
<h2>Does the pick move?</h2>
{table(["Change (one at a time)", "Pick moved?", "Pick (2050, 20 years)", "Median of the pick (real)", "Sources"], sens)}
<h2>Interactive table</h2>
<div class="controls">
<label>Gross rent yield on value <select id="ry"></select></label>
<label>Home-value growth a year <select id="hp"></select></label>
</div>
<div id="whatif-out"></div>
<p class="small">Rent yield and home-value growth are assumptions: no verified comparables and no appraisal. Values are financial positions; imputed rent is not included. Sources: {srcl(['S03','S17','S23'])}.</p>
<script type="application/json" id="whatif-data">{data}</script>
"""
    page("pages/what-if.html", "What-if and sensitivity", body, "Sensitivity of the pick and an interactive what-if table.")


def p_decision_log():
    rows = [
        ["2026-11-25", "Choice rules written (DECISION_RULES.md)", "Adopted as the pre-commitment", "Written before any model output; any change must be dated and logged.", "Repository file"],
        ["2026-11-26", "First model run", "Pick: lump-sum sale in all four cases", "Superseded by the correction below; not published.", "S03, S17"],
        ["2026-11-26", "Model correction (bug)", "Household cash flows now go to the cash account at the bill return", "Before the fix, a living household's running costs compounded at the equity return, overstating them. Living median for 2050/20 moved from -$76,930 (before the fix) to " + usd(MO["results"]["2050_20"]["paths"]["LIVE"]["mc_fin"]["median"]) + ". The pick did not change.", "Repository file (tools/model.py)"],
        ["2026-11-26", "Prop 19 allowance", "Statutory $1,044,586 used exactly", "First run used a rounded placeholder.", srcl(["S03"])],
        ["2026-11-26", "Inflation and bill-return inputs", "2.3% inflation; 3.2% bill return", "Checked against CBO's February 2026 projections; the model holds them flat (see Flagged F-22).", srcl(["S23"])],
        ["2026-11-26", "Repository cleanup for publication", "Earlier site copies and analysis folders removed from the published tree", "They carried ZIP codes, a neighbourhood name and household-level material. Kept locally outside Git; history not rewritten (see Flagged F-14).", "Repository commit"],
        ["Open", "Written occupancy commitment (Rule 3)", "Not decided", "Re-open only with a signed commitment.", "Rule 3"],
        ["Open", "Three rental comparables (Rule 4)", "Not decided", "Re-open only with three verified comparables.", "Rule 4"],
        ["Open", "Phase-in length (Rule 5 wording vs model)", "Not decided", "DECISION_RULES.md section 5 says 24 to 36 months; the model phases in over 12 months. See Flagged F-21.", "Repository file"],
    ]
    body = f"""
<h1>Decision log</h1>
<p>Each decision with its date and reason. Open rows say what would reopen the question.</p>
{table(["Date", "Item", "Decision", "Why", "Source"], rows)}
"""
    page("pages/decision-log.html", "Decision log", body, "Decisions and dates for the inherited-home model.")


def svg_lines(series, w=640, h=260):
    allv = [v for _, _, vals in series for v in vals]
    lo, hi = min(0, min(allv)), max(allv)
    n = len(series[0][2])
    pad = 34
    lines = []
    for label, color, vals in series:
        pts = []
        for i, v in enumerate(vals):
            x = pad + i * (w - 2 * pad) / (n - 1)
            y = h - pad - (h - 2 * pad) * (v - lo) / (hi - lo)
            pts.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(pts)}"/>')
    legend = "".join(f'<text x="{pad + 230*i}" y="16" font-size="12" fill="{c}">{e(l)}</text>'
                     for i, (l, c, _) in enumerate(series))
    return (f'<figure><svg viewBox="0 0 {w} {h}" role="img" aria-label="Projection lines">{legend}'
            f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#666"/>'
            f'<text x="{pad}" y="{h-10}" font-size="11">2026</text><text x="{w-pad-30}" y="{h-10}" font-size="11">2046</text>'
            f'{"".join(lines)}</svg><figcaption>Nominal dollars, rounded to $10.</figcaption></figure>')


def svg_hist(dist, key, color, label):
    d = dist[key]
    counts = d["counts"]
    w, h, pad = 620, 220, 30
    mx = max(counts) or 1
    bw = (w - 2 * pad) / len(counts)
    bars = []
    for i, c in enumerate(counts):
        bh = (h - 2 * pad) * c / mx
        bars.append(f'<rect x="{pad + i*bw:.1f}" y="{h-pad-bh:.1f}" width="{bw-2:.1f}" height="{bh:.1f}" fill="{color}"><title>{c} paths</title></rect>')
    return (f'<figure><svg viewBox="0 0 {w} {h}" role="img" aria-label="Distribution: {e(label)}">'
            f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#666"/>{"".join(bars)}'
            f'<text x="{pad}" y="{h-8}" font-size="11">{usd(d["min"])}</text>'
            f'<text x="{w-pad-90}" y="{h-8}" font-size="11">{usd(d["max"])}</text></svg>'
            f'<figcaption>{e(label)}: {MO["_meta"]["monte_carlo_draws"]:,} simulated paths, 2050 transfer, 20 years, real dollars.</figcaption></figure>')


def p_projections():
    pr = MO["projections"]
    rows = [[e(r["year"]), usd(r["a_value"]), usd(r["a_tax_live_prop19"]), usd(r["a_tax_full_reassessment"]),
             usd(r["a_insurance"]), usd(r["a_water_net_annual"]), usd(r["a_maintenance_at_1pct"]),
             usd(r["b_value"]), usd(r["b_tax_statutory_rate"]), usd(r["b_rent_income_annual"]),
             srcl(["S03", "S12", "S23"])] for r in pr if r["year"] % 5 == 0 or r["year"] in (2026, 2027)]
    body = f"""
<h1>Projections</h1>
<p>Base-case projections, every fifth year. Property A is shown under the Proposition 19 living case and under full reassessment (no exclusion). Property B is shown at the statutory San Francisco secured rate on its assessed value. Nominal dollars, rounded to $10. The 2% a year assessed-value growth cap and 2.3% inflation are assumptions (see <a href="method.html">Method</a>).</p>
<p class="small">Property B's billed tax is {pct(B_RATE,2)} of its assessed value, above the statutory rate of {pct(STAT_B,8)}. The table uses the statutory rate so the figures can be checked; the difference is Flagged F-02.</p>
{svg_lines([("Property A value", "#1b4f8a", [r["a_value"] for r in pr]), ("Property A assessed value under full reassessment", "#b5472f", [r["a_assessed_if_reassessed_2040"] for r in pr])])}
{table(["Year", "A value", "A tax (Prop 19 living)", "A tax (full reassessment)", "A insurance", "A water, net of solar", "A maintenance at 1%", "B value", "B tax (statutory rate)", "B rent (owner figure)", "Sources"], rows, cls="wide")}
<h2>Property tax saved by the living exclusion, 2040 to 2060</h2>
<p>Total difference between full reassessment and the Proposition 19 living case over those 21 years (nominal): <strong>{usd(SAVE)}</strong>. Sources: {srcl(['S03'])}. The living case is modelled as occupancy within one year; the assessed-value formula is flagged for CPA review (F-20).</p>
<h2>Spread of outcomes, 2050 transfer, 20 years</h2>
<div class="grid2">{svg_hist(MO['distribution'], 'SELL_LUMP', '#1b4f8a', 'Sell, lump sum')}{svg_hist(MO['distribution'], 'SELL_P24', '#b5472f', 'Sell, park 24 months, then phase in')}</div>
<p class="small">Sources: {srcl(['S17','S03','S23'])}.</p>
"""
    page("pages/projections.html", "Projections", body, "Year-by-year Property A and B projections.")


def p_black_swan():
    rows = []
    for pid in PATH_ORDER:
        r = R50[pid]
        rows.append([f"<strong>{e(PATH_SHORT[pid])}</strong>", usd(r["bs1929"]), usd(r["bs2008"]), usd(r["bs1973"]),
                     usd(r["bs2000"]), usd(r["stress_eq5"]), usd(r["det_base"]), srcl(["S17", "S23"])])
    body = f"""
<h1>Black-swan scenarios and economic baseline</h1>
<p>Separate from the baseline. Baseline figures are official projections where marked. Stress scenarios replay real sequences of bad years from the 1928-2025 record. Results are for the 2050 transfer and a 20-year horizon, real, rounded to $10.</p>
<h2>Baseline inputs and the official projection</h2>
{table(["Item", "Official projection (CBO, Feb 2026)", "Model input", "Status", "Source"], [
    ["Inflation (CPI)", "2.8% (2026), 2.4% (2027), 2.3% (2028 onward)", "2.3% a year, flat", badge("assumption") + " simplified; see F-22", srcl(["S23"])],
    ["PCE inflation", "2.7% (2026), 2.3% (2027), 2.1% (2028), 2.0% (2029-30)", "not used", badge("fetched"), srcl(["S23"])],
    ["3-month Treasury bills", "3.3% (2026), 3.2% (2027-2030), 3.1% (2031-36)", "3.2% a year, flat", badge("fetched") + " (2027-30 level)", srcl(["S23"])],
    ["10-year Treasury notes", "4.1% (2026), 4.3% (2027-2030), 4.4% (2031-36)", "not used", badge("fetched"), srcl(["S23"])],
    ["Equities, historical geometric mean", "not a CBO figure", f"{MO['assumptions']['equity_geo_mean_1928_2025_pct']:.2f}% a year (1928-2025 total return)", badge("academic"), srcl(["S17"])],
    ["Home-value growth", "not a CBO figure", "2.3% a year", badge("assumption"), "assumption"],
    ["Assessed-value growth cap", "not in the sources read", "2% a year, lesser of CPI or 2%", badge("unverified"), "Flagged F-18"],
])}
<h2>Stress scenarios (real, 2050 transfer, 20 years)</h2>
{table(["Path", "1929-type crash", "2008-type crash", "1973-type stagflation", "2000-type decline", "Equity at 5% a year", "Baseline", "Sources"], rows, cls="wide")}
<p class="small">Crash scenarios replay the historical annual returns from 1929, 2008, 1973 and 2000, continuing into later years (the record wraps from 2025 to 1928). They use annual steps, so a fall inside one year is not captured month by month.</p>
<h2>Limits</h2>
<ul>
<li>No historical CPI series was used. The 1973-type scenario uses that period's nominal returns and the flat 2.3% inflation, not a stagflation price path.</li>
<li>Home values are not drawn at random; only financial returns are simulated.</li>
<li>The record covers one country and one century. It has no comparable multi-decade real loss, and no month-by-month crash data.</li>
</ul>
<p class="small">Sources: {srcl(['S17','S23'])}.</p>
"""
    page("pages/black-swan.html", "Black-swan scenarios", body, "Stress scenarios and the official economic baseline.")


def p_phased():
    p = R50
    rows = []
    for pid in ("SELL_LUMP", "SELL_P24", "SELL_P36"):
        r = p[pid]
        rows.append([f"<strong>{e(PATH_SHORT[pid])}</strong>", usd(r["mc_fin"]["median"]), usd(r["mc_fin"]["p10"]),
                     usd(r["bs1929"]), usd(r["bs2008"]), usd(r["bs2000"]), usd(r["reinvest_shock"]),
                     usd(r["det_base"]), srcl(["S03", "S17", "S23"])])
    body = f"""
<h1>Phased investing and reinvestment risk</h1>
<p>Phasing parks the sale proceeds in short Treasury bills for 24 or 36 months, then moves them into equities over 12 months. Reinvestment risk is the chance that the rate earned on parked cash, or the price at which it is put back to work, is worse than expected. It is shown beside every phased result.</p>
{table(["Path (2050, 20 years)", "Median (real)", "10th pct", "1929-type crash", "2008-type crash", "2000-type decline", "Bills 1% from year 4", "Baseline (real)", "Sources"], rows, cls="wide")}
<h2>What the test shows</h2>
<ul>
<li><strong>Phasing helps in a 1929-type crash:</strong> the lump sum falls to {usd(p['SELL_LUMP']['bs1929'])}; the 36-month path holds {usd(p['SELL_P36']['bs1929'])}.</li>
<li><strong>Phasing costs in the median:</strong> the 24-month path gives {usd(p['SELL_P24']['mc_fin']['median'])} against {usd(p['SELL_LUMP']['mc_fin']['median'])} for the lump sum, {pct(abs(CHG(p['SELL_P24']['mc_fin']['median'], p['SELL_LUMP']['mc_fin']['median'])),1)} lower. Rule 5 allows 5%, so the phased paths fail.</li>
<li><strong>Reinvestment risk is small for the parked cash:</strong> when bill yields fall to 1% from year 4, the 24-month path changes by {pct(abs(CHG(p['SELL_P24']['reinvest_shock'], p['SELL_P24']['det_base'])),2)}.</li>
</ul>
<h2>Investing policy for the sale proceeds (draft; for attorney and CPA review)</h2>
<p>This follows section 5 of <code>DECISION_RULES.md</code>. It is a draft and not investment advice; no amounts are decided here.</p>
<ol>
<li><strong>Purpose:</strong> hold the proceeds for the household's stated goals and protect against a forced sale in a downturn.</li>
<li><strong>Liquidity reserve:</strong> [placeholder: months of household spending, to be set by the household before funds arrive].</li>
<li><strong>Staging, if phasing is chosen:</strong> equal monthly tranches into diversified index exposure over the period the household chooses. The rules say 24 to 36 months; the model tests 12 (Flagged F-21).</li>
<li><strong>Rebalancing:</strong> once a year, to target weights set in advance.</li>
<li><strong>No forced sales:</strong> do not sell equities to fund an emergency while the reserve is intact.</li>
<li><strong>Review:</strong> annually, with the model re-run and the Flagged items checked.</li>
<li><strong>Tax coordination:</strong> the CPA confirms the holding structure and any trust or entity wrapper before funds are invested.</li>
</ol>
<p class="small">Sources: {srcl(['S17','S23'])}. Method: <a href="method.html">Method and privacy</a>.</p>
"""
    page("pages/phased-investing.html", "Phased investing", body, "Phased investing and reinvestment risk.")


def hist_rows(hist, src):
    rows = []
    for h in hist:
        tax = usd(h["tax"]) if h["tax"] is not None else "not in owner record"
        rows.append([e(h["year"]), tax, e(h["tax_change"] or "not recorded"), usd(h["assessed"]),
                     e(h["assessed_change"] or "not recorded"), badge("owner"), srcl(src)])
    return rows


def p_property_a():
    a = INP["property_a"]
    body = f"""
<h1>Property A: inherited single-family house (Santa Clara County)</h1>
<p>Owner figures are rounded to $10 and labelled as owner records. Each rule is cited beside the figure it governs.</p>
{table(["Item", "Value", "Status", "Source"], [
    ["Market value estimate (November 2026)", usd(a['value_estimate']['value']), badge("owner"), "owner estimate; appraisal needed (F-06)"],
    ["Assessed value, 2026 roll (owner record)", usd(A_HIST[0]['assessed']), badge("owner"), srcl(["S10"]) + " (rule source)"],
    ["Property tax, 2025 bill (owner record)", usd(A_HIST[1]['tax']), badge("owner"), srcl(["S10"])],
    ["Rate implied by the 2025 bill", pct(A_RATE, 4), badge("owner"), "owner record; reconcile (F-01)"],
    ["Reference rate area total, FY 2024-25", pct(REF_A, 4), badge("snippet"), srcl(["S11"]) + " (parcel's own rate area unknown)"],
    ["Insurance, per year (owner estimate)", usd(a['insurance_annual_owner_estimate']), badge("unverified"), "no official source (F-07)"],
    ["Water, per month (owner range)", f"{usd(a['water_monthly_range'][0])} to {usd(a['water_monthly_range'][1])}", badge("owner"), "owner record"],
    ["Solar credit, per month (owner range)", f"{usd(a['solar_credit_monthly_range'][0])} to {usd(a['solar_credit_monthly_range'][1])}", badge("owner"), "owner record"],
    ["Electricity, per month", usd(a['electricity_monthly']), badge("owner"), "owner record (solar)"],
    ["Market rent", "not verified (no comparables)", badge("unverified"), "Rule 4; F-08"],
])}
<h2>Assessment and tax history</h2>
{table(["Year", "Property tax", "Change", "Assessed value", "Change", "Status", "Source"], hist_rows(A_HIST, ["S10"]), cls="wide")}
<p class="small">Rule: assessed value rises by at most the lesser of inflation or 2% a year, and is reset to market value on a change of ownership. The owner's change figures are shown as recorded; the county roll should be checked (F-12). Sources: {srcl(['S10'])} (rule), partly read.</p>
<h2>Proposition 19 at a 2040 transfer (base case)</h2>
<p>If the heir occupies A as a principal residence within a year and claims the exemption, the model uses this rule for the assessed value at transfer: the higher of the factored base and (market value less the allowance). Otherwise the house is reassessed to market value. The formula is the model's reading of the BOE letter and is flagged for CPA confirmation (F-20). Sources: {srcl(['S03','S10'])}.</p>
{table(["Year", "A tax, living (Prop 19)", "A tax, full reassessment", "Difference", "Sources"],
       [[e(r["year"]), usd(r["a_tax_live_prop19"]), usd(r["a_tax_full_reassessment"]),
         usd(r["a_tax_full_reassessment"] - r["a_tax_live_prop19"]), srcl(["S03"])]
        for r in MO["projections"] if r["year"] in (2040, 2045, 2050, 2055, 2060)])}
<h2>Maintenance</h2>
<p>No line-item budget is published, because no contractor quotes exist. The model assumes maintenance at 1% of value a year (assumption; F-26). Replace it with quotes before relying on the figure.</p>
<h2>Questions for this property</h2>
<ul>
<li>What is the parcel's rate area, and which voter bonds and direct charges appear on the bill? (F-01)</li>
<li>What is the market value on the date of death, by appraisal? (F-06)</li>
<li>Will the heir occupy it as a principal residence within a year? (Rule 3)</li>
</ul>
"""
    page("pages/property-a.html", "Property A", body, "Property A: assessment, tax history, Prop 19 and costs.")


def p_property_b():
    b = INP["property_b"]
    body = f"""
<h1>Property B: three-unit building (San Francisco County), owned by [HEIR]</h1>
<p>Property B is already owned and is held in every path. It does not change between paths, but it affects household liquidity and the choice of which property to live in.</p>
{table(["Item", "Value", "Status", "Source"], [
    ["Market value estimate (November 2026)", usd(b['value_estimate']['value']), badge("owner"), "owner estimate; appraisal needed (F-06)"],
    ["Units", f"{b['units_total']} in total; {b['units_rented']} rented (owner record)", badge("owner"), "the third unit's status is not recorded"],
    ["Rent, the two rented units (per month, total)", usd(b['rent_monthly_total']), badge("owner"), "rent-control position not verified (F-09)"],
    ["Water, all units (per month, range)", f"{usd(b['water_monthly_range'][0])} to {usd(b['water_monthly_range'][1])}", badge("owner"), "owner record"],
    ["Electricity (per month, range)", f"{usd(b['electricity_monthly_range'][0])} to {usd(b['electricity_monthly_range'][1])}", badge("owner"), "owner record"],
    ["Insurance, per year (owner estimate)", usd(b['insurance_annual_owner_estimate']), badge("unverified"), "no official source (F-07)"],
    ["Secured property tax rate, FY 2026-27", pct(STAT_B, 8), badge("snippet"), srcl(["S12"])],
    ["Allowable annual rent increase, March 2026 to February 2027", "1.6% (secondary sites only)", badge("unverified"), srcl(["S18"]) + " (not reached)"],
])}
<h2>Tax and assessment history</h2>
{table(["Year", "Property tax", "Change", "Assessed value", "Change", "Status", "Source"], hist_rows(B_HIST, ["S12"]), cls="wide")}
<p class="small">The billed tax for the 2025 year is {pct(B_RATE,2)} of assessed value, above the statutory secured rate of {pct(STAT_B,8)}. Other charges may apply; the bill was not reconciled (F-02). Sources: {srcl(['S12'])}.</p>
<h2>Depreciation and recapture (for the CPA)</h2>
<ul>
<li>Depreciable share of value: 70% (assumption; needs an appraisal that separates land from building).</li>
<li>Recovery period: 27.5 years for residential rental property (used by the model; primary source not read in this session, F-27).</li>
<li>Gain attributable to depreciation: unrecaptured section 1250 gain, taxed at a maximum 25% federal rate (IRS Pub 544, snippet). The model adds the 3.8% net investment income tax and a California assumption (F-11).</li>
</ul>
<p class="small">Sources: {srcl(['S09','S12','S18'])}.</p>
"""
    page("pages/property-b.html", "Property B", body, "Property B: owned three-unit building, rent, costs and history.")


def p_inventory():
    body = f"""
<h1>Estate inventory (structure only)</h1>
<p>The categories the inventory must cover. Documents and figures are held outside the repository; only rounded owner figures appear on other pages.</p>
{table(["Category", "Where the figure is held", "Status and next step"], [
    ["Property A: value, assessment, tax bills", "held outside this repository", "owner record; check against the county roll"],
    ["Property A: trust and title documents", "held outside this repository", "attorney to confirm the trust terms"],
    ["Property B: value, rent roll, leases", "held outside this repository", "verify leases and local rules"],
    ["Financial accounts (sale proceeds, reserve)", "placeholder: [amount set by household]", "not yet collected"],
    ["Debts and liabilities", "placeholder: none modelled", "Q-09"],
    ["Other estate assets", "placeholder: [unknown]", "needed to test the $15,000,000 exclusion (Rule 7)"],
    ["Prior taxable gifts; spouse's unused exclusion", "placeholder: [unknown]", "Q-06, Q-07"],
    ["Insurance policies (both properties)", "placeholder: quotes not yet obtained", "F-07"],
])}
"""
    page("pages/inventory.html", "Estate inventory", body, "Structure of the private estate inventory (no personal data).")


def p_tax_law():
    body = f"""
<h1>Federal, state and local rules</h1>
<p>Three systems are kept apart: <strong>estate tax</strong> at death, <strong>income tax</strong> on later gain (basis) and <strong>property tax</strong> on the assessment. Each rule shows its source and status.</p>
<h2>Federal estate and gift tax</h2>
{table(["Rule", "2026 amount or treatment", "Status", "Source"], [
    ["Basic exclusion amount per decedent", "$15,000,000", badge("partial"), srcl(["S02"])],
    ["Unified credit on the first $15,000,000", "$5,945,800", badge("partial"), srcl(["S02"])],
    ["Annual gift exclusion per recipient", "$19,000", badge("fetched"), srcl(["S01"])],
    ["Annual gift exclusion, non-citizen spouse", "$194,000", badge("fetched"), srcl(["S01"])],
    ["Rate above the exclusion", "40% (not confirmed in a fetched passage)", badge("unverified"), "Flagged F-05"],
    ["Form 706 due date", "nine months after death", badge("unverified"), "Flagged F-17"],
    ["Portability (unused spousal exclusion)", "elected on a timely Form 706", badge("partial"), srcl(["S02"])],
    ["Income-tax basis of inherited property", "fair market value at the date of death", badge("partial"), srcl(["S07"])],
    ["Main-home gain exclusion (section 121)", "$250,000 single; $500,000 joint (2 of the last 5 years)", badge("partial"), srcl(["S08"])],
    ["Unrecaptured section 1250 gain (rental depreciation)", "maximum 25%", badge("snippet"), srcl(["S09"])],
    ["Net investment income tax", "3.8% (general statute; form not read)", badge("unverified"), srcl(["S19"])],
])}
<h2>California</h2>
{table(["Rule", "Amount or treatment", "Status", "Source"], [
    ["Estate or inheritance tax", "none found in the sources read; not confirmed on an official page", badge("unverified"), "Flagged F-05"],
    ["Capital gains taxed as ordinary income", "rule as commonly stated; FTB page not read", badge("unverified"), srcl(["S06"])],
    ["Behavioral Health Services Tax", "1% of taxable income above $1,000,000", badge("partial"), srcl(["S04"])],
    ["Top California ordinary rate", "not read from the official schedule (model uses a labelled range)", badge("unverified"), srcl(["S20"])],
    ["Proposition 19 allowance (transfers 16 Feb 2025 to 15 Feb 2027)", "$1,044,586", badge("fetched"), srcl(["S03"])],
    ["Proposition 13 growth cap on assessed value", "lesser of inflation or 2% a year", badge("unverified"), "general law; not confirmed in fetched text (F-18)"],
])}
<h2>Local (county and city)</h2>
{table(["Rule", "Amount or treatment", "Status", "Source"], [
    ["Santa Clara County: documentary transfer tax", "$1.10 per $1,000 of price (county)", badge("snippet"), srcl(["S13"])],
    ["Santa Clara County: city transfer tax for A's rate area", "not confirmed; sources disagree", badge("unverified"), "Flagged F-10"],
    ["Santa Clara County: reference rate area total, FY 2024-25", pct(REF_A, 4), badge("snippet"), srcl(["S11"])],
    ["San Francisco: secured rate, FY 2026-27", pct(STAT_B, 8), badge("snippet"), srcl(["S12"])],
    ["San Francisco: allowable rent increase, March 2026 to February 2027", "1.6% (secondary sites)", badge("unverified"), srcl(["S18"])],
])}
<h2>Property tax timing</h2>
<p>Installment dates are not confirmed in a fetched passage of the county or city rate sources; they are listed on the <a href="process-timeline.html">timeline</a> as unverified (F-19).</p>
<p class="small">Not legal or tax advice. Unverified items are on the <a href="flagged.html">Flagged for Review</a> page.</p>
"""
    page("pages/tax-law.html", "Federal, state and local rules", body, "Federal, California and local rules with sources and status.")


def p_legislation():
    body = f"""
<h1>Legislation: enacted vs proposed</h1>
<p>Enacted law is kept apart from proposals. Proposals are not used in any figure. Each year the watch list is checked and the decision log is updated.</p>
<h2>Enacted (in force)</h2>
{table(["Change", "Effect on this decision", "Status", "Source"], [
    ["Federal basic exclusion of $15,000,000 for 2026", "no federal estate tax below that amount per decedent (unless verified otherwise)", badge("fetched"), srcl(["S02"])],
    ["Proposition 19 parent-child exclusion (family home, occupied by the child)", "living is the only way to keep the lower assessed base; rental property is reassessed", badge("partial"), srcl(["S03"])],
    ["Proposition 19 allowance of $1,044,586 (16 Feb 2025 to 15 Feb 2027)", "sets the living case's allowance until February 2027", badge("fetched"), srcl(["S03"])],
    ["Behavioral Health Services Tax, 1% above $1,000,000", "affects only very high California taxable income", badge("partial"), srcl(["S04"])],
])}
<h2>Proposed, or not verified</h2>
{table(["Item", "What is known", "Status", "Where to check"], [
    ["Next Proposition 19 allowance adjustment", "due 16 February 2027; amount not yet published", badge("statute"), srcl(["S03"])],
    ["Federal estate-tax changes beyond 2026", "none verified in this session", badge("unverified"), "Flagged F-05"],
    ["California inheritance or property-tax changes", "none verified in this session", badge("unverified"), "Flagged F-18"],
    ["San Francisco rent rules (annual increase)", "1.6% reported by secondary sites only", badge("unverified"), srcl(["S18"])],
])}
"""
    page("pages/legislation.html", "Legislation", body, "Enacted changes and proposals, kept apart.")


def p_process():
    body = f"""
<h1>Inheritance steps and timeline</h1>
<h2>Step by step</h2>
<ol class="steps">
<li><strong>Date of death.</strong> Record the date. The income-tax basis of Property A becomes its fair market value that day ({srcl(['S07'])}).</li>
<li><strong>Valuation.</strong> Obtain written appraisals of A and B at the date of death. The estimates used here are owner estimates (F-06).</li>
<li><strong>Trust administration.</strong> The trustee takes control of the property. The attorney confirms the trust terms and whether the transfer is by trust or by deed.</li>
<li><strong>Estate-tax check.</strong> Compare the gross estate and adjusted taxable gifts with $15,000,000. If above, or if a portability election is wanted, a Form 706 is needed on the due date (F-17).</li>
<li><strong>Property-tax claim.</strong> If the heir will live in A, file the claim and move in within the window in the BOE guidance ({srcl(['S03'])}). Otherwise expect reassessment at market value ({srcl(['S10'])}).</li>
<li><strong>Insurance.</strong> Change the policy on A to the right occupancy (owner-occupied, tenant or vacant) before the transfer date.</li>
<li><strong>Decision.</strong> Apply the <a href="decision.html">rules</a>. If a sale is chosen, the CPA and attorney review the holding structure first.</li>
<li><strong>Investing.</strong> Put the investing policy in place before the money arrives (see <a href="phased-investing.html">phased investing</a>).</li>
</ol>
<h2>Timeline</h2>
{table(["When", "What", "Status", "Source"], [
    ["Date of death (D)", "starts the clock on every item below", badge("fetched"), srcl(["S07"])],
    ["D + 1 month", "insurance and valuation requests", badge("assumption"), "planning step, not a legal deadline"],
    ["D + 9 months", "Form 706 due, if required or if portability is elected", badge("unverified"), "Flagged F-17"],
    ["About D + 12 months", "heir occupies A and claims the exemption (living case)", badge("unverified"), "Flagged F-16"],
    ["1 January after the transfer", "lien date for the next assessment; supplemental bill follows a change of ownership", badge("unverified"), "Flagged F-19"],
    ["16 February 2027", "next adjustment of the Proposition 19 amount", badge("statute"), srcl(["S03"])],
    ["Each year", "re-run the model with updated inputs; review the stress scenarios", badge("model"), "decision log"],
], cls="wide")}
<p>The three-year window to file the Proposition 19 claim is from secondary summaries and is not confirmed on an official page (F-16).</p>
"""
    page("pages/process-timeline.html", "Inheritance steps and timeline", body, "Inheritance steps and deadlines.")


def p_questions():
    qs = [
        ["Q-01", "What is the rate area and the full bill for Property A?", "Owner bill implies " + pct(A_RATE, 4) + "; reference total " + pct(REF_A, 4), "county rate-area lookup and one full bill", "Open (F-01)"],
        ["Q-02", "What is the market value on the date of death?", "owner estimate only", "written appraisal at date of death", "Open (F-06)"],
        ["Q-03", "Will the heir occupy A as a principal residence within a year?", "not decided", "written commitment (Rule 3)", "Open"],
        ["Q-04", "Are there three verified rental comparables for A?", "none", "three comparables from a licensed appraiser or property manager", "Open (Rule 4)"],
        ["Q-05", "What is the total taxable estate after debts and expenses?", "known real estate about " + usd(MO['estate']['known_real_estate_owner_estimates']) + " (owner)", "full inventory; attorney review", "Open"],
        ["Q-06", "Is there a surviving spouse, and what is the unused exclusion (portability)?", "unknown", "attorney question now", "Open"],
        ["Q-07", "Are there prior taxable gifts?", "unknown", "gift tax returns, if any", "Open"],
        ["Q-08", "What are the heir's marginal income-tax rates, federal and California?", "40% combined is an assumption", "CPA review", "Open"],
        ["Q-09", "Is there debt on either property?", "none modelled", "loan statements", "Open"],
        ["Q-10", "Insurance quotes for A and B?", "owner estimate of " + usd(INP['property_a']['insurance_annual_owner_estimate']) + " each", "three written quotes per property", "Open (F-07)"],
        ["Q-11", "Are the Property B rents and rent-control position verified?", "owner figure; rent-board rate not verified", "leases; rent-board records", "Open (F-09)"],
        ["Q-12", "What is the city transfer tax for A's rate area?", "sources disagree", "city or county schedule", "Open (F-10)"],
        ["Q-13", "What depreciable share applies to B?", "70% assumption", "appraisal that splits land and building", "Open"],
        ["Q-14", "Are the solar credit and water costs stable?", "owner records only", "twelve months of utility bills", "Open"],
    ]
    body = f"""
<h1>Questions and gaps</h1>
<p>Questions that must be answered before a decision can reasonably be made, with what is known and how to find out.</p>
{table(["ID", "Question", "What we have", "How to find it out", "Status"], qs)}
<p class="small">Sources: {srcl(['S03','S10','S02'])}.</p>
"""
    page("pages/questions.html", "Questions and gaps", body, "Missing information and how to get it.")


def p_suggestions():
    items = [
        ["SG-01", "Replace owner value estimates with written appraisals of A and B at the date of death.", "Largest unverified input.", "[pending owner decision]"],
        ["SG-02", "Pull the parcel's rate-area breakdown from the county and reconcile it to the bill.", "Closes F-01.", "[pending]"],
        ["SG-03", "Obtain three insurance quotes per property.", "Closes F-07.", "[pending]"],
        ["SG-04", "Obtain three rental comparables for A.", "The only route to a rent path beyond a floor (Rule 4).", "[pending]"],
        ["SG-05", "Ask the attorney now about portability and prior taxable gifts.", "Can change the estate-tax result.", "[pending]"],
        ["SG-06", "Add a mortgage or line-of-credit scenario.", "None is modelled; debt changes liquidity.", "[pending]"],
        ["SG-07", "Verify the top California rate schedule and the 3.8% net investment income tax on official pages.", "Closes F-05 and F-11.", "[pending]"],
        ["SG-08", "Align the phase-in period with DECISION_RULES.md section 5 (24 to 36 months) or change the rule in writing.", "Closes F-21.", "[pending owner decision]"],
        ["SG-09", "Re-run the model each year and log the result in the decision log.", "Keeps the decision tied to current inputs.", "[pending]"],
        ["SG-10", "Rewrite Git history to remove earlier ZIP codes and household material.", "The only way to remove them from history; needs owner approval.", "[pending owner approval]"],
    ]
    body = f"""
<h1>Suggestions (review and choose before any change)</h1>
<p>These are proposals. None has been applied. Record each decision, with its date, in the <a href="decision-log.html">decision log</a>.</p>
{table(["ID", "Suggestion", "Why", "Decision"], items)}
"""
    page("pages/suggestions.html", "Suggestions", body, "Proposed changes for review before implementation.")


def p_flagged():
    fl = [
        ["F-01", "Property A's billed rate (" + pct(A_RATE, 4) + ") is above the reference rate-area total (" + pct(REF_A, 4) + "). The parcel's own rate area and voter bonds are unknown.", "unverified", srcl(["S10", "S11"])],
        ["F-02", "Property B's billed tax is " + pct(B_RATE, 2) + " of assessed value, against a statutory secured rate of " + pct(STAT_B, 8) + ". Other charges are unknown.", "unverified", srcl(["S12"])],
        ["F-03", "The first model run used a rounded placeholder for the Proposition 19 amount. The statutory $1,044,586 is now used exactly.", "corrected", srcl(["S03"])],
        ["F-04", "Recapture: the model applies 25% federal, plus 3.8% net investment income tax and a 9.3% California assumption (38.1% combined). The 25% federal rate is from a snippet.", "snippet", srcl(["S09", "S19"])],
        ["F-05", "The 40% federal top rate, the California top rate, the 9.3% California capital-gain assumption and the 3.8% net investment income tax were not read from official pages in this session.", "unverified", srcl(["S19", "S20"])],
        ["F-06", "Market values of A and B are owner estimates. No appraisal exists; the date-of-death value sets the basis.", "owner estimate", srcl(["S07"])],
        ["F-07", "Insurance is an owner estimate of " + usd(INP['property_a']['insurance_annual_owner_estimate']) + " a year for each property. No official premium data was read.", "unverified", srcl(["S21"])],
        ["F-08", "Market rent for A is unknown. The 3.75% gross yield is an assumption; rent paths are a floor (Rule 4).", "assumption", "Rule 4"],
        ["F-09", "The San Francisco allowable rent increase (1.6%) comes from secondary sites; the Rent Board was not reached.", "unverified", srcl(["S18"])],
        ["F-10", "City transfer tax for A's rate area: sources disagree. The model includes only the county rate.", "unverified", srcl(["S13"])],
        ["F-11", "The 3.8% net investment income tax and the 9.3% California capital-gain rate are assumptions in the model.", "unverified", srcl(["S19"])],
        ["F-12", "Owner records to check against the county rolls: Property A's billed tax is unchanged from 2019 to 2020 and the change field is blank for 2014, 2018 and 2020; Property B's billed tax fell 5.9% in 2021 while assessed value rose 1%, and rose 18.4% in 2018.", "owner record", srcl(["S10", "S12"])],
        ["F-13", "Historical returns come from an academic dataset (not an official source). The S&P 500 column compounds to within 0.001% of the source. The T-bill column compounds to 2,579.18 against the source's 2,578.30 (+0.034%); the cause is not yet located, and the 2008 check was not run.", "academic; partly unresolved", srcl(["S17"])],
        ["F-14", "Earlier copies of the site and analysis folders contained ZIP codes, a neighbourhood name and household material. They have been removed from the published tree and kept locally outside Git. The Git history still contains them; removing them needs a history rewrite and owner approval (SG-10).", "exposure", "Suggestions SG-10"],
        ["F-15", "The Git history names a personal e-mail address as commit author. It is not reproduced on this site. The history has not been rewritten (SG-10).", "exposure", "Suggestions SG-10"],
        ["F-16", "The three-year window to file the Proposition 19 claim is from a secondary summary and not confirmed on an official page.", "unverified", srcl(["S03"])],
        ["F-17", "The Form 706 due date (nine months) is not confirmed in a fetched passage of the instructions.", "unverified", srcl(["S02"])],
        ["F-18", "The Proposition 13 growth cap and the Santa Clara 2026-27 rate book were not read in full. The 2025-26 book (S10) was read in part only.", "unverified", srcl(["S10"])],
        ["F-19", "County and city installment dates are not confirmed in a fetched passage.", "unverified", srcl(["S10", "S12"])],
        ["F-20", "The model's Proposition 19 assessed-value formula (higher of factored base and market value less the allowance) is the model's reading of the BOE letter. The CPA and attorney should confirm it.", "unverified reading", srcl(["S03"])],
        ["F-21", "Phase-in period: DECISION_RULES.md section 5 says staging over 24 to 36 months. The model tests a 12-month phase-in after 24 or 36 months of parking. The discrepancy is open (SG-08).", "open", "Repository file"],
        ["F-22", "The model holds 2.3% inflation and a 3.2% bill return flat for all years. CBO's path (S23): CPI 2.8% in 2026, 2.4% in 2027, then 2.3%; 3-month bill rate 3.3% in 2026 and 3.2% from 2027 to 2030.", "simplification", srcl(["S23"])],
        ["F-23", "Renting: no gross rent yield up to 20% lets a rent path match the lump-sum sale at 20 years. The rent path is not sensitive to the pick.", "result", "What-if"],
        ["F-24", "Model correction: a living household's running costs compounded at the equity return. Fixed; the pick is unchanged; before and after values are on the decision log.", "corrected", "Decision log"],
        ["F-25", "Interpretation: the primary metric excludes imputed rent (not cash). Including it would raise the living paths; the rule does not say which.", "interpretation", "Method"],
        ["F-26", "Maintenance is modelled at 1% of value a year. No quotes exist.", "assumption", "Property A"],
        ["F-27", "Recovery period (27.5 years) and the depreciation rules were not read in a primary source.", "unverified", "Property B"],
        ["F-28", "The model applies the section 121 main-home exclusion after 24 months of living. Eligibility for an inherited home depends on facts the CPA must confirm.", "unverified", srcl(["S08"])],
    ]
    body = f"""
<h1>Flagged for Review</h1>
<p>Everything this site cannot confirm, has corrected, or has left unreconciled. Each item links to its source. The flags do not block publication.</p>
{table(["ID", "Item", "Status", "Source"], fl)}
"""
    page("pages/flagged.html", "Flagged for Review", body, "Unverified items, corrections and open questions, with sources.")


def p_sources():
    rows = []
    for s in SRC_LIST:
        st = {"fetched": "fetched", "partial": "partial", "snippet": "snippet", "not_verified": "unverified",
              "academic": "academic"}.get(s["status"], "unverified")
        if s["id"] == "S17":
            st = "academic"
        rows.append([e(s["id"]), e(s["publisher"]), e(s["title"]), badge(st),
                     f'<a href="{e(s["url"])}">{e(s["url"])}</a>', e(s["used_for"])])
    body = f"""
<h1>Sources</h1>
<p>"Official, read in full" means the document was fetched in this session and the figures used were read from it. "Partly read" means only the first part was read. "Snippet" means the figure came from a search result on an official domain. "Unverified" means no official source was reached. Accessed {ACCESSED}.</p>
{table(["ID", "Publisher", "Title", "Status", "Link", "Used for"], rows, cls="wide")}
"""
    page("pages/sources.html", "Sources", body, "Source register with links and status.")


def p_glossary():
    terms = [
        ("Assessed value", "The value on which property tax is computed. Under Proposition 13 it rises by at most the lesser of inflation or 2% a year, until a change of ownership."),
        ("Basis (step-up)", "The income-tax cost of an inherited asset: its fair market value on the date of death (IRS Pub 551)."),
        ("Basic exclusion amount", "The federal estate-tax exemption per decedent: $15,000,000 for 2026."),
        ("Behavioral Health Services Tax", "California surtax of 1% on taxable income above $1,000,000 (FTB Form 540-ES worksheet)."),
        ("Documentary transfer tax", "Tax on a recorded sale: $1.10 per $1,000 at county level (statute snippet; city rates vary, F-10)."),
        ("Imputed rent", "The rent an owner saves by living in the home. Not cash; reported separately."),
        ("Median (real)", "The middle outcome of the simulated paths after inflation. Half are above, half below."),
        ("Mixed path", "A path that changes mode, for example living for three years and then selling or renting."),
        ("Phasing", "Moving sale proceeds from cash into equities in equal tranches, instead of all at once."),
        ("Proposition 13 / Proposition 19", "Proposition 13 limits annual growth of assessed value. Proposition 19 limits the parent-child exclusion to a family home the child occupies."),
        ("Reinvestment risk", "The risk that cash waiting to be invested earns less, or is invested at worse prices, than expected."),
        ("Section 121 exclusion", "Gain exclusion on a main home: $250,000 single, $500,000 joint, with ownership and use tests (IRS Pub 523)."),
        ("Tax-rate area", "A county geographic area with its own total rate (levy plus voter-approved bonds)."),
        ("Unrecaptured section 1250 gain", "Depreciation taken on rental property, taxed at up to 25% federal when the property is sold."),
    ]
    body = f"""
<h1>Glossary</h1>
<p>Plain-language definitions. Sources are in the <a href="sources.html">Sources</a> register.</p>
<dl class="gloss">{''.join(f'<dt>{e(t)}</dt><dd>{e(d)}</dd>' for t, d in terms)}</dl>
"""
    page("pages/glossary.html", "Glossary", body, "Glossary of terms used on the site.")


def p_method():
    A = MO["assumptions"]
    rows = [
        ["Inflation (base)", pct(A["cpi_base"] * 100, 1), "assumption; CBO path in S23 is 2.3% from 2028", srcl(["S23"])],
        ["Home-value growth", pct(A["home_value_growth"] * 100, 1), "assumption", "assumption"],
        ["Assessed-value growth cap", pct(A["prop13_growth_cap"] * 100, 1), "unverified general rule (F-18)", "F-18"],
        ["Property A tax rate, as billed", pct(A["rate_owner_implied_pct"], 4), "owner record (F-01)", srcl(["S10"])],
        ["Reference rate-area total", pct(A["rate_county_floor_pct"], 4), "snippet; not the parcel's own area", srcl(["S11"])],
        ["Property B tax rate (statutory)", pct(A["rate_sf_b_statutory_pct"], 8), "snippet", srcl(["S12"])],
        ["Insurance, per year (each property)", usd(A["insurance_annual"]), "owner estimate (F-07)", "F-07"],
        ["Water, net of solar credit, per month", usd(A["water_net_monthly"]), "owner record", "owner record"],
        ["Gross rent yield", pct(A["rent_yield"] * 100, 2), "assumption; no comparables (Rule 4)", "assumption"],
        ["Vacancy", pct(A["vacancy"] * 100, 1), "assumption", "assumption"],
        ["Maintenance, share of value a year", pct(A["maintenance_rate"] * 100, 1), "assumption (F-26)", "F-26"],
        ["Selling costs", pct(A["sale_costs_pct"], 2), "transfer tax from S13; commission 5% and other 0.5% assumed", srcl(["S13"])],
        ["Ordinary income-tax rate, combined", pct(A["ordinary_rate_combined"] * 100, 1), "assumption (F-05)", "F-05"],
        ["Capital-gain rate, combined", pct(A["ltcg_rate_combined"] * 100, 1), "20% federal + 3.8% + 9.3% CA: assumption (F-05, F-11)", "F-05"],
        ["Unrecaptured 1250 rate, combined", pct(A["recapture_rate_combined"] * 100, 1), "25% federal (snippet) + 3.8% + 9.3% assumption", srcl(["S09"])],
        ["Depreciable share of value", pct(A["building_share"] * 100, 0), "assumption (F-27)", "F-27"],
        ["Section 121 exclusion, single", usd(A["exclusion_living"]), "IRS Pub 523 (partly read)", srcl(["S08"])],
        ["Proposition 19 allowance", usd(PROP19), "statute, exact", srcl(["S03"])],
        ["Equity return, historical geometric mean 1928-2025", pct(A["equity_geo_mean_1928_2025_pct"], 2), "academic dataset", srcl(["S17"])],
        ["Bill return (forward)", pct(A["forward_bill_pct"], 1), "CBO, 2027-2030 level (S23)", srcl(["S23"])],
        ["Equity stress return", pct(A["stress_equity_pct"], 1), "stress assumption", "assumption"],
    ]
    body = f"""
<h1>Method and privacy</h1>
<h2>Privacy</h2>
<ul>
<li>No street address, ZIP code, parcel number or account number appears in the repository or on this site. Properties are labelled "Property A" and "Property B", with the county only.</li>
<li>People are shown as placeholders: [HEIR], [TRUST], [ATTORNEY], [CPA].</li>
<li>Every dollar figure is rounded to the nearest $10. Statutory amounts are printed exactly and are checked against the source register.</li>
<li>The owner figures published here are property values, insurance, utilities and rent ranges, and tax history. No income, account or debt figures were supplied; none appear.</li>
<li>Earlier copies of the site were removed from the published tree (F-14). Git history still contains them, and a rewrite needs owner approval (SG-10).</li>
</ul>
<h2>Model</h2>
<ul>
<li>Monthly simulation over 10 and 20 years for each path, with transfers in 2040 and 2050.</li>
<li>The primary metric is the real financial position at the end of the horizon. A property still held is sold at that point, with selling costs and tax. Imputed rent is excluded (F-25).</li>
<li>Monte Carlo: {MO['_meta']['monte_carlo_draws']:,} paths. Each year of a path draws one year at random, with replacement, from the 1928-2025 record; equity and bill returns come from the same year. Seed {MO['_meta']['seed']}.</li>
<li>Household cash flows (rent in; costs and tax out) go to the cash account at the bill return (F-24).</li>
<li>Crash scenarios replay the historical sequences from 1929, 2008, 1973 and 2000.</li>
<li>Rules: applied mechanically from DECISION_RULES.md. The model does not set them.</li>
<li>Property B is in every path and excluded from the comparison.</li>
</ul>
<h2>Assumptions and their status</h2>
{table(["Input", "Value used", "Status and basis", "Source"], rows)}
<h2>Limits</h2>
<ul>
<li>Owner value estimates stand in for appraisals.</li>
<li>No mortgage or other debt is modelled (Q-09).</li>
<li>Only financial returns are simulated; home values are not.</li>
<li>Annual return data are applied as monthly compounding; a fall inside one year is not captured.</li>
<li>Income tax uses one combined rate; the household's brackets are unknown (Q-08).</li>
</ul>
<h2>Reproduce</h2>
<p><code>python3 tools/model.py</code> then <code>python3 tools/build_site.py</code> then <code>python3 tools/check_site.py</code>. The model reads only files in this repository.</p>
"""
    page("pages/method.html", "Method and privacy", body, "How the model works, assumptions and privacy rules.")


def p_briefing():
    pk = R50[PICK50]
    body = f"""
<h1>Attorney and CPA briefing sheet</h1>
<p class="small">Prepared {ACCESSED}. Dollar figures rounded to $10. Owner estimates are unverified. Not legal or tax advice.</p>
<h3>Facts used</h3>
<table class="brief">
<tr><th>Item</th><th>Figure</th><th>Status</th></tr>
<tr><td>Property A value estimate</td><td>{usd(INP['property_a']['value_estimate']['value'])}</td><td>owner, unverified</td></tr>
<tr><td>Property A assessed value, 2026 roll</td><td>{usd(A_HIST[0]['assessed'])}</td><td>owner record</td></tr>
<tr><td>Property B value estimate</td><td>{usd(INP['property_b']['value_estimate']['value'])}</td><td>owner, unverified</td></tr>
<tr><td>Federal basic exclusion, 2026</td><td>$15,000,000 per decedent</td><td>official (IRS)</td></tr>
<tr><td>Proposition 19 allowance, to 15 Feb 2027</td><td>{usd(PROP19)}</td><td>official (BOE)</td></tr>
<tr><td>Section 121 main-home exclusion</td><td>$250,000 single; $500,000 joint</td><td>partly read (IRS Pub 523)</td></tr>
</table>
<h3>Model result (2050 transfer, 20 years, real)</h3>
<p>Pick under the written rules: <strong>{e(PATH_SHORT[PICK50])}</strong>, median {usd(pk['mc_fin']['median'])}. Phased (24 months): median {usd(R50['SELL_P24']['mc_fin']['median'])}; 1929-type crash {usd(R50['SELL_P24']['bs1929'])}, against {usd(R50['SELL_LUMP']['bs1929'])} for the lump sum.</p>
<h3>For the attorney</h3>
<ol>
<li>Trust terms: is A transferred by deed, and does the Proposition 19 parent-child rule apply?</li>
<li>Will the heir occupy A within a year? A written commitment is needed before any living path can be chosen.</li>
<li>Portability: is there a surviving spouse, and are there prior taxable gifts? Should a timely Form 706 be filed?</li>
<li>Is a date-of-death appraisal in hand, and who prepares it?</li>
</ol>
<h3>For the CPA</h3>
<ol>
<li>Basis: step-up to date-of-death value for A and B; confirm the appraisal split of land and building.</li>
<li>Section 121: applies only with the use and ownership tests; confirm the heir's facts.</li>
<li>Rental B: depreciation, recapture at up to 25%, and the 3.8% net investment income tax.</li>
<li>California: ordinary tax on gains (confirm), and the 1% surtax above $1,000,000 (confirm the top rate).</li>
<li>Confirm the Proposition 19 assessed-value formula used in the model (F-20).</li>
</ol>
<h3>Open items</h3>
<p>Rate area and bills for A (F-01); B's other charges (F-02); insurance quotes (F-07); market rent for A (F-08); B's rent-control position (F-09); city transfer tax (F-10). See <a href="flagged.html">Flagged for Review</a>.</p>
<p class="small">Sources: S01, S02, S03, S07, S08, S09, S10, S12, S23 (see Sources).</p>
"""
    page("pages/briefing.html", "Attorney and CPA briefing sheet", body,
         "One-page briefing sheet for the attorney and CPA.", print_mode=True)


CSS = """
:root{--ink:#1d232b;--muted:#5b6673;--line:#dfe4ea;--bg:#f6f8fa;--accent:#1b4f8a;--ok:#2e7d4f;--warn:#9a6700;--bad:#b42318;}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:12px 20px;background:#fff;border-bottom:1px solid var(--line);flex-wrap:wrap;position:sticky;top:0;z-index:2}
.brand{font-weight:700;text-decoration:none;color:var(--ink);font-size:16px}
.privacy{color:var(--muted);font-size:12px}
.layout{display:grid;grid-template-columns:260px 1fr;min-height:calc(100vh - 56px)}
.side{background:#fff;border-right:1px solid var(--line);padding:14px 10px;position:sticky;top:56px;height:calc(100vh - 56px);overflow:auto}
.navgroup{margin-bottom:12px}
.navhead{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:4px 8px}
.side a{display:block;padding:6px 8px;border-radius:6px;text-decoration:none;color:var(--ink)}
.side a:hover{background:#eef3f9}
.side a[aria-current=page]{background:#e3edf8;font-weight:600}
.content{padding:22px 28px 40px;max-width:1200px}
h1{font-size:24px;margin:0 0 10px}
h2{font-size:18px;margin:26px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
h3{font-size:15px;margin:18px 0 6px}
.lede{font-size:16px;color:#33404d}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.card.first{border-left:5px solid var(--accent)}
.changes li{margin:6px 0}
.tile{display:block;background:#fbfcfe;border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:var(--ink)}
.tile span{display:block;color:var(--muted);font-size:13px;margin-top:4px}
.tile:hover{border-color:var(--accent)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
@media(max-width:980px){.layout{grid-template-columns:1fr}.side{position:static;height:auto}.grid3,.grid2{grid-template-columns:1fr}}
.tablewrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:8px;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f1f4f8;font-weight:600}
table.wide td,table.wide th{white-space:nowrap}
table.wide td:last-child{white-space:normal}
.badge{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;border:1px solid;white-space:nowrap}
.b-ok{color:var(--ok);border-color:#b7dcc5;background:#eef8f2}
.b-owner{color:#1f5a99;border-color:#bcd3ec;background:#eff5fc}
.b-assume{color:var(--warn);border-color:#ecd9a6;background:#fdf7e6}
.b-bad{color:var(--bad);border-color:#f2b8b5;background:#fdeeed}
.b-snip{color:#4d5761;border-color:#cfd6de;background:#f5f7f9}
.b-model{color:#4b3c86;border-color:#d4cdef;background:#f4f1fc}
.small{font-size:12px;color:var(--muted)}
footer{margin-top:40px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:10px}
.controls{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0}
select{padding:5px 8px;font-size:14px}
figure{margin:12px 0;background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px}
figure svg{width:100%;height:auto}
figcaption{font-size:12px;color:var(--muted)}
dl.gloss dt{font-weight:600;margin-top:10px}
dl.gloss dd{margin:2px 0 0 0;color:#33404d}
ol.steps li{margin:8px 0}
table.brief{width:100%;font-size:12px}
table.brief th,table.brief td{padding:4px 6px;border-bottom:1px solid #ccc}
.sheetwrap{max-width:900px;margin:20px auto;padding:0 16px;background:#fff}
@media print{
 .top,.side,footer{display:none!important}
 .layout{display:block}.content{padding:0;max-width:none}
 body{background:#fff;font-size:10.5px;line-height:1.3}
 .sheetwrap{margin:0;padding:0;max-width:none;box-shadow:none}
 @page{size:letter;margin:0.45in}
}
"""

JS = """
(function(){
  var el=document.getElementById('whatif-data'); if(!el) return;
  var D=JSON.parse(el.textContent);
  var ry=document.getElementById('ry'), hp=document.getElementById('hp'), out=document.getElementById('whatif-out');
  if(!ry||!hp||!out) return;
  var names={LIVE:'Live in A',RENT:'Rent A',SELL_LUMP:'Sell, lump sum',SELL_P24:'Sell, park 24 months, phase in over 12',SELL_P36:'Sell, park 36 months, phase in over 12',LIVE3_SELL:'Mixed: live 3 years, then sell',RENT3_SELL:'Mixed: rent 3 years, then sell',LIVE3_RENT:'Mixed: live 3 years, then rent'};
  var order=['LIVE','RENT','SELL_LUMP','SELL_P24','SELL_P36','LIVE3_SELL','RENT3_SELL','LIVE3_RENT'];
  D.rent_yields.forEach(function(v,i){var o=document.createElement('option');o.value=i;o.textContent=(v*100).toFixed(2)+'%';if(i===1)o.selected=true;ry.appendChild(o);});
  D.hpa.forEach(function(v,i){var o=document.createElement('option');o.value=i;o.textContent=(v*100).toFixed(1)+'% a year';if(i===1)o.selected=true;hp.appendChild(o);});
  function money(v){return (v<0?'-$':'$')+Math.abs(v).toLocaleString('en-US');}
  function render(){
    var r=parseInt(ry.value,10), h=parseInt(hp.value,10);
    var cell=D.cells.filter(function(c){return c.rent_yield===D.rent_yields[r]&&c.hpa===D.hpa[h];})[0];
    if(!cell){out.textContent='No result for this combination.';return;}
    var best=order.reduce(function(a,b){return cell.paths[b]>cell.paths[a]?b:a;});
    var rows=order.map(function(p){return '<tr'+(p===best?' style="background:#eef8f2"':'')+'><td>'+names[p]+'</td><td>'+money(cell.paths[p])+'</td></tr>';}).join('');
    out.innerHTML='<table><thead><tr><th>Path</th><th>Real financial position, 2050 transfer + 20 years (rounded to $10)</th></tr></thead><tbody>'+rows+'</tbody></table><p class="small">Highest in this combination: '+names[best]+'. The rules still apply (see Rules and pick).</p>';
  }
  ry.addEventListener('change',render); hp.addEventListener('change',render); render();
})();
"""


def main():
    (DASH / "assets").mkdir(exist_ok=True)
    (DASH / "assets/site.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (DASH / "assets/site.js").write_text(JS.strip() + "\n", encoding="utf-8")
    for fn in (p_index, p_paths, p_decision, p_whatif, p_decision_log, p_projections, p_black_swan, p_phased,
               p_property_a, p_property_b, p_inventory, p_tax_law, p_legislation, p_process, p_questions,
               p_suggestions, p_flagged, p_sources, p_glossary, p_method, p_briefing):
        fn()
    print("built site")


if __name__ == "__main__":
    main()
