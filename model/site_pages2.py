"""
site_pages2.py — the registers and governance pages: what to do next, what is missing, what
is doubtful, what has been verified, and the one page the advisers get.
"""
import json

from site_lib import (PROPERTY_A, PROPERTY_B, RULES, ECON, TRANSACT, SOURCES, QUESTIONS,
                      SUGGESTIONS, FLAGS, HISTORY_A, ASOF, NEXT_CHECK, e, m, pc, num, srclink,
                      simple_table, pill, status_pill, page, note)
import inputs as I
import registers as R
import history as H
import engine as E
import projections as P
from site_pages import SHORT


def srclink_note(key):
    """One line on what each source is used for, so the table answers 'why is this here?'."""
    notes = {
        "BOE-P19": "the exclusion formula, the occupancy and filing conditions, the indexed amount",
        "BOE-LTA25009": "the published allowance and its effective window",
        "BOE-PUB801": "the plain-language fact sheet used to sanity-check the formula",
        "SCC-RATEBOOK": "the 1% levy, the factoring rule, the bond lines, the due dates and penalties",
        "SCC-RATEBOOK-PAGE": "proves FY 2025-26 is the newest edition, so nothing here is labelled 2026-27",
        "SCC-RECORDER-FEES": "recording fees on the sell path, including the offset when DTT applies",
        "RTC-11911": "the county transfer tax and the 'exclusive of liens' measurement",
        "RTC-61": "the 35-year lease rule that makes a tenanted sale a change in ownership",
        "FTB-CG": "no preferential state rate for capital gains",
        "FTB-540-2025": "the resident return's treatment of gains and exemptions",
        "FTB-540-BOOKLET-2024": "the 1% line over the $1M threshold, as a printed number",
        "IRS-ESTATE": "threshold by year of death and the portability requirement",
        "IRS-409": "the gain bands, the 25% recapture cap, the loss deduction limit",
        "IRS-706": "the nine-month deadline and the extension mechanism",
        "IRS-523": "the 2-of-5-years test for the exclusion",
        "IRS-544": "holding period for inherited property and the recapture mechanics",
        "IRS-946": "27.5 years, straight line, mid-month convention",
        "IRS-559": "basis at death and the estate's own income tax",
        "SF-TTC-RATE": "the San Francisco secured rate used for Property B",
        "SF-TRANSFER-TAX": "the cliff tiers and the exemptions, including transfer at death",
        "SF-RECORDING-FEES": "why the recording fee is zero on a Property B sale",
        "SF-OMI": "the owner-move-in conditions and the protected-tenant bars",
        "SF-NEWCON": "which units are exempt from rent caps and still subject to just cause",
        "SF-RELO": "the relocation amounts used in any possession scenario",
        "SFPUC-RATES": "the water, wastewater and stormwater charges behind Property B's utility line",
        "SF-PROP-H": "the parcel tax text, including the pass-through cap",
        "SF-PROP-H-MTC": "the certified result and the first billing year",
        "SCVWD-MEASURES": "the district parcel fee that likely explains the implied-rate gap",
        "DAMO": "every return series, episode and rolling statistic on the risk pages",
        "UST-DAILY": "the short-rate environment the parking lane is priced on",
        "CDTFA-RATES": "the sales tax that raises the cost of every repair in the capital plan",
    }
    return notes.get(key, "")


# ------------------------------------------------------------- watch list ----
def watch(ctx):
    body = []
    body.append('<p class="lede">Rules are dated. This list separates what has been enacted from what '
                "has merely been proposed, and gives each item the authority that has to be re-read and the "
                "date it should be re-read. Nothing in the model uses a proposal; nothing uses an "
                "unverified figure without saying so on the face of the page.</p>")
    rows = []
    for L in R.LAWS:
        rows.append([L["id"], f"<b>{e(L['rule'])}</b>", e(L["jurisdiction"]), L["system"],
                     status_pill(L["status"]), e(L["detail"]),
                     e(L["effective"] or ""), e(L["expires"] or "none stated"),
                     L["next_check"], e(L["watch"]), srclink(L["src"])])
    body.append(simple_table([("Ref", "l"), ("Rule", "l"), ("Who sets it", "l"), ("System", "l"),
                              ("Status", "l"), ("What it says", "l"), ("Effective", "l"), ("Expires", "l"),
                              ("Re-read by", "l"), ("Watch for", "l"), ("Source", "src")], rows))
    body.append("<h2>Where to look, by authority</h2>")
    auth = [
        ("Federal - estate tax, basis, gains, depreciation", "irs.gov",
         "Forms and instructions for 706, 4768, 544, 946, 523, plus Topic 409. Check each January for the "
         "indexed amounts, and after any major reconciliation bill."),
        ("California - income tax on the gain", "ftb.ca.gov",
         "The Form 540 booklet and instructions, in particular the line carrying the 1% tax on taxable "
         "income above $1,000,000. That threshold was not indexed in the booklet read here - verify each "
         "January."),
        ("California - property tax, Prop 13 and Prop 19", "boe.ca.gov",
         "Letters to Assessors (the indexed Prop 19 amount is published this way, every other February 16), "
         "Publication 801, and the BOE-19-P instructions."),
        ("Santa Clara County - the actual rate on this parcel", "controller.santaclaracounty.gov",
         "The annual Compilation of Tax Rates, by tax rate area. It is the only document that settles the "
         "implied-rate anomaly, and it is published every autumn."),
        ("San Francisco - transfer tax, secured rate, parcel taxes", "sftreasurer.org, sfasr.org, sf.gov",
         "The secured rate each July or August; the Assessor-Recorder's transfer-tax page for the tiers; the "
         "Rent Board for owner-move-in rules and the Form 579 amounts each March 1."),
        ("State statutes", "leginfo.legislature.ca.gov",
         "Revenue & Taxation Code 61, 63.2, 11911 and 11930, and Civil Code 1947.12. Read the section, not "
         "a summary of it, and note the chapter's effective-date line."),
        ("Ballot measures", "county registrar results, then the measure text",
         "Proposition H and RTM were read from the body reporting the certified results; re-read after the "
         "2026-12-03 certification and again when the first bills issue."),
    ]
    body.append(simple_table([("What", "l"), ("Where", "l"), ("How to use it", "l")],
                             [[a, f"<b>{b}</b>", c] for a, b, c in auth], short=True))
    body.append("<h2>Proposed, not enacted - deliberately modelled as nothing</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "Any change to the federal step-up in basis. Repeatedly proposed, never enacted. If it ever passes "
        "with a grandfather date, the value of selling at the death jumps - so it is worth one look each "
        "January.",
        "Any measure to restore the full Prop 13 parent-child transfer without the value cap or the "
        "occupancy condition. It would make the live paths and the rent paths nearly identical; it has "
        "failed at the ballot more than once.",
        "Any San Francisco measure to widen the transfer-tax exemptions or to add a tier. It changes the net "
        "proceeds of a Property B sale by tens of thousands.",
        "Any change to the statewide rent cap or its stated expiry around 2030. It is the difference between "
        "'rent grows with the market' and 'rent grows with the cap' in the rent paths.",
    ]) + "</ul>" + note("No bill numbers are quoted, because no bill was verified in this pass. A list of "
                        "bill numbers copied from a search result would look like research and be a "
                        "guess wearing a citation; the honest entry is 'watch these four things, and here is "
                        "the authority that would tell us'.")
    )
    return page("watch", "Legislation and rate watch list", "".join(body))


# ------------------------------------------------------------- recheck ----
def recheck(ctx):
    body = []
    body.append('<p class="lede">The transfer is years away, so the only thing that has to be true every '
                "year is that these numbers still describe the world. This is the checklist, plus the "
                "extreme-scenario re-run that keeps the model honest.</p>")
    rows = []
    for it in R.RECHECK:
        key = e(it["what"][:24])
        rows.append(['<input type="checkbox" class="ck" data-k="' + key + '">', e(it["what"]),
                     e(it["where"]), e(it["why"]), f"<b>{e(it['cadence'])}</b>", e(it["affects"]),
                     srclink(it.get("src"))])
    body.append(simple_table([("&#9744;", "l"), ("Re-read", "l"), ("Where", "l"), ("Why", "l"),
                              ("Every", "l"), ("What it moves", "l"), ("Source", "src")], rows))
    body.append("<h2>The annual re-run</h2>")
    body.append("<ol class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "Replace the previous calendar year's equity and bill returns in model/history.py with the published "
        "table, and note the date that table was updated. The Black-Swan and phased pages are computed from "
        "it, so a stale file silently becomes a stale conclusion.",
        "Re-read the assumption ranges in model/inputs.py against the current year: inflation, short rates, "
        "insurance, and the two house values. Change the ranges, not the point estimates - there are no "
        "point estimates.",
        "Run python3 model/build.py && python3 model/site.py and read the diff of the generated tables. A "
        "ranking that has not moved at all in twelve months is usually a sign the inputs were not touched, "
        "not that the world was stable.",
        "Re-run the two extreme scenarios specifically: entering the market in a crash year, and inflation "
        "running above the 2% assessment cap. If either changes the recommendation, write that on the "
        "decision-rules page - it is exactly the kind of fact the household agreed to collect.",
        "Move the status column on the watch page only with an effective date attached: 'proposed' does not "
        "become 'enacted' because a measure is popular.",
        "Update the decision log with one line, even if the line is 'no change, and here is why not'.",
    ]) + "</ol>")
    body.append("<h2>Sign-off</h2>")
    body.append('<div class="card"><table class="signoff"><tr><th>Reviewed by</th><th>Date</th>'
                "<th>What changed</th></tr>"
                + "".join("<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>" for _ in range(5)) +
                "</table></div>" + note("Print this section each December. A recheck with no record is a "
                                        "recheck that did not happen."))
    return page("recheck", "Annual recheck", "".join(body))


# --------------------------------------------------------- open questions ----
def open_questions(ctx):
    kinds = {"legal": "for counsel", "fact": "a number or document to obtain",
             "family": "for the household"}
    openn = [q for q in QUESTIONS if q["status"] == "OPEN"]
    body = []
    body.append(f'<p class="lede">These are the reasons the ranking elsewhere on this site is provisional. '
                f"{len(openn)} of {len(QUESTIONS)} are unresolved. Each states the question, what it changes "
                "in the model, where the answer physically comes from, and - where we tried and failed - "
                "what was already searched. None of it needs a subscription; most of it needs a phone call, "
                "a records request, or a conversation.</p>")
    body.append('<div class="grid">')
    for k, lab in [("fact", "Documents to obtain"), ("legal", "Questions for counsel"),
                   ("family", "Decisions only the household can make")]:
        n = len([q for q in QUESTIONS if q["kind"] == k])
        body.append(f'<div class="stat"><div class="l">{lab}</div><div class="v">{n}</div>'
                    f'<div class="n">{kinds[k]}</div></div>')
    body.append('<div class="stat"><div class="l">Rough cost to close them all</div><div class="v">'
                f"{m(3500)} to {m(9000)}</div><div class=\"n\">appraisal, inspection, three insurance "
                "quotes, a rent-counsel consultation, an hour of CPA time - deliberately approximate</div></div>")
    body.append("</div>")
    for k in ("fact", "legal", "family"):
        body.append(f"<h2>{kinds[k].capitalize()}</h2>")
        rows = []
        for q in [x for x in QUESTIONS if x["kind"] == k]:
            rows.append([f"<b>{q['id']}</b>", e(q["topic"]), e(q["q"]), e(q["why"]), e(q["where"]),
                         srclink(q["src"])])
        body.append(simple_table([("Ref", "l"), ("Topic", "l"), ("Question", "l"),
                                  ("Why it changes the answer", "l"), ("How to find out", "l"),
                                  ("Source / lead", "src")], rows))
    body.append("<h2>What we searched and did not find</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "The city's water and sewer rate schedule. Every attempt returned a different city's "
        "rates. Left blank rather than borrowed - see F-5.",
        "An official edition of San Francisco Form 579 covering notices served after 2025-02-28. The latest "
        "table found is the 2024-25 one; its amounts are used and flagged as possibly superseded (F-4).",
        "A Santa Clara County tax rate book for FY 2026-27. Only FY 2025-26 exists, so every rate on this "
        "site carries that label rather than a newer one.",
        "The text of R&amp;T Code 11930, the gift and death exemption from documentary transfer tax. The "
        "county materials cite it; the section itself was not read (F-10).",
        "Any authority for a small-landlord exemption from eviction limits in San Francisco. The material "
        "found describes Los Angeles, so it is not assumed here.",
        "The specific tax rate area for Property A. The county publishes 816 of them and the parcel-level "
        "lookup needs the assessor record, which is deliberately not stored in this repository (Q-04).",
    ]) + "</ul>")
    return page("open-questions", "Open questions and missing information", "".join(body))


# ------------------------------------------------------------ suggestions ----
def suggestions(ctx):
    body = []
    body.append('<p class="lede">A review board, not a to-do list. Each proposal says what it costs to '
                "skip. Pick the lane at the bottom before any of it is implemented - the lanes are different "
                "amounts of work with different amounts of confidence, and that choice belongs to the "
                "household, not to the model.</p>")
    rows = []
    for s in SUGGESTIONS:
        rows.append([f"<b>{s['id']}</b>", f"<b>{e(s['title'])}</b>", e(s["body"]),
                     pill(e(s["effort"]), "info"),
                     pill(e(s["impact"]), "ok" if s["impact"] == "high" else ""),
                     e(s["risk_if_skipped"]),
                     pill(e(s["status"]), "ok" if s["status"] == "done" else "warn")])
    body.append(simple_table([("Ref", "l"), ("Proposal", "l"), ("What it means", "l"), ("Effort", "l"),
                              ("Impact", "l"), ("If skipped", "l"), ("Status", "l")], rows))
    body.append("<h2>Your decision on each</h2>")
    body.append('<div class="card noprint"><div class="check">'
                + "".join(f'<label><input type="checkbox" class="sg" data-k="{s["id"]}"> '
                          f'<span><b>{s["id"]}</b> {e(s["title"])} <span class="tag">tick to mark adopted in '
                          f'this browser; nothing is sent anywhere</span></span></label>'
                          for s in SUGGESTIONS)
                + "</div><p class='small'>Choices are kept in local storage because this site has no server "
                  "and should not have one. To make them official, write them into the decision log on the "
                  "decision-rules page.</p></div>")
    body.append("<h2>Choose the implementation lane</h2>")
    lanes = [
        ("Lane 1 - evidence first",
         "Close Q-02, Q-03, Q-04 and Q-12 (appraisal, comparables, tax rate area, insurance quotes), then "
         "re-run. Change no tax rule and no method.",
         "Two weekends and a few hundred dollars. It settles the two highest-severity flags.",
         "The model stays as it is; the numbers under it become real."),
        ("Lane 2 - legal first",
         "Take the briefing sheet to an estate attorney and a CPA before anything else, and answer Q-01, "
         "Q-08, Q-11 and Q-20 (occupancy and the claim window, trust mechanics, California estate tax, liens "
         "and claims). Assume nothing about whether the exclusion is even available.",
         "Two paid consultations. It is the only lane that can surface a hard stop, which is the one thing no "
         "projection can price.",
         "The ranking may become irrelevant - in a good way - if a hard stop exists."),
        ("Lane 3 - decide the shape now",
         "Answer Q-07 and Q-15 (where the household wants to live, and what would make them choose each "
         "path), commit to the criteria, and preserve the option: occupy and file on the transfer, defer the "
         "sale decision by two or three years.",
         "Nothing but a conversation and one dated signature. It also keeps every other door open.",
         "The model then checks a decision already made, which is what a framework is for."),
        ("Lane 4 - refine the model",
         "Add what this workspace does not yet carry: a mortgage or line of credit, a co-owner split, a "
         "Medi-Cal claim, the tax character of the cash, a replacement-property purchase and 1031 mechanics.",
         "Cheapest in money, dearest in time, and it makes the model prettier without making the decision "
         "less uncertain.",
         "Only worth doing after the open questions are answered; otherwise it is decoration."),
    ]
    body.append(simple_table([("Lane", "l"), ("What it is", "l"), ("Cost", "l"), ("Consequence", "l")],
                             [[f"<b>{a}</b>", e(b), e(c), e(dd)] for a, b, c, dd in lanes], short=True))
    body.append('<p class="small">The lanes are not exclusive. The order is the decision, and the honest '
                "recommendation from a model that keeps finding its own inputs missing is: <b>Lane 2, then "
                "Lane 1, then Lane 3</b> - and treat Lane 4 as optional forever.</p>")
    return page("suggestions", "Method suggestions - review board", "".join(body))


# ---------------------------------------------------------------- flagged ----
def flagged(ctx):
    body = []
    body.append('<p class="lede">Non-blocking. Nothing here prevents a decision; each item is a place where '
                "the evidence is thinner than the number looks, or where two sources disagree. They are "
                "listed with what was done about it and what would close it, because the failure mode of this "
                "kind of workspace is a figure quietly graduating from assumption to fact.</p>")
    counts = {}
    for f in FLAGS:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    body.append('<div class="grid">' + "".join(
        f'<div class="stat"><div class="l">{k}</div><div class="v">{v}</div><div class="n">'
        + {"high": "could change the decision if resolved badly",
           "medium": "changes a number, not the answer",
           "low": "changes the confidence, not the number"}[k] + "</div></div>"
        for k, v in sorted(counts.items())) + "</div>")
    rows = []
    for f in FLAGS:
        rows.append([f"<b>{f['id']}</b>", f"<b>{e(f['item'])}</b>",
                     pill(e(f["severity"]), {"high": "bad", "medium": "warn", "low": ""}[f["severity"]]),
                     e(f["detail"]), e(f["action"]),
                     " ".join(srclink(s) for s in f.get("srcs", [])) or srclink(None)])
    body.append(simple_table([("Ref", "l"), ("Item", "l"), ("Severity", "l"), ("What it is", "l"),
                              ("How to close it", "l"), ("Source", "src")], rows))
    body.append("<h2>Deliberately left out</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li><b>{e(a)}</b> - {e(b)}</li>" for a, b in [
        ("A mortgage or line of credit", "none was reported on either building; if one exists, tell the "
         "model, and the ranking will move toward liquidity."),
        ("Rent benchmarked to voucher schedules", "it would have produced a number, and a number that is not "
         "what a market tenant pays is worse than a blank cell."),
        ("A small-landlord exemption from eviction limits", "no authority for it in San Francisco was found; "
         "the material describing it is about a different city."),
        ("Estate-tax planning beyond whether a return is due", "the gross estate is unknown until the cash is "
         "characterised; planning on top of an unknown is fortune-telling."),
        ("A state inheritance tax", "California is assumed to have none, and that assumption is flagged (F-6) "
         "rather than modelled as fact."),
        ("Names, addresses, parcel numbers and account numbers", "they belong in the offline folder. This "
         "site is built so that it can be public without being legible about anyone."),
    ]) + "</ul>")
    return page("flagged", "Flagged for review", "".join(body))


# ------------------------------------------------------------ comparables ----
def comparables(ctx):
    rd = ctx["rent_diag"]
    body = []
    body.append('<p class="lede">Several of the twelve paths rank on a rent figure that came from the '
                "household rather than from the market. This page is the protocol for fixing that: what to "
                "collect, where it comes from, and the arithmetic it feeds. The table below is empty on "
                "purpose - the cells are blank because the evidence has not been gathered, and an "
                "illustrative comp would be read as a finding.</p>")
    need = [
        ("Closed sales of comparable single-family houses near Property A", "4, last 6 months",
         "County assessor-recorder sale data is public and carries price and date; an agent's comp sheet is "
         "faster and adds square footage and condition.",
         "Adjust for the three things that move prices here: school attendance boundary, alley or no alley, "
         "and whether the house was remodelled."),
        ("Houses listed and not sold", "3-5, same period",
         "Expired listings, from the MLS.",
         "They are the only evidence of the price buyers actually declined to pay."),
        ("Signed leases for comparable houses", "4, last 12 months",
         "A leasing agent or property manager with local inventory. Some cities publish rent registrations; "
         "this county does not.",
         "Asking rents are advertising. Signed lease rents are data."),
        ("Two written management fee quotes", "2",
         "Local single-family managers.",
         "They price vacancy, turn cost and maintenance coordination - the three lines that decide whether "
         "the rent path is real."),
        ("A retrospective appraisal at the date of death", "1",
         "A licensed appraiser, engaged when the date is known.",
         "One document serves the estate return, the income-tax basis and the Prop 19 calculation."),
    ]
    body.append("<h2>What has to be collected</h2>")
    body.append(simple_table([("What", "l"), ("How many", "r"), ("Where it comes from", "l"),
                              ("Why it is the right evidence", "l")],
                             [[f"<b>{e(a)}</b>", e(b), e(c), e(d)] for a, b, c, d in need], short=True))
    body.append("<h2>The sheet to fill in</h2>")
    hdr = [("Comp", "l"), ("Date", "l"), ("Sale / lease / expired", "l"), ("Beds / baths", "l"),
           ("Sq ft", "r"), ("Price or rent", "r"), ("Per sq ft", "r"), ("Remodelled?", "l"),
           ("Distance and boundary", "l"), ("Adjusted", "r")]
    rows = [[f"{kind}{i + 1}", '<span class="na">to be collected</span>',
             '<span class="na">to be collected</span>', '<span class="na">to be collected</span>',
             "", "", "", "", "", ""]
            for kind, n in (("Sale", 4), ("Lease", 4), ("Expired", 3)) for i in range(n)]
    body.append(simple_table(hdr, rows, caption="Keep this sheet offline with the addresses on it. Only the "
                                                "adjusted conclusion belongs on the published pages.",
                             short=True))
    body.append("<h2>What the evidence has to settle</h2>")
    body.append(simple_table([("Question", "l"), ("Current input", "r"),
                              ("Threshold that changes the ranking", "l"), ("Where it feeds", "l")],
        [["Gross rent on Property A", m(rd["rent_month"]) + " a month (owner estimate)",
          f"{m(rd['break_even_month'])} just covers the carrying cost; {m(rd['need_rent_month'])} matches a "
          "safe Treasury yield on the same money", "P-03, P-08, P-10, P-11 and the imputed-rent column"],
         ["Gross yield on the house", f"{rd['gross_yield']:.1f}%",
          f"needs roughly {rd['safe_yield']:.1f}% after tax before it beats sitting in bills at all",
          "the whole rent family"],
         ["Property tax on a reassessed A", m(rd["tax"]) + " a year",
          "the actual composite rate for this parcel's tax rate area - Q-04 and F-2", "every keep path"],
         ["Vacancy and turn loss", "5% assumed", "two of the four managers quoted will price it", "rent paths"],
         ["Upkeep at a market rent", m(rd["maintenance"]) + " a year",
          "the inspection findings, not the percentage", "all paths"]], short=True))
    body.append(note("The comparison is made against the after-tax yield on the sale proceeds, not against "
                     "'what a house might do someday'. A rental that cannot beat bills plus a risk premium "
                     "is not an investment, it is an occupation with paperwork - which may be exactly what "
                     "the household wants, and is a perfectly good reason to choose a path. It is not a "
                     "reason to call the path profitable."))
    return page("comparables", "Comparables protocol - the missing evidence", "".join(body))


# ---------------------------------------------------------------- sources ----
def sources(ctx):
    body = []
    body.append('<p class="lede">Every figure on this site traces to a row here. The status means what it '
                "says: <b>official</b> - the document was opened and the figure read from it during this "
                "session; <b>ballot text</b> - the measure as published for voters; <b>academic</b> - a "
                "published research dataset rather than a government record; <b>owner</b> - supplied by the "
                "household and not checked; and anything with no source at all is blank on the pages rather "
                "than listed here. Verified " + ASOF + ".</p>")
    rows = []
    for key, (title, url, status) in SOURCES.items():
        rows.append([f"<b>{key}</b>", e(title),
                     f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">'
                     f"{e(url[:78])}{'&hellip;' if len(url) > 78 else ''}</a>",
                     status_pill(status), e(srclink_note(key))])
    body.append(simple_table([("Key", "l"), ("Document", "l"), ("Link", "l"), ("Status", "l"),
                              ("Used for", "l")], rows))
    body.append("<h2>Verification log</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "Opened the county's FY 2025-26 compilation of tax rates and read the 1.00000% maximum levy, the "
        "CPI-or-2% factoring rule, the installment and delinquency dates, the 10% penalty plus 1.5% monthly "
        "redemption penalty, and the school-district and community-college-district bond lines that could "
        "make up the composite rate for this parcel.",
        "Opened the State Board of Equalization's Prop 19 pages and the letter to assessors carrying the "
        "indexed amount, and read the allowance across all three published windows.",
        "Read R&amp;T Code 11911 in full from the Legislature's site, and R&amp;T Code 61.",
        "Read the IRS estate-tax threshold table, Topic 409 for the rates and the recapture cap, and the "
        "publication pages for 523, 544, 946 and 559.",
        "Read the FTB capital-gains page and the 2024 Form 540 booklet, where the 1% surtax line is printed "
        "as a number; the 2025 instructions were opened for the gains treatment.",
        "Read San Francisco's FY 2026-27 secured rate, the Assessor-Recorder's transfer-tax tiers and "
        "exemptions, the Administrative Code section capping the owner-occupier rate, the Rent Board's "
        "owner-move-in rules and Form 579 amounts, and the utility district's FY 2026-27 schedule.",
        "Read the county clerk-recorder's fee schedule, including the offset that applies when transfer tax "
        "is due.",
        "Read the reporting of the certified November 2026 ballot results for the San Francisco parcel tax, "
        "including the pass-through limits in the measure text.",
        "Read the full annual equity and bill series from the academic dataset and recomputed every statistic "
        "on the risk pages from those rows, rather than quoting a summary of them.",
        "Tried and did not obtain: the county's FY 2026-27 rate book (not yet published), an official CPI "
        "series, the 2025-26 Form 579 edition, municipal utility rates, and the text of R&amp;T Code 11930. "
        "Those appear as blanks and flags, not as numbers.",
    ]) + "</ul>")
    body.append(note("No page on this site was populated from a search-result summary. Where a summary was "
                     "the only thing available, the figure was left blank and the gap written up instead."))
    return page("sources", "Source register and verification log", "".join(body))


# ------------------------------------------------------------- framework ----
def framework(ctx):
    c = R.CRITERIA
    body = []
    body.append("<p class='lede'>These criteria were written before the projections were argued about, and "
                "they exist so that the projection cannot be reverse-engineered into a justification. If a "
                "number moves and the thresholds still hold, the answer has not changed. If the number moves "
                "and the answer does, the honest conclusion is that the decision was never inside the "
                "projection.</p>")
    body.append(f'<div class="card"><b>Why this page exists</b><p class="small">{e(c["purpose"])}</p></div>')
    for key, title in [("live", "Choose 'live in Property A' when"),
                       ("rent", "Choose 'keep it as a rental' when"),
                       ("sell", "Choose 'sell' when"),
                       ("mixed", "Choose a mixed path when")]:
        body.append(f"<h2>{title}</h2><ol class='tight'>" +
                    "".join(f"<li>{e(x)}</li>" for x in c[key]) + "</ol>")
    body.append("<h2>Hard stops - not trade-offs</h2><ul class='tight'>" +
                "".join(f"<li>{e(x)}</li>" for x in c["hard_stops"]) + "</ul>")
    body.append(f'<div class="card accent"><b>Tie-break, agreed in advance:</b> {e(c["tie_break"])}</div>')
    body.append("<h2>How the ranking is computed</h2>")
    body.append("<pre>score = 100 &times; ( 0.50 &times; normalised median real terminal wealth\n"
                "          + 0.25 &times; normalised 10th percentile\n"
                "          + 0.15 &times; (1 - relative spread of outcomes)\n"
                "          + 0.10 &times; liquidity / no-forced-sale flag )</pre>")
    body.append(simple_table([("Weight", "r"), ("Why it is there", "l"), ("Where it comes from", "l")],
        [["50%", "the thing everyone argues about: what you end up with",
          "median of 1,200 block-bootstrap paths, in 2026 dollars, after tax on everything"],
         ["25%", "the household's own tolerance for the bad version of that",
          "the 10th percentile of the same paths"],
         ["15%", "how much the answer depends on which decade you happen to get",
          "the p10-p90 width, relative to its own size"],
         ["10%", "whether the path can be lived without selling something in a bad year",
          "the worst annual cash flow the path produces, against the liquidity floor"]], short=True))
    body.append(note("Wealth and utility are reported side by side and never added together silently. "
                     "Turning on the imputed-rent column changes some of the ranking, which is the point: it "
                     "is a value judgement the household owns, not a result the model claims. The scoring "
                     "weights themselves are a judgement too, and they are stated so that they can be argued "
                     "with."))
    body.append("<h2>Decision log</h2>")
    body.append(simple_table([("Date", "l"), ("Decision", "l"), ("Reasoning", "l"), ("Status", "l"),
                              ("Owner", "l")],
                             [[d["date"], f"<b>{e(d['decision'])}</b>", e(d["rationale"]),
                               pill(e(d["status"]), "ok" if d["status"] == "adopted" else "warn"),
                               e(d["owner"])] for d in R.DECISION_LOG]))
    body.append("<h2>How to add to it</h2>")
    body.append("<p class='small'>One line per decision, in <code>model/registers.py</code> under "
                "<code>DECISION_LOG</code>: date, what was decided, why, status, who owns it. A decision "
                "that reverses an earlier one keeps both lines, so the record shows the reversal instead of "
                "quietly replacing it. The alternative - a spreadsheet in which only the current answer "
                "survives - is how households argue with themselves three times about the same house.</p>")
    return page("framework", "Decision rules agreed in advance", "".join(body))


# ------------------------------------------------------------- briefing ----
def briefing(ctx):
    p19, rd = ctx["prop19"], ctx["rent_diag"]
    sales = ctx["sales"]
    body = []
    body.append('<div class="print"><p class="small">One page. Figures are rounded to the nearest $10 by '
                "design: if you need an exact number, ask the client for the offline folder rather than "
                "trying to reconstruct it from this sheet.</p></div>")
    body.append('<div class="card"><div class="kicker">Attorney &amp; CPA briefing sheet - ' + ASOF + "</div>")
    body.append("<h2>Situation</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "The client owns Property B outright: a three-unit building in San Francisco - one unit vacant "
        "and livable, two units let. The client can occupy the vacant unit without displacing a tenant.",
        "The client is a beneficiary of a trust holding Property A: a single-family house in Santa Clara "
        "County with solar, expected to pass at the settlor's death, provisionally 2040-2050 "
        "(modelled at 2045).",
        "The inheritance is expected to include a considerable amount of cash, possibly above the federal "
        "exclusion. The character of that cash - taxable brokerage, retirement accounts, insurance - is "
        "unknown and changes the plan more than the house does.",
        "No mortgage was reported on either building. No co-beneficiary has been identified, which is itself "
        "an open question.",
        "The decision sought: live in Property A, rent it, sell it, or sequence those.",
    ]) + "</ul>")
    body.append("<h2>Figures</h2>")
    g10 = [s for s in sales if s["label"].startswith("Rent 10")][0]
    body.append(simple_table([("Item", "l"), ("Figure", "r"), ("Status", "l")],
        [["Property A market value (2026)", m(PROPERTY_A["value_2026"]), "owner estimate; appraisal needed"],
         ["Property A assessed value (2026)", m(PROPERTY_A["assessed_2026"]), "county record, rounded"],
         ["Property A property tax (2025)", m(HISTORY_A[1][1]), "county bill, rounded"],
         ["Property A tax if reassessed in full (2045)", m(p19["tax_full"]), "model, at the implied rate"],
         ["Property A tax with the Prop 19 exclusion (2045)", m(p19["tax_excluded"]), "model, BOE formula"],
         ["Prop 19 indexed allowance, current window", m(RULES["prop19_indexed_amount"]), "BOE notice"],
         ["Property B market value (2026)", m(PROPERTY_B["value_2026"]), "owner estimate"],
         ["Property B assessed / tax (2025)",
          m(PROPERTY_B["assessed_2025"]) + " / " + m(PROPERTY_B["tax_2025"]),
          "county record, rounded; does not reconcile to the published rate"],
         ["Property B rent roll", m(PROPERTY_B["rent_roll_mo"]) + " a month (2 units)", "owner"],
         ["Property B new parcel tax, from FY 2027-28",
          m(RULES["sf_prop_h_multifamily_base"]) + " + $0.195/sq ft over 5,000", "voter-approved, pending certification"],
         ["Estimated market rent for A", m(rd["rent_month"]) + " a month", "unverified - no comparables yet"],
         ["Rent needed merely to cover carrying cost", m(rd["break_even_month"]) + " a month", "model"],
         ["Rent needed to beat after-tax Treasury yield", m(rd["need_rent_month"]) + " a month", "model"],
         ["Friction to sell A", m(ctx["transfer"]["A"]["total"]) + " ("
          + str(ctx["transfer"]["A"]["pct_of_price"]) + "% of price)", "model, at published transfer tax and fees"],
         ["Friction to sell B", m(ctx["transfer"]["B"]["total"]) + " ("
          + str(ctx["transfer"]["B"]["pct_of_price"]) + "% of price)", "model, SF tier table"],
         ["Tax on a sale after 10 years of renting A",
          m(g10["total_tax"]) + f" on a {m(g10['price'])} sale ({pc(g10['effective_rate']/100,1)} of gain)",
          "model; California has no preferential rate on gains"],
         ["Federal estate-tax filing threshold, 2026 death", m(RULES["fed_bea_2026"]), "IRS published table"],
    ], short=True))
    body.append("<h2>Questions for counsel</h2>")
    body.append("<ol class='tight'>" + "".join(
        f"<li><b>{q['id']}</b> {e(q['q'])}</li>" for q in QUESTIONS if q["kind"] == "legal") + "</ol>")
    body.append("<h2>Questions for the CPA</h2>")
    body.append("<ol class='tight'>" + "".join(
        f"<li>{e(x)}</li>" for x in [
            "Confirm in writing that California imposes no estate or inheritance tax on this transfer, with "
            "the authority relied on.",
            "Confirm the passive-activity position: are rental losses deductible against salary, suspended, "
            "or is a real-estate-professional election in play?",
            "Confirm the treatment of the 1% mental/behavioral health surtax on a large gain in a sale year, "
            "and whether the $1,000,000 threshold is indexed in the return year.",
            "Advise on section 121 where the heir occupies for about three years and then rents: the "
            "non-qualified-use proration is the one rule here that is genuinely arguable.",
            "Confirm that the trust distribution itself triggers no documentary transfer tax, and get the "
            "exemption cited rather than assumed.",
            "Produce a land/building allocation, ideally a cost-segregation study, so depreciation and "
            "recapture are not 75% of a guess.",
            "Say, before any listing, whether a 1031 exchange is worth structuring - it must be set up "
            "before closing and cannot be elected on the return.",
            "Tell us the character of the inherited cash, because an inherited retirement account has no "
            "step-up and pays ordinary income tax while a brokerage account has both.",
        ]) + "</ol>")
    body.append("<h2>What is already decided, and what is not</h2>")
    body.append("<p class='small'>The criteria for choosing each path are written down (decision-rules "
                "page). The client has agreed not to choose a path from a single projection, to treat "
                "occupancy as the controlling fact, and to re-run annually. Counsel's view on the trust "
                "mechanics, the claim window, and any Medi-Cal or lien exposure is needed before the "
                "sell-versus-hold question is argued at all.</p>")
    body.append('<table class="signoff"><tr><th>Reviewed by</th><th>Role</th><th>Date</th><th>Notes</th></tr>'
                "<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>"
                "<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr></table></div>")
    return page("briefing", "Attorney &amp; CPA briefing sheet", "".join(body),
                "One printable page for the two professionals whose answers the model is waiting on.")


# ---------------------------------------------------------------- glossary ----
def glossary(ctx):
    body = []
    body.append('<p class="lede">The vocabulary on this site is deliberately narrow: if a word appears in a '
                "table, it appears here. Terms are grouped by which of the three tax systems they belong to, "
                "because most confusion in this decision comes from using one system's vocabulary in "
                "another's argument.</p>")
    PENDING = ("definition pending - this term is used on the flagged and sources pages, and will "
               "be defined here when its definition is settled")
    groups = {
        "Property tax (the assessment)": ["Factored base year value (FBYV)", "Ad valorem",
                                          "Non-ad-valorem / direct assessment", "Tax Rate Area (TRA)",
                                          "Change in ownership", "Supplemental bill",
                                          "Homeowners' exemption", "Escrow holdback / concessions"],
        "Income tax (the gain)": ["Adjusted basis", "Recapture (unrecaptured 1250)", "Depreciation",
                                  "Section 121 exclusion", "Suspended loss", "NIIT", "Mid-month convention"],
        "Estate / transfer (the death)": ["Basic exclusion amount", "DSUE / portability",
                                          "Alternate valuation date", "Documentary transfer tax"],
        "Renting and tenancy": ["Owner move-in (OMI)", "Just cause", "Rent cap", "Vacancy / turn allowance"],
        "Money and method": ["Real vs nominal", "Present value", "Sequence-of-returns risk",
                             "Block bootstrap", "Imputed rent", "Use value", "Opportunity cost",
                             "Liquidity floor", "Treasury parking lane"],
    }
    look = dict(R.GLOSSARY)
    for g, terms in groups.items():
        body.append("<h2>" + g + "</h2>")
        items = []
        for i, t in enumerate(terms):
            d = e(look.get(t, PENDING))
            items.append('<dt id="g-' + g[:3] + str(i) + '">' + e(t) + "</dt><dd>" + d + "</dd>")
        body.append('<dl class="gloss">' + "".join(items) + "</dl>")
    extra = [t for t in look if not any(t in v for v in groups.values())]
    if extra:
        body.append("<h2>Also used</h2><dl class='gloss'>" + "".join(
            f"<dt>{e(t)}</dt><dd>{e(look[t])}</dd>" for t in sorted(extra)) + "</dl>")
    body.append("<h2>Index of pages</h2>")
    body.append('<div class="grid">' + "".join(
        f'<a class="card" href="{pid}.html"><b>{lab}</b><p class="small">{d}</p></a>'
        for pid, lab, d in [
            ("index", "Overview", "what would change the answer, and where things stand"),
            ("paths", "Paths", "twelve ways of handling Property A, compared on one date and three horizons"),
            ("what-if", "What if", "six dials over 162 pre-computed scenarios"),
            ("projections", "Projections", "year-by-year value, assessment, tax and carrying cost"),
            ("tax-rules", "Tax rules", "the three systems, each rule with its status and source"),
            ("costs", "Costs & capital", "the five-year plan, utilities, insurance, transfer friction"),
            ("black-swan", "Black swans", "what the record says about regimes and sequences"),
            ("phased", "Phased investing", "the parking lane, tested against the crash years"),
            ("process", "Process & deadlines", "the trust route, step by step, with the dates that bind"),
            ("framework", "Decision rules", "the thresholds agreed in advance, and the decision log"),
            ("open-questions", "Open questions", "what is missing, and how to go and get it"),
            ("suggestions", "Suggestions", "the method board and the four implementation lanes"),
            ("flagged", "Flagged", "where the evidence is thinner than the number looks"),
            ("comparables", "Comparables", "the evidence the rent paths are waiting on"),
            ("sources", "Sources", "every document, with status, and the verification log"),
            ("watch", "Law watch", "enacted versus proposed, with re-read dates"),
            ("recheck", "Annual recheck", "the December checklist and sign-off"),
            ("briefing", "Briefing sheet", "the one page for counsel and the CPA"),
            ("glossary", "Glossary", "this page"),
            ("model", "How it works", "the engine, its conventions and its limits"),
        ]) + "</div>")
    return page("glossary", "Glossary and page index", "".join(body))


# ----------------------------------------------------------------- model ----
def model(ctx):
    body = []
    body.append('<p class="lede">The model is a small, boring Python program. This page is its honest '
                "documentation: what it computes, the conventions it uses, the things it refuses to guess, "
                "and how to make it say something new.</p>")
    body.append("<h2>Files</h2>")
    body.append(simple_table([("File", "l"), ("What it holds", "l")],
        [[f"<code>model/{n}</code>", d] for n, d in [
            ("inputs.py", "every number on the site, each with its source key and verification status, plus "
                          "the question register, the suggestion board and the flag list"),
            ("history.py", "the annual equity and bill return series the risk pages are computed from"),
            ("engine.py", "the path definitions, the yearly simulation, the Monte Carlo, the phased backtest "
                          "and the sensitivity grid"),
            ("projections.py", "the assessment scenarios, carrying-cost projections, gain calculations, "
                               "transfer costs, the capital plan and the inheritance process"),
            ("registers.py", "the legal rules with their status, the deadline timeline, the pre-committed "
                             "criteria, the decision log, the recheck list and the glossary"),
            ("build.py", "runs the model, scrubs and rounds everything, and writes the JSON data"),
            ("site.py", "renders the pages you are reading"),
        ]], short=True))
    body.append("<h2>Conventions, stated so they can be attacked</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "Paths are ranked on terminal household wealth assuming everything is sold at market and the tax on "
        "the unrealised gain is paid. It is a liquidation measure: it deliberately ignores that a house you "
        "live in is also something you consume, which is what the imputed-rent column is for.",
        "Cash flow that a path generates or consumes runs through a household account earning the bill rate "
        "- an opportunity-cost convention. Charging the live paths a consumer-loan spread for a shortfall "
        "they would fund from savings would have biased the answer toward selling.",
        "Rental losses are treated as suspended rather than deductible against salary, and depreciation "
        "shelters the rent until it does not. That is conservative for the rent paths and flagged as "
        "unconfirmed.",
        "Inflation enters the tax base only through the Prop 13 cap: whenever CPI runs above 2% the assessed "
        "value grows slower than prices, so a keep path looks better in real terms in a high-inflation world. "
        "That is the rule, not a modelling artefact - and it is the quietest strong argument for holding.",
        "Every dollar figure leaves the build through one rounding step and one text filter, so the published "
        "site cannot be traced back to a public record. Exact values exist only in the household's offline "
        "folder.",
        "Values with no official source are blank. The blank is the finding.",
        "Nothing is modelled on proposed legislation, and nothing is modelled on a figure from a search "
        "result that was not then read in the underlying document.",
    ]) + "</ul>")
    body.append("<h2>What it cannot do</h2>")
    body.append("<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in [
        "It cannot tell you the rent, because nobody has gathered the comparables yet. Two of the twelve "
        "paths are therefore provisional in a way the others are not.",
        "It cannot tell you the parcel's actual tax rate. Both the county's published composites and the "
        "household's own bills imply rates that do not reconcile, and the difference is the second largest "
        "line in the model.",
        "It cannot see the family. A co-owner, a wish, a dispute, or a Medi-Cal claim is outside every table "
        "here and inside the outcome.",
        "It cannot forecast 2045. The transfer year is a placeholder inside a ten-year window "
        "(2040-2050) and there is no dial for it here, because a dial would imply the date was a matter of "
        "taste rather than of fact. Narrowing that window is the estate attorney's job, not the model's.",
        "Its tails are as wide as the record is long: a 98-year sample of annual returns cannot tell you the "
        "probability of a decade that has not happened in it.",
    ]) + "</ul>")
    body.append("<h2>Reproducing it</h2>")
    body.append("<pre>cd model\n"
                "python3 build.py     # model -&gt; decision-workspace/data/*.json  (rounded + scrubbed)\n"
                "python3 site.py      # data -&gt; ../ *.html and assets/data.js\n"
                "python3 engine.py    # prints the run summary, no files written</pre>")
    body.append(note("The Monte Carlo is seeded (seed " + str(E.SEED) + ", " + str(E.N_SIMS) +
                     " simulations, three-year blocks), so the same inputs always produce the same tables. "
                     "The environment needs nothing but the standard library - no numpy, no pandas - which is "
                     "why the simulation is small enough to run at build time instead of in the browser."))
    body.append("<h2>Where the model is wrong on purpose</h2>")
    body.append(simple_table([("Choice", "l"), ("Why it was made", "l"), ("How to see its effect", "l")],
        [["No mortgage on either building", "none was reported; adding one would change every cash-flow line",
          "add the balance and rate to inputs.py and re-run"],
         ["Top marginal tax rate on all income", "the household is assumed to stay in the top brackets; the "
          "alternative is a rate dial nobody could pin down",
          "change MARG_ORD in engine.py; the rent paths are the sensitive ones"],
         ["75% building share for depreciation", "a placeholder in place of a cost-segregation study",
          "F-7; the recapture column scales with it"],
         ["2% growth in the Prop 19 allowance", "the indexing rule is official and biennial; the rate is our "
          "extrapolation", "the live paths' tax line moves about proportionally"],
         ["5% vacancy and turn loss on A", "an assumption, because no manager has quoted it yet",
          "the comparables page lists it as evidence to collect"],
         ["One shared transfer year", "so all twelve paths are comparable",
          "not adjustable in the browser - edit ECON['transfer_year'] and re-run"]], short=True))
    return page("model", "How the model works", "".join(body))
