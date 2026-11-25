"""
inputs.py — single source of truth for every number on the site.

PRIVACY RULE (binding for this repo)
  * No names, no street addresses, no APNs, no parcel/book-document numbers, no
    account numbers, no birth dates. Properties are "Property A" and "Property B".
  * Every dollar figure that leaves this file on a page is rounded to the nearest
    $10 so it cannot be matched to a public record by search.
  * ZIP codes are kept at 5 digits because the tax rate, the rent rules and the
    utility rates are set at ZIP/county level and the decision is wrong without them.

VERIFICATION RULE
  * `src` is the official (or, where noted, academic) document this figure was read
    from. `v` is the verification status:
      "official"   read from a government source during the 2026-11-25 session
      "owner"      supplied by the household; not independently confirmable
      "academic"   read from a published research dataset (NYU Stern / Shiller style)
      "unverified" no source located in this pass -> MUST NOT drive a decision
  * Anything not `official` and not arithmetic on an `official` value is listed on the
    Flagged for Review page.
"""

SESSION = "9ca44509"
ASOF = "2026-11-25"
D = 10  # rounding increment, dollars


def r10(x):
    """Round a dollar figure to the nearest $10 (privacy rule)."""
    if x is None:
        return None
    return int(round(float(x) / D) * D)


# ---------------------------------------------------------------- sources ----
SOURCES = {
    "BOE-P19": ("California State Board of Equalization, Proposition 19 "
                "(comparison charts, filing periods, $1M indexed amount table)",
                "https://www.boe.ca.gov/prop19/", "official"),
    "BOE-LTA25015": ("BOE Letter to Assessors 2025/015 (Prop 19 intergenerational "
                     "exclusion, $1,044,586 for 2/16/2025-2/15/2027)",
                     "https://boe.ca.gov/proptaxes/pdf/lta25015.pdf", "official"),
    "BOE-PUB801": ("BOE Publication 801, Proposition 19 Fact Sheet",
                   "https://www.boe.ca.gov/pdf/pub801.pdf", "official"),
    "SCC-RATEBOOK": ("County of Santa Clara, Compilation of Tax Rates & Information, "
                     "FY 2025-26 (1% limit, CPI-or-2% factor, 816 tax rate areas, due "
                     "and delinquency dates, 10% penalty, 1.5%/mo redemption penalty)",
                     "https://files.santaclaracounty.gov/exjcpb1531/2025-11/tax-rate-book-2025-2026.pdf"
                     "?VersionId=HHMZ1VmGwFXqVvpM36xuptkIcV2V8ctE", "official"),
    "SCC-RATEBOOK-PAGE": ("Santa Clara County Controller-Treasurer, Property Tax Rate "
                          "Book index (current + archive back to FY2004-05)",
                          "https://controller.santaclaracounty.gov/property-tax-distribution/property-tax-rate-book",
                          "official"),
    "SCC-RECORDER-FEES": ("Santa Clara County Clerk-Recorder fee schedule "
                          "(first page $102.00 incl. $10 fraud fee, $75 SB2 fee, $2 AB1466; "
                          "$3.00 per additional page; $10 subtracted when DTT applies)",
                          "https://clerkrecorder.santaclaracounty.gov/resources/fee-schedule", "official"),
    "RTC-11911": ("Cal. Rev. & Tax. Code s.11911 (documentary transfer tax: "
                  "$0.55 per $500 or fraction; city may add one-half; county credits city tax)",
                  "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=11911",
                  "official"),
    "RTC-61": ("Cal. Rev. & Tax. Code s.61 (what is, and is not, a change in ownership "
               "for property tax purposes)",
               "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=61",
               "official"),
    "FTB-CG": ("California Franchise Tax Board, Capital gains and losses "
               "('California does not have a lower rate for capital gains. "
               "All capital gains are taxed as ordinary income.')",
               "https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html", "official"),
    "FTB-540-2025": ("FTB 2025 Instructions for Form 540 (resident income tax; "
                     "reference date of the return read in this session)",
                     "https://www.ftb.ca.gov/forms/2025/2025-540-instructions.html", "official"),
    "FTB-540-BOOKLET-2024": ("FTB 2024 Form 540 Booklet, Line 62 - Mental Health Services Tax: "
                             "taxable income above $1,000,000 x 1%",
                             "https://www.ftb.ca.gov/forms/2024/2024-540-booklet.pdf", "official"),
    "IRS-ESTATE": ("IRS, Estate tax page - filing threshold table by year of death "
                   "(2025: $13,990,000; 2026: $15,000,000) and portability note",
                   "https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax", "official"),
    "IRS-409": ("IRS Topic no. 409, Capital gains and losses (0/15/20% bands for 2025; "
                "unrecaptured section 1250 gain taxed at a maximum 25%; NIIT reference)",
                "https://www.irs.gov/taxtopics/tc409", "official"),
    "IRS-706": ("IRS Form 706 and Instructions (estate tax return; due 9 months after death; "
                "extension on Form 4768; portability election)",
                "https://www.irs.gov/forms-pubs/about-form-706", "official"),
    "IRS-523": ("IRS Publication 523, Selling Your Home (section 121 exclusion: "
                "$250,000 / $500,000 if married filing jointly; 24 of the last 60 months "
                "ownership and use)",
                "https://www.irs.gov/publications/p523", "official"),
    "IRS-544": ("IRS Publication 544, Sales and Other Dispositions of Assets "
                "(holding period for property inherited; section 1250 recapture)",
                "https://www.irs.gov/publications/p544", "official"),
    "IRS-946": ("IRS Publication 946, How To Depreciate Property "
                "(residential rental property: 27.5 years, straight line, mid-month convention)",
                "https://www.irs.gov/publications/p946", "official"),
    "IRS-559": ("IRS Publication 559, Survivors, Executors, and Administrators "
                "(basis of property acquired from a decedent; income the estate earns)",
                "https://www.irs.gov/forms-pubs/about-publication-559", "official"),
    "SF-TTC-RATE": ("SF Treasurer & Tax Collector, Secured Property Taxes - FY 2026-27 "
                    "secured tax rate 1.18162182%; bills mailed October; two installments",
                    "https://sftreasurer.org/property/secured-property-taxes", "official"),
    "SF-TRANSFER-TAX": ("SF Office of the Assessor-Recorder, Transfer Tax - tier schedule "
                        "($2.50/$3.40/$3.75/$11.25/$27.50/$30.00 per $500) and exemptions "
                        "(married, gift, inheritance, own trust)",
                        "http://sfasr.org/recorder-information/recording-document/transfer-tax", "official"),
    "SF-RECORDING-FEES": ("City & County of San Francisco, Fees to record a document "
                          "(exemptions from the recording fee for documents subject to "
                          "transfer tax or transferring a residential dwelling to an owner-occupier)",
                          "https://www.sf.gov/reports--march-2024--fees-record-document-san-francisco", "official"),
    "SF-OMI": ("SF Rent Board, Evictions Based on Owner or Relative Move-In "
               "(36 continuous months, one unit per building, 25% ownership, "
               "elderly/disabled long-tenants protected)",
               "https://www.sf.gov/information--evictions-based-owner-or-relative-move", "official"),
    "SF-NEWCON": ("SF Rent Board, Partial Exemption for Newly Constructed Rental Units "
                  "(post-6/13/1979 units and substantial rehab: exempt from rent caps, "
                  "covered by just cause since 1/20/2020)",
                  "https://www.sf.gov/information--partial-exemption-newly-constructed-rental-units", "official"),
    "SF-RELO": ("SF Rent Board Form 579, Relocation Payments under s.37.9C "
                "(notice served 3/1/24-2/28/25: $7,912 per tenant, $23,733 per unit max, "
                "plus $5,275 per elderly/disabled/minor-child household member)",
                "https://www.sf.gov/file/579-multilingual-relocation-payments-379c-24-25-124pdf", "official"),
    "SFPUC-RATES": ("SFPUC Rate Schedules and Fees for Water and Sewer Service, "
                    "FY 2026-27 and FY 2027-28 (multi-family service charge $13.13/unit, "
                    "wastewater $6.62 + $11.34/discharge unit, stormwater Tier 1 $12.63/mo)",
                    "https://www.sfpuc.gov/sites/default/files/accounts-and-services/Rates_Schedule_Water_Sewer_2026-7.pdf",
                    "official"),
    "SF-PROP-H": ("San Francisco Proposition H (Nov 3 2026): parcel tax to fund Muni - "
                  "multifamily base $249 per parcel for the first 5,000 sq ft of building "
                  "area + $0.195/sq ft above, capped $50,000; single-family base $129; "
                  "15 years from July 2027; 50% pass-through capped $65 per unit for "
                  "rent-controlled units whose initial base rent predates 6/1/2027",
                  "https://www.californiachoices.org/san-francisco-proposition-h-2026", "official-ballot-summary"),
    "SF-PROP-H-MTC": ("Bay Area Transit Authority / MTC, 'Bay Area Voters Approve Transit "
                      "Funding Measures' (Nov 4 2026): Prop H approved; revenues begin on "
                      "FY 2027-28 tax bills; results certified by county registrars by Dec 3, 2026",
                      "https://www.sfcta.org/blogs/bay-area-voters-approve-transit-funding-measures", "official"),
    "SCVWD-MEASURES": ("Santa Clara Valley Water District Measure S (Nov 2020) - renewal of the "
                       "Safe, Clean Water and Natural Flood Protection Program parcel tax, "
                       "~$45.5M/yr, no expiry, up to 2%/yr adjustment",
                       "https://files.santaclaracounty.gov/migrated/Measure%20S.pdf", "official"),
    "DAMO": ("A. Damodaran, 'Historical Returns on Stocks, Bonds and Bills: 1928-2024' "
             "(S&P 500 total return incl. dividends; 3-month T-bill average rate during "
             "the year), NYU Stern, table updated Jan 5 2026",
             "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html", "academic"),
    "UST-DAILY": ("U.S. Treasury, Daily Treasury Par Yield Curve Rates, 2026 "
                  "(3-month 3.65%, 2-year 3.47% on 01/02/2026; 3-month 3.67%, 2-year 3.55% on 01/20/2026)",
                  "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026",
                  "official"),
    "CDTFA-RATES": ("California Department of Tax and Fee Administration, city/county sales "
                    "and use tax rates (the city's rate is 9.750% from 10/1/2026)",
                    "https://cdtfa.ca.gov/taxes-and-fees/rates.aspx", "official"),
}

# ------------------------------------------------------------------- A / B ----
PROPERTY_A = {
    "label": "Property A - single-family house, Santa Clara County",
    "role": "The inherited house (single-family, solar installed).",
    "value_2026": r10(3_100_000),
    "value_source": "owner estimate, November 2026",
    "assessed_2026": r10(550_537),
    "water_mo": (r10(100 * 12), r10(150 * 12)),        # owner: $100-$150 per month
    "electric_mo_net": (r10(-20 * 12), r10(-10 * 12)),  # solar net credit, owner
    "insurance_yr_owner": r10(1500),
    "maintenance_pct_of_value": (0.004, 0.008),
    "rent_mo_range": (r10(7500), r10(9500)),   # UNVERIFIED - see comparables page
    "property_mgmt_pct": (0.06, 0.08),
    "units": 1,
    "occupancy_after_transfer": "heir's principal residence if they move; otherwise 100% rented",
}

# Property A: owner-supplied tax history, every figure rounded to $10.
# pct columns are the year-over-year change as the household recorded it.
HISTORY_A = [
    # year, tax, assessed, tax change %, assessed change %
    (2026, None, r10(550_537), None, 2.0),
    (2025, r10(7_207), r10(539_743), 2.9, 2.0),
    (2024, r10(7_003), r10(529_161), 1.2, 2.0),
    (2023, r10(6_917), r10(518_786), 2.4, 2.0),
    (2022, r10(6_755), r10(508_614), 1.4, 2.0),
    (2021, r10(6_662), r10(498_642), 1.5, 1.0),
    (2020, r10(6_565), r10(493_530), 0.0, 2.0),
    (2019, r10(6_565), r10(483_854), 2.8, 2.0),
    (2018, r10(6_383), r10(474_368), None, 2.0),
    (2017, r10(6_383), r10(465_067), -0.5, 2.0),
    (2016, r10(6_414), r10(455_949), 4.6, 1.5),
    (2015, r10(6_130), r10(449_101), 2.8, 2.0),
    (2014, r10(5_965), r10(440_305), None, 0.5),
]

PROPERTY_B = {
    "label": "Property B - three-unit building, San Francisco",
    "role": "Already owned outright by the person who inherits Property A. 3 livable "
            "units, 2 rented, 1 vacant; owner can occupy one unit without giving up rent.",
    "value_2026": r10(1_800_000),
    "assessed_2025": r10(114_248),
    "tax_2025": r10(2_439),
    "units": 3,
    "units_rented": 2,
    "rent_roll_mo": r10(7_150),
    "vacant_unit_rent_mo": (r10(3_300), r10(3_800)),   # UNVERIFIED
    "water_mo": (r10(330 * 12), r10(400 * 12)),        # whole 3-unit building
    "electric_mo": (r10(30 * 12), r10(70 * 12)),       # common area, per owner
    "insurance_yr_owner": r10(1500),
    "maintenance_pct_of_value": (0.012, 0.020),
    "property_mgmt_pct": (0.05, 0.08),
}

HISTORY_B = [
    (2025, r10(2_439), r10(114_248), 5.3, 2.0),
    (2024, r10(2_315), r10(112_008), 6.2, 2.0),
    (2023, r10(2_179), r10(109_814), 3.4, 2.0),
    (2022, r10(2_107), r10(107_662), 2.0, 2.0),
    (2021, r10(2_066), r10(105_595), -5.9, 1.0),
    (2020, r10(2_197), r10(104_513), 3.0, 2.0),
    (2019, r10(2_134), r10(102_465), 3.5, 2.0),
    (2018, r10(2_061), r10(100_456), 18.4, 2.0),
    (2017, r10(1_740), r10(98_488), 3.9, 2.0),
    (2016, r10(1_675), r10(96_557), 1.6, 1.5),
]

# ------------------------------------------------------------- tax & rules ----
RULES = {
    "prop19_indexed_amount": 1_044_586,
    "prop19_window": "transfers 2026-02-16 through 2027-02-15 window is not yet published; "
                     "current published amount $1,044,586 applies to transfers 2025-02-16 to 2027-02-15",
    "prop19_prior_amounts": [(1_000_000, "2021-02-16 to 2023-02-15"),
                             (1_022_600, "2023-02-16 to 2025-02-15"),
                             (1_044_586, "2025-02-16 to 2027-02-15")],
    "prop19_requires": [
        "was the transferor's principal residence",
        "becomes the transferee's principal residence, and the transferee must apply for the "
        "homeowners' exemption within 1 year of the transfer",
        "value cap = factored base year value + indexed $1,000,000; market value above the cap "
        "is added to the transferred base year value",
        "claim form (BOE-19-P) filed within 3 years of the transfer or before transfer to a third party",
    ],
    "sc_rate_central": 0.01334,      # implied by the household's own bills; see Flagged F-2
    "sc_rate_components_official": "1.00000% maximum tax levy + voter-approved bonds by tax rate area",
    "sf_rate_central": 0.0118162182,  # SF Treasurer FY 2026-27 secured rate
    "sf_prop_h_multifamily_base": 249,
    "sf_prop_h_sqft_over": 5000,
    "sf_prop_h_per_sqft": 0.195,
    "sc_dtt_per_500": 0.55,
    "sf_dtt_tiers": [(250_000, 2.50), (1_000_000, 3.40), (5_000_000, 3.75),
                     (10_000_000, 11.25), (25_000_000, 27.50), (10**12, 30.00)],
    "homeowner_exemption": 7_000,
    "prop13_factor_cap": 0.02,
    "fed_bea_2026": 15_000_000,
    "fed_bea_2025": 13_990_000,
    "fed_top_rate": 0.40,
    "fed_ltcg_top": 0.20,
    "fed_1250_cap": 0.25,
    "niit": 0.038,
    "ca_top": 0.123,
    "ca_bhst": 0.01,
    "ca_mhst_threshold": 1_000_000,
    "sec121_single": 250_000,
    "sec121_joint": 500_000,
    "depr_life_resid": 27.5,
    "ab1482_cap": (0.05, 0.10),
}

# ------------------------------------------------------ economic assumptions ----
# Deliberately expressed as ranges, never as single round numbers (task: replace
# round-number assumptions with ranges). Each entry states who says so.
ECON = {
    "home_value_growth": {"low": 0.015, "mid": 0.030, "high": 0.045,
                          "basis": "assumption; no official long-run forecast exists. "
                                   "Owner must replace with an appraisal + 3 comps (see Comparables)."},
    "rent_growth": {"low": 0.015, "mid": 0.028, "high": 0.042,
                    "basis": "assumption bounded by AB 1482 (5% + CPI, max 10%) for covered units"},
    "inflation": {"low": 0.015, "mid": 0.025, "high": 0.038,
                  "basis": "assumption - BLS CPI series was not read in this session; FLAGGED"},
    "equity_real_return": {"low": 0.045, "mid": 0.068, "high": 0.090,
                           "basis": "arithmetic on the Damodaran annual S&P 500 total-return series"},
    "tbill_return": {"low": 0.005, "mid": 0.033, "high": 0.050,
                     "basis": "arithmetic on the Damodaran 3-month T-bill series; "
                              "Treasury's 2026 curve shows 3M 3.65% / 2Y 3.47%"},
    "insurance_growth": {"low": 0.03, "mid": 0.05, "high": 0.08,
                         "basis": "assumption; California market disruption - FLAGGED, quotes required"},
    "transfer_year": 2045,
    "transfer_year_range": (2040, 2050),
    "horizons": [10, 20, 30],
    "discount_rate": 0.035,
}

# Selling costs, by market. Percentages, not dollars, so they survive re-pricing.
TRANSACT = {
    "A": {"commission_pct": 0.050, "seller_concessions_pct": 0.005,
          "dtt_pct": 0.0011, "dtt_note": "Santa Clara County $0.55 per $500 = 0.11%; "
                                         "no city transfer tax identified for the property's "
                                         "city - FLAG, confirm with escrow",
          "prep_pct": 0.006, "closing_flat": 100},
    "B": {"commission_pct": 0.055, "seller_concessions_pct": 0.008,
          "dtt_pct": 0.0075, "dtt_note": "SF tier for $1M-$5M value: $3.75 per $500 = 0.75%, "
                                         "applied to the whole consideration (a cliff, not a marginal rate)",
          "prep_pct": 0.010, "closing_flat": 200},
}

# Phased-investing lane the household asked for.
PHASING = {
    "park_months": [0, 12, 24, 36],
    "phase_in_months": [1, 12, 24, 36],
    "instrument": "3-month to 2-year U.S. Treasury bills/notes, ladder rolled to maturity",
    "crash_entries": [1929, 1930, 1937, 1973, 2000, 2007, 2008, 2020, 2021, 2025],
}

# ---------------------------------------------------------------- questions ----
# The register the user asked for: what must be answered before a decision is defensible.
# kind: "fact" (a number we need), "legal" (counsel), "family" (household), "action" (task)
QUESTIONS = [
    dict(id="Q-01", kind="legal", topic="Prop 19 eligibility",
         q="Will the heir actually occupy Property A as a principal residence within one year of "
           "the transfer, and will they file for the homeowners' exemption in that window?",
         why="Without both, there is no parent-child exclusion at all and the full market value "
             "becomes the new taxable value - that is the single biggest swing in the model.",
         status="OPEN", where="Trustee + CPA; county assessor claim BOE-19-P",
         src="BOE-P19"),
    dict(id="Q-02", kind="fact", topic="Valuation at death",
         q="What is the fair market value of Property A on the date of death (retrospective appraisal)?",
         why="It sets the income-tax basis AND the Prop 19 excess reassessment. A $100k error moves "
             "the property-tax projection by about $1,340 a year forever.",
         status="OPEN", where="Licensed appraiser; must be a written, dated report",
         src="owner"),
    dict(id="Q-03", kind="fact", topic="Market rent for Property A",
         q="What does a comparable Santa Clara County single-family house actually rent for today?",
         why="Two of the eleven paths rank on rent. Right now that ranking rests on the owner's "
             "estimate, not on evidence. Get 4 closed comparables plus 2 landlord fee quotes.",
         status="OPEN", where="Broker comp sheet + RentBoard/rent-data cross-check", src="owner"),
    dict(id="Q-04", kind="fact", topic="Property A tax rate area",
         q="What is the parcel's Tax Rate Area number and the total rate printed on its bill?",
         why="Santa Clara County publishes 816 TRA rates. The household's own bills imply ~1.33%, "
             "which is above the county's city-level summaries, so the difference is either a "
             "parcel-specific charge or a data-entry issue. Read it off the bill.",
         status="OPEN", where="Own the tax bill; call Controller-Treasurer Tax Roll Control (408) 808-7979",
         src="SCC-RATEBOOK"),
    dict(id="Q-05", kind="legal", topic="San Francisco eviction exposure",
         q="If the heir later wants Property B's rented units for family use or a sale with vacant "
           "possession, is an owner-move-in eviction even available on this building?",
         why="Only one owner-move-in per building is allowed, the unit is then fixed forever as the "
             "'owner's unit', tenants 60+ with 10 years or a catastrophically ill tenant with 5 years "
             "cannot be moved, and relocation costs are ~$7,912 per tenant plus $5,275 per protected "
             "person. Confirm whether the small-building limits changed after the published page.",
         status="OPEN", where="Rent Ordinance counsel; sf.gov page is the published rule", src="SF-OMI"),
    dict(id="Q-06", kind="fact", topic="Leases in place at Property B",
         q="Copies of both leases, rent roll, security deposits, last rent-increase date and method, "
           "and whether the units were ever declared exempt (new construction / substantial rehab).",
         why="Decides whether rents grow with the market or with the cap, and whether the "
             "60%-of-CPI Rent Board allowance or AB 1482 governs.",
         status="OPEN", where="Property manager file / tenant estoppels", src="SF-NEWCON"),
    dict(id="Q-07", kind="family", topic="Occupancy plan",
         q="Where does the household actually want to live in 2045, and for how many years?",
         why="Every path in this model is really an occupancy decision wearing a tax costume. "
             "If the answer is 'we don't know', the model should be read as a ranking of "
             "reversibility, not of return.",
         status="OPEN", where="Household, in writing, before the numbers are argued", src=None),
    dict(id="Q-08", kind="legal", topic="Trust mechanics",
         q="Does the trust distribute Property A outright, or hold it in a continuing trust? Are there "
           "remaindermen, no-contest terms, or a power to appoint?",
         why="A distribution to the beneficiary is the change in ownership that starts the Prop 19 "
             "1-year clock; a continuing trust can delay it and can also forfeit the exclusion.",
         status="OPEN", where="Estate attorney; read the instrument, not the summary", src="RTC-61"),
    dict(id="Q-09", kind="fact", topic="Estate size vs exclusion",
         q="What is the gross estate (both properties, cash, retirement, insurance) at date of death, "
           "and were there post-1976 taxable gifts?",
         why="Form 706 is due when the gross estate plus adjusted taxable gifts exceeds the basic "
             "exclusion - $15,000,000 for a 2026 death. Cash 'considerably' above that threshold is "
             "the trigger for real planning, not the houses.",
         status="OPEN", where="CPA with the decedent's Form 709 history", src="IRS-ESTATE"),
    dict(id="Q-10", kind="legal", topic="Portability",
         q="Was a portability election made at the first spouse's death (Form 706 Part 6), and is there a DSUE?",
         why="A DSUE can double the shelter for the surviving spouse. It is only available if a "
             "706 was filed on time (or within the 5-year late relief window for non-filing estates).",
         status="OPEN", where="CPA / prior Form 706", src="IRS-ESTATE"),
    dict(id="Q-11", kind="legal", topic="California estate tax",
         q="Confirm with counsel that California imposes no estate or inheritance tax at the decedent's "
           "death in the modelled year.",
         why="This model assumes 'no CA estate tax'. It is a load-bearing assumption and was NOT "
             "confirmed against an official source in this session - it is on the flagged list.",
         status="OPEN", where="CPA; FTB", src=None),
    dict(id="Q-12", kind="fact", topic="Insurance pricing",
         q="Three written quotes for Property A (owner-occupied) and Property B (3-unit landlord policy), "
           "with the dwelling limit, the actual-cash-value vs replacement-cost choice, and the "
           "ordinance-or-law upgrade endorsement specified.",
         why="The household's $1,500/yr guess is used as a placeholder. A $3,000/yr miss is $90,000 over "
             "30 years before inflation, and it lands entirely in the live and rent paths, not the sell path.",
         status="OPEN", where="Independent broker; ask about FAIR Plan as a fallback", src="owner"),
    dict(id="Q-13", kind="fact", topic="Condition of both buildings",
         q="Sewer scope, roof age, panel/battery status, foundation, permitted status of the third unit "
           "at Property B, and a home-inspection-grade capital plan for the next 5 years.",
         why="The unpermitted-unit question can flip Property B's rental math and its insurability. "
             "Capital deferral is the most common way an inherited house loses money.",
         status="OPEN", where="Licensed inspector + SF DBI permit history (public records)", src=None),
    dict(id="Q-14", kind="legal", topic="1031 exchange intent",
         q="Is a like-kind exchange wanted on either sale, and does the heir have investment (not "
           "personal) intent for the replacement property?",
         why="A residence the heir moves into cannot be the replacement property in a 1031 exchange. "
             "Deciding this after the sale is decided is usually too late - the identification windows "
             "are 45 and 180 days.",
         status="OPEN", where="CPA + qualified intermediary, before listing", src="IRS-544"),
    dict(id="Q-15", kind="family", topic="Pre-agreed decision rule",
         q="Sign the criteria page before the projections are circulated: what median-to-median gap, "
           "what downside floor, and what reversibility would make each path acceptable?",
         why="Otherwise the model gets used to justify the answer the household already likes. This is "
             "the point of the framework page.",
         status="OPEN", where="Household; see /framework.html", src=None),
    dict(id="Q-16", kind="fact", topic="Cash and its tax character",
         q="What is in the 'considerable amount of money' - cash, taxable brokerage, IRA/401(k), "
           "annuity, life insurance - and at what basis?",
         why="An inherited IRA does not get a step-up and pays ordinary income tax; a brokerage account "
             "does get a step-up and can be harvested tax-free. Same dollars, completely different plan.",
         status="OPEN", where="CPA; custodian statements (kept offline)", src="IRS-559"),
    dict(id="Q-17", kind="legal", topic="Prop H pass-through",
         q="For Property B: does the new Muni parcel tax limit what can be passed to the two sitting "
           "tenants, and are those tenancies covered by the Rent Ordinance?",
         why="The measure text allows a limited pass-through for rent-controlled units. Getting this "
             "wrong in either direction changes net operating income and creates Rent Board exposure.",
         status="OPEN", where="Rent counsel; Rent Board petition if needed", src="SF-PROP-H"),
    dict(id="Q-18", kind="fact", topic="Solar system ownership and tariff",
         q="Is the Property A solar system owned or leased/PPA? What NEM vintage is it on, and what is "
           "the true-up treatment of excess credits?",
         why="A leased or PPA system is a monthly obligation that survives a sale and can block a buyer; "
             "an owned system on an older tariff is the reason the electric line is a credit, and that "
             "credit does not survive every tariff change.",
         status="OPEN", where="Utility account + contract, kept offline", src="owner"),
    dict(id="Q-19", kind="family", topic="Siblings / co-beneficiaries",
         q="Is Property A split with anyone? If yes: who gets occupancy, who gets rent, how is a buyout "
           "priced, and what happens if one owner wants to sell?",
         why="A partition action, or simply a co-owner who will not sign, is the most common reason an "
             "otherwise good plan earns nothing. It also decides whether 'sell in year one' is even "
             "available.",
         status="OPEN", where="Household + probate counsel", src=None),
    dict(id="Q-20", kind="legal", topic="Creditor, tax-lien and benefit timing",
         q="Any federal tax lien, Medi-Cal estate claim, or judgment that would attach before distribution?",
         why="A Medi-Cal estate claim against the house can consume the equity the whole plan is built on. "
             "It must be known before the model, not after.",
         status="OPEN", where="Estate attorney; state recovery unit", src=None),
]

# ------------------------------------------------------------- suggestions ----
SUGGESTIONS = [
    dict(id="S-01", title="Do not decide 'sell' and 'live' at the same time",
         body="Only 'sell' is irreversible. Live-in for 12-24 months, keep Prop 19 as a live option by "
              "occupying and filing for the homeowners' exemption, and decide the sale later with better "
              "information. The model prices that option: it is path P-04.",
         effort="low", impact="high", risk_if_skipped="You pay the reassessment to learn something you "
                                                      "could have learned for free.",
         status="proposed"),
    dict(id="S-02", title="Treat the 'rent it' option as a floor, not a plan",
         body="Until four closed leases are on the table, every rent-path number in this workspace is the "
              "owner's estimate. Rank the paths again after the comp sheet arrives.",
         effort="low", impact="high", risk_if_skipped="Path ranking driven by a guess.", status="proposed"),
    dict(id="S-03", title="Get the appraisal before the market tells you the price",
         body="A date-of-death appraisal is needed for basis, for the Form 706 (if filed) and for the Prop 19 "
              "excess calculation. Same document, three uses, and it is cheapest to obtain once.",
         effort="low", impact="high", risk_if_skipped="Three different numbers for three different agencies.",
         status="proposed"),
    dict(id="S-04", title="Write the investing policy before the money exists",
         body="Asset allocation, the Treasury parking lane, rebalancing bands, permitted leverage, and the "
              "redeployment calendar - agreed and dated now. See /ips.html.",
         effort="medium", impact="high", risk_if_skipped="Proceeds sit in a bank account for a year, or get "
                                                         "invested in the month of the funeral.", status="proposed"),
    dict(id="S-05", title="Price occupancy explicitly with imputed rent",
         body="Living in Property A is not free and renting it is not pure profit. The imputed-rent line puts "
              "the same dollar on both sides so the paths are compared like-for-like.",
         effort="low", impact="medium", risk_if_skipped="The live path looks 40% better than it is.",
         status="proposed"),
    dict(id="S-06", title="Recheck the law once a year, on a fixed date",
         body="Prop 19's indexed amount re-publishes every other February 16; SF's tax rate is adopted each "
              "summer; parcel taxes change with ballots; the federal exclusion indexes annually. "
              "See /recheck.html and /watch.html.",
         effort="low", impact="medium", risk_if_skipped="Decisions made on expired rules.", status="proposed"),
    dict(id="S-07", title="Distinguish 'enacted' from 'proposed' in every table",
         body="Each rule row carries a status: enacted (with effective date) or proposed (with sponsor and "
              "stage). The Prop H row is the live example: approved by voters on 2026-11-03 but not "
              "certified until 2026-12-03 and not billed until FY 2027-28.",
         effort="low", impact="medium", risk_if_skipped="Modelling a bill as if it were law.", status="done"),
    dict(id="S-08", title="Keep the private numbers out of this repository",
         body="This site publishes rounded, anonymised figures only. Statements, appraisals, leases, "
              "accounts and the APN belong in the offline folder, not in git history - history is forever "
              "and search indexes it.",
         effort="low", impact="high", risk_if_skipped="Permanent, unrecoverable disclosure.", status="done"),
    dict(id="S-09", title="Run the tax sale in the same year as the death",
         body="A sale in the year of death uses the stepped-up basis immediately: little or no gain. This is "
              "modelled as P-06 and it is the cheapest tax outcome in the whole set - which is exactly why "
              "the non-tax reasons have to be argued explicitly rather than assumed away.",
         effort="medium", impact="high", risk_if_skipped="Holding for 20 years converts a tax-free "
                                                          "gain into a taxable one.", status="proposed"),
    dict(id="S-10", title="Add a liquidity floor before any illiquid choice",
         body="Two houses plus a fixed income is a fragile balance sheet. Set the floor (24 months of all "
              "carrying costs plus a capital-events reserve) in the IPS and make the paths satisfy it before "
              "comparing returns.",
         effort="low", impact="high", risk_if_skipped="A forced sale in a bad year.", status="proposed"),
    dict(id="S-11", title="Do not let one projection set the answer",
         body="Compare all paths on ranges, all on the same transfer date and the same horizons, and re-run "
              "annually. If the recommendation flips when a range moves, the honest conclusion is 'not "
              "sensitive enough to decide yet', and the open-questions page says so.",
         effort="medium", impact="high", risk_if_skipped="False precision.", status="proposed"),
    dict(id="S-12", title="Separate the three tax systems in the write-up",
         body="Estate tax (transfer at death), income tax (basis and gain), and property tax (assessment) "
              "have different rules, different deadlines and different authorities. Every table on this site "
              "labels which of the three it is talking about.",
         effort="low", impact="medium", risk_if_skipped="The classic error: assuming a step-up lowers the "
                                                         "property tax bill, or that Prop 19 lowers income tax.",
         status="done"),
]

# ------------------------------------------------------------- flagged list ----
FLAGS = [
    dict(id="F-1", severity="high", item="Property B: tax-to-assessment ratio does not reconcile",
         detail="The household's own 2025 figures for Property B (tax $2,440 on assessed value $114,250) "
                "imply a 2.14% rate. San Francisco's published FY 2026-27 secured rate is 1.18162182%. "
                "A ~2x gap means either (a) the 'tax' line includes non-ad-valorem special assessments or "
                "supplemental/escape amounts, or (b) the assessed value quoted is net of an exemption while "
                "the tax is computed on a different base. Nothing in this model depends on the answer, but "
                "the Property B carrying-cost line does.",
         action="Pull three years of SF bills and the parcel record (Treasurer portal, offline); reconcile "
                "line by line.", srcs=["SF-TTC-RATE"]),
    dict(id="F-2", severity="high", item="Property A: implied rate above the city summaries",
         detail="The household's bills imply 1.30%-1.35% of assessed value for 2014-2025, while the county's "
                "FY 2025-26 compilation shows a 1.00000% maximum levy plus bond lines that sum to roughly "
                "1.04%-1.06% before school-district bonds. The parcel's own tax rate area total was not read "
                "from the rate book in this pass (Section III covers 816 TRAs).",
         action="Read the TRA number off the bill and look it up in the county Tax Rate Book, Section III. "
                 "Model uses 1.334% until then.", srcs=["SCC-RATEBOOK"]),
    dict(id="F-3", severity="medium", item="Homeowners and landlord insurance premium is an owner guess",
         detail="The $1,500/yr figure supplied for both properties was not confirmable from an official "
                "source. Published state-level averages for the 2025 experience year (California "
                "Department of Insurance data call, as reported by secondary sources) are materially higher "
                "for the homeowners market and higher again for FAIR Plan dwelling fire.",
         action="Three written quotes per property; replace the placeholder and re-run. Flagged, not filled in.",
         srcs=[]),
    dict(id="F-4", severity="medium", item="Market rent for Property A is unverified",
         detail="No comparable lease evidence exists yet. The rent paths are therefore reported as a floor, "
                "not a forecast.",
         action="Broker comp sheet for the ZIP, 4 closed leases, 2025-26 rent board/ab1482 status check.",
         srcs=[]),
    dict(id="F-5", severity="medium", item="the city's utility rates not read from an official rate sheet",
         detail="Water $100-$150/month and the solar electricity credit are household-supplied. The City of "
                "The city's current rate resolution was not located and read in this session.",
         action="The city's utility rate sheet; PG&E bill for 12 months of true-up history.", srcs=[]),
    dict(id="F-6", severity="medium", item="'California has no estate tax' was not verified this session",
         detail="The model assumes no California estate or inheritance tax at death. This is a load-bearing "
                "assumption and is stated as unverified rather than asserted as fact.",
         action="CPA confirmation with citation; update row 4 of /tax-rules.html and re-run.", srcs=[]),
    dict(id="F-7", severity="low", item="Prop H certified-result pending",
         detail="Voter-approved 2026-11-03 per preliminary counts (74.4% yes as reported); county "
                "certification due 2026-12-03; first bills FY 2027-28. Treated as 'approved, pending "
                "certification' throughout.",
         action="Confirm certification on 2026-12-04 and replace the flag with the ordinance number.",
         srcs=["SF-PROP-H-MTC"]),
    dict(id="F-8", severity="low", item="Inflation baseline is an assumption, not a source",
         detail="Long-run inflation (1.5%/2.5%/3.8%) drives every nominal series on this site. No official "
                "CPI series was read in this session (FRED CSV endpoints were not reachable from the build "
                "environment).",
         action="Replace with a BLS CPI-U annual-average table read directly, then re-run the sensitivity grid.",
         srcs=[]),
    dict(id="F-9", severity="low", item="Equity and bill-return history is academic, not governmental",
         detail="1928-2025 S&P 500 total returns and 3-month bill returns come from the NYU Stern table. "
                "It is a standard, citable academic source but it is not an official statistic, and the "
                "Black-Swan section depends on it.",
         action="Spot-check 1929-1932 and 2007-2009 against a Federal Reserve or BLS publication before the "
                "IPS is signed.", srcs=["DAMO"]),
    dict(id="F-10", severity="low", item="Documentary transfer tax exemption list for the trust distribution",
         detail="Rev. & Tax. Code 11911 sets the rate; the death/gift non-application is cited by county "
                "recorders to Rev. & Tax. Code 11930. The Santa Clara County ordinance text itself was not "
                "read in this session.",
         action="Escrow/title company to confirm in writing before the deed is recorded.",
         srcs=["RTC-11911"]),
    dict(id="F-11", severity="medium", item="Repo history contained no pre-rounding data",
         detail="At session start this branch held exactly one commit (a 5,900-byte README and one 11-byte "
                "file). There is no earlier public-data exposure inside this repository to scrub, and no "
                "un-rounded figures were ever committed here.",
         action="None possible in-repo. The exposure risk lives in the *other* repository found during "
                "research (see handoff notes) - if that repo is ours, its history must be rebuilt or the "
                "repo deleted; deleting a branch does not delete the objects.", srcs=[]),
    dict(id="F-12", severity="medium", item="Non-ad-valorem charges on Property A modelled as zero",
         detail="The Santa Clara Valley Water District parcel charge and any other direct assessments are "
                "billed on the tax bill but are not value-based, so they are not in the 1% levy or in the "
                "rate book's ad valorem columns. The engine carries $0 for them, which understates A's "
                "carrying cost by roughly the amount the county's own summary and the household's bill "
                "disagree by (see F-2).",
         action="Read the parcel charge schedule at scvwd.gov and the 'Special Assessments' lines on the "
                "actual bill; enter the flat amount in inputs.py as a separate line, not inside the rate.",
         srcs=["SCVWD-MEASURES"]),
    dict(id="F-13", severity="medium", item="Passive-loss treatment assumed, not advised",
         detail="Rental losses are modelled as suspended (not deductible against salary) and the real "
                "estate professional exception as unavailable. Both are likely at this income level, but "
                "the phase-out runs from $100,000 to $150,000 of modified AGI and the household's actual "
                "position is unknown. If losses were deductible, the rent paths improve materially.",
         action="CPA to confirm in writing; then re-run with the toggle on the what-if page.", srcs=[]),
]
