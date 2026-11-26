"""
model/params.py — every input the model uses, with its provenance and status.

PRIVACY: values here are the ROUNDED, PUBLISHED values from data/facts.json.
Exact household figures are never placed in this file. See PRIVACY.md.

STATUS LEGEND
  verified    checked against an official source in this repo's research session
  secondary   official-ish but not fetched directly; flagged on the site
  unverified  household estimate or heuristic; flagged on the site
  assumption  a modelling choice, not a fact

Every parameter carries `source` = a fact id in data/facts.json, or None for a
pure modelling assumption.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Param:
    key: str
    value: object
    unit: str
    status: str
    source: Optional[str]
    note: str = ""


# ----------------------------------------------------------------------------
# Horizon
# ----------------------------------------------------------------------------
START_YEAR = 2026
END_YEAR = 2076          # 50-year horizon; the household asked for 50-year realism
BASE_YEAR = START_YEAR

# The trust is expected to distribute between 2040 and 2050. Model all three
# points so the decision is not hostage to one projected transfer date.
TRANSFER_YEARS = (2040, 2045, 2050)
BASE_TRANSFER_YEAR = 2045

# ----------------------------------------------------------------------------
# Property A (inherited)
# ----------------------------------------------------------------------------
A_VALUE_2026 = 3_100_000
A_VALUE_STATUS = "unverified"
A_VALUE_SOURCE = "HH-PROPERTY-A-VALUE"

# Factored base year value, banded for privacy (facts.json HH-PROPERTY-A-ASSESSED)
A_ASSESSED_2026_LOW = 545_000
A_ASSESSED_2026_HIGH = 560_000

# Effective tax rate = total bill / assessed value. Derived from the household's
# own 13-year series: roughly 1.2%-1.4%. Includes the 1% Prop 13 base plus
# voter-approved debt and fixed charges.
A_TAX_RATE_LOW = 0.0120
A_TAX_RATE_HIGH = 0.0140
A_TAX_RATE_BASE = 0.0130

A_PROP13_CAP = 0.02          # verified, CA-PROP13-CAP

# Market rent for a ~2,000 sq ft SFR in [ZIP-A]. Household did not supply one.
# Rangewide estimate from a gross-yield band rather than a voucher benchmark.
A_RENT_YIELD_LOW = 0.0230    # 2.3% gross yield  -> ~$5,940/mo on $3.1M
A_RENT_YIELD_BASE = 0.0290   # 2.9% gross yield  -> ~$7,490/mo
A_RENT_YIELD_HIGH = 0.0360   # 3.6% gross yield  -> ~$9,300/mo
A_RENT_STATUS = "unverified"
A_RENT_NOTE = ("No comparables obtained. Expressed as a gross-yield band so the rent path is "
               "ranked on a range rather than on the Section 8 payment standard, which the "
               "household correctly objected to. Get real [ZIP-A] SFR comps.")

# Operating cost bands (annual, 2026 dollars). All unverified household/heuristic.
A_INSURANCE_LOW = 1_500
A_INSURANCE_BASE = 3_000
A_INSURANCE_HIGH = 4_500
# MAINTENANCE IS A PERCENTAGE OF BUILDING VALUE, NOT OF MARKET VALUE.
# This is a deliberate correction to a bug in the first version of this model.
# Property A market value is roughly 75% land; land requires no roof, no sewer
# lateral and no paint. Tying maintenance to market value made the modelled cost
# compound at the house-price rate for fifty years and buried every holding path
# in year 30. Maintenance scales with *replacement cost of the structure*, which
# tracks construction costs (CPI + a spread), not land prices.
A_LAND_SHARE_2026 = 0.75
A_MAINT_LOW = 0.0125         # of BUILDING value, per year
A_MAINT_BASE = 0.0200
A_MAINT_HIGH = 0.0300
A_CONSTRUCTION_INFLATION_SPREAD = 0.010   # construction costs outrun CPI by ~1%/yr
A_WATER_LOW = 100 * 12
A_WATER_HIGH = 150 * 12
A_ELECTRIC_NET_LOW = -20 * 12     # net credit
A_ELECTRIC_NET_HIGH = -10 * 12

# Selling costs
SELL_COMMISSION = 0.050      # assumption; negotiable, and NAR settlement changed
                             # buyer-broker compensation disclosure in 2024
SELL_OTHER_COSTS = 0.010     # escrow, title, transfer tax, recording, staging

# ----------------------------------------------------------------------------
# Property B — San Francisco (already owned)
# ----------------------------------------------------------------------------
B_VALUE_2026 = 1_800_000
B_VALUE_STATUS = "unverified"
B_ASSESSED_LOW = 110_000
B_ASSESSED_HIGH = 120_000
B_TAX_RATE_LOW = 0.0190      # flagged: household series implies ~2.1%
B_TAX_RATE_HIGH = 0.0225
B_TAX_RATE_BASE = 0.0205

B_RENT_MONTHLY = 7_150
B_UNITS = 3
B_UNITS_RENTED = 2

B_WATER_LOW = 330 * 12
B_WATER_HIGH = 400 * 12
B_ELECTRIC_LOW = 30 * 12
B_ELECTRIC_HIGH = 70 * 12

B_INSURANCE_LOW = 1_500
B_INSURANCE_BASE = 3_800
B_INSURANCE_HIGH = 6_500
# Same correction as Property A: maintenance is a share of BUILDING value.
# A 3-unit pre-war Property B's neighbourhood building carries more maintenance per building
# dollar than a single-family house: three kitchens, three baths, shared systems,
# and tenants who cannot be told no. Banded higher for that reason.
B_LAND_SHARE_2026 = 0.60
B_MAINT_LOW = 0.0125
B_MAINT_BASE = 0.0200
B_MAINT_HIGH = 0.0300

# SF rent control: the allowable annual increase is a CAP, not a forecast.
B_RENT_GROWTH_LOW = 0.020
B_RENT_GROWTH_HIGH = 0.035

# ----------------------------------------------------------------------------
# Macro scenarios (nominal, annual)
# ----------------------------------------------------------------------------
# Each is a named regime with a value for: CPI, house-price growth, equity
# total return, Treasury (3M) yield, and a flag for whether a crash happens.
MACRO = {
    "base": {
        "label": "Long-run base case",
        "cpi": 0.025,
        "house": 0.035,
        "equity": 0.065,
        "cash": 0.040,
        "note": "Deliberately below the post-1980 U.S. averages. Growth and inflation are never "
                "consistent over 50 years, so the base case is set conservatively and every "
                "other scenario is a deviation from it.",
    },
    "stagflation": {
        "label": "1970s stagflation repeat",
        "cpi": 0.055,
        "house": 0.045,
        "equity": 0.035,
        "cash": 0.065,
        "note": "Stocks lose in real terms while nominal house prices rise and cash yields high. "
                "This regime favours the property paths and punishes the sell-and-invest path.",
    },
    "japan": {
        "label": "Balance-sheet recession / Japanification",
        "cpi": 0.012,
        "house": 0.012,
        "equity": 0.035,
        "cash": 0.015,
        "note": "Low growth, low inflation, low returns everywhere. Favours holding; punishes "
                "nothing much. This is the scenario where the decision is nearly a wash.",
    },
    "household-productivity": {
        "label": "Bay Area productivity boom",
        "cpi": 0.030,
        "house": 0.055,
        "equity": 0.080,
        "cash": 0.040,
        "note": "Both assets do well; the property wins because it is levered by Prop 13 "
                "rather than by a mortgage.",
    },
    "tech-bust": {
        "label": "Regional tech contraction",
        "cpi": 0.020,
        "house": 0.015,
        "equity": 0.050,
        "cash": 0.035,
        "note": "Property A is a single-industry town. A durable regional contraction hits the "
                "house directly and the stock market only partly. This is the scenario the "
                "concentration risk lives in.",
    },
}

# ----------------------------------------------------------------------------
# Black-swan crash overlays (user's explicit request)
# ----------------------------------------------------------------------------
# Each overlay: a crash begins `years_after_transfer` and unfolds over
# `duration` years with the given cumulative drawdowns, then recovers.
CRASHES = {
    "none": {
        "label": "No crash",
        "years_after_transfer": None,
        "equity_dd": 0.0,
        "house_dd": 0.0,
        "cpi_shock": 0.0,
        "recover_years": 0,
        "source": "— (the control case; the baseline the household has not been shown)",
    },
    "1929": {
        "label": "1929-style: 43-month deflationary collapse",
        "years_after_transfer": 1,
        "duration": 4,
        "equity_dd": 0.89,       # Dow peak Sep 1929 -> trough Jul 1932 ~ -89%
        "house_dd": 0.30,        # nominal house prices fell far less than stocks
        "cpi_shock": -0.07,      # deflation, peak annual
        "recover_years": 25,     # Dow did not regain 1929 nominal peak until 1954
        "source": "FED-NBER-CYCLES; drawdown magnitudes are the standard historical record "
                  "and are published here as MODELLING INPUTS, flagged as not individually "
                  "re-verified from a primary statistical release in this session.",
    },
    "2008": {
        "label": "2008-style: 18-month financial crisis",
        "years_after_transfer": 1,
        "duration": 2,
        "equity_dd": 0.57,       # S&P 500 Oct 2007 -> Mar 2009 ~ -57%
        "house_dd": 0.27,        # Case-Shiller national ~ -27%
        "cpi_shock": -0.02,
        "recover_years": 5,      # nominal S&P regained 2007 peak in 2013
        "source": "FED-NBER-CYCLES (Dec 2007 - Jun 2009); magnitudes as above.",
    },
    "1973": {
        "label": "1973-style: oil shock with high inflation",
        "years_after_transfer": 1,
        "duration": 2,
        "equity_dd": 0.45,
        "house_dd": 0.05,
        "cpi_shock": 0.06,       # inflation ACCELERATES
        "recover_years": 8,
        "source": "FED-NBER-CYCLES (Nov 1973 - Mar 1975). Included because a crash with "
                  "rising inflation behaves nothing like 1929 or 2008.",
    },
    "2000": {
        "label": "2000-style: slow three-year grind",
        "years_after_transfer": 1,
        "duration": 3,
        "equity_dd": 0.49,
        "house_dd": 0.0,         # housing kept rising through 2001-2005
        "cpi_shock": 0.0,
        "recover_years": 7,
        "source": "FED-NBER-CYCLES (Mar 2001 - Nov 2001 recession; the equity bear market ran "
                  "2000-2002). Included as the 'crash that is not a housing crash'.",
    },
    "2022": {
        "label": "2022-style: stocks and bonds fall together",
        "years_after_transfer": 1,
        "duration": 1,
        "equity_dd": 0.25,
        "house_dd": 0.10,
        "cpi_shock": 0.08,
        "recover_years": 3,
        "source": "Included specifically to test the phased-investing path, because this is the "
                  "scenario in which Treasuries do NOT protect you: both legs fall at once.",
    },
}

# ----------------------------------------------------------------------------
# Tax parameters
# ----------------------------------------------------------------------------
FED_ESTATE_EXCLUSION_2026 = 15_000_000     # verified FED-ESTATE-EXCLUSION-2026
FED_ESTATE_EXCLUSION_GROWTH = 0.025        # assumption: indexed for inflation
FED_ESTATE_RATE = 0.40                     # verified FED-ESTATE-RATE
FED_TOP_LTCG = 0.20                        # verified FED-LTCG-RATES-2025
FED_NIIT = 0.038                           # verified FED-NIIT-RATE
FED_UNRECAPTURED_1250 = 0.25               # verified FED-1250-UNRECAPTURED-25
FED_S121_SINGLE = 250_000                  # verified FED-S121-EXCLUSION
FED_S121_JOINT = 500_000
FED_DEPR_LIFE = 27.5                       # verified FED-DEPRECIATION-27.5

CA_TOP_MARGINAL = 0.123                    # verified CA-FTB-TOP-MARGINAL (FTB 2025 schedule, read 2026-11-26)
CA_BHST = 0.01                             # verified CA-FTB-MHST-THRESHOLD
CA_BHST_THRESHOLD = 1_000_000              # verified, NOT indexed, same for MFJ
CA_EFFECTIVE_ON_LARGE_GAIN = 0.105         # RETIRED as default (2026-11-26). Unsourced blend. Kept only as an explicit flat override.

# Official 2025 California tax rate schedules (FTB, 2025-540-tax-rate-schedules.pdf),
# as (lower bound of bracket, tax at lower bound, marginal rate above it).
# Verified 2026-11-26. Schedule X = single / MFS; Y = MFJ / RDP / QSS; Z = head of household.
CA_SCHEDULES = {
    "single": [(0, 0.00, .01), (11079, 110.79, .02), (26264, 414.49, .04), (41452, 1022.01, .06),
               (57542, 1987.41, .08), (72724, 3201.97, .093), (371479, 30986.19, .103),
               (445771, 38638.27, .113), (742953, 72219.84, .123)],
    "joint":  [(0, 0.00, .01), (22158, 221.58, .02), (52528, 828.98, .04), (82904, 2044.02, .06),
               (115084, 3974.82, .08), (145448, 6403.94, .093), (742958, 61972.37, .103),
               (891542, 77276.52, .113), (1485906, 144439.65, .123)],
    "hoh":    [(0, 0.00, .01), (22173, 221.73, .02), (52530, 828.87, .04), (67716, 1436.31, .06),
               (83805, 2401.65, .08), (98990, 3616.45, .093), (505208, 41394.72, .103),
               (606251, 51802.15, .113), (1010417, 97472.91, .123)],
}
CA_DEFAULT_STATUS = "joint"                # household filing status is NOT supplied; see Q-CA-STATUS
CA_OTHER_TAXABLE_INCOME = 0.0              # other taxable income in the sale year; NOT supplied

A_LAND_SHARE = A_LAND_SHARE_2026            # assumption: Property A land is most of the value

# ----------------------------------------------------------------------------
# Phased investing (the feature the household asked for)
# ----------------------------------------------------------------------------
PARK_YIELD_FALLBACK = 0.045                # verified FED-TREASURY-YIELDS (1-2y ~4.6%)
PARK_MAX_YEARS = 3                         # 24-36 months in 3M-2Y Treasuries
PARK_MIN_YEARS = 2
DCA_MONTHS = 36                            # phase into equities over 36 months

# ----------------------------------------------------------------------------
# Household composition for estate-tax math
# ----------------------------------------------------------------------------
ESTATE_OTHER_ASSETS_LOW = 1_900_000        # Property B plus cash, if A were sold
ESTATE_OTHER_ASSETS_BASE = 2_500_000
ESTATE_OTHER_ASSETS_HIGH = 6_000_000       # "a considerable amount of money"

INVESTMENT_POLICY_MIN_CASH_YEARS = 2.0     # years of household spending held in cash


def macro(name):
    return MACRO[name]


def crash(name):
    return CRASHES[name]
