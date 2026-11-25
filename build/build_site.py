"""Static site builder: reads data/*.json and writes docs/*.html (GitHub Pages).
Every number is rounded to the nearest $10. Unverified inputs are blank and flagged.
Privacy: no names, addresses, parcel numbers, or ZIP codes are written by this script."""
import json, os, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda n: json.load(open(os.path.join(ROOT, "data", n)))
INP = D("inputs.json"); SRC = D("sources.json"); PRJ = D("projections.json"); FLG = D("flags.json")
SRC_BY = {s["id"]: s for s in SRC["sources"]}
INP_BY = {x["id"]: x for x in INP["inputs"]}
OUTDIR = os.path.join(ROOT, "docs")
ASOF = "2026-11-25"
VERIFIED = {"V-PRIMARY", "V-SNIPPET", "OWNER"}   # owner-provided values are shown but labelled

def r10(x):
    return int(round(x / 10.0)) * 10

def m(x):  # money, nearest $10
    if x is None: return "—"
    v = int(round(x / 10.0)) * 10
    return ("-$" if v < 0 else "$") + f"{abs(v):,}"
def pct(x, d=2): return "—" if x is None else f"{x:.{d}f}%"
def e(s): return html.escape(str(s))
def link(sid):
    s = SRC_BY.get(sid)
    if not s or s["url"].startswith("internal:"): return e(sid) + " (internal, not published)"
    if not s: return e(sid)
    return f'<a href="{e(s["url"])}" rel="noopener">{e(sid)}</a>'
def links(ids): return " ".join(link(i) for i in ids) if ids else '<span class="flag">no source</span>'
def badge(lvl):
    cls = {"V-PRIMARY":"ok","V-SNIPPET":"ok","OWNER":"own","S-SECONDARY":"warn","ASSUMPTION":"warn"}.get(lvl,"warn")
    return f'<span class="badge {cls}">{e(lvl)}</span>'

CSS = """
body{font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif;margin:0;color:#1d2433;background:#f6f7fb}
header{background:#1d2b4a;color:#fff;padding:14px 22px}header a{color:#cfe0ff}
nav a{margin-right:14px;color:#cfe0ff;text-decoration:none}
main{max-width:1180px;margin:0 auto;padding:20px}
h1{font-size:26px;margin:6px 0}h2{font-size:19px;margin-top:28px;border-bottom:2px solid #d9dfeb;padding-bottom:4px}
.card{background:#fff;border:1px solid #dfe4ee;border-radius:10px;padding:14px 16px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.kpi b{font-size:22px;display:block}.kpi span{color:#56607a;font-size:13px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px;margin:8px 0}
th,td{border:1px solid #e1e6f0;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef2fa}td.n{text-align:right;white-space:nowrap}
.badge{font-size:11px;padding:1px 6px;border-radius:8px;white-space:nowrap}
.badge.ok{background:#dff5e6;color:#17622c}.badge.warn{background:#fff1d6;color:#7a4b00}.badge.own{background:#e5ecff;color:#1d3a8a}
.flag{color:#a33;font-weight:600}.blank{background:#fff7e0;color:#7a4b00}
.warnbox{border-left:5px solid #d98c00;background:#fffaf0;padding:10px 14px;border-radius:6px}
.small{color:#56607a;font-size:12.5px}
@media print{header nav,.noprint{display:none}body{background:#fff}.card{border:none}main{max-width:none}}
"""

def page(name, title, body, extra_head=""):
    nav = " ".join(f'<a href="{f}">{t}</a>' for f, t in NAV)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · Inheritance decision analysis</title>
<style>{CSS}</style>{extra_head}</head><body>
<header><div><b>Inheritance decision analysis</b> · as of {ASOF} · all $ rounded to nearest $10 · 2026 dollars unless stated</div>
<nav>{nav}</nav></header><main>
<h1>{e(title)}</h1>{body}
<p class="small">Not legal or tax advice. Verify with an attorney and CPA. Private family data is held internally and is not published.</p>
</main></body></html>"""
    open(os.path.join(OUTDIR, name), "w").write(doc)

NAV = [("index.html","Home"),("executive.html","Executive summary"),("paths.html","Paths"),
       ("blackswan.html","Black Swan"),("inputs.html","Inputs"),("tax.html","Tax law"),
       ("deadlines.html","Deadlines"),("triggers.html","Decision triggers"),("flagged.html","Flagged for Review"),
       ("briefing.html","Attorney & CPA sheet"),("glossary.html","Glossary"),("sources.html","Sources")]

R = PRJ["results"]; B = R["base"]
def cell(s, T, H, path): return R[s][str(T)][str(H)][path]
rank_base = sorted(B["2045"]["10"], key=lambda k: -B["2045"]["10"][k]["total_real"])
rec = PRJ["recommendation_check"]
mc = PRJ["monte_carlo"]; rr = PRJ["reinvestment_risk"]; bs = PRJ["blackswan_entry_test"]
sens = PRJ["sensitivity"]
flips = [r for r in sens["rows"] if r["flips_top_path"]]

# ---------- what-would-change-the-answer (shown first on the landing page) ----------
def wwca():
    rows = []
    for sname in ["downside","upside","stagflation","lost_decade","crash_1929","crash_2008","rate_cut","step_up_cap","pre_prop19"]:
        t = rec["10"]["top_by_scenario"][sname]
        rows.append(f"<tr><td>{e(PRJ['scenarios'][sname]['label'])}</td><td>{e(PRJ['paths'][t]['label'])}</td><td class='small'>{e(PRJ['scenarios'][sname]['desc'])}</td></tr>")
    return f"""<table><tr><th>Scenario</th><th>Highest total real wealth, 10-year horizon, transfer 2045</th><th>Scenario definition</th></tr>{''.join(rows)}</table>"""

def wwca_list():
    lines = []
    for r in flips[:8]:
        lines.append(f"<li><b>{e(r['label'])}</b>: top path moves to {e(PRJ['paths'][r['top_at_low']]['label'])} at the low value, {e(PRJ['paths'][r['top_at_high']]['label'])} at the high value.</li>")
    return "<ul>" + "".join(lines) + "</ul>"

# ---------- index (landing) ----------
def build_index():
    b = B["2045"]["10"]
    k = lambda p: m(b[p]["total_real"])
    body = f"""
<div class="card warnbox"><b>What would change the answer (read first)</b>
<p>The ranking depends on <b>which scenario you assume</b> and on a few inputs. Under the base case, selling Property A
and investing gives the highest total real wealth (10-year horizon, transfer 2045). In several stress tests the
ranking changes, and in a long lost-decade test a rental path ranks first. The inputs that flip the top path are listed below.</p>
{wwca()}
<p class="small">Inputs whose range flips the top path (one at a time, base otherwise):</p>{wwca_list()}
<p class="small">Decision triggers are on the <a href="triggers.html">decision triggers</a> page.</p></div>

<div class="grid">
 <div class="card kpi"><span>Sell now, invest (base, real)</span><b>{k('SELL_A')}</b><span>Transfer 2045 · 10 yr horizon</span></div>
 <div class="card kpi"><span>Sell now, phased into stocks (base)</span><b>{k('SELL_A_PHASED')}</b><span>3M–2Y Treasuries parked {int(INP_BY['park_months']['base'])} months, then phased</span></div>
 <div class="card kpi"><span>Rent Property A (base)</span><b>{k('RENT_A')}</b><span>Taxes on rent included; imputed rent excluded</span></div>
 <div class="card kpi"><span>Live in Property A (base)</span><b>{k('LIVE_A')}</b><span>Excludes imputed rent of about {m(b['LIVE_A']['imputed_real'])} (shown separately)</span></div>
</div>

<h2>Reinvestment risk (beside the headline)</h2>
<div class="card">Cash parked in short Treasuries earns {pct(rr['base_yield_pct'])} at the 3-month par yield on 24 Nov 2026 [S01].
If yields fall to {pct(rr['shock_yield_pct'])}, each $1,000,000 parked earns about {m(rr['annual_income_lost_per_1m_r'])} a year less.
The phased path rests on this rate for {int(rr['park_months_base'])} months. Figures are approximate.</div>

<h2>What-if controls</h2>
<div class="card noprint">
 <label>Transfer year <select id="ty"><option>2040</option><option selected>2045</option><option>2050</option></select></label>
 <label>Horizon (years) <select id="hz"><option>5</option><option selected>10</option><option>20</option></select></label>
 <label>Scenario <select id="sc">{''.join(f'<option value="{s}">{e(v["label"])}</option>' for s,v in PRJ['scenarios'].items())}</select></label>
 <table id="wt"></table>
 <p class="small">Precomputed from the model (no live recalculation). Real 2026 dollars, nearest $10. Imputed rent is excluded from totals.</p>
</div>
<script>
const R={json.dumps({s:{T:{H:{p:{'total_real':r10(v['total_real']),'cash_real':r10(v['cash_real']),'property_real':r10(v['property_real']),'taxes_real':r10(v['taxes_real'])} for p,v in R[s][T][H].items()} for H in R[s][T]} for T in R[s]} for s in R})};
const L={json.dumps({p:v['label'] for p,v in PRJ['paths'].items()})};
function up(){{const t=ty.value,h=hz.value,s=sc.value;const c=R[s][t][h];
 const rows=Object.keys(c).sort((a,b)=>c[b].total_real-c[a].total_real);
 let html='<tr><th>Path</th><th>Total real wealth</th><th>Cash / liquid</th><th>Property equity</th><th>Taxes paid</th></tr>';
 for(const p of rows){{const v=c[p];html+=`<tr><td>${{L[p]}}</td><td class=n>${{'$'+v.total_real.toLocaleString('en-US')}}</td><td class=n>${{'$'+v.cash_real.toLocaleString('en-US')}}</td><td class=n>${{'$'+v.property_real.toLocaleString('en-US')}}</td><td class=n>${{'$'+v.taxes_real.toLocaleString('en-US')}}</td></tr>`}}
 document.getElementById('wt').innerHTML=html}}
['ty','hz','sc'].forEach(i=>document.getElementById(i).addEventListener('change',up));up();
</script>
<p class="small">Rounding note: the on-page numbers are already rounded to $10 by the builder.</p>
"""
    page("index.html", "Inheritance decision: Cupertino inheritance vs San Francisco rental", body)

# ---------- executive summary and suggestions ----------
def build_exec():
    b = B["2045"]["10"]
    bs1 = bs["crash_1929"]; bs2 = bs["crash_2008"]
    body = f"""
<div class="card"><h2 style="margin-top:0">Summary</h2>
<ul>
<li>Property A (Cupertino) is inherited through the trust. Property B (San Francisco, 94122) is already owned by the heir. The analysis treats this asymmetry explicitly: the choice is about Property A only.</li>
<li>Base case (transfer 2045, 10 years): selling Property A and investing ranks first, at about {m(b['SELL_A']['total_real'])} in real wealth. Renting ranks lower at about {m(b['RENT_A']['total_real'])} after taxes.</li>
<li>Living in Property A keeps the Prop 19 base year value, but the house produces no cash income. Its real total is about {m(b['LIVE_A']['total_real'])}. Adding the imputed rent of about {m(b['LIVE_A']['imputed_real'])} (a non-cash value that is not spendable) gives about {m(b['LIVE_A']['total_incl_imputed_real'])}, still below the sell path.</li>
<li>The ranking changes in {sum(1 for s in rec['10']['top_by_scenario'] if rec['10']['top_by_scenario'][s]!=rec['10']['top_by_scenario']['base'])} of 10 stress sets. Phased entry ranks first in downside and crash cases; a rental path can rank first in the long lost-decade case.</li>
<li>Black Swan: a 1929-style fall at transfer would take a lump sum to about {m(bs1['lump_crash_at_transfer'])} in real wealth; the phased path would keep about {m(bs1['phased_crash_at_transfer'])}, because the cash is parked during the fall. The 2008-style fall gives about {m(bs2['lump_crash_at_transfer'])} lump versus {m(bs2['phased_crash_at_transfer'])} phased.</li>
<li>Monte Carlo (5,000 runs, 20 years): the phased path beats lump sum in {mc['prob_phased_beats_lump_pct']}% of paths. Median lump {m(mc['lump']['p50'])}; median phased {m(mc['phased']['p50'])}.</li>
</ul>
<p class="warnbox">These figures are model outputs under assumptions. Several inputs are unverified and are flagged (see Flagged for Review). They are not a recommendation to buy or sell.</p></div>

<h2>Suggestions (for discussion with counsel and CPA)</h2>
<div class="card"><ol>
<li>Obtain a written valuation of Property A at the date of death. The Prop 19 base year value and any sale price both depend on it.</li>
<li>Confirm the Cupertino tax rate on the actual bill and the Santa Clara tax rate book (flag F-03).</li>
<li>Decide, with the CPA, whether Property A will be occupied (Prop 19 homeowners' exemption within 1 year; claim within 3 years) or rented or sold. These are different legal paths.</li>
<li>Get two insurance quotes for each property (flag F-08) and a rental-rate check for Property A (flag F-05).</li>
<li>Keep any sale proceeds in short Treasuries until the phase-in plan is set. Re-check yields against the reinvestment-risk line before each tranche.</li>
<li>Do not rely on the step-up cap in the reported Treasury proposal. It is not law (see Tax law).</li>
</ol></div>
"""
    page("executive.html", "Executive summary and suggestions", body)

# ---------- paths ----------
def build_paths():
    rows = []
    for H in ["5","10","20"]:
        for pn, pv in PRJ["paths"].items():
            c = cell("base", 2045, H, pn)
            rows.append(f"<tr><td>{e(pv['label'])}</td><td>{H} yr</td><td class=n>{m(c['total_real'])}</td><td class=n>{m(c['cash_real'])}</td><td class=n>{m(c['property_real'])}</td><td class=n>{m(c['taxes_real'])}</td><td class=n>{m(c['imputed_real'])}</td><td class=small>{links(['S01','S02','S08','S13'])}</td></tr>")
    tab1 = f"""<table><tr><th>Path</th><th>Horizon</th><th>Total real wealth</th><th>Cash / liquid</th><th>Property equity</th><th>Taxes</th><th>Imputed rent (not in total)</th><th>Sources</th></tr>{''.join(rows)}</table>"""
    rows2 = []
    for T in [2040, 2045, 2050]:
        c = B[str(T)]["10"]
        rows2.append(f"<tr><td>{T}</td>" + "".join(f"<td class=n>{m(c[p]['total_real'])}</td>" for p in ["LIVE_A","RENT_A","SELL_A","SELL_A_PHASED","LIVE_THEN_SELL"]) + "</tr>")
    tab2 = f"""<table><tr><th>Transfer year</th><th>Live</th><th>Rent</th><th>Sell now</th><th>Sell, phased</th><th>Live 2 yr then sell</th></tr>{''.join(rows2)}</table>"""
    rows3 = []
    for s, v in PRJ["scenarios"].items():
        c = R[s]["2045"]["10"]
        rows3.append(f"<tr><td>{e(v['label'])}</td>" + "".join(f"<td class=n>{m(c[p]['total_real'])}</td>" for p in ["LIVE_A","RENT_A","SELL_A","SELL_A_PHASED"]) + f"<td>{e(PRJ['paths'][rec['10']['top_by_scenario'][s]]['label'])}</td></tr>")
    tab3 = f"""<table><tr><th>Scenario (2045, 10 yr)</th><th>Live</th><th>Rent</th><th>Sell now</th><th>Sell, phased</th><th>Highest</th></tr>{''.join(rows3)}</table>"""
    body = f"""<p>Real 2026 dollars, nearest $10. Taxes include federal and CA tax on rent and gains where applicable. Owner-occupied homes produce no cash; imputed rent is shown separately and is not added to totals.</p>
<h2>All paths by horizon (base, transfer 2045)</h2>{tab1}
<h2>Transfer year sensitivity (base, 10 yr)</h2>{tab2}
<h2>Scenarios (2045, 10 yr)</h2>{tab3}
<h2>Mixed paths: definitions</h2>
<div class="card"><ul>
<li><b>Live 2 yr then sell</b>: Prop 19 claimed; the §121 exclusion (up to $250,000 single / $500,000 if the surviving spouse rules apply) is applied to the gain at sale.</li>
<li><b>Live 5 yr then rent</b>: Prop 19 claimed while occupied; then rent at market, which reassesses property tax to market value (Prop 19 does not protect rentals).</li>
<li><b>Rent 10 yr then sell</b>: no Prop 19 base year benefit; rent taxed; depreciation recaptured at sale.</li>
<li><b>Sell now, phased</b>: proceeds parked in 3M–2Y Treasuries for {int(INP_BY['park_months']['base'])} months, then phased into stocks over {int(INP_BY['phase_months']['base'])} months.</li>
</ul><p class="small">Path definitions are in <code>model/model.py</code>. Sources for each row: {links(['S01','S02','S06','S08','S13','S17'])}.</p></div>
"""
    page("paths.html", "Paths and mixed scenarios", body)

# ---------- black swan ----------
def build_blackswan():
    bs1 = bs["crash_1929"]; bs2 = bs["crash_2008"]
    body = f"""
<div class="card warnbox">Black Swan analysis. Historical anchors are from official or institutional sources. The crash shapes used in the model are <b>calibrated approximations</b>, not forecasts. Real-economy conditions include inflation above 3% (CPI Sept 2026 3.7% y/y, [S16]) and an upward-sloping Treasury curve (2-year 4.63%, [S01]).</div>
<h2>Historical anchors</h2>
<table><tr><th>Event</th><th>Measure</th><th>Value</th><th>Source</th></tr>
<tr><td>1929–1932 crash</td><td>Dow Jones decline (381.17 on 9/3/1929 to 41.22 on 7/8/1932)</td><td class=n>-89%</td><td>{links(['S17'])}</td></tr>
<tr><td>1929 crash</td><td>Years to regain the 1929 peak (11/23/1954)</td><td class=n>25 yrs</td><td>{links(['S17'])}</td></tr>
<tr><td>2007–2009 crash</td><td>S&amp;P 500 decline (Oct 2007–Mar 2009)</td><td class=n>-57%</td><td>{links(['S18'])}</td></tr>
<tr><td>2007–2009</td><td>Home prices (national, approximate)</td><td class=n>about -30%</td><td>{links(['S18'])}</td></tr>
</table>
<h2>Entry-timing test (transfer 2045, 10 yr, real wealth)</h2>
<table><tr><th>Scenario</th><th>Lump sum at transfer</th><th>Phased (crash at transfer)</th><th>Phased (crash during phase-in)</th><th>Lump, no crash</th><th>Phased, no crash</th></tr>
<tr><td>1929-style (-87% stocks, 36 months)</td><td class=n>{m(bs1['lump_crash_at_transfer'])}</td><td class=n>{m(bs1['phased_crash_at_transfer'])}</td><td class=n>{m(bs1['phased_crash_during_phase_in'])}</td><td class=n>{m(bs1['lump_no_crash'])}</td><td class=n>{m(bs1['phased_no_crash'])}</td></tr>
<tr><td>2008-style (-57% stocks, 17 months)</td><td class=n>{m(bs2['lump_crash_at_transfer'])}</td><td class=n>{m(bs2['phased_crash_at_transfer'])}</td><td class=n>{m(bs2['phased_crash_during_phase_in'])}</td><td class=n>{m(bs2['lump_no_crash'])}</td><td class=n>{m(bs2['phased_no_crash'])}</td></tr></table>
<p class="small">The -87% and -57% shocks are model calibrations from [S17] and [S18], not historical replays.</p>
<h2>Phased investing through 3M–2Y Treasuries (24–36 months)</h2>
<div class="card">Proposed structure: park proceeds in 3-month and 2-year Treasuries (live yields on 24 Nov 2026: 4.36% and 4.63% [S01]) for {int(INP_BY['park_months']['base'])} months, then move into equities over {int(INP_BY['phase_months']['base'])} months. Park period range: 24–36 months. Phasing reduces the chance of entering just before a crash; it also gives up upside if markets rise during the wait. Reinvestment risk: the parked cash earns less if short yields fall (see the landing page).</div>
<h2>Monte Carlo (20 years, transfer 2045, {mc['runs']:,} runs, seeded)</h2>
<table><tr><th>Measure</th><th>Lump sum</th><th>Phased</th></tr>
<tr><td>10th percentile (real)</td><td class=n>{m(mc['lump']['p10'])}</td><td class=n>{m(mc['phased']['p10'])}</td></tr>
<tr><td>Median (real)</td><td class=n>{m(mc['lump']['p50'])}</td><td class=n>{m(mc['phased']['p50'])}</td></tr>
<tr><td>90th percentile (real)</td><td class=n>{m(mc['lump']['p90'])}</td><td class=n>{m(mc['phased']['p90'])}</td></tr></table>
<p class="small">Assumptions: stock return mean {mc['assumptions']['equity_mu_pct']}% and volatility {mc['assumptions']['equity_vol_pct']}% per year; 5% chance each year of a -35% year. Phased share beats lump sum in {mc['prob_phased_beats_lump_pct']}% of runs. Equity assumptions are unverified (see Flagged).</p>
"""
    page("blackswan.html", "Black Swan: entry risk and phased investing", body)

# ---------- inputs ----------
def build_inputs():
    rows = []
    for x in INP["inputs"]:
        ok = x["status"] in VERIFIED
        def v(val):
            if x["unit"] == "USD" or x["unit"].startswith("USD"):
                return m(val)
            if x["unit"].startswith("%"):
                return pct(val)
            return str(val)
        shown = (v(x["low"]) + " / " + v(x["base"]) + " / " + v(x["high"])) if ok else '<span class="blank">blank: unverified</span>'
        flag = "" if ok else '<span class="flag">UNVERIFIED</span>'
        rows.append(f"<tr><td>{e(x['label'])}<div class=small>{e(x['id'])}</div></td><td>{e(x['group'])}</td><td class=n>{shown}</td><td>{badge(x['status'])} {flag}</td><td>{links(x['sources'])}</td><td class=small>{e(x['note'])}</td></tr>")
    body = f"""<p>Low / base / high ranges used by the model. Unverified values are <b>blank</b> in this table and flagged; the model still runs on the assumption range recorded in <code>data/inputs.json</code>.
Owner-provided values are labelled OWNER and are not verified online.</p>
<table><tr><th>Input</th><th>Group</th><th>Low / base / high</th><th>Status</th><th>Sources</th><th>Note</th></tr>{''.join(rows)}</table>"""
    page("inputs.html", "Inputs and sources", body)

# ---------- tax law (enacted vs proposed) ----------
def build_tax():
    enacted = [
     ("Federal estate tax: basic exclusion 2026 $15,000,000; top rate 40%; Form 706 due 9 months after death", "Enacted", ["S03"]),
     ("Federal LTCG 0%/15%/20% thresholds for 2026 (single: 0% to $49,450; 15% to $545,500)", "Enacted (inflation-adjusted)", ["S02"]),
     ("Net investment income tax 3.8% above $200,000 single / $250,000 MFJ (not indexed)", "Enacted (IRC §1411)", ["S04"]),
     ("Prop 19: parent-child exclusion; homeowners' exemption within 1 year; claim within 3 years; cap = FBYV + $1,044,586 (transfers 2/16/2025–2/15/2027)", "Enacted (California)", ["S08"]),
     ("CA has no estate or inheritance tax (inherited property not income to the recipient)", "Enacted (verify: S08 and CA sources)", ["S08"]),
     ("CA Mental Health Services Tax 1% on taxable income above $1,000,000 (Form 540 line)", "Enacted; line read in the 2025 instructions pending (S06)", ["S06","S32"]),
     ("§121 home sale exclusion $250,000 single / $500,000 MFJ; 2-of-5-year tests", "Enacted (verify Pub 523)", ["S05"]),
     ("SALT cap $40,400 for 2026 (OBBBA), phase-down above $500,000 MAGI", "Enacted (secondary; verify IRS)", ["S27"]),
     ("CA SB 974 (ch. 665, signed 9/27/2026, effective 1/1/2027): special needs trusts and Prop 19 parent-child rules", "Reported enacted; UNVERIFIED on leginfo (F-01)", ["S28"]),
     ("Prop 19 repeal initiative did not qualify for 2026", "Reported; verify on sos.ca.gov", ["S29"]),
    ]
    proposed = [
     ("Treasury NPRM (reported 5/12/2026): cap IRC §1014 basis step-up at $3,000,000 per decedent ($6,000,000 with portability); deaths on/after 1/1/2027 if finalized", "PROPOSAL — not law; Federal Register text not located", ["S30"]),
     ("H.R. 1340 (More Homes on the Market Act): §121 exclusion to $500,000 / $1,000,000, indexed", "PROPOSAL — referred to Ways and Means", ["S26"]),
     ("Don't Tax the American Dream Act (introduced 1/13/2026)", "PROPOSAL — introduced; text not read", []),
     ("H.Res.206 (2025): non-binding resolution on step-up basis", "NON-BINDING RESOLUTION — not law", ["S25"]),
    ]
    er = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{links(c)}</td></tr>" for a,b,c in enacted)
    pr = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{links(c) if c else '<span class=flag>no source yet</span>'}</td></tr>" for a,b,c in proposed)
    body = f"""<h2>Enacted law</h2><table><tr><th>Rule</th><th>Status</th><th>Sources</th></tr>{er}</table>
<h2>Proposals (not law; tracked separately)</h2><div class="warnbox">These items may change, or never pass. Do not use them as current law.</div>
<table><tr><th>Proposal</th><th>Status</th><th>Sources</th></tr>{pr}</table>
<p class="small">Pending: the Treasury step-up text, the MHST line in the 2025 instructions, and the Pub 523 §121 rule.</p>"""
    page("tax.html", "Tax law: enacted vs proposed", body)

# ---------- deadlines ----------
def build_deadlines():
    items = [
     ("Date of death (transfer date for Prop 19)", "Transfer date = date of death", "Date varies", ["S08"]),
     ("Prop 19 homeowners' exemption", "Claim within 1 year of transfer to keep the base year value", "1 year after transfer", ["S08"]),
     ("Prop 19 claim (BOE-19-P)", "Claim within 3 years of transfer", "3 years after transfer", ["S08"]),
     ("Form 706 federal estate tax return", "Due 9 months after death (extension possible)", "9 months after death", ["S03"]),
     ("Prop 19 cap window ends (current figure)", "Cap $1,044,586 applies to transfers up to 2/15/2027; indexing after", "2/15/2027", ["S08"]),
     ("SB 974 effective (reported)", "Prop 19 parent-child rules changed (UNVERIFIED)", "1/1/2027", ["S28"]),
     ("Proposed step-up cap (not law)", "Would apply to deaths on/after 1/1/2027 if finalized", "1/1/2027 (proposal)", ["S30"]),
     ("SF secured property tax, 1st installment", "Due 12/10; 10% penalty after delinquency", "12/10 each year", ["S11"]),
     ("SF secured property tax, 2nd installment", "Due 4/10; 10% penalty after delinquency", "4/10 each year", ["S11"]),
     ("CA Form 540 (2025 tax year)", "Due 4/15/2026 (for reference)", "4/15 each year", ["S06"]),
     ("Phased investing: park period", "Cash held in 3M–2Y Treasuries", "24–36 months after sale", ["S01"]),
    ]
    rows = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td><td>{links(d)}</td></tr>" for a,b,c,d in items)
    body = f"<table><tr><th>Event</th><th>What must happen</th><th>When</th><th>Sources</th></tr>{rows}</table>"
    page("deadlines.html", "Deadlines timeline", body)

# ---------- decision triggers ----------
def build_triggers():
    body = """<div class="card warnbox"><b>Timing disclosure.</b> The triggers below were written after the first model run (25 Nov 2026), so they were not set entirely before the figures. They are fixed here and should not be changed to fit the results.</div>
<table><tr><th>Trigger</th><th>Threshold (fixed)</th><th>Action if met</th></tr>
<tr><td>Legal occupancy plan</td><td>Heir will live in Property A within 1 year of transfer</td><td>Claim homeowners' exemption; use the Prop 19 LIVE paths</td></tr>
<tr><td>Written valuation</td><td>Valuation at death differs from $3,100,000 by more than 10%</td><td>Re-run model with the written value; re-check Prop 19 cap and sale path</td></tr>
<tr><td>Rent vs sell gap</td><td>Rent path trails sell path by more than 15% at 10 yr horizon</td><td>Choose sell path unless occupancy is confirmed</td></tr>
<tr><td>Yield shock</td><td>3M Treasury yield below 3.0% at phase-in start</td><td>Shorten or pause phase-in; review reinvestment risk</td></tr>
<tr><td>Market drawdown</td><td>Equity index down more than 30% from the value at sale within the park period</td><td>Hold phased schedule; do not accelerate</td></tr>
<tr><td>Tax law change</td><td>A proposal listed on the Tax law page is enacted or the SB 974 text differs from the summary</td><td>Re-run model; update the tax inputs</td></tr>
<tr><td>Rate verification</td><td>Official Cupertino tax rate differs from the owner-implied 1.34%</td><td>Use official rate; update F-03</td></tr>
</table>"""
    page("triggers.html", "Decision-trigger criteria", body)

# ---------- flagged ----------
def build_flagged():
    rows = "".join(f"<tr><td>{e(f['id'])}</td><td>{e(f['topic'])}</td><td>{e(f['issue'])}</td><td>{e(f['action'])}</td><td>{links(f['sources'])}</td><td>{'yes' if f['blocks_merge'] else 'no'}</td></tr>" for f in FLG["flags"])
    body = f"<p>{e(FLG['note'])} As of {ASOF}.</p><table><tr><th>ID</th><th>Topic</th><th>Issue</th><th>Next action</th><th>Sources</th><th>Blocks merge?</th></tr>{rows}</table>"
    page("flagged.html", "Flagged for Review", body)

# ---------- glossary ----------
def build_glossary():
    g = [("Base year value (FBYV)","Assessed value used as the starting point for Prop 19 cap."),
         ("Prop 19 cap","FBYV plus $1,044,586 (current figure); taxable value cannot exceed this under the parent-child rule."),
         ("Step-up in basis","Reset of cost basis to market value at death. Current law; a cap is a proposal only."),
         ("§121 exclusion","Up to $250,000 (single) or $500,000 (MFJ) of gain excluded on a home sold after 2 of the last 5 years owned and used as a residence."),
         ("Depreciation recapture","Tax on depreciation taken on a rental (25% unrecaptured §1250 gain at max rate)."),
         ("NIIT","3.8% net investment income tax above income thresholds (not indexed)."),
         ("MHST","CA Mental Health Services Tax, 1% above $1,000,000 taxable income (verify on Form 540 line)."),
         ("Imputed rent","Value of living in an owned home. Not cash; shown separately."),
         ("Real dollars","Nominal dollars adjusted to 2026 purchasing power using the model CPI assumptions."),
         ("Reinvestment risk","Risk that cash has to be reinvested at lower yields later."),
         ("3M–2Y Treasuries","U.S. Treasury bills and notes maturing in 3 months to 2 years, used as the parking place."),
         ("Monte Carlo","Repeated random simulation of stock returns to estimate a range of outcomes.")]
    rows = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td></tr>" for a,b in g)
    page("glossary.html", "Glossary", f"<table><tr><th>Term</th><th>Meaning</th></tr>{rows}</table>")

# ---------- briefing sheet (printable) ----------
def build_briefing():
    b = B["2045"]["10"]
    body = f"""<div class="card">
<p><b>Purpose.</b> One-page briefing for counsel and CPA on the inherited Cupertino property (Property A) and the owned San Francisco rental (Property B). Figures are real 2026 dollars, rounded to $10.</p>
<table><tr><th>Question for counsel</th><th>Question for CPA</th></tr>
<tr><td>Confirm date-of-death transfer and the 1-year occupancy rule for Prop 19 (BOE-19-P within 3 years). [S08]</td><td>Confirm base year value at death and the Prop 19 cap figure for transfers after 2/15/2027. [S08]</td></tr>
<tr><td>Confirm SB 974 text and effective date (1/1/2027). [S28] (unverified)</td><td>Confirm MHST line on Form 540 and 1% threshold. [S06]</td></tr>
<tr><td>Confirm step-up status: proposal only; not law. [S30]</td><td>Confirm §121 for a 2-year occupancy then sale (surviving-spouse rule). [S05]</td></tr>
<tr><td>Trust terms: who holds title; any sale or occupancy restrictions.</td><td>Depreciation and recapture on rental use. [S31]</td></tr>
<tr><td>Federal estate tax: no tax expected at the stated value (2026 exclusion $15,000,000). [S03]</td><td>Federal tax on rent, NIIT threshold, SALT cap. [S04][S27]</td></tr></table>
<p><b>Key figures (2045 transfer, 10 yr, real):</b> sell now {m(b['SELL_A']['total_real'])}; sell phased {m(b['SELL_A_PHASED']['total_real'])}; rent {m(b['RENT_A']['total_real'])}; live {m(b['LIVE_A']['total_real'])}.</p>
<p><b>Unverified:</b> see Flagged for Review (F-01 to F-08). Not legal or tax advice.</p></div>"""
    page("briefing.html", "Attorney & CPA briefing sheet (print)", body)

# ---------- sources ----------
def build_sources():
    def title_cell(s):
        if s["url"].startswith("internal:"):
            return e(s["title"]) + " (internal, not published)"
        return '<a href="' + e(s["url"]) + '">' + e(s["title"]) + "</a>"
    rows = "".join(f"<tr><td>{e(s['id'])}</td><td>{e(s['publisher'])}</td><td>{title_cell(s)}</td><td>{badge(s['level'])}</td><td class=small>{e(s['supports'])}</td></tr>" for s in SRC["sources"])
    body = f"<p>Accessed {SRC['accessed']}. Levels: V-PRIMARY (official page read in session), V-SNIPPET (official, read in search result), S-SECONDARY (cross-check only; unverified), OWNER (internal, not published online).</p><table><tr><th>ID</th><th>Publisher</th><th>Title</th><th>Level</th><th>Supports</th></tr>{rows}</table>"
    page("sources.html", "Sources", body)

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    for f in ["index.html"]: pass
    build_index(); build_exec(); build_paths(); build_blackswan(); build_inputs(); build_tax()
    build_deadlines(); build_triggers(); build_flagged(); build_glossary(); build_briefing(); build_sources()
    open(os.path.join(OUTDIR, ".nojekyll"), "w").write("")
    print("built", len(os.listdir(OUTDIR)), "files")
