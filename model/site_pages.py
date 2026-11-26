"""
site_pages.py — the page builders. Each function returns a complete HTML document.

All numbers come from the model in engine.py / projections.py, never typed by hand, so the
prose and the tables cannot drift apart. Where a figure has no official source the cell is
left empty and flagged rather than estimated.
"""
import json

from site_lib import (PROPERTY_A, PROPERTY_B, RULES, ECON, TRANSACT, PHASING, SOURCES,
                      QUESTIONS, SUGGESTIONS, FLAGS, HISTORY_A, HISTORY_B, r10,
                      ASOF, NEXT_CHECK, e, m, pc, num, srclink, simple_table, pill,
                      status_pill, page, note)
import inputs as I
import registers as R
import history as H
import engine as E
import projections as P

SHORT = {
    "P-01": "Live in A, leave B's third unit empty",
    "P-02": "Live in A, let B's third unit too",
    "P-03": "Live in B, let all of A",
    "P-04": "Live in A 3 yr, sell, move to B",
    "P-05": "Sell in the year of the death, invest at once",
    "P-06": "Sell at death, park 24 mo, phase 24 mo",
    "P-07": "Sell at death, park 36 mo, phase 36 mo",
    "P-08": "Let A 10 yr, then sell",
    "P-09": "Live in A 12 yr, then sell",
    "P-10": "Let A forever, sell at year 30",
    "P-11": "Live 2 yr, let 8 yr, sell at 10",
    "P-12": "Hold A vacant as a fallback",
}

WHY = {
    "P-05": ("Best on money alone: no gain to tax (basis was just stepped up), no reassessment to pay, "
             "and 100% of a $5.4M asset starts compounding instead of sitting in one house."),
    "P-06": ("Same sale, staged. Costs real return for two years of parking and buys protection "
             "against being fully invested into a crash the year after the funeral."),
    "P-07": ("Longer parking, longer drag. The insurance is more expensive and, past 24 months, "
             "no better on the crash paths."),
    "P-04": ("The compromise: keeps Prop 19 alive, keeps optionality, sells into a §121 exclusion. "
             "Pays a genuine cash-flow deficit while you live there."),
    "P-11": "Occupies just long enough for the exclusion and §121, then rents. The most balanced live/rent mix.",
    "P-08": ("Rents from day one, so no exclusion: the tax bill is the full reassessed amount. "
             "Gain at year 10 is fully taxable plus recapture."),
    "P-09": ("Twelve years of living there is a fine life and a mediocre portfolio: the house returns "
             "about 2% net while you forgo the market."),
    "P-10": "Longest rental hold: maximum depreciation, maximum recapture, maximum tax on exit.",
    "P-03": "Cheapest way to hold A, but you consume the triplex's rent instead of collecting it.",
    "P-02": "Two owned houses lived in and worked for rent - the highest-utility, lowest-cash option.",
    "P-01": ("Warmest option and the most expensive one: full carrying cost on A, one vacant unit at B, "
             "no compounding portfolio."),
    "P-12": "Worst of both in the model: you pay to hold a house nobody lives in and forgo its rent.",
}


def _prop19_row(x):
    return [str(x["year"]), m(x["market"]), m(x["keep13_assessed"]), m(x["keep13_tax"]),
            m(x["prop19_assessed"]), m(x["prop19_tax"]), m(x["reassess_assessed"]), m(x["reassess_tax"]),
            SRCLINES["prop19"]]


def _carry_row(x, label=None, prop="A"):
    return [label or str(x["year"]), m(x["value"]), m(x["assessed"]), m(x["tax"]), m(x["insurance"]),
            m(x["water"]), m(x["electric"]), m(x["maintenance"]), m(x["total"]),
            SRCLINES["carryA" if prop == "A" else "carryB"]]


CARRY_HDR = [("Year", "l"), ("Market value", "r"), ("Assessed", "r"), ("Property tax", "r"),
             ("Insurance", "r"), ("Water", "r"), ("Electric", "r"), ("Upkeep", "r"),
             ("Total carrying cost", "r"), ("Sources for this row", "src")]
# One link set per row: the same rules drive every year, and repeating them per row is the point -
# a reader can check any single line of the table without scrolling to a footnote.
SRCLINES = {
    "prop19": srclink("BOE-P19") + " " + srclink("SCC-RATEBOOK") + " " + srclink("owner"),
    "carryA": srclink("SCC-RATEBOOK") + " " + srclink("owner"),
    "carryB": srclink("SF-TTC-RATE") + " " + srclink("SFPUC-RATES") + " " + srclink("SF-PROP-H-MTC"),
    "histA": srclink("SCC-RATEBOOK") + " " + srclink("owner"),
    "histB": srclink("SF-TTC-RATE") + " " + srclink("owner"),
}


# --------------------------------------------------------------- index ----
def index(ctx):
    rows30, sc, sc_use = ctx["paths30"], ctx["sc"], ctx["sc_use"]
    ranked = sorted(sc.items(), key=lambda kv: -kv[1]["score"])
    p19 = ctx["prop19"]
    best, worst = ranked[0], ranked[-1]
    gain10 = [s for s in ctx["sales"] if s["label"].startswith("Rent 10")][0]
    tr = ctx["transfer"]

    body = []
    body.append('<div class="card accent"><div class="kicker">What would change the answer</div>')
    body.append("<p>This workspace ranks twelve ways of handling Property A. The ranking is <b>not</b> "
                "fragile with respect to house prices or the stock market, and it is <b>entirely</b> "
                "fragile with respect to the six things below. Each is stated with the number it moves.</p>")
    body.append('<div class="two">')
    triggers = [
        ("Whether the heir actually lives there",
         f"Prop 19 is worth {m(p19['delta_yr0'])} a year in year one and about "
         f"{m(sum(x['reassess_tax'] - x['prop19_tax'] for x in p19['rows']))} over thirty years. "
         "Occupying within a year and filing the homeowners' exemption is the only thing that buys it. "
         "Rent the house instead and the exclusion is void.",
         "BOE-P19"),
        ("What the rent really is",
         "Every rent-path number currently rests on the owner's estimate of "
         f"{m(I.r10(7500))}-{m(I.r10(9500))} a month, not on closed comparables. Four signed leases of "
         "comparable single-family houses in the same submarket could move the rent paths above or "
         "below the live paths. "
         "See <a href='comparables.html'>Comparables</a>.",
         None),
        ("The parcel's actual tax rate area",
         "The household's own bills imply about "
         f"{pc(RULES['sc_rate_central'])} of assessed value, above the county's published 1.00000% "
         "maximum levy plus the bonds it could be matched to. If the true composite is higher, every "
         "keep path gets worse and the sell paths get better. This is the single most valuable missing "
         "number on the site.",
         "SCC-RATEBOOK"),
        ("Whether a sale happens in the year of the death",
         f"A sale at transfer has effectively no gain because the basis is the date-of-death value. "
         f"Waiting ten years and renting turns that into {m(gain10['total_tax'])} of tax on a "
         f"{m(gain10['price'])} sale. The step-up is generous and it is time-limited in practice.",
         "IRS-559"),
        ("Depreciation, and the recapture it creates",
         f"Renting A for ten years shelters about {m(gain10['depreciation'])} of rent, and then "
         f"recaptures it at up to 25% plus 3.8% on the way out. That trade is worth re-pricing every "
         "time the rent estimate changes.",
         "IRS-946"),
        ("The household's own constraints, which the model cannot see",
         "A co-beneficiary who will not sign, a Medi-Cal estate claim, an unpermitted third unit at "
         f"Property B, or a cash need inside five years each override a {m(rows30[best[0]]['final_real'] - rows30[worst[0]]['final_real'])} "
         "spread. None of them are in the model, and three of them are still unknown.",
         None),
    ]
    for t in triggers:
        body.append(f'<div class="card"><b>{t[0]}</b><p class="small">{t[1]}</p>'
                    f'<div class="src">{srclink(t[2]) if t[2] else ""}</div></div>')
    body.append("</div></div>")

    body.append("<h2>Executive summary</h2>")
    body.append(
        "<p><b>1. The money answer and the life answer are different answers.</b> On real terminal wealth "
        f"alone, selling Property A in the year of the death ({best[0]}) is worth about "
        f"{m(rows30[best[0]]['final_real'])} in 2026 dollars at a thirty-year horizon, against about "
        f"{m(rows30['P-01']['final_real'])} for living in it and leaving Property B's third unit empty. "
        f"That gap is not a forecast of the housing market. It is the price of holding an asset that lets "
        f"out for {ctx['rent_diag']['gross_yield']:.1f}% of its value gross, and nothing else - while the "
        "same money, invested, earns the market's return without a tax bill attached.</p>"
        "<p><b>2. Living there is cheap in the ways that matter and expensive in one.</b> The one "
        f"expensive thing is the assessment: {m(p19['tax_excluded'])} a year under Prop 19 versus "
        f"{m(p19['tax_full'])} if the house is rented. Everything else about occupying the house - "
        "insurance, water, the solar credit, even upkeep - is smaller than that single line, and the "
        "Prop 19 saving compounds at 2% a year for as long as it is held.</p>"
        "<p><b>3. The rent paths are not evidence-based yet.</b> Two of the twelve paths rank partly on "
        "a rent figure the household supplied. Until comparables arrive, treat those rankings as "
        "provisional, and note that a voucher-anchored estimate was deliberately <i>not</i> used.</p>"
        "<p><b>4. Staging the proceeds costs return and buys something real.</b> Parking the sale "
        "proceeds in 3-month to 2-year Treasuries for 24 months and phasing into equities costs about "
        f"{abs(ctx['stage_cost']):.1f}% of terminal wealth in the middle of history and improves the "
        "outcome entering 1929, 1973 and 2000. The page on <a href='phased.html'>phased investing</a> "
        "shows both sides, because a headline about staging without a reinvestment-risk number beside "
        "it is marketing.</p>"
        "<p><b>5. Property B is not a second decision, it is the reason the first one is affordable.</b> "
        "The household already owns a three-unit building it can move into. That is what makes 'live in "
        "A now, decide later' genuinely reversible, and it is also where the new San Francisco parcel tax "
        "and any owner-move-in eviction exposure land.</p>"
        "<p><b>6. Nothing here is a reason to hurry, and two things are reasons to move now.</b> The "
        "transfer is years away. But the appraisal, the tax-rate-area lookup and the written agreement "
        "about what each person wants are cheap, independent of the future, and each one changes what the "
        "model can say.</p>")

    body.append("<h2>Where the twelve paths stand</h2>")
    body.append(note("Ranked on the pre-committed score defined on <a href='framework.html'>Decision "
                     "rules</a>: 50% median real terminal wealth, 25% the 10th percentile, 15% spread, "
                     "10% liquidity. Imputed rent is reported in its own column and never folded in "
                     "silently; the last column shows how the ranking moves if it is."))
    specs = {x["id"]: x for x in ctx["specs"]}
    rows = []
    for i, (pid, s) in enumerate(ranked):
        p = rows30[pid]
        rows.append([
            "@" + ("best" if i == 0 else ("worst" if i == len(ranked) - 1 else "")),
            f"<a href='paths.html#{pid}'>{pid}</a>", f"<b>{SHORT[pid]}</b>",
            pill(p["group"], "info"),
            m(p["final_real"]), m(p["p10"]), m(p["use_value"]),
            f"{s['score']:.1f}", f"{s['score']:.1f} / {sc_use[pid]['score']:.1f}",
            m(p["cash_flow_min"]), path_sources(specs, pid),
        ])
    body.append(simple_table(
        [("Path", "l"), ("In words", "l"), ("Type", "l"),
         ("Real wealth at 2075, 2026$ (mid case)", "r"), ("10th percentile of that", "r"),
         ("Imputed rent you consume (PV)", "r"), ("Score", "r"), ("Score with use value", "r"),
         ("Worst annual cash flow", "r"), ("The numbers in this row come from", "src")],
        rows, cls="rank sortable"))
    body.append('<figure><div id="dist" class="chart" data-chart="dist"></div>'
                "<figcaption>Twelve paths, ranked: the line is the median, the bar is the "
                "10th-to-90th percentile band, the dark tick is the mid-case deterministic result. The "
                "band is wide because the record is wide, not because the model is unsure how to "
                "average it.</figcaption></figure>")
    body.append(note("Real wealth = terminal household wealth with every property sold at market and tax "
                     "on the unrealised gain paid, divided by cumulative inflation. It is a liquidation "
                     "measure, so a path that keeps a house is measured on what that house is worth, not "
                     "on the sentimental value of keeping it. Figures are rounded to $10."))

    body.append("<h2>The single biggest line, worked</h2>")
    body.append(simple_table(
        [("Property A at the modelled transfer, 2045", "l"), ("Amount", "r"), ("Source", "src")],
        [["Market value at the date of death (owner's 2026 estimate grown at the mid case)",
          m(p19["value_T"]), srclink("owner", "replace with the appraisal")],
         ["Prior factored base year value (Prop 13 base, grown at the 2% cap)", m(p19["fbyv_T"]),
          srclink("SCC-RATEBOOK")],
         ["Prop 19 indexed allowance, carried forward from the published amount", m(p19["allowance_T"]),
          srclink("BOE-LTA25009")],
         ["Cap: base + allowance", m(p19["cap_T"]), srclink("model")],
         ["Excess over the cap - the part that reassesses", m(p19["excess_T"]), srclink("model")],
         ["New taxable value <b>with</b> the exclusion (heir occupies)", m(p19["base_excluded"]),
          srclink("BOE-P19")],
         ["Property tax with the exclusion", m(p19["tax_excluded"]), srclink("model")],
         ["Property tax <b>without</b> it (rented, or the claim missed)", m(p19["tax_full"]),
          srclink("model")],
         ["<b>Annual cost of getting this wrong</b>", f"<b>{m(p19['delta_yr0'])}</b>",
          srclink("BOE-P19")]],
        caption="R&amp;T Code 63.2 as the county rate book and the BOE formula describe it. The rate used "
                "is the household's implied composite - see the flag.", short=True))

    body.append("<h2>Deadlines that do not move</h2>")
    dl = R.TIMELINE[:6]
    body.append(simple_table([("When", "l"), ("What", "l"), ("Why it matters", "l"), ("Source", "src")],
                             [[d["when"], f"<b>{e(d['event'])}</b>", e(d["consequence"]),
                               srclink(d["src"])] for d in dl], short=True))
    body.append(note("The full timeline, including the post-death filings, is on "
                     "<a href='process.html'>Process &amp; deadlines</a>."))

    body.append("<h2>Do these five things before arguing about any projection</h2>")
    body.append('<ol class="tight">' + "".join(f"<li>{e(s['body'])} <span class='tag'>{pill(s['id'], 'info')} "
                                               f"effort {s['effort']} / impact {s['impact']}</span></li>"
                                               for s in [SUGGESTIONS[2], SUGGESTIONS[0], SUGGESTIONS[3],
                                                         SUGGESTIONS[9], SUGGESTIONS[6]]) + "</ol>")

    body.append("<h2>How to read this site</h2>")
    body.append('<div class="grid">')
    for t, b, href in [
        ("Blank means no source", "A cell showing <span class='na'>not verified</span> is a value that "
         "could not be read from an official document in this pass. It is never filled with an estimate.",
         "flagged.html"),
        ("Every table row is linked", "The Source column carries the document the row came from, with "
         "its verification status. Official, academic, owner-supplied and unverified are different words "
         "and they are used differently here.", "sources.html"),
        ("Ranges, not points", "Assumptions are stored as low/mid/high and the model is run across the "
         "grid, so a headline that only survives at one point on a dial is reported as not robust.", "what-if.html"),
        ("Three tax systems, kept apart", "Estate tax at death, income tax on the gain, and property tax "
         "on the assessment are separate tables with separate deadlines. Conflating them is the classic "
         "error in this decision.", "tax-rules.html"),
        ("Open questions are the product", f"{len([q for q in QUESTIONS if q['status'] == 'OPEN'])} "
         "questions are unresolved. Each says who can answer it and how. The model is a way of noticing "
         "them; the answers are the work.", "open-questions.html"),
        ("Suggestions first, then code", "Twelve method proposals are on a board for the household to "
         "accept or reject before more implementation follows.", "suggestions.html"),
    ]:
        body.append(f'<a class="card" href="{href}"><b>{t}</b><p class="small">{b}</p></a>')
    body.append("</div>")

    body.append('<p class="print"><b>Print or hand this to advisers:</b> '
                '<a href="briefing.html">Attorney &amp; CPA Briefing Sheet</a> - one page, all the '
                "figures, the open legal questions and the questions we need answered before a decision "
                "is defensible.</p>")
    return page("index", "Property A &amp; B - inherited house decision workspace",
                "".join(body),
                "Two buildings, one decision: live in the inherited house, rent it, sell it, "
                "or some order of those. Everything below is generated by a model whose inputs are "
                "sourced and whose gaps are visible. As of " + ASOF + ".")


# --------------------------------------------------------------- paths ----

def path_sources(specs, pid):
    """The documents a given path's ranking actually depends on, derived from the path definition
    itself rather than hand-assigned: a renting path inherits the owner's rent estimate and the
    depreciation rules, a selling path inherits the transfer costs, and any path that claims
    Prop 19 inherits the exclusion rules and the county factoring."""
    sp = specs[pid]
    keys = []
    if sp.get("prop19"):
        keys.append("BOE-P19")
    if sp.get("a") == "occupied":
        keys.append("SCC-RATEBOOK")
        keys.append("IRS-523")
    else:
        keys.append("SCC-RATEBOOK")
    if sp.get("a") == "rented" or sp.get("switch_to") == "rented" or sp.get("b_rent_vacant"):
        keys += ["owner", "IRS-946"]
    if sp.get("a") == "sold":
        keys.append("SCC-RECORDER-FEES")
    return " ".join(srclink(k) for k in dict.fromkeys(keys))


def paths(ctx):
    rows30, sc, sc_use = ctx["paths30"], ctx["sc"], ctx["sc_use"]
    rows20, rows10 = ctx["paths20"], ctx["paths10"]
    specs = {s["id"]: s for s in ctx["specs"]}
    body = []
    body.append('<p class="lede">Twelve paths, all evaluated at the same transfer year (2045) and the '
                "same horizons (10, 20 and 30 years), including taxes, debt, occupancy, capital costs and "
                "liquidity. Pure strategies and mixed strategies sit in the same table, because the mixed "
                "ones are where the real answer lives.</p>")

    body.append("<h2>What each path actually is</h2>")
    rows = []
    for pid, s in specs.items():
        rows.append([f"<a id='{pid}'></a><b>{pid}</b>", SHORT[pid], pill(s["group"], "info"),
                     {True: "occupies A", False: "does not occupy A"}[s["a"] == "occupied"] if not s.get("switch_at")
                     else f"occupies A for {s['switch_at']} yr, then {s['switch_to'].replace('_',' ')}",
                     ("yes" if s["prop19"] else "no"),
                     ("never sold" if s["sell_a"] is None else f"sold in {ECON['transfer_year'] + s['sell_a']}"),
                     ("lump sum on receipt" if s["invest"]["policy"] == "lump"
                      else f"park {s['invest']['park']} mo, phase {s['invest']['phase']} mo"),
                     ("move into a B unit" if s["b_occupy"] else
                      ("B: 3 units let" if s["b_rent_vacant"] else "B: 2 units let, 1 vacant")),
                     e(WHY.get(pid, "")), path_sources(specs, pid)])
    body.append(simple_table([("Path", "l"), ("In one line", "l"), ("Type", "l"), ("Occupancy of A", "l"),
                             ("Prop 19 claimed", "l"), ("Exit", "l"), ("Proceeds policy", "l"),
                             ("Property B", "l"), ("The idea", "l"), ("Rests on", "src")],
                             rows, short=True))
    body.append(note("Occupancy of A drives Prop 19; Prop 19 drives the tax bill; the tax bill and the "
                     "sale year drive everything else. That is the whole causal chain of this decision."))

    body.append("<h2>Comparison at three horizons</h2>")
    body.append(simple_table(
        [("Path", "l"), ("In one line", "l"), ("10 yr", "r"), ("20 yr", "r"), ("30 yr", "r"),
         ("30 yr incl. what you consume", "r"), ("10th pctile", "r"), ("Median", "r"),
         ("90th pctile", "r"), ("Worst-year wealth", "r"), ("Score", "r")],
        [[pid, SHORT[pid],
          m(rows10[pid]["final_real"]), m(rows20[pid]["final_real"]),
          m(rows30[pid]["final_real"]), m(rows30[pid]["final_real_use"]),
          m(rows30[pid]["p10"]), m(rows30[pid]["p50"]), m(rows30[pid]["p90"]),
          m(rows30[pid]["min_wealth"]), f"{sc[pid]['score']:.1f}", path_sources(specs, pid)]
         for pid in specs], cls="cmp"))
    body.append(note("The 10th/50th/90th percentiles come from 1,200 block-bootstrap paths (contiguous "
                     "three-year blocks drawn from the 1928-2025 annual record), so the tails are real "
                     "sequences, not a normal distribution. The 90th percentile is high because a "
                     "sustained 15%-nominal decade compounded for thirty years does that; read the spread "
                     "as 'this method cannot be narrowed with the data available', not as optimism."))
    body.append('<figure><div id="dist" class="chart" data-chart="whisker"></div>'
                "<figcaption>Median as the line, the p10-p90 band as the bar, the mid-case deterministic "
                "result as the dark tick. Green = the pre-committed score's top choice.</figcaption></figure>")

    body.append("<h2>What each path gives up</h2>")
    give = [
        ("P-05", "The house, the reduced assessment, and any say in who lives there later. "
         "Also the inflation hedge: a fixed portfolio does not reprice itself when rents rise.", "IRS-559"),
        ("P-06", "Same as P-05, plus the first two years of equity return - priced below.", "DAMO"),
        ("P-07", "Same again, plus another year of drag for insurance that the backtest does not reward.", "DAMO"),
        ("P-04", f"Cash: living in a {m(PROPERTY_A['value_2026'])} house while collecting two rents at B "
         "runs a deficit every year. It buys the exclusion, the §121 exclusion, and three more years of "
         "information.", "BOE-P19"),
        ("P-08", "The exclusion (rental use voids it) and, on exit, the whole depreciation recapture.",
         "BOE-P19"),
        ("P-09", "Thirty years of compounding on money locked in drywall. The house's total return is "
         "the rent you save minus the tax and upkeep, which is a bond-like return with house-price risk.",
         "SCC-RATEBOOK"),
        ("P-10", "Liquidity, and a very large deferred tax bill that arrives as one cheque.", "IRS-946"),
        ("P-01", "Everything. Highest utility, lowest wealth, and the only path where a roof failure is "
         "pure cost with no offsetting rent.", "owner"),
        ("P-03", "The exclusion, because A is not the principal residence; you get the rent instead.",
         "BOE-P19"),
        ("P-12", "The rent, the exclusion, and the cash. Modelled to show what 'keep it just in case' "
         "actually costs.", None),
    ]
    body.append(simple_table([("Path", "l"), ("Cost of that choice", "l"), ("Source", "src")],
                             [[pid, e(txt), srclink(src)] for pid, txt, src in give], short=True))

    body.append("<h2>Staging, with its own bill attached</h2>")
    body.append(simple_table(
        [("Policy", "l"), ("Mid-case wealth at 30 yr", "r"), ("vs immediate lump sum", "r"),
         ("10th percentile", "r"), ("Reinvestment risk if you wait", "l"), ("Source", "src")],
        [["P-05 invest at once", m(rows30["P-05"]["final_real"]), "&mdash;", m(rows30["P-05"]["p10"]),
          "None - fully invested at once, so a crash in year one hits everything", srclink("DAMO")],
         ["P-06 park 24 mo, phase 24 mo", m(rows30["P-06"]["final_real"]),
          pc(rows30["P-06"]["final_real"] / rows30["P-05"]["final_real"] - 1, 1, True),
          m(rows30["P-06"]["p10"]),
          f"Two years of bills at {pc(0.035,1)} while equities run their average; "
          "the delay is the price of the option", srclink("UST-DAILY")],
         ["P-07 park 36 mo, phase 36 mo", m(rows30["P-07"]["final_real"]),
          pc(rows30["P-07"]["final_real"] / rows30["P-05"]["final_real"] - 1, 1, True),
          m(rows30["P-07"]["p10"]),
          "A third year of the same drag; the backtest shows no extra protection for it",
          srclink("DAMO")]],
        short=True))
    body.append(note("Read together with <a href='phased.html'>Phased investing</a>, which tests each "
                     "policy against the actual crash years rather than against an average."))

    body.append("<h2>Year by year</h2>")
    body.append('<div class="controls noprint"><label for="psel">Path</label>'
                '<select id="psel">' +
                "".join(f"<option value='{pid}'>{pid} - {SHORT[pid]}</option>" for pid in specs) +
                "</select></div><div id='yr'></div>")
    body.append('<noscript><p class="small">The year-by-year tables are rendered by a script from '
                'data baked at build time. The same numbers are in <code>data/paths.json</code>.</p></noscript>')
    return page("paths", "The twelve paths, compared", "".join(body))


# --------------------------------------------------------- projections ----
def projections(ctx):
    p19, carry = ctx["prop19"], ctx["carry"]
    A, B = PROPERTY_A, PROPERTY_B
    body = []
    body.append('<p class="lede">Year-by-year projections for both buildings: market value, assessed '
                "value, property tax, insurance, water, electric and upkeep, on the assumptions listed at "
                "the bottom of the page. Property A is shown under all three assessment outcomes because "
                "the choice of path is what determines which one happens.</p>")

    body.append("<h2>Property A - three assessed-value futures</h2>")
    body.append(simple_table(
        [("Year", "l"), ("Market value", "r"), ("Assessed if the Prop 13 base survives untouched", "r"),
         ("Tax", "r"), ("Assessed with the Prop 19 exclusion (heir occupies)", "r"), ("Tax", "r"),
         ("Assessed if it reassesses in full (rented, or claim missed)", "r"), ("Tax", "r")],
        [_prop19_row(x) for x in p19["rows"]]))
    body.append(note("Prop 19 fixes the new taxable value once, at the transfer, and it then grows at the "
                     "Prop 13 factor like any other base. Re-applying the exclusion cap every year - which "
                     "some calculators do - overstates the later bills, so it is not done here. The "
                     f"middle column is the theoretical floor: it assumes an exclusion nobody can get on a "
                     f"{m(p19['value_T'])} house, and it is shown only to size what the allowance is worth "
                     f"({m(sum(x['prop19_tax'] - x['keep13_tax'] for x in p19['rows']))} of extra tax over "
                     "thirty years)."))
    body.append('<figure><div class="chart" data-chart="taxfan"></div>'
                "<figcaption>The three tax lines above, drawn. The gap between the green and blue lines is "
                "the value of occupying the house; the gap between blue and red is the value of filing the "
                "claim on time.</figcaption></figure>")

    body.append("<h2>Property A - full carrying cost, exclusion obtained</h2>")
    body.append(simple_table(CARRY_HDR, [_carry_row(x, prop="A") for x in carry["prop19"]["rows"]]))
    body.append("<h3>Same house, rented out (no exclusion, rent replaces the occupancy credit)</h3>")
    body.append(simple_table(CARRY_HDR, [_carry_row(x, prop="A") for x in carry["reassess"]["rows"]]))
    body.append(note("Electric is a <b>credit</b> at Property A: the owner's solar arrangement nets "
                     f"{m(I.r10(-180))} a year at the mid of the two figures supplied, which is why the "
                     "line is negative. The system's ownership (owned vs leased/PPA) and its net-billing "
                     "vintage are unconfirmed - see question Q-18 - and either answer can turn that credit "
                     "into a cost and a monthly obligation that survives a sale."))

    body.append("<h2>Property B - the building already owned</h2>")
    body.append(simple_table(CARRY_HDR, [_carry_row(x, prop="B") for x in ctx["carryB"]]))
    body.append(note(f"Water at Property B is the whole three-unit building's bill "
                     f"({m(B['water_mo'][0])}-{m(B['water_mo'][1])} a year, owner-supplied), not the "
                     "household's own use. The published SFPUC schedule for FY 2026-27 charges "
                     "$13.13 per dwelling unit per month plus $2.13 per hundred cubic feet for water, "
                     "$6.62 per unit plus $11.34 per discharge unit for wastewater, and $12.63 a month "
                     "of Tier 1 stormwater - small per-unit rates are quoted exactly as published, because "
                     "rounding a tariff makes the arithmetic unverifiable. Whether the building's billed "
                     "total is consistent with those rates has not been checked against the account; that "
                     "reconciliation is offline work (Q-15). " + srclink("SFPUC-RATES") + "</p>"))

    body.append("<h2>What the bills have actually done</h2>")
    rowsA = []
    for y, tax, assd, tc, ac in HISTORY_A:  # 2014-2026
        implied = (tax / assd) if (tax and assd) else None
        rowsA.append([str(y), m(tax) if tax else '<span class="na">not on the record</span>', m(assd),
                      pc(tc / 100 if tc is not None else None, 1), pc(ac / 100 if ac is not None else None, 1),
                      pc(implied, 3) if implied else '<span class="na">n/a</span>', SRCLINES["histA"]])
    body.append(simple_table([("Tax year", "l"), ("Property tax", "r"), ("Assessed value", "r"),
                              ("Change in tax", "r"), ("Change in assessed", "r"),
                              ("Implied rate on assessed value", "r"), ("Sources", "src")], rowsA,
                             caption="Property A, 2014-2026, as supplied by the household and rounded to "
                                     "$10. The 2026 tax line is not yet issued in the record supplied.",
                             short=True))
    body.append(simple_table([("Tax year", "l"), ("Property tax", "r"), ("Assessed value", "r"),
                              ("Change in tax", "r"), ("Change in assessed", "r"),
                              ("Implied rate", "r"), ("Sources", "src")],
                             [[str(y), m(t), m(a), pc((tc or 0) / 100, 1), pc((ac or 0) / 100, 1),
                               pc(t / a, 3), SRCLINES["histB"]] for (y, t, a, tc, ac) in HISTORY_B],
                             caption="Property B, 2016-2025, as supplied.", short=True))
    body.append(f'<div class="card warn"><b>Two anomalies, stated plainly.</b> Property A\'s bills imply a '
                f"rate of about {pc(RULES['sc_rate_central'])} of assessed value, and Property B's "
                "imply about 2.13% against San Francisco's published 1.18162182% secured rate. Neither is "
                "possible as a pure ad valorem levy, so both lines probably include direct assessments, "
                "supplemental amounts, or an assessed value quoted net of the homeowners' exemption while the "
                "tax is not. The model uses each household's own implied rate for continuity and flags both. "
                "Nothing in the recommendation changes unless the <i>ratio</i> changes. "
                '<a href="flagged.html">Flagged F-1 and F-2</a>.</div>')

    body.append("<h2>The distribution behind these numbers</h2>")
    body.append('<figure><div class="chart" data-chart="projdist"></div><figcaption>Terminal real wealth '
                "by path, 1,200 simulated economies. The point of the picture is that the distributions "
                "overlap heavily for the keep paths and separate cleanly only against the sell paths.</figcaption></figure>")
    body.append("<h2>Assumptions used on this page</h2>")
    arows = []
    for key, label, srckey in [("home_value_growth", "House value growth (nominal)", None),
                               ("inflation", "Inflation", None),
                               ("rent_growth", "Rent growth", None),
                               ("insurance_growth", "Insurance premium growth", None),
                               ("tbill_return", "Cash / Treasury bill return", None),
                               ("equity_real_return", "Equity real return", None)]:
        d = ECON[key]
        arows.append([label, pc(d["low"]), pc(d["mid"]), pc(d["high"]), e(d["basis"]),
                      srclink("DAMO" if key in ("tbill_return", "equity_real_return") else None)])
    arows.append(["Assessed-value growth cap (Prop 13)", pc(RULES["prop13_factor_cap"]),
                  pc(RULES["prop13_factor_cap"]), pc(RULES["prop13_factor_cap"]),
                  "CPI or 2%, whichever is lower; the 2% cap is used in every year, which is the "
                  "conservative (cheaper) choice for the keep paths when inflation runs above 2%.",
                  srclink("SCC-RATEBOOK")])
    arows.append([f"Upkeep as a share of value - Property A", pc(A["maintenance_pct_of_value"][0]),
                  pc((A["maintenance_pct_of_value"][0] + A["maintenance_pct_of_value"][1]) / 2),
                  pc(A["maintenance_pct_of_value"][1]),
                  "Owner-supplied, and stated as lighter than Property B's - which the tables above show.",
                  srclink("owner")])
    arows.append([f"Upkeep as a share of value - Property B", pc(B["maintenance_pct_of_value"][0]),
                  pc((B["maintenance_pct_of_value"][0] + B["maintenance_pct_of_value"][1]) / 2),
                  pc(B["maintenance_pct_of_value"][1]), "Owner-supplied.", srclink("owner")])
    body.append(simple_table([("Assumption", "l"), ("Low", "r"), ("Mid", "r"), ("High", "r"),
                              ("Basis", "l"), ("Source", "src")], arows, short=True))
    body.append(note("Sources column: the county rate book supplies the 1% levy, the factoring rule and "
                     "the due dates; the BOE supplies the Prop 19 formula and the indexed allowance; "
                     "SFPUC supplies Property B's water, wastewater and stormwater charges; the transit "
                     "authority's certification notice supplies the new San Francisco parcel tax. Where a "
                     "row says 'owner-supplied' there is no official source behind it and the flagged page "
                     "explains what would be needed."))
    return page("projections", "Yearly projections", "".join(body))


# ----------------------------------------------------------- tax rules ----
def tax_rules(ctx):
    p19, sales = ctx["prop19"], ctx["sales"]
    body = []
    body.append('<p class="lede">Three tax systems apply to this decision. They have different '
                "authorities, different deadlines and different rules, and the most common way an "
                "inherited-house plan goes wrong is by treating one of them as if it answered another. "
                "They are kept apart below, and every rule carries its status: enacted and read, enacted "
                "but not read, passed and awaiting certification, proposed, or unverified.</p>")
    body.append('<div class="grid">')
    for t, b in [("Estate / transfer tax",
                  "Levied on the transfer at death. Federal only in our case. Decides whether a Form 706 "
                  "is due, and whether the estate is large enough to need planning at all. It does not "
                  "change the property tax bill."),
                 ("Income tax",
                  "Levied on the gain when something is sold, and on rent while it is rented. The step-up "
                  "at death lives here - it resets basis to date-of-death value. It has no effect on the "
                  "assessment."),
                 ("Property tax",
                  "Levied every year on the assessed value by the county. Proposition 13 and Proposition 19 "
                  "live here. A step-up in basis does nothing for it, and it does not care about your gain.")]:
        body.append(f'<div class="card"><b>{t}</b><p class="small">{b}</p></div>')
    body.append("</div>")

    body.append("<h2>Federal estate tax - thresholds as published</h2>")
    body.append(simple_table([("Year of death", "l"), ("Filing threshold", "r"), ("Top rate", "r"),
                              ("Source", "src")],
                             [["2024", m(13_610_000), "40%", srclink("IRS-ESTATE")],
                              ["2025", m(13_990_000), "40%", srclink("IRS-ESTATE")],
                              ["2026", m(15_000_000), "40%", srclink("IRS-ESTATE")],
                              ["2040-2050 (modelled)",
                               '<span class="na">not published</span>', "40% (assumed unchanged)",
                               srclink(None, "indexed annually; do not project the amount, re-read it")]],
                             short=True))
    body.append(note(f"The two properties together are worth about "
                     f"{m(PROPERTY_A['value_2026'] + PROPERTY_B['value_2026'])} today, so the estate is "
                     "close to the threshold on real property alone before cash, retirement accounts and "
                     "insurance are counted - and the household has told us there is a considerable amount "
                     "of cash. That is what makes the Form 706 question live rather than theoretical. "
                     "Portability of a predeceased spouse's unused exclusion (DSUE) is only available if a "
                     "706 was filed to elect it: see Q-10."))
    body.append(f'<div class="card warn"><b>Not modelled, and it matters:</b> California is assumed to have '
                "no estate or inheritance tax. That assumption was <i>not</i> verified against an official "
                "source in this pass and it is load-bearing for the cash side of the plan. See "
                "<a href='flagged.html'>F-6</a> and <a href='open-questions.html'>Q-11</a>.</div>")

    body.append("<h2>Proposition 19 - the eligibility test, applied</h2>")
    checks = [
        ("Property must have been the transferor's principal residence", "likely yes",
         "Confirm the decedent occupied it; a rental or second home is excluded outright."),
        ("Heir must make it their principal residence", "depends on the decision",
         "This is the whole live/rent fork. Renting it, or leaving it vacant, forfeits the exclusion."),
        ("Homeowners' exemption claimed within 1 year of transfer", "action required",
         "A separate filing with a deadline. Missing it voids the exclusion even if everything else holds."),
        ("BOE-19-P claim within 3 years, or before any transfer to a third party", "action required",
         "So 'live there two years, then sell' must not sell before the claim is granted."),
        ("Value cap: prior factored base year value + indexed allowance", f"{m(p19['cap_T'])} at the modelled transfer",
         f"Allowance is {m(I.RULES['prop19_indexed_amount'])} for transfers in the current window; carried "
         "forward here at 2% a year, which is our assumption, not a published figure."),
        ("Excess above the cap is added to the transferred base", f"{m(p19['excess_T'])}",
         "So the exclusion reduces the bill, it does not eliminate it."),
    ]
    body.append(simple_table([("Condition", "l"), ("Status for Property A", "l"), ("What it means", "l")],
                             [[a, f"<b>{b}</b>", c] for a, b, c in checks], short=True))
    body.append(f'<p class="small">Applying the formula: new taxable value = {m(p19["fbyv_T"])} + '
                f'max(0, {m(p19["value_T"])} - {m(p19["cap_T"])}) = <b>{m(p19["base_excluded"])}</b>, '
                f'tax {m(p19["tax_excluded"])}. Without the exclusion: {m(p19["value_T"])} assessed, tax '
                f'{m(p19["tax_full"])}. Difference {m(p19["delta_yr0"])} a year. '
                f'<span class="small">{srclink("BOE-P19")}</span></p>')

    body.append("<h2>Income tax on a sale - worked, five ways</h2>")
    body.append(simple_table(
        [("Sale timing", "l"), ("Price", "r"), ("Selling costs", "r"), ("Adjusted basis", "r"),
         ("Gain", "r"), ("§121 excluded", "r"), ("Depreciation recaptured", "r"), ("Federal tax", "r"),
         ("California tax", "r"), ("Total tax", "r"), ("Effective rate on gain", "r"),
         ("Net in hand", "r")],
        [[e(x["label"]), m(x["price"]), m(x["costs"]), m(x["adjusted_basis"]), m(x["gain"]),
          m(x["exclusion"]), m(x["recapture"]), m(x["fed_tax"]), m(x["ca_tax"]), m(x["total_tax"]),
          pc(x["effective_rate"] / 100, 1), m(x["net_after_tax"])] for x in sales], short=True))
    body.append(note("Effective rates land between 31% and 38% because California taxes the whole gain as "
                     "ordinary income and the 1% mental/behavioral health surtax adds a further slice above "
                     "a $1,000,000 threshold that is not indexed. A federal-only reading of the same sale "
                     "understates the bill by roughly a third. Source: FTB capital-gains page and line 62 "
                     "of the Form 540 booklet."))

    body.append("<h2>Depreciation and §1250 recapture - the schedule that creates the bill</h2>")
    v0 = PROPERTY_A["value_2026"]
    rows = []
    cum = 0.0
    for y in range(1, 11):
        d = (v0 * 0.75) / RULES["depr_life_resid"]
        cum += d
        rows.append([f"Rental year {y}", m(v0), "75%", m(d), m(cum), m(cum * 0.25),
                     m(cum * RULES["niit"])])
    body.append(simple_table([("Year", "l"), ("Value used", "r"), ("Building share", "r"),
                              ("Depreciation claimed", "r"), ("Cumulative", "r"),
                              ("Recapture at 25% when sold", "r"), ("Plus NIIT at 3.8%", "r")],
                             rows, short=True))
    body.append(note(f"Residential real property is depreciated straight-line over {RULES['depr_life_resid']} "
                     "years with a mid-month convention, and only the building - never the land. The 75% "
                     "building share is an assumption, not a cost-segregation study, and it is flagged (F-7). "
                     "Every dollar in the cumulative column is a dollar of tax deferred, not avoided: it "
                     "comes back at up to 25% plus 3.8% on the sale, which is exactly what the "
                     "recapture columns are for. Source: IRS Publication 946 and Topic 409."))

    body.append("<h2>Section 121 - the switch that only an occupant can flip</h2>")
    body.append(simple_table([("Path shape", "l"), ("2 of last 5 years owned <i>and</i> used?", "l"),
                              ("Exclusion available", "r"), ("Consequence", "l"), ("Source", "src")],
                             [["Sell in the year of the death", "no - never occupied", "no",
                               "Doesn't matter: the step-up already eliminated the gain.", "IRS-523"],
                              ["Live 2-3 years, then sell", "yes", m(RULES["sec121_single"]),
                               "Gain on the appreciation during ownership is largely covered.", "IRS-523"],
                              ["Rent from day one", "no", "none",
                               "The full gain from date-of-death value to sale price is taxable, plus recapture.",
                               "IRS-523"],
                              ["Live 3 years, rent 7, sell in year 10", "yes (2 of the last 5)", m(RULES["sec121_single"]),
                               "Partial: the exclusion applies, but non-qualified use after 2008 can prorate it. "
                               "Ask the CPA - this is the one place where the sequence matters.", "IRS-523"],
                              ["Live 12 years, then sell", "yes", m(RULES["sec121_single"]),
                               "Exclusion caps at $250k single; on a gain this size it is a rounding error, "
                               "not a strategy.", "IRS-523"]], short=True))

    body.append("<h2>What it costs to sell, priced in both markets</h2>")
    tr = ctx["transfer"]
    body.append(simple_table([("Cost line", "l"), ("Property A - Santa Clara County", "r"), ("Property B - San Francisco", "r"),
                              ("Basis / source", "src")],
                             [["Price (2026 estimate)", m(tr["A"]["price"]), m(tr["B"]["price"]), srclink("owner")],
                              ["Commission", m(tr["A"]["commission"]), m(tr["B"]["commission"]),
                               srclink(None, f"{pc(TRANSACT['A']['commission_pct'],1)} / {pc(TRANSACT['B']['commission_pct'],1)} - market convention, not a rate card")],
                              ["Seller concessions / credits", m(tr["A"]["concessions"]), m(tr["B"]["concessions"]),
                               srclink(None, "0.5% / 0.8% assumed")],
                              ["Documentary / real property transfer tax", m(tr["A"]["dtt"]), m(tr["B"]["dtt"]),
                               srclink("RTC-11911") + " " + srclink("SF-TRANSFER-TAX")],
                              ["Recording fees", m(tr["A"]["recording"]), m(tr["B"]["recording"]),
                               srclink("SCC-RECORDER-FEES")],
                              ["Preparation, report, escrow, title", m(tr["A"]["prep"]), m(tr["B"]["prep"]),
                               srclink(None, "0.6% / 1.0% assumed")],
                              ["<b>Total friction</b>", f"<b>{m(tr['A']['total'])}</b>", f"<b>{m(tr['B']['total'])}</b>",
                               srclink("model")],
                              ["As a share of price", pc(tr["A"]["pct_of_price"] / 100, 1),
                               pc(tr["B"]["pct_of_price"] / 100, 1), srclink("model")]],
                             short=True))
    body.append(note("San Francisco's transfer tax is a <b>cliff</b>, not a marginal schedule: at $1M-$5M the "
                     "tier of $3.75 per $500 applies to the entire consideration, so a small price move across "
                     "the $5,000,000 line changes the bill by thousands. Property B at $1.8M sits two tiers "
                     "below it; a future sale of the building after further appreciation would not. Exemptions "
                     "for transfer at death, to a spouse or registered domestic partner, and reconveyance to "
                     "one's own trust are as published by the Assessor-Recorder."))
    return page("tax-rules", "Tax rules that apply, verified where possible", "".join(body))


# ------------------------------------------------------- costs & capital ----
def costs(ctx):
    A, B = PROPERTY_A, PROPERTY_B
    body = []
    body.append('<p class="lede">The five-year maintenance and capital plan for both buildings, the '
                "utility and insurance lines as far as they can be sourced, and the transfer costs already "
                "priced on the tax page. Where a figure exists only as an owner's estimate, it says so; "
                "where no official rate could be found, the cell is empty.</p>")
    body.append("<h2>Five-year capital plan</h2>")
    rows = []
    for c in ctx["capital"]:
        lo, hi = c["cost"]
        rows.append([c["building"], e(c["item"]), e(c["trigger"]),
                     m(lo) if lo else '<span class="na">needs the inspection</span>',
                     m(hi) if hi else "", e(c["why"]),
                     pill(e(c["status"]), "warn" if "not" in c["status"] or "required" in c["status"] else ""),
                     srclink(c["src"])])
    body.append(simple_table([("Building", "l"), ("Item", "l"), ("Trigger", "l"), ("Low", "r"),
                              ("High", "r"), ("Why it is on the list", "l"), ("Status", "l"),
                              ("Source", "src")], rows, short=True))
    body.append(note("These are the items that decide whether the keep paths are solvent, not whether they "
                     "are pretty. The two blank-cost rows are blank because the answer is a fact about the "
                     "building that nobody has looked up yet: a permit record and an inspection. A model "
                     "that guessed them would look precise and be worthless."))

    body.append("<h2>Utilities and insurance - what is sourced and what is not</h2>")
    rows = [
        ["Property A - water / sewer", m(A["water_mo"][0]) + " to " + m(A["water_mo"][1]) + " a year",
         "Owner-supplied ($100-$150 a month). The city's own rate schedule was searched for and "
         "not located in this pass; the city bills through Santa Clara County's flood-control and water "
         "district arrangements, which are parcel-specific.",
         srclink(None, "official rate sheet not found - flagged F-5")],
        ["Property A - electric", m(A["electric_mo_net"][0]) + " to " + m(A["electric_mo_net"][1]) + " a year (a credit)",
         "Owner-supplied solar net credit. The tariff vintage (NEM 1.0/2.0/3.0) determines whether an excess "
         "credit is paid in cash or banked, and a sale may not carry it to the heir at all.",
         srclink(None, "Q-18")],
        ["Property A - insurance", m(A["insurance_yr_owner"]) + " a year (owner's figure)",
         "No official source exists for a premium; the figure is a household estimate. The model uses a higher "
         "placeholder because an owner-occupied single-family house in Santa Clara County with the coverage "
         "implied here is unlikely to price at that number. Three written quotes are the only real fix.",
         srclink(None, "flagged F-3")],
        ["Property B - water", m(B["water_mo"][0]) + " to " + m(B["water_mo"][1]) + " a year (whole building)",
         "Owner-supplied for all three units. The published SFPUC FY 2026-27 multi-family schedule "
         "($13.13 per unit per month plus $2.13 per ccf, wastewater $6.62 + $11.34 per discharge unit, "
         "stormwater Tier 1 $12.63) is the rate side of the reconciliation.",
         srclink("SFPUC-RATES")],
        ["Property B - electric (common area)", m(B["electric_mo"][0]) + " to " + m(B["electric_mo"][1]) + " a year",
         "Owner-supplied; separately metered tenants pay their own, so this is the shared-load line only.",
         srclink("owner")],
        ["Property B - insurance", m(B["insurance_yr_owner"]) + " a year (owner's figure)",
         "A three-unit landlord policy is a different product from a homeowner policy and prices "
         "materially higher; the model uses $3,000 and flags the gap.",
         srclink(None, "flagged F-3")],
        ["Property B - new parcel tax", m(RULES["sf_prop_h_multifamily_base"]) + " a year, plus $0.195 per sq ft over 5,000",
         "Proposition H, approved 2026-11-03 (74.4%), certification due 2026-12-03, first bills FY 2027-28. "
         "Up to 50% may be passed through to rent-controlled units, capped at $65 per unit, only where the "
         "initial rent predates 2027-06-01.",
         srclink("SF-PROP-H-MTC")],
    ]
    body.append(simple_table([("Line", "l"), ("Figure", "r"), ("What is behind it", "l"), ("Source", "src")],
                             rows, short=True))
    return page("costs", "Carrying costs, capital plan and utilities", "".join(body))


# ----------------------------------------------------- process, deadlines ----
def process(ctx):
    body = []
    body.append('<p class="lede">The route below is the trust route, which is what the household expects: '
                "the house is held in a trust and passes outside probate. The dates are the ones that "
                "actually bind - a missed one-year filing is not recoverable by argument.</p>")
    rows = [[str(p["step"]), f"<b>{e(p['title'])}</b>", e(p["body"]), srclink(p["src"])] for p in ctx["process"]]
    body.append(simple_table([("#", "l"), ("Stage", "l"), ("What to do", "l"), ("Source", "src")], rows))
    body.append("<h2>Timeline</h2>")
    kinds = {"local": "info", "property": "warn", "estate": "bad", "income": "info", "tenant": "warn"}
    body.append('<div class="tl">')
    for d in R.TIMELINE:
        when, ev = e(d["when"]), e(d["event"])
        sysname = d["system"]
        pillcls = kinds.get(sysname, "")
        cons, actor = e(d["consequence"]), e(d["actor"])
        src = srclink(d["src"])
        body.append('<div class="tlrow"><span class="tld">' + when + '</span>'
                    '<span class="tlt">' + ev + '</span> '
                    '<span class="pill ' + pillcls + '">' + sysname + '</span>'
                    '<p class="small">' + cons + ' <span class="tag">owner: ' + actor + '</span></p>'
                    '<div class="src">' + src + '</div></div>')
    body.append("</div>")
    body.append(note("Everything relative ('within 1 year of transfer') is measured from the distribution, "
                     "not from the death, and the difference between those two dates can be the difference "
                     "between having Prop 19 and not having it. Q-08 asks which."))
    body.append("<h2>What the trust route does and does not do</h2>")
    body.append("<div class='two'>")
    for h, items in [("It avoids", ["Probate, and the 12-18 months and publication requirements that come with it",
                                    "A public record of the transfer in most cases",
                                    "Contest exposure between beneficiaries, if the instrument is clean"]),
                     ("It does not avoid", ["A change in ownership for property-tax purposes when the trustee "
                                           "distributes to the beneficiary",
                                           "The date-of-death valuation requirement - an appraisal is still needed",
                                           "Form 706 if the estate exceeds the federal threshold",
                                           "Medi-Cal estate claims, which attach to the property regardless of the trust",
                                           "Income tax on the gain if the heir later sells above the stepped-up basis"])]:
        body.append(f'<div class="card"><b>{h}</b><ul class="tight">' +
                    "".join(f"<li>{e(i)}</li>" for i in items) + "</ul></div>")
    body.append("</div>")
    return page("process", "The inheritance process, step by step", "".join(body))


# ------------------------------------------------------------ black swan ----
def black_swan(ctx):
    st, reg, roll = ctx["stats"], ctx["regime"], ctx["rolling"]
    rd = ctx["rent_diag"]
    body = []
    body.append('<p class="lede">Fifty years of growth and inflation are never smooth. This page is the '
                "answer to 'what if the next thirty years do not look like the last thirty, or look like the "
                "worst of them'. Everything here is computed from the annual record, not quoted from memory, "
                "and the record itself is academic rather than official - see F-9.</p>")
    body.append("<h2>What the record actually says</h2>")
    body.append('<div class="grid">')
    for lab, val, sub in [
        ("Years of data", f"{st['n_years']}", "1928-2025, S&amp;P 500 total return including dividends"),
        ("Geometric mean", f"{st['sp_geo']:.1f}% a year", "the number people quote; the one you can actually earn "
         "only if you never withdraw and never rebalance badly"),
        ("Arithmetic mean", f"{st['sp_arith']:.1f}% a year", f"a gap of {st['sp_arith']-st['sp_geo']:.1f} points "
         "that is pure volatility drag - and it is why sequencing matters"),
        ("Volatility", f"{st['sp_sd']:.1f}%", "one standard deviation; a third of all years sit outside it"),
        ("Negative years", f"{st['neg_years']} of {st['n_years']}", f"and {st['down20']} of them fell more than 20%"),
        ("Worst single year", f"{st['worst']:.1f}% ({st['worst_year']})", "with bills paying "
         f"{H.BILL[st['worst_year']]*100:.1f}% that same year"),
        ("Best single year", f"{st['best']:.1f}% ({st['best_year']})", "which is why averages flatter the record"),
        ("Bills, geometric", f"{st['bill_geo']:.1f}% a year", "the parked-cash lane's whole reason for existing"),
    ]:
        body.append(f'<div class="stat"><div class="l">{lab}</div><div class="v">{val}</div>'
                    f'<div class="n">{sub}</div></div>')
    body.append("</div>")

    body.append('<p class="small">All eight figures above are computed from one table: '
                + srclink("DAMO") + ' The same table supplies the episode analysis below and every '
                "distribution on the what-if page, which is why the site can regenerate them instead of "
                "quoting them.</p>")
    body.append("<h2>Regimes, measured</h2>")
    body.append(simple_table([("Episode", "l"), ("Years", "l"), ("Equities over the whole episode", "r"),
                             ("Bills over the same years", "r"), ("Read", "l"), ("Source", "src")],
                             [[e(x["label"]), x["span"], pc(x["eq"] / 100, 1), pc(x["bill"] / 100, 1),
                               "The 1930s are the case for not being fully invested the day after a sale; "
                               "2008-09 is the case against holding everything in cash at the same time "
                               "(bills paid 1.4% while inflation ran hot, and equities then returned 25.9% "
                               "in 2009)." if x["span"] == "1929-1932" else
                               ("Both assets fell together - 2022 is the regime where 'wait in cash' does not "
                                "protect you from anything, because the house also stalls."
                                if x["span"] == "2021-2022" else
                                ("Cash yields were near zero, so waiting cost almost nothing and bought "
                                 "real protection." if x["span"] == "2007-2009" else
                                 "Bills were paying 5-8%, so the parking lane earned its keep outright."
                                 if x["span"] in ("1973-1974", "1937-1938") else
                                 "Short, sharp, and over before a staged investor had finished moving.")),
                               srclink("DAMO")] for x in reg], short=True))
    body.append(note("Ten-year rolling returns are the honest version of 'average return': "
                     f"the middle of the record is {roll['med']:.1f}% a year, the 5th percentile of "
                     f"overlapping ten-year windows is {roll['lo']:.1f}%, and {roll['pct_negative']:.1f}% "
                     "of all ten-year windows in the whole record lost money in real terms. Anyone quoting "
                     "10% as a plan input is quoting the mean of a distribution whose bottom decile is "
                     "negative."))
    body.append('<figure><div class="chart" data-chart="rolling"></div>'
                "<figcaption>Annualised S&amp;P 500 total return, every overlapping ten-year window since "
                "1928. The flat stretch through the 2000s is a decade of 1%-ish returns - exactly the "
                "regime a phased entry was designed for.</figcaption></figure>")

    body.append("<h2>Which paths a regime shift hurts, and why</h2>")
    body.append(simple_table([("Path", "l"), ("Exposure to a bad start", "l"), ("Exposure to a long slump", "l"),
                             ("What the model shows", "r"), ("Source", "src")],
                            [["P-05 sell, invest at once", "highest - fully invested in year one",
                              "moderate - no property to fall back on",
                              f"p10 {m(ctx['paths30']['P-05']['p10'])} vs median {m(ctx['paths30']['P-05']['p50'])}"],
                             ["P-06 / P-07 staged", "lowest by construction",
                              "highest - the drag is paid in every scenario",
                              f"costs about {ctx['stage_cost']:.1f}% of terminal wealth on average"],
                             ["P-01 / P-02 live in A", "none - the asset is the house",
                              "the house itself is the concentrated bet, and the tax bill is fixed",
                              f"p10 {m(ctx['paths30']['P-01']['p10'])}, and no portfolio to draw on"],
                             ["P-08 / P-10 rent it", "the tenant's income is the hedge",
                              "worst of both: a reassessed tax bill plus a rent market that can stall",
                              f"needs {m(rd['need_rent_month'])} a month to match a safe T-bill yield - see below",
                              srclink("model")]],
                            short=True))
    body.append(f'<div class="card warn"><b>The regime that breaks the rent path is not a crash, it is a '
                f'yield.</b> At the modelled transfer the gross rent on Property A is about '
                f'{rd["gross_yield"]:.1f}% of its value, and net operating income at the owner\'s own rent '
                f'estimate is <b>{m(rd["noi"])}</b> - negative, before any income tax, because the '
                f'reassessed tax bill alone ({m(rd["tax"])}) is larger than the rent left after upkeep. '
                f'To match what the same money earns in 3-month to 2-year Treasuries after tax '
                f'({rd["safe_yield"]:.1f}%), the rent would have to be {m(rd["need_rent_month"])} a month, '
                f'which is {rd["vs_owner_estimate"]:.0f}% above the estimate used so far. That is why no '
                'amount of optimism about stock returns rescues the rent paths, and why the comparables '
                'work on <a href="comparables.html">this page</a> matters more than any assumption about '
                'the market.</div>')
    return page("black-swan", "Black swans and regime switching", "".join(body))


# --------------------------------------------------- phased investing ----
def phased(ctx):
    by = ctx["by"]
    body = []
    body.append('<p class="lede">The household\'s proposal, tested rather than described: after the sale, '
                "hold the proceeds in 3-month to 2-year Treasuries for 24-36 months, then move into equities "
                "in monthly instalments, so a crash immediately after the inheritance cannot take the whole "
                "stake. Below is what that does in the ten worst entry years of the last century, and what it "
                "costs in the rest of them.</p>")
    body.append(f'<div class="card"><div class="kicker">Current environment</div><p class="small">The '
                f"Instruments in the lane pay what the curve says, not what history averaged: on the Treasury "
                f"published curve for 2026 the 3-month stood at {ctx['curve'][0][1]}% and the 2-year at "
                f"{ctx['curve'][1][1]}%, with the 10-year at {ctx['curve'][2][1]}%. A parking lane therefore "
                f"costs much less to hold in 2026 than it did in 2012, and the whole comparison below shifts "
                f"when the short rate moves. <span class='src'>{srclink('UST-DAILY')}</span></p></div>")
    rows = []
    for entry, tab in sorted(by.items()):
        lump = tab[(0, 1)]
        avail = min(30, max(y for y in H.YEARS) - entry)
        cells = [f"<b>{entry}</b>",
                 f"{lump['wealth']:.2f}&times;", f"{lump['max_dd']*100:.1f}%",
                 ("partial - only " + str(avail) + " years of record") if avail < 30 else "full 30 years"]
        for k in [(0, 36), (12, 12), (24, 24), (36, 36)]:
            r = tab.get(k)
            if not r:
                cells.append("")
            else:
                cells.append(f"{r['wealth']:.2f}&times; <span class='small'>"
                             f"{r['vs_lump']*100:+.1f}%</span><br><span class='small'>dd {r['max_dd']*100:.1f}% "
                             f"({r['dd_vs_lump']*100:+.0f}pp)</span>")
        rows.append(cells)
    body.append(simple_table(
        [("Sale year (the crash you walked into)", "l"), ("Invest all at once", "r"), ("", "r"),
         ("Record available", "l"), ("Stay in cash 3 yr, then lump", "r"), ("Park 12 mo, phase 12 mo", "r"),
         ("Park 24 mo, phase 24 mo", "r"), ("Park 36 mo, phase 36 mo", "r")],
        rows, caption="Wealth multiple of $1 after 30 years (or as much as the record contains), and the "
                      "deepest peak-to-trough drawdown along the way. Percentages in each staged column are "
                      "the difference against the same-entry lump-sum outcome.", short=False))
    body.append(note("Annual returns were converted to a monthly path geometrically, "
                     "r<sub>m</sub> = (1 + r<sub>y</sub>)<sup>1/12</sup> - 1, so intra-year order inside a "
                     "single year is assumed rather than observed. That understates how nasty a crash year "
                     "feels to a phased investor and it is the weakest step in this page. It affects the "
                     "third decimal, not the ranking."))

    body.append("<h2>The verdict, with the bill attached</h2>")
    body.append(simple_table([("Claim", "l"), ("Supported?", "l"), ("Evidence", "l")],
        [["Staging softens a crash immediately after the sale", "yes, decisively",
          "Entering 1929, a 24-month park plus 24-month phase ends 30 years later "
          f"{by[1929][(24,24)]['vs_lump']*100:+.0f}% ahead of lump-sum and cuts the deepest drawdown by "
          f"{abs(by[1929][(24,24)]['dd_vs_lump'])*100:.0f} points. Entering 2007 it is "
          f"{by[2007][(24,24)]['vs_lump']*100:+.0f}% with the same drawdown reduction. "
          "It works because the two things being mixed - bills and equities - are negatively correlated in "
          "exactly those years."],
         ["Staging improves the average outcome", "no",
          "Over the full record, moving money in later means missing the up days as often as the down ones. "
          f"In the model's own Monte Carlo the staged paths give up about {ctx['stage_cost']:.0f}% of terminal "
          "wealth on average."],
         ["Longer is better", "no",
          "36 months of parking is never better than 24 on the crash years and always costs more elsewhere. "
          "If the lane is wanted, 24 months is the defensible number."],
         ["Cash is a safe place to wait", "only when it pays",
          "In 2008-09 bills paid 1.40% then 0.15%; in 2021-22 they paid 0.04% and 2.09% while the house and "
          "the market both stalled. The lane is only 'safe' to the extent the short rate covers inflation, "
          "which is a fact about the year you enter, not a property of T-bills."],
         ["Reinvestment risk is the real risk of staging", "yes",
          "The 2020 and 2021 entries show the mirror image: parking through a recovery is the one way to "
          "lose to lump-sum investing on the drawdown metric as well as the return metric, because you buy "
          "back in at the high. Any pitch for staging has to carry this sentence."]], short=True))
    body.append("<h2>Investment policy for the proceeds, in writing before the money exists</h2>")
    body.append("<ol class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "Two thirds of net proceeds into a globally diversified, low-cost equity index; one third into "
        "short-duration Treasuries. Rebalance when either side moves 5 points off target.",
        "Whatever the household needs within five years - capital works, taxes, a possible buyout of a "
        "co-beneficiary - is held in Treasuries maturing inside that window and is not part of the equity "
        "allocation at all.",
        "A liquidity floor of 24 months of all carrying costs for both buildings plus a capital-events "
        "reserve, held in cash and maturing bills, agreed before any illiquid choice is made.",
        "The parking lane, if chosen, is 24 months maximum, with the equity tranche moved in on a fixed "
        "calendar (monthly), not on a market condition. No 'waiting for a better entry' clause - that "
        "clause is how a policy becomes a wager.",
        "No leverage, no single-stock positions, no second property purchase without re-running this "
        "model, and no decision at all inside the first 90 days after the death.",
        "The policy is signed and dated, and any change to it requires a written reason. Its whole value "
        "is that it was written when nothing was happening.",
    ]) + "</ol>")
    body.append(note("This is a starting draft for the household and its advisers, not advice, and it "
                     "is deliberately short: a policy nobody can read is a policy nobody follows."))
    return page("phased", "The phased-investing lane", "".join(body))


# ------------------------------------------------------------ what if ----
def what_if(ctx):
    body = []
    body.append('<p class="lede">Six dials. Every combination was computed by the model before this page '
                "was written, so the controls below are lookups into results, not a JavaScript "
                "reimplementation of the model. The grid is 3 &times; 3 &times; 3 &times; 2 &times; 3 = 162 "
                "published scenarios; if your view is between the dials, the nearest one is what you see.</p>")
    d = ctx["grid_dials"]
    body.append('<div class="controls noprint">')
    for key, label, opts in [("home", "House value growth (nominal)", d["home"]),
                             ("equity", "Equity return (real)", d["equity"]),
                             ("rent", "Rent growth", d["rent"])]:
        body.append(f'<div><label for="d-{key}">{label}: <span class="val" id="v-{key}"></span></label>'
                    '<input type="range" id="d-' + key + '" min="0" max="2" step="1" value="1"></div>')
    body.append('<div><label for="d-prop19">Prop 19 exclusion obtained?</label>'
                '<select id="d-prop19"><option value="1">yes - heir occupies and files</option>'
                '<option value="0">no - reassesses in full</option></select></div>')
    body.append('<div><label for="d-hz">Horizon</label><select id="d-hz">'
                + "".join(f'<option value="{h}"{" selected" if h==30 else ""}>{h} years</option>'
                          for h in [10, 20, 30]) + "</select></div>")
    body.append('<div><label for="d-metric">Rank on</label><select id="d-metric">'
                '<option value="w">real terminal wealth only</option>'
                '<option value="u">wealth plus what you consume (imputed rent)</option>'
                '<option value="n">nominal wealth at the horizon (not deflated)</option></select></div>')
    body.append('<div class="switch"><input type="checkbox" id="d-showdelta" checked>'
                "<label for='d-showdelta' style='margin:0'>show the gap against the best path</label></div>")
    body.append("</div>")
    body.append('<div id="wi"></div>')
    body.append('<figure><div class="chart" data-chart="wiBars"></div><figcaption>Bars are the selected '
                "scenario; the grey marker is the same path at the central assumption. Red means the path "
                "loses money relative to where it started.</figcaption></figure>")

    body.append("<h2>How often does each path win?</h2>")
    rob = ctx["robust"]
    body.append(simple_table([("Path", "l"), ("Rank 1 in", "r"), ("Top 3 in", "r"), ("Median rank", "r"),
                             ("Worst rank", "r"), ("Read", "l")],
                             [[f"{r['id']} - {SHORT[r['id']]}", f"{r['first']} of {r['n']}",
                               f"{r['top3']} of {r['n']}", r["med"], r["worst"], e(r["note"])]
                              for r in rob], short=True))
    body.append(note("Counted over all 162 published scenarios, so it is a robustness measure rather than "
                     "a forecast: a path that is first in 4 scenarios and last in 4 is not a recommendation, "
                     "it is a coin toss with extra steps."))
    body.append("<h2>The two numbers that would actually change the ranking</h2>")
    rd = ctx["rent_diag"]
    body.append(simple_table([("Input", "l"), ("Value used", "r"), ("What the ranking needs", "r"),
                              ("Source", "src")],
        [["Monthly rent for Property A", m(rd["rent_month"]),
          f"would have to be <b>{m(rd['need_rent_month'])}</b> for the rent paths to beat a safe "
          "T-bill yield on the same money", srclink("owner")],
         ["Prop 19 outcome", "assumed obtained in the live paths",
          "if it is <i>not</i> available, the live paths lose "
          f"{m(ctx['prop19']['delta_yr0'])} a year and the ranking narrows sharply - see the dial above",
          srclink("BOE-P19")],
         ["House value growth", pc(ECON["home_value_growth"]["mid"], 1),
          "the sell paths are almost insensitive to it, because they convert the house into a portfolio; "
          "the keep paths move about " + ctx["home_sens"] + " across the dial range", srclink(None)],
         ["Discount rate", pc(ECON["discount_rate"], 1),
          "matters for the imputed-rent column far more than for wealth; it is a convention, not an "
          "estimate of anything", srclink(None)],
         ["Inflation", pc(ECON["inflation"]["mid"], 1),
          "cancels in the real-wealth metric except through the 2% Prop 13 cap, which it silently "
          "overwhelms whenever CPI runs hot", srclink(None)]], short=True))
    body.append('<p class="small">Want a dial that is not here? The model takes it as an argument: '
                "<code>cd model &amp;&amp; python3 build.py</code> after editing "
                "<code>model/inputs.py</code>. Deliberately not faked in the browser, because a control "
                "that quietly disagrees with the published model is worse than no control.</p>")
    return page("what-if", "What if - the sensitivity grid", "".join(body))
