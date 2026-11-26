"""
Builds the static GitHub Pages site at the repository root from:
  data/model_outputs.json   (written by model/model.py; contains rounded results only)
  tools/content.py          (sources, facts placeholders, law, legislation, timeline, rules)

Run:  python3 tools/build_site.py      (does not need the private inputs)
Then: python3 tools/check_site.py      (privacy scan, link check, row-link check)
Standard library only.
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import content as C  # noqa: E402

DATA = json.load(open(os.path.join(ROOT, "data", "model_outputs.json")))
CHECKED = C.CHECKED
REPO_URL = "https://github.com/kanlerxz87-cyber/TinoDash4"
PATHS = DATA["paths"]
BASE = DATA["base_results_real_2026"]
BE = DATA["breakevens"]
MC = DATA["monte_carlo"]["summary"]
HIST = DATA["monte_carlo"]["histogram"]
CRASH = DATA["crash_test"]
GRID = DATA["grid"]
PROJ = DATA["projection_base"]
BASE_CASE = DATA["meta"]["base_case"]
SHORT = {
    "S": "Sell in transfer year, invest lump sum",
    "SP24": "Sell, park 24 months, then phase in",
    "SP36": "Sell, park 36 months, then phase in",
    "R": "Rent long-term, sell at horizon",
    "L": "Live long-term, sell at horizon (no rent credit)",
    "L2S": "Mixed: live 2 years, then sell",
    "L5S": "Mixed: live 5 years, then sell",
    "R10S": "Mixed: rent 10 years, then sell",
    "L5R_B": "Mixed: live 5 years, then rent (reading B)",
    "L5R_A": "Mixed: live 5 years, then rent (reading A)",
}
ORDER = ["S", "SP24", "SP36", "L2S", "R10S", "R", "L5S", "L5R_A", "L5R_B", "L"]
# Official sources for each path's row (every row links to at least one)
PATH_SOURCES = {
    "S": ["TREASURY-YIELD", "IRS-FORM-706", "IRS-PUB-523"],
    "SP24": ["TREASURY-YIELD", "SP-DRAWDOWN", "FTB-540ES-2025"],
    "SP36": ["TREASURY-YIELD", "SP-DRAWDOWN", "FTB-540ES-2025"],
    "R": ["IRS-PUB-527", "BOE-PROP19-INTRO", "FTB-540ES-2025"],
    "L": ["IRS-PUB-523", "BOE-PROP19-INTRO", "BOE-LTA-2026-002"],
    "L2S": ["IRS-PUB-523", "BOE-PROP19-INTRO"],
    "L5S": ["IRS-PUB-523", "BOE-PROP19-INTRO"],
    "R10S": ["IRS-PUB-527", "BOE-PROP19-INTRO"],
    "L5R_A": ["CA-RTC-63.2", "BOE-PROP19-INTRO"],
    "L5R_B": ["CA-RTC-63.2", "BOE-PROP19-INTRO"],
}
NAV = [
    ("Decide", [("index.html", "Dashboard"), ("paths.html", "Paths and what-if"),
                ("decision-rules.html", "Decision rules"), ("suggestions.html", "Suggestions"),
                ("brief.html", "Attorney and CPA brief")]),
    ("Analysis", [("projections.html", "Projections"), ("blackswan.html", "Black swan and phasing"),
                  ("inputs.html", "Facts and inputs")]),
    ("Tax and law", [("estate-tax.html", "Estate tax"), ("income-basis.html", "Income-tax basis"),
                     ("property-tax.html", "Property-tax assessment"), ("tax-law.html", "All law (enacted)"),
                     ("legislation.html", "Proposed and reported"), ("timeline.html", "Deadlines timeline")]),
    ("Work", [("questions.html", "Questions and gaps"), ("flagged.html", "Flagged for Review")]),
    ("Reference", [("glossary.html", "Glossary"), ("sources.html", "Sources")]),
]
PAGES_NAV = [href for _, links in NAV for href, _ in links]


def e(x):
    return html.escape("" if x is None else str(x))


def r10(x):
    return int(round(x / 10.0) * 10)


def money(x):
    """Every published money value: rounded to the nearest $10."""
    if x is None:
        return "blank (UNVERIFIED)"
    return "${:,}".format(r10(x))


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def tag(st):
    key = st.lower().split()[0].strip("()")
    cls = {"enacted": "enacted", "proposed": "proposal", "passed": "passed", "failed": "failed",
           "unverified": "unverified", "secondary": "secondary", "fetched": "fetched",
           "excerpt": "excerpt", "link": "link", "user": "user", "derived": "derived",
           "assumption": "assumption"}.get(key, "link")
    return f'<span class="tag t-{cls}">{e(st)}</span>'


def links(ids):
    """Official-source links for one row. An empty list links to the repository record."""
    if not ids:
        return f'<a href="{REPO_URL}/commits/main">repository record</a>'
    out = []
    for i in ids:
        s = C.SOURCES[i]
        out.append(f'<a href="{e(s["url"])}" title="{e(s["title"])}">{e(i)}</a> {tag(s["status"])}')
    return "<br>".join(out)


def table(headers, rows, cls="wide"):
    th = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def card(title, body, cls=""):
    return f'<section class="card {cls}"><h2>{e(title)}</h2>{body}</section>'


def page(filename, title, body, extra_js=""):
    nav = []
    for group, items in NAV:
        links_html = " ".join(
            f'<a href="{h}" class="{"on" if h == filename else ""}">{e(l)}</a>' for h, l in items)
        nav.append(f'<div class="navgroup"><span class="navlabel">{e(group)}</span>{links_html}</div>')
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | Inheritance decision dashboard</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top"><a class="brand" href="index.html">Inheritance decision dashboard</a>
<span class="sub">Property A (Santa Clara County) &middot; Property B (San Francisco) &middot; $ rounded to $10 &middot; checked {CHECKED}</span></header>
<nav class="menu">{''.join(nav)}</nav>
<main>
<h1>{e(title)}</h1>
{body}
</main>
<footer>
<p>Not legal or tax advice. Figures use placeholders for households and are rounded to the nearest $10. Each row shows a source status: FETCHED (official page opened), EXCERPT (official excerpt reviewed), SECONDARY (secondary source, official link given for checking), LINK (official page identified, not opened), ASSUMPTION (modelling choice), DERIVED (computed), USER (household figure held internally), UNVERIFIED (blank).</p>
<p><a href="flagged.html">Flagged for Review</a> &middot; <a href="sources.html">Sources</a> &middot; <a href="{REPO_URL}">Repository</a></p>
</footer>
<script src="assets/app.js"></script>{extra_js}
</body></html>
"""
    with open(os.path.join(ROOT, filename), "w", encoding="utf-8") as f:
        f.write(doc)


# ---------------------------------------------------------------- charts
def svg_lines(series, xs, title, width=860, height=320):
    pl, pr, pt, pb = 84, 16, 28, 40
    allv = [v for _, vals, _ in series for v in vals if v is not None]
    ymax = max(allv) * 1.05

    def X(i):
        return pl + (width - pl - pr) * i / (len(xs) - 1)

    def Y(v):
        return pt + (height - pt - pb) * (1 - v / ymax)

    p = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{e(title)}" class="chart">']
    for k in range(6):
        v = ymax * k / 5
        y = Y(v)
        p.append(f'<line x1="{pl}" x2="{width - pr}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        p.append(f'<text x="{pl - 6}" y="{y + 4:.1f}" text-anchor="end" class="axis">${v / 1e6:.1f}M</text>')
    for i in range(0, len(xs), 5):
        p.append(f'<text x="{X(i):.1f}" y="{height - pb + 16}" text-anchor="middle" class="axis">{xs[i]}</text>')
    for _, vals, color in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4"/>')
    lx = pl
    for label, _, color in series:
        p.append(f'<rect x="{lx}" y="6" width="12" height="12" fill="{color}"/>')
        p.append(f'<text x="{lx + 17}" y="16" class="legend">{e(label)}</text>')
        lx += 40 + 6.3 * len(label)
    p.append("</svg>")
    return "".join(p)


def svg_hist(hist, title, width=860, height=300):
    """Outcome distribution: counts per bin for each path (real 2026 dollars)."""
    pl, pr, pt, pb = 60, 16, 30, 40
    colors = {"S": "#2b6cb0", "R": "#718096", "L": "#dd6b20"}
    names = {"S": "Sell and invest", "R": "Rent", "L": "Live"}
    xmin = min(h["lo"] for h in hist.values())
    xmax = max(h["lo"] + h["width"] * len(h["counts"]) for h in hist.values())
    cmax = max(max(h["counts"]) for h in hist.values())

    def X(v):
        return pl + (width - pl - pr) * (v - xmin) / (xmax - xmin)

    def Y(c):
        return pt + (height - pt - pb) * (1 - c / cmax)

    p = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{e(title)}" class="chart">']
    lx = pl
    for k, h in hist.items():
        p.append(f'<rect x="{lx}" y="8" width="12" height="12" fill="{colors[k]}"/>')
        p.append(f'<text x="{lx + 17}" y="18" class="legend">{names[k]}</text>')
        lx += 150
        pts = []
        for i, c in enumerate(h["counts"]):
            v = h["lo"] + h["width"] * (i + 0.5)
            pts.append(f"{X(v):.1f},{Y(c):.1f}")
        p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colors[k]}" stroke-width="2.2"/>')
    p.append(f'<text x="{pl}" y="{height - 8}" class="axis">${xmin / 1e6:.1f}M</text>')
    p.append(f'<text x="{width - pr}" y="{height - 8}" text-anchor="end" class="axis">${xmax / 1e6:.1f}M (real 2026 $, rounded)</text>')
    p.append(f'<text x="{pl - 6}" y="{pt + 4}" text-anchor="end" class="axis">{cmax}</text>')
    p.append(f'<text x="{pl - 6}" y="{height - pb}" text-anchor="end" class="axis">0</text>')
    p.append("</svg>")
    return "".join(p)


def svg_bars(labels, values, title, width=860):
    rh = 26
    pl, pr = 300, 110
    h = rh * len(labels) + 10
    vmax = max(values)
    p = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="{e(title)}" class="chart">']
    for i, (lab, v) in enumerate(zip(labels, values)):
        y = 5 + i * rh
        bw = (width - pl - pr) * v / vmax
        p.append(f'<text x="{pl - 8}" y="{y + 16}" text-anchor="end" class="axis">{e(lab)}</text>')
        p.append(f'<rect x="{pl}" y="{y + 4}" width="{bw:.1f}" height="16" fill="#2b6cb0"/>')
        p.append(f'<text x="{pl + bw + 6:.1f}" y="{y + 16}" class="axis">{money(v)}</text>')
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- derived helpers
def grid_row(T, H, ap, eq, c):
    for r in GRID:
        if r["T"] == T and r["H"] == H and r["appreciation"] == ap and r["equity"] == eq and abs(r["credit"] - c) < 1e-9:
            return r["results"]
    raise KeyError((T, H, ap, eq, c))


RANGE = {}
for p in PATHS:
    vals = [grid_row(2045, 20, a, q, 0.0)[p] for a in ("low", "base", "high") for q in ("low", "base", "high")]
    RANGE[p] = (min(vals), max(vals))

BE_CREDIT = BE["credit_for_live_to_tie_sell"]
BE_APP_RENT = BE["appreciation_for_rent_to_tie_sell"]
BE_EQ_RENT = BE["equity_for_rent_to_tie_sell"]
BE_APP_LIVE0 = BE["appreciation_for_live_credit0_to_tie_sell"]
NOCRASH_PHASE_COST = 1 - CRASH["No crash|0"]["phase24_20y"] / CRASH["No crash|0"]["lump_20y"]
GRID_PHASE_COST = 1 - BASE["SP24"] / BASE["S"]  # base-case grid: sell now vs park and phase
PROJ45 = next(r for r in PROJ if r["year"] == 2045)
PROJ_YEARS = [r["year"] for r in PROJ]

FACT_COUNT = len(C.PROPERTY_A_FACTS) + len(C.PROPERTY_B_FACTS)
UNVER = sum(1 for r in C.PROPERTY_A_FACTS + C.PROPERTY_B_FACTS if r[2] == "UNVERIFIED")


# ---------------------------------------------------------------- pages
def build_index():
    readiness = card("Decision status: exploratory, not decision-ready", """
<p><strong>No path is endorsed by this dashboard today.</strong> Property A is the future inheritance; Property B is already owned and has existing rental cash flow. Keep Property B as the household's current baseline rather than treating it as inheritance proceeds.</p>
<p>The rankings and projections below are conditional outputs from a published model, not a personalized forecast or recommendation. This checkout does not contain the private input file required to reproduce the model, and key inputs and legal interpretations remain unresolved. Do not rely on the numerical ranking until the private inputs are reviewed and the model is rebuilt.</p>
<p><strong>Decision gates:</strong> obtain a written date-of-death valuation and basis record; confirm estate size, prior taxable gifts and portability; determine intended occupancy and verify Proposition 19 and home-sale exclusion eligibility; obtain market-rent comparables, lease/local-law review, insurance quotes, tax bills and a five-year capital plan; then agree a written investment and loss-tolerance policy before comparing the same transfer-year sale with live, rent, mixed and phased paths.</p>
<p>Start with <a href="questions.html">Questions and gaps</a>, review <a href="flagged.html">Flagged for Review</a>, and check the <a href="inputs.html">Facts and inputs</a> register. Rebuild after evidence or assumptions change.</p>
""", "warn")
    summary = card("Executive summary", f"""
<ul class="bullets">
<li><strong>Conditional model ranking only (not a recommendation):</strong> the current published base-case output ranks a transfer-year sale and lump-sum investment first; phasing over 24 months ranks second. These outputs are not decision-ready until the source inputs and unresolved items are checked.</li>
<li>Base case: transfer in 2045, 20-year horizon, real 2026 dollars, no imputed rent credit. Sell and invest: <strong>{money(BASE['S'])}</strong>. Phased over 24 months: <strong>{money(BASE['SP24'])}</strong>. Rent then sell: <strong>{money(BASE['R'])}</strong>. Live with no rent credit: <strong>{money(BASE['L'])}</strong>.</li>
<li>Living in Property A ties with selling only if the household values avoided rent at about <strong>{pct(BE_CREDIT, 0)}</strong> of market rent.</li>
<li>Phasing is an insurance choice: in the base-case grid it gives up about <strong>{pct(GRID_PHASE_COST, 0)}</strong> of the 20-year value if no crash comes (stylised no-crash test: about {pct(NOCRASH_PHASE_COST, 0)}), and it protects against an early 1929- or 2008-type fall.</li>
<li>Evidence gap: {UNVER} input(s) are UNVERIFIED and left blank. Household inputs are held internally and shown only as placeholders.</li>
</ul>""", "lean")
    change = card("What would change the answer", f"""
<ul class="bullets">
<li><strong>Living in Property A</strong> ties with selling only at an imputed rent credit of about <strong>{pct(BE_CREDIT, 0)}</strong> (base credit 0%).</li>
<li><strong>Renting</strong> ties with selling if Property A's appreciation reaches about <strong>{pct(BE_APP_RENT)}</strong> a year (base {pct(DATA['meta']['base_case'].get('appreciation', 0.025))}), or stock returns fall to about <strong>{pct(BE_EQ_RENT)}</strong> a year.</li>
<li><strong>Phasing in</strong> gives up about <strong>{pct(GRID_PHASE_COST, 0)}</strong> of the base-case 20-year value if no crash comes, and reduces entry risk if a 1929- or 2008-type fall starts while the money is parked.</li>
<li><strong>Prop 19</strong>: if the heir does not live in Property A, the property is reassessed to market on transfer. In 2045 terms (base assumptions), the property tax on the reassessed value is about <strong>{money(PROJ45['property_tax_if_rented'])}</strong> a year, against about <strong>{money(PROJ45['property_tax_if_living'])}</strong> if the Prop 19 base applies.</li>
<li><strong>Unknowns that could move the answer:</strong> the valuation at date of death, Property A's market rent, insurance quotes, estate size against the federal exclusion, and the heir's occupancy plan.</li>
</ul>""", "")
    risk = card("Reinvestment risk (beside every headline)", f"""
<p>Sell and invest: the 10th-percentile outcome is <strong>{money(MC['S']['p10'])}</strong> and the 90th is <strong>{money(MC['S']['p90'])}</strong> (simulated, base distribution).</p>
<p>Phased over 24 months: <strong>{money(MC['SP24']['p10'])}</strong> to <strong>{money(MC['SP24']['p90'])}</strong>. Rent then sell: <strong>{money(MC['R']['p10'])}</strong> to <strong>{money(MC['R']['p90'])}</strong>.</p>
<p class="note">These are assumption-based distributions, not forecasts. The Paths page lets you change the assumptions.</p>""", "risk")
    rows = []
    for p in ORDER:
        lo, hi = RANGE[p]
        rows.append([
            e(SHORT[p]),
            money(BASE[p]),
            e(f"{money(lo)} to {money(hi)}"),
            e(f"{money(MC[p]['p10'])} to {money(MC[p]['p90'])}"),
            links(PATH_SOURCES[p] + ["MODEL"]),
        ])
    results = table(["Path", "Base case (real 2026 $)", "Range across growth and stock-return cases", "Simulated 10th to 90th percentile", "Sources"], rows)
    res = card("All paths: transfer 2045, 20-year horizon", "<p>Each path is liquidated after tax at the horizon so liquid and illiquid choices compare fairly. Real 2026 dollars, rounded to $10.</p>" + results)
    ev = card("Evidence status", f"""<p>{FACT_COUNT} input rows are on the Facts page. {UNVER} are UNVERIFIED and left blank. Household figures are held internally and are not published. Secondary-source figures are labelled and linked for checking. Irregularities are on the <a href="flagged.html">Flagged for Review</a> page.</p>""")
    nav = "".join(
        f'<a class="navcard" href="{h}"><strong>{e(l)}</strong><span>{e(g)}</span></a>'
        for g, items in NAV for h, l in items if h != "index.html")
    body = readiness + summary + change + risk + res + ev + f"<section><h2>Go to</h2><div class='navgrid'>{nav}</div></section>"
    page("index.html", "Dashboard", body)


def build_paths():
    grid_json = json.dumps(GRID, separators=(",", ":"))
    controls = card("What-if controls", """
<p>Change a setting. Results come from the precomputed model grid (the same numbers as the tables); the grid is not re-simulated in the browser. The highest displayed number is a conditional model result, not a recommendation, and inherits all flagged input and source limitations.</p>
<div class="controls">
<label>Transfer year<select id="w-T"><option>2040</option><option selected>2045</option><option>2050</option></select></label>
<label>Horizon (years after transfer)<select id="w-H"><option>10</option><option selected>20</option></select></label>
<label>Property A appreciation<select id="w-ap"><option value="low">Low (0.0%)</option><option value="base" selected>Base (2.5%)</option><option value="high">High (4.5%)</option></select></label>
<label>Stock returns<select id="w-eq"><option value="low">Low (4.0%)</option><option value="base" selected>Base (6.5%)</option><option value="high">High (8.5%)</option></select></label>
<label>Imputed rent credit (living)<select id="w-c"><option value="0">0% (no credit)</option><option value="0.5">50%</option><option value="1">100% (full market rent)</option></select></label>
</div>
<div id="w-out"></div>
<script type="application/json" id="grid-data">""" + grid_json + "</script>")
    defs = table(["Path", "What it means", "Occupancy", "Tax points that matter"], [
        [e("S"), e(PATHS["S"]), "none", links(PATH_SOURCES["S"])],
        [e("SP24 / SP36"), e(PATHS["SP24"]), "none", links(PATH_SOURCES["SP24"])],
        [e("R"), e(PATHS["R"]), "tenants", links(PATH_SOURCES["R"])],
        [e("L"), e(PATHS["L"]), "primary residence", links(PATH_SOURCES["L"])],
        [e("L2S / L5S"), "Mixed: live 2 or 5 years, then sell", "2 or 5 years", links(PATH_SOURCES["L2S"])],
        [e("R10S"), "Mixed: rent 10 years, then sell", "rented", links(PATH_SOURCES["R10S"])],
        [e("L5R_A / L5R_B"), "Mixed: live 5 years, then rent", "5 years, then rented", links(PATH_SOURCES["L5R_A"])],
    ])
    rows = []
    for T in (2040, 2045, 2050):
        for H in (10, 20):
            r = grid_row(T, H, "base", "base", 0.0)
            rc = grid_row(T, H, "base", "base", 1.0)
            rows.append([str(T), str(H)] + [money(r[p]) for p in ORDER] + [money(rc["L"]), links(["MODEL", "TREASURY-YIELD", "IRS-PUB-523"])])
    combos = table(["Transfer", "Horizon"] + [SHORT[p] for p in ORDER] + ["Live with full rent credit", "Sources"], rows)
    be_rows = [
        [e("Imputed rent credit at which living ties with selling"), pct(BE_CREDIT, 1), links(["MODEL"])],
        [e("Property A appreciation at which renting ties with selling"), pct(BE_APP_RENT, 2), links(["MODEL", "IRS-PUB-527"])],
        [e("Stock return at which renting ties with selling"), pct(BE_EQ_RENT, 2), links(["MODEL", "TREASURY-YIELD"])],
        [e("Property A appreciation at which living (0% credit) ties with selling"), pct(BE_APP_LIVE0, 2), links(["MODEL", "BOE-PROP19-INTRO"])],
    ]
    be = table(["Break-even", "Value", "Sources"], be_rows)
    mcrows = [[e(SHORT[p]), money(MC[p]["p10"]), money(MC[p]["p50"]), money(MC[p]["p90"]), money(MC[p]["mean"]), links(["MODEL"])] for p in ORDER]
    mc = table(["Path", "10th percentile", "Median", "90th percentile", "Mean", "Sources"], mcrows)
    body = (
        controls
        + card("Pure and mixed paths, same transfer dates and horizons",
               "<p>Real 2026 dollars, rounded to $10, imputed rent credit 0% unless stated. The last column shows living in Property A with a full market-rent credit.</p>" + combos)
        + card("Break-evens: what would change the answer", be)
        + card("Distribution of outcomes (simulated)",
               "<p>2,000 simulated paths (fixed seed). Annual stock returns: normal, mean 6.5%, standard deviation 15%. Property A appreciation: normal, mean 2.5%, standard deviation 4%. These are assumptions, not forecasts.</p>"
               + mc + '<div class="chartbox">' + svg_hist(HIST, "Distribution of simulated outcomes") + "</div>")
        + card("Path definitions", defs)
    )
    page("paths.html", "Paths and what-if", body)


def build_projections():
    xs = PROJ_YEARS
    series = [
        ("Taxable value if heir lives in A (Prop 19)", [r["taxable_if_living_prop19"] for r in PROJ], "#2b6cb0"),
        ("Taxable value if rented (reassessed)", [r["taxable_if_rented"] for r in PROJ], "#dd6b20"),
        ("Assessed value, no transfer (Prop 13)", [r["assessed_no_transfer"] for r in PROJ], "#718096"),
        ("Market value (base 2.5%)", [r["market_value"] for r in PROJ], "#2f855a"),
    ]
    chart = svg_lines(series, xs, "Property A projection (base case, transfer 2045)")
    rows = []
    for r in PROJ:
        if r["year"] % 5 == 0 or r["year"] in (2027, 2045):
            rows.append([str(r["year"]), money(r["market_value"]), money(r["assessed_no_transfer"]),
                         money(r["taxable_if_living_prop19"]), money(r["taxable_if_rented"]),
                         money(r["property_tax_if_living"]), money(r["property_tax_if_rented"]),
                         links(["BOE-LTA-2026-002", "BOE-PROP19-INTRO", "MODEL"])])
    tbl = table(["Year", "Market value", "Assessed (no transfer)", "Taxable if living (Prop 19)", "Taxable if rented",
                 "Property tax if living", "Property tax if rented", "Sources"], rows)
    body = (
        "<p>Base case: transfer in 2045, appreciation 2.5%, Prop 13 factor 2% a year. The Prop 19 line applies if the heir lives in Property A and qualifies; the reassessed line applies if the property is rented. Costs of insurance, water, and maintenance are not shown here because they are household figures held internally.</p>"
        + f'<div class="chartbox">{chart}</div>'
        + card("Property A, every five years", tbl)
        + card("Property B (already owned by the heir)",
               "<p>Property B is not inherited, but its cash flow affects the household's choice. It is held constant here. A year-by-year projection needs the leases and the Measure H tier for the building (see Facts).</p>")
    )
    page("projections.html", "Projections", body)


def build_inputs():
    a_rows = [[e(l), e(v) if v else "blank (UNVERIFIED)", tag(s), links(src), e(n)] for l, v, s, src, n in C.PROPERTY_A_FACTS]
    b_rows = [[e(l), e(v) if v else "blank (UNVERIFIED)", tag(s), links(src), e(n)] for l, v, s, src, n in C.PROPERTY_B_FACTS]
    body = (
        "<p>Household figures are held internally and appear here only as placeholders. Official values are shown where a source was checked. Blank cells are UNVERIFIED.</p>"
        + card("Property A (Santa Clara County): facts and inputs", table(["Item", "Figure", "Status", "Source", "Note"], a_rows))
        + card("Property B (San Francisco): facts and inputs", table(["Item", "Figure", "Status", "Source", "Note"], b_rows))
        + card("Not published", "<p>Historical tax and assessment records, parcel numbers, addresses, and household cost bills are not published. They are checked outside this repository and recorded as flags where they affect the decision.</p>")
    )
    page("inputs.html", "Facts and inputs", body)


def build_blackswan():
    base_rows = [
        ["Inflation (PCE)", "2.7% in 2026, falling to 2.0% by 2030", "2.0% long-run (model deflator)", links(["CBO-OUTLOOK-2026"])],
        ["3-month Treasury, Nov 24, 2026", "4.36%", "3.5% after tax (parking, assumption)", links(["TREASURY-YIELD"])],
        ["2-year Treasury, Nov 24, 2026", "4.63%", "parked money in the 3-month to 2-year range", links(["TREASURY-YIELD"])],
        ["10-year Treasury, Nov 24, 2026", "4.91%; CBO projects about 4.4% in 2031-35", "4.4% bond return (CBO anchor)", links(["TREASURY-YIELD", "CBO-OUTLOOK-2026"])],
        ["Property A appreciation", "not sourced", "2.5% base; 0.0% low; 4.5% high", links(["MODEL"])],
        ["Stock returns (nominal)", "not sourced", "6.5% base; 4.0% low; 8.5% high", links(["MODEL"])],
    ]
    base_tbl = table(["Indicator", "Official or sourced value", "Model setting", "Sources"], base_rows)
    stress_rows = [
        ["Baseline (CBO-type path)", "inflation falling to 2.0%; real growth about 1.8%", "base case of this site", links(["CBO-OUTLOOK-2026"])],
        ["1929-type fall at sale", "stock decline of 86.2% (secondary), recovery modelled at 300 months", "stylised crash test (below)", links(["SP-DRAWDOWN"])],
        ["2008-type fall at sale", "stock decline of 56.8% (secondary), recovery modelled at 66 months", "stylised crash test (below); recovery reported as about 4.5 to 5.5 years", links(["SP-DRAWDOWN"])],
        ["Housing stagnation", "0.0% nominal appreciation for 20 years", "low appreciation case", links(["MODEL"])],
    ]
    stress_tbl = table(["Regime", "Description", "How the site uses it", "Sources"], stress_rows)
    rows = []
    for name in ("1929-type", "2008-type", "No crash"):
        for st in (0, 12, 24, 36):
            r = CRASH[f"{name}|{st}"]
            rows.append([name, f"month {st}",
                         f"{r['lump_10y']:.2f}x", f"{r['phase24_10y']:.2f}x", f"{r['phase36_10y']:.2f}x",
                         f"{r['lump_20y']:.2f}x", f"{r['phase24_20y']:.2f}x", f"{r['phase36_20y']:.2f}x",
                         links(["SP-DRAWDOWN", "MODEL"])])
    crash_tbl = table(["Fall type", "Fall starts", "Lump sum 10y", "Phase 24m 10y", "Phase 36m 10y",
                       "Lump sum 20y", "Phase 24m 20y", "Phase 36m 20y", "Sources"], rows)
    body = (
        card("Economic conditions: baseline", "<p>The baseline is the official near-term projection. The stress cases are tests, not forecasts.</p>" + base_tbl)
        + card("Black swan regimes", stress_tbl)
        + card("Phased investing test (1929 and 2008 entry risk)",
               "<p>Money is sold and held in 3-month to 2-year Treasuries (parking, taxed as ordinary income at an assumed 40%). It is then bought into stocks in equal steps over 12 months. The test uses the depth and timing of the two falls, not a daily replay. Each cell is the multiple of starting capital after tax (1.00x = no change).</p>"
               + crash_tbl
               + f"<p class='note'>Reading the table: phasing helps when a fall begins during the parking window. With no crash, a 24-month phase-in gives up about {pct(NOCRASH_PHASE_COST, 0)} of the 20-year value in this stylised test (about {pct(GRID_PHASE_COST, 0)} in the base-case grid, where the stock path differs).</p>")
        + card("Decision points for this test", """<ul class="bullets">
<li>Parking is a hedge against entry timing, not a return enhancement.</li>
<li>A fall that starts after the parking window leaves the lump sum and the phase-in close; luck decides which one wins.</li>
<li>Parked money earns less than stocks in a calm market. The household accepts a lower median to buy protection.</li>
</ul>""")
    )
    page("blackswan.html", "Black swan and phased investing", body)


def law_page(filename, title, intro, topics):
    rows = [[e(a), e(b), tag(c), links(d), e(f)] for a, b, c, d, f in C.LAW_ROWS if a in topics]
    body = f"<p>{e(intro)}</p>" + table(["Topic", "Rule", "Status", "Sources", "What it means here"], rows)
    page(filename, title, body)


def build_law_pages():
    law_page("estate-tax.html", "Estate tax",
             "Federal estate and gift tax: exclusion, portability and prior gifts. Estate size is unknown; the estate-tax module is not in the base model.",
             {"Federal estate and gift exclusion, deaths in 2026", "Federal exclusion, deaths in 2027",
              "Annual gift exclusion", "Portability of unused exclusion"})
    law_page("income-basis.html", "Income-tax basis",
             "Basis, sale gains, and income tax in the transfer year. Section 121, depreciation, and the state surcharge matter for a sale.",
             {"Basis at death (step-up)", "Capital gains rates (federal, 2026)", "Section 121 home-sale exclusion",
              "Like-kind exchange (section 1031)", "Depreciation of rental property", "California tax on capital gains",
              "Trust and estate income tax", "Solar net billing (NEM 3.0)"})
    law_page("property-tax.html", "Property-tax assessment",
             "Prop 13 and Prop 19: how the assessed value changes at transfer and whether the heir's occupancy keeps the Prop 19 base.",
             {"Prop 13 (property tax)", "Prop 19 parent-child exclusion (family home)", "Prop 19 claim filing window",
              "Prop 19 after the heir moves out", "SB 974 (special needs trusts and Prop 19)",
              "San Francisco documentary transfer tax", "Santa Clara County documentary transfer tax",
              "SF Measure H parcel tax (Muni)"})
    law_page("tax-law.html", "All enacted law",
             "Every row shows a status. ENACTED rows are current law as stated by the source. Secondary rows must be checked on the official link before use.",
             {r[0] for r in C.LAW_ROWS})


def build_legislation():
    rows = [[e(a), tag(b), e(c), links(d), e(f)] for a, b, c, d, f in C.LEGISLATION]
    body = ("<p>Proposals are listed separately from enacted law. None is in the base model. Bill numbers and texts were not verified in this session; check Congress.gov and the state legislature before relying on them.</p>"
            + table(["Measure", "Status", "Notes", "Sources", "Effect if enacted (not modelled)"], rows)
            + card("Recheck schedule", """<ul class="bullets">
<li>Monthly: bill status on Congress.gov and the California Legislature site (manual).</li>
<li>Each rate change: IRS inflation release (October or November) and BOE inflation letter (early in the year).</li>
<li>Before any decision: the Treasury curve, the HUD Fair Market Rent notice (October 1), and the SF election certification.</li>
</ul>"""))
    page("legislation.html", "Proposed and reported", body)


def build_timeline():
    rows = [[e(a), e(b), e(c), links(d)] for a, b, c, d in C.TIMELINE]
    body = ("<p>Steps from date of death. Dates are the deadlines shown on the linked sources; check them against the trust's own calendar.</p>"
            + table(["When", "Action", "Why", "Sources"], rows))
    page("timeline.html", "Deadlines timeline", body)


def build_questions():
    items = "".join(f'<li><strong>{e(a)}:</strong> {e(b)}<br><span class="note">Why it matters: {e(c)}. How to get it: {e(d)}.</span></li>'
                    for a, b, c, d in C.QUESTIONS)
    body = ("<p>Questions and information needed before a decision. These are not values; they have no source to link. Household answers are kept internally.</p>"
            + card("Questions and information gaps", f'<ul class="bullets">{items}</ul>'))
    page("questions.html", "Questions and gaps", body)


def build_decision_rules():
    items = "".join(f'<li><strong>{e(a)}.</strong> {e(b)} <span class="note">Basis: {e(c)}</span></li>' for a, b, c in C.DECISION_RULES)
    body = (card("Status: DRAFT, not yet signed",
                 f"<p>Drafted {CHECKED} from preliminary figures. The rules are proposed until the household confirms or edits each one, records the date, and signs outside this public repository.</p>", "warn")
            + card("Proposed decision rules", f'<ul class="bullets">{items}</ul>'))
    page("decision-rules.html", "Decision rules", body)


def build_suggestions():
    items = "".join(f'<li><strong>{e(a)}.</strong> {e(b)}. <span class="note">Why: {e(c)}.</span> {tag(d)} &nbsp; <span class="choice">[ ] approve</span></li>'
                    for a, b, c, d in C.SUGGESTIONS)
    body = ("<p>Suggestions for approval before implementation. None has been implemented. Mark the ones to implement by ID.</p>"
            + card("Suggestions", f'<ul class="bullets">{items}</ul>'))
    page("suggestions.html", "Suggestions", body)


def build_flagged():
    rows = [[e(a), e(b), e(c), links(d)] for a, b, c, d in C.IRREGULARITIES]
    body = (card("Flagged for Review", "<p>These items do not block the site. Each has its source link so the household can review it and request a change.</p>", "warn")
            + table(["Item", "What we found", "Action needed", "Sources"], rows)
            + card("Repository and privacy", """<ul class="bullets">
<li>Containment is partial: the current Pages configuration excludes alternate generated site trees and source folders, but the GitHub repository remains public and those tracked files and historical commits can still be fetched directly.</li>
<li>The earlier pre-rounding history was not scrubbed in this change. The current checkout does not provide the earlier objects needed to inspect or safely rewrite that history.</li>
<li>The root checker runs artifact and structural checks in a clean checkout; its exact household-value comparison explicitly reports SKIP when the offline private input file is absent. That skip is not a full household-signature privacy scan.</li>
</ul>"""))
    page("flagged.html", "Flagged for review", body)


def build_brief():
    facts = [
        ("Property A (Santa Clara County): value, Nov 2026", "held internally (household estimate; not an appraisal)"),
        ("Property A: Prop 19 allowance", "$1,044,586 (BOE LTA 2025/009, read)"),
        ("Property A: Prop 13 factor", "1.02 a year (BOE, secondary)"),
        ("Property B (San Francisco): units", "three livable units; two rented; owner occupancy possible"),
        ("Federal exclusion, per person", "$15,000,000 (2026; IRS); $15,480,000 (2027; secondary)"),
        ("Measure H (SF parcel tax)", "passed, preliminary, 74.42% yes; certification due by Dec 3, 2026"),
        ("Base result, sell and invest (2045, 20 yr)", money(BASE["S"])),
        ("Base result, live with no rent credit", money(BASE["L"])),
    ]
    qa = ["Is the trust funded for Property A, and what is the date-of-death valuation plan?",
          "Is portability to be elected, and were prior taxable gifts made (Form 709)?",
          "Will the heir occupy Property A within one year; when is the homeowners' exemption filed?",
          "Who files the BOE-19-P claim, and when is it calendared?",
          "Counsel to confirm the Prop 19 reading after a move-out (reading A or B)."]
    qc = ["Basis at date of death and the transfer-year sale (step-up; section 121 if the heir lives there).",
          "Confirm the 1% Behavioral Health Services Tax and the state rate on large gains.",
          "Depreciation and recapture if Property A is rented; the land share is needed.",
          "Solar credit tariff (NEM 3.0 or earlier) and property tax on the Prop 19 base.",
          "Trust income tax: compressed brackets if sale income stays in the trust."]
    dl = ["Day 0: date of death; appraisal at date of death.",
          "9 months: Form 706 if required or to elect portability (6-month extension on Form 4768).",
          "Within 1 year: occupancy and homeowners' exemption (Prop 19 only).",
          "Within 3 years of transfer: BOE-19-P claim (secondary).",
          "Within 5 years: late portability relief (Rev. Proc. 2022-32; secondary)."]
    src_for = {
        "Property A (Santa Clara County): value, Nov 2026": ["HOUSEHOLD"],
        "Property A: Prop 19 allowance": ["BOE-LTA-2025-009"],
        "Property A: Prop 13 factor": ["BOE-LTA-2026-002"],
        "Property B (San Francisco): units": ["SF-RENT-BOARD"],
        "Federal exclusion, per person": ["IRS-IR-2025-103", "IRS-NEWS-2027"],
        "Measure H (SF parcel tax)": ["SF-ELECTIONS-2026"],
        "Base result, sell and invest (2045, 20 yr)": ["MODEL"],
        "Base result, live with no rent credit": ["MODEL"],
    }
    frow = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{links(src_for[a])}</td></tr>" for a, b in facts)
    body = f"""
<section class="brief">
<div class="briefhead"><strong>Attorney &amp; CPA Briefing Sheet</strong> &middot; Property A (Santa Clara County, inherited) and Property B (San Francisco, owned) &middot; prepared {CHECKED} &middot; placeholders for all names</div>
<div class="cols">
<div>
<h3>1. Key facts (household figures held internally)</h3>
<table class="brieftbl"><tbody>{frow}</tbody></table>
<h3>2. Results (real 2026 $, transfer 2045, 20 years, rounded to $10)</h3>
<p>Conditional model outputs only, not a recommendation: sell and invest {money(BASE['S'])}; phased over 24 months {money(BASE['SP24'])}; rent then sell {money(BASE['R'])}; live with no rent credit {money(BASE['L'])}. Living ties with selling only at a rent credit of about {pct(BE_CREDIT, 0)}. The private inputs are unavailable in this checkout, so the figures cannot be reproduced here; verify the flagged assumptions and rebuild before relying on them.</p>
<h3>3. Deadlines</h3><ul>{''.join(f'<li>{e(x)}</li>' for x in dl)}</ul>
</div>
<div>
<h3>4. Questions for counsel</h3><ul>{''.join(f'<li>{e(x)}</li>' for x in qa)}</ul>
<h3>5. Questions for the CPA</h3><ul>{''.join(f'<li>{e(x)}</li>' for x in qc)}</ul>
<h3>6. Law status</h3>
<ul><li>Enacted: federal $15,000,000 exclusion (2026); Prop 19 family-home rules; 1% state surcharge over $1,000,000.</li>
<li>Proposed or reported, not enacted: federal estate-tax changes (not in the model).</li>
<li>Secondary, to check: SF transfer-tax tiers (unverified); 2027 federal figures; SB 974.</li></ul>
<h3>7. Flags</h3><ul><li>Property A market rent and insurance: unverified.</li><li>Historical tax records: check against bills.</li><li>Prop 19 move-out reading: counsel to confirm.</li></ul>
</div></div>
<p class="foot">Sources: IRS IR-2025-103 and What's new (estate and gift tax); FTB Form 540-ES instructions; U.S. Treasury yield table; CBO Feb 2026 outlook; SF Department of Elections (Nov 3, 2026, preliminary). Full register: sources.html. Not legal or tax advice.</p>
</section>"""
    page("brief.html", "Attorney and CPA briefing sheet", body)


def build_glossary():
    dl = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in C.GLOSSARY)
    page("glossary.html", "Glossary", card("Terms", f"<dl class='gloss'>{dl}</dl>"))


def build_sources():
    rows = []
    for k, s in C.SOURCES.items():
        rows.append([e(k), e(s["publisher"]), f'<a href="{e(s["url"])}">{e(s["title"])}</a>', tag(s["status"]), e(CHECKED)])
    body = ("<p>Every row on the site links to one of these entries. FETCHED and EXCERPT entries were checked in this session. SECONDARY entries repeat an official rule and must be checked on the link before relying on them. LINK entries were identified but not opened.</p>"
            + table(["ID", "Publisher", "Title and link", "Status", "Checked"], rows))
    page("sources.html", "Sources", body)


def write_irregularities_json():
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    out = [{"item": a, "found": b, "action": c, "sources": d} for a, b, c, d in C.IRREGULARITIES]
    with open(os.path.join(ROOT, "data", "irregularities.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_assets():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    css = """
:root{--ink:#1a202c;--mut:#4a5568;--line:#e2e8f0;--bg:#f7fafc;--acc:#2b6cb0}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
header.top{background:#1a365d;color:#fff;padding:12px 20px;display:flex;flex-wrap:wrap;gap:12px;align-items:baseline}
header.top .brand{color:#fff;font-weight:700;text-decoration:none;font-size:18px}
header.top .sub{opacity:.85;font-size:13px}
nav.menu{background:#fff;border-bottom:1px solid var(--line);padding:10px 20px;display:flex;flex-wrap:wrap;gap:14px 22px}
.navgroup{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.navlabel{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin-right:2px}
nav.menu a{color:var(--acc);text-decoration:none;padding:3px 7px;border-radius:5px;font-size:13.5px}
nav.menu a.on{background:var(--acc);color:#fff}
main{max-width:1180px;margin:0 auto;padding:18px 20px 40px}
h1{font-size:25px;margin:8px 0 12px}
h2{font-size:18px;margin:4px 0 10px}
h3{font-size:14px;margin:12px 0 6px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.card.warn{background:#fff5e6;border-color:#f6ad55}
.card.lean{background:#ebf8ff;border-color:#90cdf4}
.card.risk{background:#fffaf0}
.bullets li{margin:6px 0}
.note,.small{color:var(--mut);font-size:13px}
.tablewrap{overflow-x:auto;margin:8px 0}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px}
table.wide{min-width:760px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#edf2f7;font-weight:600}
.tag{display:inline-block;font-size:10.5px;letter-spacing:.04em;padding:1px 6px;border-radius:4px;background:#e2e8f0;color:#2d3748;vertical-align:middle}
.t-fetched,.t-excerpt,.t-enacted{background:#c6f6d5}.t-secondary,.t-passed{background:#fefcbf}.t-link{background:#e2e8f0}
.t-user{background:#bee3f8}.t-derived{background:#e9d8fd}.t-assumption{background:#feebc8}.t-unverified,.t-proposal{background:#fed7d7}.t-failed{background:#e2e8f0}
.navgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.navcard{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px;color:var(--ink);text-decoration:none}
.navcard span{display:block;color:var(--mut);font-size:13px;margin-top:4px}
.controls{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin:8px 0 12px}
.controls label{display:flex;flex-direction:column;font-size:13px;color:var(--mut)}
.controls select{margin-top:4px;padding:6px;font-size:14px;border:1px solid #cbd5e0;border-radius:6px;background:#fff}
.wbar{display:grid;grid-template-columns:300px 1fr 150px;gap:10px;align-items:center;margin:5px 0;font-size:14px}
.wbar .bar{height:14px;background:var(--acc);border-radius:3px;display:block}
.chart{width:100%;height:auto}
.chart .grid{stroke:#e2e8f0}
.chart .axis{font-size:11px;fill:#4a5568}
.chart .legend{font-size:12px;fill:#2d3748}
.chartbox{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px;margin:12px 0;overflow-x:auto}
dl.gloss dt{font-weight:700;margin-top:10px}
dl.gloss dd{margin:2px 0 0 0;color:#2d3748}
.choice{color:var(--mut);font-size:12.5px}
.brief{background:#fff;border:1px solid var(--line);padding:14px 16px;font-size:11.5px;line-height:1.35}
.brief h3{font-size:12.5px;margin:6px 0 3px}
.brief .briefhead{border-bottom:2px solid #1a365d;padding-bottom:4px;margin-bottom:6px;font-size:12px}
.brief .cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.brief ul{margin:2px 0 4px 16px;padding:0}
.brief li{margin:1px 0}
.brieftbl td{border:none;padding:1px 4px 1px 0;font-size:11.5px}
.brief .foot{font-size:10px;color:var(--mut);margin:6px 0 0}
footer{max-width:1180px;margin:0 auto;padding:10px 20px 30px;color:var(--mut);font-size:12.5px}
@media print{
  @page{size:letter;margin:.45in}
  body{background:#fff;font-size:10px}
  header.top,nav.menu,footer,.noprint,.controls{display:none}
  main{max-width:none;padding:0}
  .brief{border:none;padding:0;font-size:9px;line-height:1.2}
  .brief .cols{gap:10px}
}
"""
    js = """// Dependency-free what-if: reads the precomputed grid only (no re-simulation in the browser).
(function(){
  var el = document.getElementById('grid-data');
  if(!el) return;
  var grid = JSON.parse(el.textContent);
  var labels = {S:'Sell in transfer year, invest lump sum',SP24:'Sell, park 24 months, then phase in',SP36:'Sell, park 36 months, then phase in',
    L2S:'Mixed: live 2 years, then sell',R10S:'Mixed: rent 10 years, then sell',R:'Rent long-term, sell at horizon',
    L5S:'Mixed: live 5 years, then sell',L5R_A:'Mixed: live 5 years, then rent (reading A)',L5R_B:'Mixed: live 5 years, then rent (reading B)',
    L:'Live long-term, sell at horizon'};
  var order = ['S','SP24','SP36','L2S','R10S','R','L5S','L5R_A','L5R_B','L'];
  function v(id){ return document.getElementById(id).value; }
  function money(x){ return '$' + (Math.round(x/10)*10).toLocaleString('en-US'); }
  function render(){
    var T = parseInt(v('w-T'),10), H = parseInt(v('w-H'),10), ap = v('w-ap'), eq = v('w-eq'), c = parseFloat(v('w-c'));
    var row = grid.find(function(r){ return r.T===T && r.H===H && r.appreciation===ap && r.equity===eq && Math.abs(r.credit-c)<1e-9; });
    var out = document.getElementById('w-out');
    if(!row){ out.textContent = 'No grid row for these settings.'; return; }
    var max = Math.max.apply(null, order.map(function(p){ return row.results[p]; }));
    var best = order.reduce(function(a,p){ return row.results[p] > row.results[a] ? p : a; }, order[0]);
    var html = '<p><strong>Largest model output for these settings (not a recommendation):</strong> ' + labels[best] + ' (' + money(row.results[best]) + ', real 2026 dollars).</p>';
    order.forEach(function(p){
      var w = Math.max(2, Math.round(100 * row.results[p] / max));
      html += '<div class="wbar"><span>' + labels[p] + '</span><span><span class="bar" style="width:' + w + '%"></span></span><strong>' + money(row.results[p]) + '</strong></div>';
    });
    html += '<p class="note">Settings: transfer ' + T + ', horizon ' + H + ' years, appreciation ' + ap + ', stock returns ' + eq + ', imputed rent credit ' + Math.round(c*100) + '%. Liquidated after tax; rounded to $10.</p>';
    out.innerHTML = html;
  }
  ['w-T','w-H','w-ap','w-eq','w-c'].forEach(function(id){ var n=document.getElementById(id); if(n) n.addEventListener('change', render); });
  render();
})();
"""
    open(os.path.join(ROOT, "assets", "style.css"), "w", encoding="utf-8").write(css.lstrip())
    open(os.path.join(ROOT, "assets", "app.js"), "w", encoding="utf-8").write(js.lstrip())


def build_exec_pages():
    pass


def main():
    write_assets()
    build_index()
    build_paths()
    build_projections()
    build_inputs()
    build_blackswan()
    build_law_pages()
    build_legislation()
    build_timeline()
    build_questions()
    build_decision_rules()
    build_suggestions()
    build_flagged()
    build_brief()
    build_glossary()
    build_sources()
    write_irregularities_json()
    # Keep Jekyll enabled so _config.yml exclusions constrain the Pages artifact.
    print("site built:", len(PAGES_NAV), "navigation pages")


if __name__ == "__main__":
    main()
