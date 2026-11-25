"""
registers.py — the non-numeric registers: legal status of every rule used, the deadline
timeline, the pre-committed decision criteria, the annual recheck list, the decision log
and the glossary. Kept separate from inputs.py so a number change and a rule change never
arrive in the same edit.

STATUS VOCABULARY (used on /tax-rules.html and /watch.html)
  enacted-verified     text read in this session at the official source
  enacted-not-read     the rule is real and cited, but the statute text was not read this session
  pending-certification passed by voters, not yet certified / not yet operative
  proposed             a legislative idea, NOT law; must never enter the model
  unverified           could not be confirmed; the model treats it as unknown (see flagged page)
"""

ASOF = "2026-11-25"

# system: "estate" (transfer at death) | "income" | "property" | "local" | "tenant"
LAWS = [
    dict(id="L-01", system="estate", jurisdiction="Federal",
         rule="Unified estate/gift tax; basic exclusion amount",
         status="enacted-verified",
         detail="Filing threshold by year of death, as published: 2024 $13,610,000; "
                "2025 $13,990,000; 2026 $15,000,000. Top rate 40% above the threshold. "
                "Portability of the unused exclusion (DSUE) requires a timely Form 706.",
         effective="calendar-year indexed", expires=None,
         src="IRS-ESTATE", next_check="2027-01-15",
         watch="Any bill changing the exclusion or the 40% rate. No pending measure was "
               "verified in this session - do not model one."),
    dict(id="L-02", system="estate", jurisdiction="California",
         rule="California estate tax / inheritance tax",
         status="unverified",
         detail="This model assumes California imposes NO estate or inheritance tax. That is the "
                "conventional position and it matches the FTB materials reviewed, but no official "
                "source was read that states it in terms. Flagged (F-6) because it is load-bearing "
                "for the 'considerable cash' side of the plan.",
         effective="assumed", expires=None, src=None, next_check="2026-12-15",
         watch="Ask the CPA to put the 'no CA estate tax' conclusion in writing with a citation."),
    dict(id="L-03", system="income", jurisdiction="Federal",
         rule="Basis step-up at death (IRC 1014)",
         status="enacted-verified",
         detail="Basis becomes fair market value at the date of death (or the alternate valuation "
                "date if elected and it lowers the estate tax). This is why a sale in the year of "
                "death usually produces little or no gain - and it has NOTHING to do with the "
                "property tax bill.",
         effective="permanent", expires=None, src="IRS-559", next_check="2027-01-15",
         watch="Repeal or limitation of the step-up has been proposed in past Congresses and never "
               "enacted; nothing verified as pending now."),
    dict(id="L-04", system="income", jurisdiction="Federal",
         rule="Long-term capital gains rates + net investment income tax",
         status="enacted-verified",
         detail="2025/2026 published bands 0% / 15% / 20%; the 20% band begins above $533,400 "
                "(single) / $600,050 (married filing jointly). Unrecaptured section 1250 gain on "
                "depreciation is capped at 25%. NIIT of 3.8% applies above modified AGI thresholds.",
         effective="indexed annually", expires=None, src="IRS-409", next_check="2027-01-15",
         watch="Watch the NIIT thresholds and any surtax proposal; the model adds 3.8% to gains."),
    dict(id="L-05", system="income", jurisdiction="California",
         rule="No preferential rate for capital gains",
         status="enacted-verified",
         detail="FTB, verbatim position: 'California does not have a lower rate for capital gains. "
                "All capital gains are taxed as ordinary income.' This is why a $2.5M gain costs far "
                "more here than the federal tables suggest.",
         effective="permanent", expires=None, src="FTB-CG", next_check="2027-01-15",
         watch="No change verified."),
    dict(id="L-06", system="income", jurisdiction="California",
         rule="Mental/Behavioral Health Services Tax: 1% on taxable income over $1,000,000",
         status="enacted-verified",
         detail="Read as line 62 of the 2024 Form 540 booklet: 1% of the amount by which CA taxable "
                "income exceeds $1,000,000, reduced by certain credits. The threshold is NOT indexed. "
                "Applied in the model on top of the 12.3% top rate for every sale year in which a "
                "large gain is recognised.",
         effective="tax years beginning after 2024-01-01", expires=None,
         src="FTB-540-BOOKLET-2024", next_check="2027-01-15",
         watch="Recheck with the 2026 booklet when posted; confirm whether the threshold indexes."),
    dict(id="L-07", system="income", jurisdiction="Federal",
         rule="Section 121 principal-residence exclusion",
         status="enacted-verified",
         detail="$250,000 single / $500,000 married filing jointly of gain, requiring ownership AND "
                "use as principal residence for 2 of the last 5 years. Inherited property usually "
                "qualifies only if the heir moves in - which is why 'live first, sell later' is a "
                "separate path (P-04, P-09, P-11).",
         effective="permanent", expires=None, src="IRS-523", next_check="2027-01-15",
         watch="No change verified."),
    dict(id="L-08", system="income", jurisdiction="Federal",
         rule="Depreciation of residential rental property: 27.5 years straight line, mid-month",
         status="enacted-verified",
         detail="Only the building (land excluded) is depreciable, and only while held for rent. "
                "Every dollar claimed reduces the gain on sale - the deferral is real, the bill is "
                "too. Modelled with a 75% building allocation, which is an assumption (F-7).",
         effective="permanent", expires=None, src="IRS-946", next_check="2027-01-15",
         watch="No change verified."),
    dict(id="L-09", system="property", jurisdiction="California (constitution)",
         rule="Proposition 13: acquisition base year, factored at CPI or 2%, whichever is lower",
         status="enacted-verified",
         detail="Reaffirmed in the county's FY 2025-26 rate book. The 2% cap is what the model uses "
                "for every future year, including high-inflation years - that is the conservative "
                "(low tax) side of the assumption for the 'keep' paths.",
         effective="1978-07-01", expires=None, src="SCC-RATEBOOK", next_check="2026-12-15",
         watch="No change verified."),
    dict(id="L-10", system="property", jurisdiction="California",
         rule="Proposition 19 parent-child exclusion, R&TC 63.2",
         status="enacted-verified",
         detail="New taxable value = prior factored base year value + any market value above "
                "(prior FBYV + indexed allowance). Published allowance: $1,000,000 -> $1,022,600 -> "
                "$1,044,586 for transfers 2025-02-16 to 2027-02-15, indexed biennially by the "
                "California FHFA house-price index. Conditions: prior principal residence, heir's "
                "principal residence, homeowners'-exemption claim within 1 year, BOE-19-P within 3 "
                "years. Income use (rental) voids it entirely.",
         effective="2021-02-16", expires=None, src="BOE-P19", next_check="2027-02-16",
         watch="Next allowance publication expected 2027-02-16; a restoration of the full exclusion "
               "for all property types has been proposed in the Legislature (Prop 15 lineage) and "
               "has not passed - do not model it."),
    dict(id="L-11", system="property", jurisdiction="Santa Clara County",
         rule="County documentary transfer tax, R&TC 11911",
         status="enacted-verified",
         detail="$0.55 per $500 of consideration (0.11%), measured on the price EXCLUSIVE of debt "
                "that stays with the property. A city may add one-half of the county amount and the "
                "county credits it. No municipal add-on was identified in the FY 2025-26 compilation "
                "(F-11: confirm with escrow).",
         effective="statute; county administered", expires=None, src="RTC-11911",
         next_check="2027-06-30",
         watch="A gift or transfer at death is not a sale; counties rely on R&TC 11930 to exempt it. "
               "11930's text was not read this session (F-10) - get escrow's written confirmation."),
    dict(id="L-12", system="property", jurisdiction="San Francisco",
         rule="San Francisco real property transfer tax (cliff tiers per $500)",
         status="enacted-verified",
         detail="$2.50 up to $250k; $3.40 to $1M; $3.75 to $5M; $11.25 to $10M; $27.50 to $25M; "
                "$30.00 above. The tier applies to the ENTIRE consideration, so it is a cliff, not a "
                "marginal schedule - a 1% price move can cost thousands. Exemptions include transfer "
                "to spouse/domestic partner, gift, transfer at death, and reconveyance to a trust the "
                "grantor owns. Owner-occupied realty for a resident is capped at 3.75 (Admin Code "
                "1108.6).",
         effective="fiscal year", expires=None, src="SF-TRANSFER-TAX", next_check="2027-07-01",
         watch="Proposition I (2026) would have redirected half of this tax to affordable housing; "
               "it FAILED, so the tier table stands."),
    dict(id="L-13", system="local", jurisdiction="San Francisco",
         rule="Proposition H Muni parcel tax (multifamily)",
         status="pending-certification",
         detail="Approved 2026-11-03 with 74.4% (245,712 yes / 84,456 no). Multifamily: $249 base for "
                "the first 5,000 sq ft plus $0.195 per additional sq ft, capped at $50,000; 15 years "
                "starting July 2027; results certified by 2026-12-03; first bills FY 2027-28. Landlords "
                "may pass through no more than 50%, capped at $65 per unit, only where the rent was set "
                "before 2027-06-01.",
         effective="2027-07-01", expires="2042-06-30", src="SF-PROP-H-MTC", next_check="2026-12-03",
         watch="Certification is the only remaining step; after that it is a cost in every Property B "
               "path and must be re-read when the first bills issue."),
    dict(id="L-14", system="local", jurisdiction="SF + Santa Clara County",
         rule="Proposition RTM regional transit assessment (1 cent SF / half cent SCC)",
         status="pending-certification",
         detail="Approved 2026-11-03; collection begins April 2027. It is a sales/use tax surcharge, so "
                "it raises the cost of every appliance, roof and repair in the capital plan rather than "
                "the property tax.",
         effective="2027-04-01", expires=None, src="SF-PROP-H-MTC", next_check="2027-04-01",
         watch="Confirm the start month before pricing the 5-year capital plan."),
    dict(id="L-15", system="local", jurisdiction="Santa Clara Valley Water District",
         rule="Measure S parcel fee (Safe, Clean Water and Flood Protection)",
         status="enacted-not-read",
         detail="Approved November 2020, no expiry date, adjusts up to 2% a year, billed as a line on the "
                "property tax bill. This is the most likely reason the household's bills imply a rate "
                "above the county's 1% levy (F-2). Modelled as a separate $0 for now and flagged, "
                "because the per-parcel charge for this parcel was not read.",
         effective="FY 2021-22 onward", expires=None, src="SCVWD-MEASURES", next_check="2026-12-15",
         watch="Read the district's current parcel-charge schedule and put the actual number here."),
    dict(id="L-16", system="tenant", jurisdiction="California",
         rule="AB 1482 rent cap: 5% + CPI, maximum 10%; just-cause eviction",
         status="enacted-not-read",
         detail="Used in the model only as an UPPER BOUND on assumed rent growth for covered units, "
                "and to justify a 5% vacancy/turn allowance. The statute text (Civ. Code 1947.12) was "
                "not read this session, and the local CPI ordinance for Santa Clara County was not "
                "obtained (F-3).",
         effective="2020-01-01", expires="2030-01-01 (an expiry is stated in the summaries; not verified)",
         src=None, next_check="2027-01-15",
         watch="The 2030 expiry is the single most consequential tenant-law date for the rent paths."),
    dict(id="L-17", system="tenant", jurisdiction="San Francisco",
         rule="Owner move-in eviction, Rent Ordinance 37.9(a)(11) and 37.9C relocation",
         status="enacted-verified",
         detail="One owner-move-in per building; the heir must move in within 3 months and live there "
                "36 continuous months; 25% ownership minimum; tenants aged 60+ with 10 years' tenancy "
                "(or catastrophically ill with 5) cannot be moved out of a 2+ unit building. Relocation "
                "per the latest table read: $7,912 per tenant, $23,733 per unit maximum, plus $5,275 "
                "for each elderly/disabled/minor household member with NO cap on the extras "
                "(notices served 2024-03-01 to 2025-02-28).",
         effective="annual adjustment each March 1", expires=None, src="SF-RELO",
         next_check="2027-03-01",
         watch="The 2025-03-01 onward schedule was not located - do not rely on the dollar amounts "
               "without re-reading the current Form 579 (F-4)."),
    dict(id="L-18", system="property", jurisdiction="California",
         rule="Change in ownership on sale of a leased property, R&TC 61",
         status="enacted-verified",
         detail="A transfer of the lessor's interest in a lease with a remaining term UNDER 35 years IS "
                "a change in ownership: selling Property B with tenants in place reassesses it in full. "
                "That is a property-tax consequence of the 'sell B' paths that most analyses miss.",
         effective="statute", expires=None, src="RTC-61", next_check="2027-06-30",
         watch="No change verified."),
    dict(id="L-19", system="income", jurisdiction="Federal",
         rule="Passive activity losses and the $25,000 allowance phase-out",
         status="enacted-not-read",
         detail="The model treats rental losses as SUSPENDED rather than deductible against salary, and "
                "treats the real estate professional exception as unavailable. That is conservative for "
                "the rent paths. Phase-out runs from $100,000 to $150,000 modified AGI.",
         effective="permanent", expires=None, src=None, next_check="2027-01-15",
         watch="Have the CPA confirm the household's actual position; it changes the rent paths "
               "materially (F-13)."),
    dict(id="L-20", system="income", jurisdiction="Federal",
         rule="Like-kind exchange (IRC 1031) for rental property",
         status="enacted-verified",
         detail="Available only for property held for investment or business use - never for the "
                "principal residence, and never for Property A if the heir lives in it. Defers gain and "
                "carries the low basis forward; combined with a fresh Prop 13 base at the replacement "
                "property it can be the cheapest option, but it locks in illiquidity. Decision and "
                "written advice must be obtained BEFORE a sale (see Q-14).",
         effective="2018-01-01 (real property only)", expires=None, src="IRS-544",
         next_check="2027-01-15", watch="Recurring proposals to limit or repeal 1031."),
]

# ---------------------------------------------------------------- timeline ----
# days are relative to the triggering event; "date" entries are absolute.
TIMELINE = [
    dict(when="2026-12-03", event="SF Proposition H results certification deadline",
         system="local", consequence="After this date the FY 2027-28 parcel tax on Property B is fixed.",
         actor="n/a - monitor", src="SF-PROP-H-MTC"),
    dict(when="2026-12-15", event="Annual law recheck (this workspace)", system="all",
         consequence="Re-read every source on /sources.html; update the ranges and the flags.",
         actor="household", src=None),
    dict(when="2027-02-16", event="Next Prop 19 indexed allowance publication expected",
         system="property",
         consequence="Changes the excess-reassessment threshold in every live path; re-run the model.",
         actor="household", src="BOE-P19"),
    dict(when="2027-04-01", event="Prop RTM sales-tax surcharge begins (SF + half cent SCC)",
         system="local", consequence="Raises the cost of every repair and capital item in the 5-year plan.",
         actor="household", src="SF-PROP-H-MTC"),
    dict(when="2027-07-01", event="First Proposition H bills (FY 2027-28)", system="local",
         consequence="Adds a recurring charge to Property B; check the pass-through limit before "
                     "raising rents.", actor="property manager", src="SF-PROP-H"),
    dict(when="within 150 days of distribution", event="Change in ownership statement (BOE-502-D)",
         system="property", consequence="Filing obligation on the transferee; penalties if missed.",
         actor="heir", src=None),
    dict(when="within 1 year of transfer", event="Homeowners' exemption claim for Property A",
         system="property",
         consequence="MANDATORY precondition of the Prop 19 exclusion. Miss it and the exclusion dies.",
         actor="heir", src="BOE-P19"),
    dict(when="within 3 years of transfer", event="File BOE-19-P parent-child claim",
         system="property",
         consequence="Or before any transfer to a third party - whichever is first. Selling early "
                     "forfeits the claim.", actor="heir", src="BOE-P19"),
    dict(when="9 months after date of death", event="Form 706 estate tax return (if required)",
         system="estate",
         consequence="Also the vehicle for the portability election. Six-month extension on Form 4768.",
         actor="executor + CPA", src="IRS-706"),
    dict(when="6 months after date of death", event="Alternate valuation date window (IRC 2032)",
         system="estate",
         consequence="Only usable if it lowers BOTH the estate tax and the deductions; it also lowers "
                     "the heir's basis - a real trade-off, not a free option.", actor="CPA", src="IRS-706"),
    dict(when="April 15 following the death", event="Decedent's final Form 1040; estate's Form 1041",
         system="income", consequence="Income the property earns before distribution is taxed there.",
         actor="executor + CPA", src="IRS-559"),
    dict(when="each 11-01 and 02-01", event="Santa Clara County property tax installments",
         system="property",
         consequence="Delinquent 12-10 and 04-10 with 10% penalty plus 1.5%/month redemption penalty.",
         actor="owner", src="SCC-RATEBOOK"),
    dict(when="0-9 months after a change in ownership", event="Supplemental tax bills (SB 813)",
         system="property",
         consequence="A reassessment arrives as extra bills AFTER the transfer, not as a higher annual "
                     "bill - the classic cash-flow surprise. Budget for two supplemental bills.",
         actor="owner", src="SCC-RATEBOOK"),
    dict(when="12 months + 3 months", event="SF owner-move-in notice period and occupancy clock",
         system="tenant",
         consequence="If the plan depends on occupying a Property B unit, the notice, the relocation "
                     "payment (half at service, half at vacancy) and the 36-month occupancy start here.",
         actor="heir + rent counsel", src="SF-OMI"),
    dict(when="before any listing", event="Obtain written 1031 advice; decide exchange vs sale",
         system="income",
         consequence="The exchange must be structured BEFORE closing; it cannot be elected on the "
                     "return.", actor="CPA + intermediary", src="IRS-544"),
    dict(when="before money exists", event="Sign the investment policy statement",
         system="estate",
         consequence="Allocation, Treasury parking lane, redeployment calendar, liquidity floor, and "
                     "permitted leverage - agreed in writing so the month of the funeral is not the "
                     "decision window.", actor="household", src=None),
]

# ------------------------------------------- pre-committed decision rules ----
# Written BEFORE the projections were argued, per the household's own instruction.
CRITERIA = dict(
    purpose="Fix the thresholds that make each choice correct, in writing, before arguing about "
            "any projection. If a projection moves and the thresholds still hold, the answer has "
            "not changed.",
    live=[
        "The household intends Property A to be their principal residence for at least 5 years "
        "(that is what makes Prop 19 and later section 121 real, and what justifies the reassessment).",
        "Gross rental yield on A is BELOW the after-tax yield available on Treasury bills - i.e. the "
        "rental market is not paying them enough to give up the liquidity.",
        "Written insurance quotes for the owner-occupied house are below the modelled figure, and the "
        "5-year capital plan needs under $150,000.",
        "No co-beneficiary needs cash, and no creditor or Medi-Cal claim can attach to the house.",
        "They can fund the annual shortfall between A's carrying cost and Property B's net operating "
        "income without borrowing.",
    ],
    rent=[
        "Four closed leases for comparable Santa Clara County single-family houses show net yield (after tax, "
        "insurance, upkeep, vacancy and management) above the after-tax yield on Treasuries by at least "
        "0.5 percentage points.",
        "The household accepts that a non-owner-occupied inherited house gets NO Prop 19 exclusion: "
        "the model's rent paths therefore carry a fully reassessed tax bill from year one.",
        "Depreciation is wanted, and the household has read the recapture line in this workspace and "
        "accepts the deferred-tax trade.",
        "The rental losses will be suspended under the passive rules - i.e. there is no salary offset.",
    ],
    sell=[
        "Net after-tax proceeds would produce more income in a diversified portfolio than the house "
        "produces net, at the household's own risk tolerance, for the whole planning horizon.",
        "The household needs liquidity, wants to consolidate debt, or a co-owner requires cash.",
        "Expected carrying costs plus the reassessment penalty exceed the rent they can actually prove.",
        "They will not live in it - in which case Prop 19 is unavailable and the tax argument for "
        "holding collapses.",
    ],
    mixed=[
        "Occupancy is uncertain, or the housing/rent evidence is still thin: live in A, claim the "
        "exemption and the exclusion, and defer the sale decision by 24-36 months. This keeps every "
        "door open, costs only the option's own carrying cost, and it is the only path that preserves "
        "both Prop 19 and section 121.",
    ],
    hard_stops=[
        "Any Medi-Cal estate claim, tax lien or judgment against the property.",
        "An unpermitted unit at Property B that the insurer or a buyer will not accept.",
        "A co-owner who will not sign (partition risk).",
        "A liquidity shortfall that forces a sale in whatever year it happens.",
    ],
    tie_break="If two paths are within 10% of each other on real terminal wealth, choose the more "
              "reversible one. Reversibility is worth more than a modelling margin.",
)

# ------------------------------------------------------------- decision log ----
DECISION_LOG = [
    dict(date="2026-11-25", decision="Publish only rounded figures; keep the raw numbers offline",
         rationale="The household's exact tax bills and rent roll are traceable through public records. "
                   "Every dollar figure in this repository passes through a $10 rounding step, and no "
                   "address, APN or account number is stored here.",
         status="adopted", owner="workspace"),
    dict(date="2026-11-25", decision="Rank paths on real terminal wealth, with use value shown separately",
         rationale="Wealth and utility are different things. Folding imputed rent into the objective "
                   "function would let a lifestyle preference drive a financial recommendation. It is "
                   "now a reported column and an explicit toggle, never silent.",
         status="adopted", owner="workspace"),
    dict(date="2026-11-25",
         decision="Treat path cash flow at the risk-free opportunity cost, not at a borrowing rate",
         rationale="Every path is funded the same way, so the comparison is clean. Charging the live-in "
                   "paths a consumer-loan spread for a shortfall they would actually fund from savings "
                   "or salary would have biased the answer toward selling. Stated as a convention.",
         status="adopted", owner="workspace"),
    dict(date="2026-11-25", decision="Treat rental losses as suspended (no salary offset)",
         rationale="Conservative for the rent paths, and the likely legal outcome at this income level. "
                   "Marked for CPA confirmation as L-19 / F-13.", status="provisional", owner="CPA"),
    dict(date="2026-11-25", decision="Do not model any un-enacted legislation",
         rationale="Proposed bills appear on /watch.html with their status and nothing else. A plan built "
                   "on a bill that has not passed is a wager, not a plan.", status="adopted",
         owner="workspace"),
    dict(date="2026-11-25", decision="Leave unconfirmable figures blank rather than estimating them",
         rationale="municipal utility rates, the CPI series, the 2025-26 Form 579 amounts and the parcel's "
                   "tax rate area could not be read from an official source in this session. They are "
                   "blank + flagged, and the affected rows say so.", status="adopted", owner="workspace"),
    dict(date="2026-11-25", decision="Keep the 2045 transfer year as the shared comparison date",
         rationale="The trust transfer window is 2040-2050. A single mid-point date is used so all twelve "
                   "paths are compared like-for-like; the what-if page lets the date move, and the "
                   "sensitivity to it is published.", status="adopted", owner="workspace"),
]

# --------------------------------------------------------------- recheck ----
RECHECK = [
    dict(what="Santa Clara County tax rate book for the current fiscal year",
         where="controller.santaclaracounty.gov - Property Tax Rate Book",
         why="The composite rate for the parcel's tax rate area, and the 1% levy language.",
         cadence="each October, when published", affects="every property-tax row",
         src="SCC-RATEBOOK-PAGE"),
    dict(what="BOE Proposition 19 indexed allowance",
         where="boe.ca.gov/prop19 plus the biennial Letter to Assessors",
         why="Sets the excess-reassessment threshold in every live path.",
         cadence="every other February 16", affects="P-01, P-02, P-04, P-09, P-11",
         src="BOE-P19"),
    dict(what="San Francisco secured tax rate for the coming fiscal year",
         where="sftreasurer.org - Secured Property Taxes",
         why="Used as the Property B rate; the household's bills do not reconcile to it (F-1).",
         cadence="each July or August", affects="Property B carrying costs",
         src="SF-TTC-RATE"),
    dict(what="San Francisco transfer-tax tiers and exemptions",
         where="sfasr.org - Transfer Tax, and Admin Code 1108",
         why="The tiers are cliffs, so a change alters the net proceeds of any Property B sale.",
         cadence="annually, and before any listing", affects="P-08 and every sell-B variant",
         src="SF-TRANSFER-TAX"),
    dict(what="Form 579 relocation amounts",
         where="sf.gov - Rent Board forms",
         why="The table read here covers notices served 2024-03-01 to 2025-02-28; a later edition "
             "must exist and was not located.",
         cadence="each March 1", affects="any path needing possession", src="SF-RELO"),
    dict(what="IRS estate-tax threshold and top rate",
         where="irs.gov - Estate tax",
         why="The only number that decides whether a Form 706 is required at all.",
         cadence="each January", affects="the estate plan, not the housing choice",
         src="IRS-ESTATE"),
    dict(what="FTB Form 540 instructions and booklet: the 1% surtax line",
         where="ftb.ca.gov - forms by year",
         why="The $1,000,000 threshold was not indexed in the booklet read here, so it quietly "
             "captures more of the gain each year.",
         cadence="each January", affects="sale-year tax in every sell path",
         src="FTB-540-BOOKLET-2024"),
    dict(what="Damodaran historical returns table",
         where="pages.stern.nyu.edu - Historical Returns on Stocks, Bonds and Bills",
         why="The Black-Swan and phased-investing lanes are computed from it; it gains a year each "
             "January.",
         cadence="each January", affects="black-swan.html and phased.html", src="DAMO"),
    dict(what="Treasury par yield curve for the parking lane",
         where="home.treasury.gov - Daily Treasury Par Yield Curve Rates",
         why="The parked-cash return is an input, not a constant; in early 2026 it sat near 3.5% "
             "for 3-month to 2-year paper.",
         cadence="each quarter", affects="phased.html", src="UST-DAILY"),
    dict(what="Insurance quotes for both buildings",
         where="an independent broker - three written quotes",
         why="The owner-supplied figures are placeholders; California wildfire and insurance-market "
             "pricing moves quickly.",
         cadence="annually, and at every non-renewal", affects="live and rent paths", src=None),
]

GLOSSARY = [
    ("Adjusted basis", "What you 'paid' for tax purposes: stepped-up value at death, plus capital "
     "improvements, minus depreciation claimed. Gain = net sale price - adjusted basis."),
    ("Ad valorem", "'According to value' - a tax computed as a percentage of assessed value, as "
     "opposed to a flat parcel charge."),
    ("Alternate valuation date", "An estate-tax election to value assets 6 months after death instead "
     "of at death. It lowers the estate tax only if values fell - and it lowers the heir's basis by "
     "the same amount."),
    ("Basic exclusion amount", "The federal estate/gift threshold above which the 40% estate tax "
     "applies ($15,000,000 for a 2026 death)."),
    ("Block bootstrap", "Resampling in fixed-length contiguous blocks instead of single years, so a "
     "simulated path keeps real sequences of bad years together. Used here with 3-year blocks."),
    ("BOE-19-P", "The claim form that actually starts the Proposition 19 parent-child exclusion. Filing "
     "the homeowners' exemption is NOT the same filing."),
    ("Change in ownership", "The property-tax event that resets a base year value. A distribution under "
     "a trust can be one; whether it is depends on who holds what before and after."),
    ("DSUE / portability", "A deceased spouse's unused estate-tax exclusion, transferable to the "
     "surviving spouse - but only if a Form 706 was filed to elect it."),
    ("Escrow holdback / concessions", "Seller-paid credits at closing. Modelled as a percentage of "
     "price so the number survives re-pricing."),
    ("Factored base year value (FBYV)", "A parcel's Prop 13 base, grown each year by CPI or 2%, "
     "whichever is lower. This - not market value - drives the bill on an unchanged property."),
    ("Imputed rent", "The market rent an owner-occupier avoids by living in their own house. It is the "
     "price of occupying the asset, so a 'live there' path is not free."),
    ("Mid-month convention", "Residential depreciation starts (and stops) as if in the middle of the "
     "month, so a December purchase gets half a month of it."),
    ("NIIT", "Net investment income tax - 3.8% on investment income including capital gains above "
     "modified AGI thresholds. It stacks on top of the 20% rate, not instead of it."),
    ("Non-ad-valorem / direct assessment", "A flat parcel charge (water district, flood control, some "
     "bonds) billed on the tax bill regardless of value. The likeliest explanation of both properties' "
     "odd implied rates."),
    ("Owner move-in (OMI)", "A San Francisco no-fault eviction allowing an owner with 25%+ ownership to "
     "take one unit for their own use, subject to a 36-month occupancy promise and relocation payments."),
    ("Present value", "What a future dollar is worth today at a chosen discount rate. Used here to make "
     "30-year streams comparable; the discount rate itself is an assumption on the what-if page."),
    ("Real vs nominal", "Nominal is dollars; real is dollars divided by prices. Two properties and a "
     "stock portfolio are only comparable in real terms."),
    ("Recapture (unrecaptured 1250)", "Depreciation you took is taxed again on sale at up to 25% - a "
     "rate that exists specifically because the underlying gain would otherwise be taxed at 20%."),
    ("RPTT", "San Francisco's real property transfer tax, payable at recording, with tiered cliff rates."),
    ("Section 121 exclusion", "$250,000 (single) of gain on a principal residence, needing 2 of the "
     "last 5 years of both ownership and use. Inherited houses usually fail the 'use' test until someone "
     "moves in."),
    ("Sequence-of-returns risk", "The same average return producing very different outcomes depending on "
     "the ORDER of the years. It is the whole reason a sale at 2045 might be staged."),
    ("Suspended loss", "A passive rental loss the tax law will not let you deduct now; it waits, unused, "
     "until there is passive income or a sale."),
    ("Supplemental bill", "A catch-up bill issued after a reassessment, for the part-year already billed "
     "at the old value. Two of them typically follow a change in ownership."),
    ("Tax Rate Area (TRA)", "The parcel-level map code that determines which voter-approved bonds add on "
     "top of the 1% levy. Santa Clara County has 816 of them."),
    ("Treasury parking lane", "Holding sale proceeds in 3-month to 2-year Treasuries for a fixed period "
     "before buying risk assets, so a crash just after the sale cannot hit the whole stake at once."),
    ("Use value", "The benefit of consuming the housing yourself, as opposed to the money it could "
     "earn. Reported separately here, and never used silently."),
    ("Vacancy / turn allowance", "A haircut on gross rent for empty periods and re-letting costs; 5% is "
     "used in this model as an assumption, not a measurement."),
]
