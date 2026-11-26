#!/usr/bin/env python3
"""
TinoDash4 decision model generator — session arena-65b70013.
Generates every JSON consumed by the static site under site/data/.

PRIVACY: every dollar figure written to JSON is rounded to the nearest $10.
No names, addresses, APNs, or account identifiers are emitted.

VERIFICATION RULE: values from official sources carry a source id (see SOURCES).
Household-provided values are marked unverified. Model assumptions carry an
"assumption" flag. Nothing is invented: unverified table cells are null.
"""
import json, math, random, statistics, os, datetime

OUT = os.path.join(os.path.dirname(__file__), "..", "site", "data")
os.makedirs(OUT, exist_ok=True)
TODAY = "2026-11-25"

def r10(x):
    """Round to nearest $10 (privacy rule). None passes through."""
    if x is None: return None
    return int(round(x / 10.0) * 10)

def pct(x, nd=2):
    return round(x * 100, nd)

# ----------------------------------------------------------------------------
# 1. SOURCE REGISTRY
# ----------------------------------------------------------------------------
SOURCES = {
  # Federal
  "irs-rp2532": {"t": "IRS Rev. Proc. 2025-32 (2026 inflation adjustments; $15M basic exclusion; LTCG brackets)", "u": "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf", "o": "Internal Revenue Service", "k": "gov", "v": TODAY},
  "irs-obbb": {"t": "IRS — One, Big, Beautiful Bill provisions (PL 119-21)", "u": "https://www.irs.gov/newsroom/one-big-beautiful-bill-provisions-individuals-and-workers", "o": "Internal Revenue Service", "k": "gov", "v": TODAY},
  "irs-706": {"t": "IRS Instructions for Form 706 (07/2026) — $15M, 9-month due date", "u": "https://www.irs.gov/instructions/i706", "o": "Internal Revenue Service", "k": "gov", "v": TODAY},
  "irs-estgift": {"t": "IRS — What's new: Estate and gift tax (portability, DSUE)", "u": "https://www.irs.gov/businesses/small-businesses-self-employed/whats-new-estate-and-gift-tax", "o": "Internal Revenue Service", "k": "gov", "v": TODAY},
  "irs-p523": {"t": "IRS Publication 523 — Selling Your Home (step-up basis, §121)", "u": "https://www.irs.gov/publications/p523", "o": "Internal Revenue Service", "k": "gov", "v": TODAY},
  "irs-1040d": {"t": "IRS Instructions for Schedule D / Capital Gains", "u": "https://www.irs.gov/instructions/i1040sd", "o": "Internal Revenue Service", "k": "gov", "v": None},
  "irs-i8960": {"t": "IRS Instructions for Form 8960 (3.8% NIIT, IRC §1411)", "u": "https://www.irs.gov/instructions/i8960", "o": "Internal Revenue Service", "k": "gov", "v": None},
  "usc-121": {"t": "26 U.S.C. §121 (incl. (d)(11) inherited-home rule) — OLRC", "u": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section121", "o": "Office of the Law Revision Counsel", "k": "gov", "v": None},
  "irs-p544": {"t": "IRS Publication 544 — Sales and Other Dispositions (recapture)", "u": "https://www.irs.gov/publications/p544", "o": "Internal Revenue Service", "k": "gov", "v": None},
  "congress-hr601": {"t": "H.R.601 — Estate Tax Rate Reduction Act (119th Congress, in committee)", "u": "https://www.congress.gov/bill/119th-congress/house-bill/601", "o": "Congress.gov", "k": "gov", "v": TODAY},
  # California
  "boe-prop19": {"t": "California BOE — Proposition 19 (value cap, filing windows, $1,044,586)", "u": "https://www.boe.ca.gov/prop19/", "o": "CA State Board of Equalization", "k": "gov", "v": TODAY},
  "boe-lta25009": {"t": "BOE Letter to Assessors 2025/009 — $1M amount adjustment", "u": "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf", "o": "CA State Board of Equalization", "k": "gov", "v": TODAY},
  "leginfo-13302": {"t": "R&T Code §13302 — CA estate tax keyed to federal credit (collects $0)", "u": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=13302", "o": "CA Legislative Information", "k": "gov", "v": TODAY},
  "leginfo-aca11": {"t": "ACA 11 (Proposition 19 text)", "u": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=201920200ACA11", "o": "CA Legislative Information", "k": "gov", "v": None},
  "ftb-capgain": {"t": "FTB — Capital gains and losses (CA taxes gains as ordinary income)", "u": "https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html", "o": "CA Franchise Tax Board", "k": "gov", "v": TODAY},
  "ftb-540i": {"t": "FTB 2025 Instructions for Form 540 — line 62: 1% over $1,000,000", "u": "https://www.ftb.ca.gov/forms/2025/2025-540-instructions.html", "o": "CA Franchise Tax Board", "k": "gov", "v": TODAY},
  "ftb-taxnews26": {"t": "FTB Tax News March 2026 — Behavioral Health Services Act rename; OBBBA non-conformity", "u": "https://www.ftb.ca.gov/about-ftb/newsroom/tax-news/2026/03.html", "o": "CA Franchise Tax Board", "k": "gov", "v": TODAY},
  "ftb-fedchanges": {"t": "FTB — Summary of Federal Income Tax Changes (capital-gain conformity)", "u": "https://www.ftb.ca.gov/about-ftb/data-reports-plans/summary-of-federal-income-tax-changes/index.html", "o": "CA Franchise Tax Board", "k": "gov", "v": TODAY},
  "sf-ab1482": {"t": "SF.gov — California Tenant Protection Act (AB 1482), SF rate 8.8% (Aug 2026–Jul 2027)", "u": "https://www.sf.gov/reports--california-tenant-protection-act-2019-ab-1482", "o": "City & County of San Francisco", "k": "gov", "v": TODAY},
  "ag-init250035": {"t": "CA Attorney General Title & Summary — Initiative 25-0035 (60+ property tax exemption)", "u": "https://oag.ca.gov/system/files/initiatives/pdfs/Title%20and%20Summary%20(25-0035).pdf", "o": "CA Attorney General", "k": "gov", "v": TODAY},
  # Santa Clara County (Property A)
  "scc-recorder": {"t": "SCC Clerk-Recorder — recording fees & transfer tax ($0.55/$500; city tax only SJ/PA/MV)", "u": "https://clerkrecorder.santaclaracounty.gov/recording-documents/recording-document-fees/record-fees", "o": "Santa Clara County", "k": "gov", "v": TODAY},
  "scc-assessor": {"t": "SCC Assessor — 2026 Assessment Information Booklet (800+ TRAs; typical 1.1488%; $7,000 exemption)", "u": "https://files.santaclaracounty.gov/exjcpb1521/2026-04/assessment-information-2026-booklet-english-3-23-26-web.pdf", "o": "Santa Clara County Assessor", "k": "gov", "v": TODAY},
  "scc-aab": {"t": "SCC Assessment Appeals Board — July 2–Sept 15 window (BOE-305-AH)", "u": "https://www.santaclaracounty.gov/your-government/departments/assessor", "o": "Santa Clara County", "k": "gov", "v": None},
  "csd-ord135": {"t": "Special district (Property A) Ordinance 135 — sewer rates FY2025-26 ($802/yr SFR)", "u": "https://cupertinosanitarydistrict.org/i/u/10207194/f/Agendas/2025-05-21_Agenda_Packet.pdf", "o": "Special district (Property A)", "k": "gov", "v": TODAY},
  # San Francisco
  "sf-treasurer": {"t": "SF Treasurer & Tax Collector — secured property tax rate FY2026-27: 1.18162182%", "u": "https://sftreasurer.org/property/secured-property-taxes", "o": "City & County of San Francisco", "k": "gov", "v": TODAY},
  "sf-recorder": {"t": "SF Assessor-Recorder — recording fees & transfer-tax rate table (Art. 12-C)", "u": "https://www.sf.gov/reports--march-2024--fees-record-document-san-francisco", "o": "City & County of San Francisco", "k": "gov", "v": TODAY},
  "sf-proph-text": {"t": "SF Prop H official legal text — Stronger Muni For All Ordinance (§§1804–1806)", "u": "https://media.api.sf.gov/documents/Legal_Text_3X0F1JU.pdf", "o": "City & County of San Francisco", "k": "gov", "v": TODAY},
  "sf-vip": {"t": "SF Voter Information Pamphlet, Nov 3 2026 — Prop H summary ($129/$249/$799, 15 yrs, CPI)", "u": "https://media.api.sf.gov/documents/N26_EN_VIP.pdf", "o": "City & County of San Francisco", "k": "gov", "v": TODAY},
  "sf-results": {"t": "SF election results Nov 3 2026 (pre-certification; cert. due Dec 3 2026)", "u": "https://www.sf.gov/past-election-results", "o": "SF Dept. of Elections (index) / press tallies", "k": "media", "v": TODAY},
  "sfpuc-rates": {"t": "SFPUC rate schedules FY2026-27 (water W-1A, sewer Sch. A, stormwater)", "u": "https://www.sfpuc.gov/sites/default/files/accounts-and-services/Rates_Schedule_Water_Sewer_2026-7.pdf", "o": "San Francisco PUC", "k": "gov", "v": TODAY},
  "sfrb": {"t": "SF Rent Board — Rent Ordinance allowable annual increase (Mar 2026–Feb 2027: 1.6%)", "u": "https://sfrb.org/", "o": "SF Rent Board", "k": "gov", "v": None},
  # Market / macro
  "damodaran": {"t": "Damodaran (NYU Stern) — Historical annual returns, stocks/bonds/bills 1928–2025 (academic)", "u": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html", "o": "NYU Stern (academic)", "k": "academic", "v": TODAY},
  "bls-cpi": {"t": "BLS Monthly Labor Review — inflation 1979 11.3%, 1980 13.5%, 1981 10.3%", "u": "https://www.bls.gov/opub/mlr/2016/article/the-monthly-labor-review-at-100-part-iii.htm", "o": "Bureau of Labor Statistics", "k": "gov", "v": TODAY},
  "nber": {"t": "NBER Business Cycle Dating Committee — U.S. recession chronology", "u": "https://www.nber.org/research/business-cycle-dating", "o": "NBER", "k": "academic", "v": TODAY},
  "fred-cpi": {"t": "FRED CPIAUCSL — Consumer Price Index (all urban consumers)", "u": "https://fred.stlouisfed.org/series/CPIAUCSL", "o": "Federal Reserve Bank of St. Louis", "k": "gov", "v": None},
  "fhfa-hpi": {"t": "FHFA House Price Index — California (2025Q4: 1-yr −0.83%, 5-yr +28.88%)", "u": "https://www.fhfa.gov/document/d/hpi/fhfa-house-price-index-report-2025q4", "o": "FHFA", "k": "gov", "v": TODAY},
  "hud-fmr": {"t": "HUD FY2026 Fair Market Rents — San Francisco County 2-BR $3,604 (voucher floor only)", "u": "https://www.huduser.gov/portal/datasets/fmr.html", "o": "U.S. HUD", "k": "gov", "v": None},
  "cdi-report": {"t": "CA Dept. of Insurance — Residential Property Insurance Report (ZIP-level, 2018–2023)", "u": "https://www.insurance.ca.gov/0400-news/0200-studies-reports/0250-homeowners-study/", "o": "CA Department of Insurance", "k": "gov", "v": TODAY},
  "cpuc-nbt": {"t": "CPUC Decision D.22-12-056 — Net Billing Tariff (NEM 3.0), eff. 2023-04-15", "u": "https://docs.cpuc.ca.gov/", "o": "CA Public Utilities Commission", "k": "gov", "v": None},
  # Household
  "household": {"t": "Household-provided figures (rounded to $10) — not independently verified", "u": None, "o": "Household", "k": "household", "v": TODAY},
  "repo-public": {"t": "GitHub repository metadata — visibility and Pages publication state", "u": "https://api.github.com/repos/kanlerxz87-cyber/TinoDash4", "o": "GitHub REST API", "k": "official", "v": "2026-11-26"},
}

# ----------------------------------------------------------------------------
# 2. VERIFIED ANNUAL RETURNS (Damodaran, fetched 2026-11-25)
# ----------------------------------------------------------------------------
RET = {  # year: (S&P500 total return %, 3-month T-bill %)
1928:(43.81,3.08),1929:(-8.30,3.16),1930:(-25.12,4.55),1931:(-43.84,2.31),1932:(-8.64,1.07),
1933:(49.98,0.96),1934:(-1.19,0.28),1935:(46.74,0.17),1936:(31.94,0.17),1937:(-35.34,0.28),
1938:(29.28,0.07),1939:(-1.10,0.05),1940:(-10.67,0.04),1941:(-12.77,0.13),1942:(19.17,0.34),
1943:(25.06,0.38),1944:(19.03,0.38),1945:(35.82,0.38),1946:(-8.43,0.38),1947:(5.20,0.60),
1948:(5.70,1.05),1949:(18.30,1.12),1950:(30.81,1.20),1951:(23.68,1.52),1952:(18.15,1.72),
1953:(-1.21,1.89),1954:(52.56,0.94),1955:(32.60,1.72),1956:(7.44,2.62),1957:(-10.46,3.22),
1958:(43.72,1.77),1959:(12.06,3.39),1960:(0.34,2.87),1961:(26.64,2.35),1962:(-8.81,2.77),
1963:(22.61,3.16),1964:(16.42,3.55),1965:(12.40,3.95),1966:(-9.97,4.86),1967:(23.80,4.29),
1968:(10.81,5.34),1969:(-8.24,6.67),1970:(3.56,6.39),1971:(14.22,4.33),1972:(18.76,4.06),
1973:(-14.31,7.04),1974:(-25.90,7.85),1975:(37.00,5.79),1976:(23.83,4.98),1977:(-6.98,5.26),
1978:(6.51,7.18),1979:(18.52,10.05),1980:(31.74,11.39),1981:(-4.70,14.04),1982:(20.42,11.09),
1983:(22.34,8.95),1984:(6.15,9.92),1985:(31.24,7.72),1986:(18.49,6.15),1987:(5.81,5.96),
1988:(16.54,6.89),1989:(31.48,8.39),1990:(-3.06,7.75),1991:(30.23,5.54),1992:(7.49,3.51),
1993:(9.97,3.07),1994:(1.33,4.37),1995:(37.20,5.66),1996:(22.68,5.15),1997:(33.10,5.20),
1998:(28.34,4.91),1999:(20.89,4.78),2000:(-9.03,6.00),2001:(-11.85,3.48),2002:(-21.97,1.64),
2003:(28.36,1.03),2004:(10.74,1.40),2005:(4.83,3.22),2006:(15.61,4.85),2007:(5.48,4.48),
2008:(-36.55,1.40),2009:(25.94,0.15),2010:(14.82,0.14),2011:(2.10,0.05),2012:(15.89,0.09),
2013:(32.15,0.06),2014:(13.52,0.03),2015:(1.38,0.05),2016:(11.77,0.32),2017:(21.61,0.95),
2018:(-4.23,1.97),2019:(31.21,2.11),2020:(18.02,0.36),2021:(28.47,0.04),2022:(-18.04,2.09),
2023:(26.06,5.28),2024:(24.88,5.18),2025:(17.78,4.21),
}
stocks = [v[0]/100 for v in RET.values()]
bills  = [v[1]/100 for v in RET.values()]
STOCK_MEAN = statistics.mean(stocks)          # arithmetic, 1928-2025
STOCK_SD   = statistics.pstdev(stocks)
BILL_MEAN  = statistics.mean(bills)

# ----------------------------------------------------------------------------
# 3. INPUTS (all $ rounded to $10)
# ----------------------------------------------------------------------------
IN_YEARS   = [2040, 2045, 2050]          # inheritance windows (household plan)
BASE_YEAR  = 2026
A_VALUE_2026 = r10(3_100_000)            # household estimate Nov 2026
B_VALUE_2026 = r10(1_800_000)
A_AV_2026    = r10(550_540)              # household 2026 assessment (2026 bill pending; +2% of 539,740)
B_AV_2025    = r10(114_250)
B_TAX_2025   = r10(2_440)
A_TAX_2025   = r10(7_210)
A_RATE_IMPL  = 7207 / 539743             # implied all-in from household bill (flagged)
B_RATE_IMPL  = 2439 / 114248
SF_RATE_2627 = 0.0118162182              # official
SC_TYPICAL   = 0.011488                  # official typical TRA example (booklet)

# ranges (model assumptions — flagged in assumptions register)
HOME_G = {"low": 0.010, "base": 0.035, "high": 0.055}   # calibrated on FHFA CA history
STOCK_G= {"low": 0.060, "base": 0.085, "high": 0.120}   # forward-looking; historical arith. mean reported separately
INFL   = {"low": 0.015, "base": 0.025, "high": 0.045}
BILL_G = {"low": 0.015, "base": 0.025, "high": 0.040}    # treasury park yield assumption

A_INS_2026  = r10(1500)     # household guess (flagged; CA DOI statewide averages higher)
B_INS_2026  = r10(1500)
A_WATER_MO  = r10(125)      # household range 100-150 midpoint
B_WATER_MO  = r10(365)      # household range 330-400 midpoint
A_ELEC_MO   = r10(-15)      # household: solar generates +10..20 credit → net -15
B_ELEC_MO   = r10(50)       # household range 30-70 midpoint
A_SEWER_YR  = r10(802.14)   # official CSD FY25-26
B_RENT_MO   = r10(7150)     # household: 2 units
PROP_H_MF   = r10(249)      # official Prop H multifamily floor (≤5,000 sqft)
PROP_H_SFR  = r10(129)
A_MAINT_PCT = 0.0075        # assumption (flag): % of market value/yr
B_MAINT_PCT = 0.0100        # assumption (flag): user says B costs more
A_RENT_FLOOR_MO = r10(3604) # HUD FY2026 SF County 2-BR FMR — FLOOR ONLY, not comps
PROP19_CAP_2026 = 1_044_586 # official for transfers 2026-02-16..2027-02-15 (odd $ — display rounds)
XFER_SC     = 0.0011        # official: $0.55/$500 = 0.11%
RECORD_FEE  = r10(110)      # official SCC recording bundle for a deed (25+3+10+10+75→~113; use 110)
SELL_COST_PCT = 0.055       # assumption (flag): broker/negotiated selling costs
MGMT_PCT    = 0.08          # assumption (flag): property management on rented A
DEPRECIABLE_SHARE = 0.65    # assumption (flag): improvements share for depreciation
SEC_121_MFJ = r10(500_000)
BEA_2026    = r10(15_000_000)
ESTATE_RATE = 0.40
CA_ORD_TOP  = 0.123
CA_BHST     = 0.01          # Form 540 line 62: 1% over $1,000,000 (verified)
CA_TOP_ALLIN= CA_ORD_TOP + CA_BHST   # 13.3% on income above $1M (stacking simplified — flagged)
FED_LTCG_TOP= 0.20
NIIT        = 0.038
HORIZONS    = [10, 20, 30]

# ----------------------------------------------------------------------------
# 4. HELPERS
# ----------------------------------------------------------------------------
def av_path(av0, years):  # Prop 13 factored growth 2%/yr
    return [av0 * (1.02 ** t) for t in years]

def fmv_path(v0, g, years):
    return [v0 * ((1 + g) ** t) for t in years]

def prop19_taxable(fmv, av, cap):
    # BOE rule: taxable = FBYV + excess above (FBYV + cap)  == max(av, fmv - cap)
    return max(av, fmv - cap)

def portfolio_path2(net0, stock_g, bill_g, park_months, phase_months, years_n):
    """Clean implementation: money in bills until scheduled move; stocks grow with stock_g;
    bills grow with bill_g; tranches move at year-start (integer) or mid-year (half return)."""
    if park_months <= 0:
        bal_s, bal_b = float(net0), 0.0
        sched = []
    else:
        bal_s, bal_b = 0.0, float(net0)
        park_y = park_months / 12.0
        phase_y = max(phase_months / 12.0, 1e-9)
        n_tr = max(int(round(phase_y * 2)), 1)
        sched = [(round(park_y + i * phase_y / n_tr, 2), 1.0 / n_tr) for i in range(n_tr)]
    vals = []
    for t in range(years_n):
        # moves at start of year t
        for w, frac in sched:
            if abs(w - t) < 1e-9:
                mv = net0 * frac
                if bal_b >= mv - 1e-6:
                    bal_b -= mv; bal_s += mv
        mid_mv = 0.0
        for w, frac in sched:
            if abs(w - (t + 0.5)) < 1e-9:
                mv = net0 * frac
                if bal_b >= mv - 1e-6:
                    bal_b -= mv; bal_s += mv; mid_mv += mv
        # grow
        bal_s *= (1 + stock_g)
        bal_b *= (1 + bill_g)
        bal_s += mid_mv * stock_g * 0.5          # mid-year tranche earns half year
        vals.append(bal_s + bal_b)
    return vals

def hist_portfolio(start_year, net0, park_months, phase_months, horizon):
    """Backtest with actual annual returns from Damodaran series."""
    bal_s, bal_b = 0.0, float(net0)
    if park_months <= 0:
        bal_s, bal_b = float(net0), 0.0
        sched = []
    else:
        park_y = park_months / 12.0
        phase_y = max(phase_months / 12.0, 1e-9)
        n_tr = max(int(round(phase_y * 2)), 1)
        sched = [(round(park_y + i * phase_y / n_tr, 2), 1.0 / n_tr) for i in range(n_tr)]
    vals, dds, peak = [], [], float(net0)
    for t in range(horizon):
        yr = start_year + t
        if yr not in RET: break
        r_s = RET[yr][0] / 100.0; r_b = RET[yr][1] / 100.0
        for w, frac in sched:
            if abs(w - t) < 1e-9:
                mv = net0 * frac
                if bal_b >= mv - 1e-6: bal_b -= mv; bal_s += mv
        mid_mv = 0.0
        for w, frac in sched:
            if abs(w - (t + 0.5)) < 1e-9:
                mv = net0 * frac
                if bal_b >= mv - 1e-6: bal_b -= mv; bal_s += mv; mid_mv += mv
        bal_s *= (1 + r_s); bal_b *= (1 + r_b)
        bal_s += mid_mv * r_s * 0.5
        v = bal_s + bal_b
        peak = max(peak, v); dds.append(v / peak - 1)
        vals.append(v)
    return vals, (min(dds) if dds else 0.0)

# ----------------------------------------------------------------------------
# 5. SAME-YEAR SALE (first analysis required by the brief)
# ----------------------------------------------------------------------------
def same_year_sale(Y, g):
    v0 = A_VALUE_2026 * ((1 + g) ** (Y - BASE_YEAR))
    xfer = v0 * XFER_SC
    sell = v0 * SELL_COST_PCT
    net = v0 - xfer - sell - RECORD_FEE
    # step-up basis at death ≈ FMV; sale within same tax year → gain ≈ 0 (loss after costs)
    fed_tax = 0.0; ca_tax = 0.0
    return {
        "year": Y,
        "fmv_at_death": r10(v0),
        "transfer_tax_sc_county": r10(xfer),
        "recording_fees": r10(RECORD_FEE),
        "selling_costs_assumption_pct": pct(SELL_COST_PCT,1),
        "selling_costs": r10(sell),
        "net_proceeds": r10(net),
        "taxable_gain_after_stepup": r10(0),
        "federal_income_tax": r10(fed_tax),
        "california_income_tax": r10(ca_tax),
        "note": "Step-up basis = FMV at death (IRS Pub 523). Same-tax-year sale realizes ~no gain; "
                "transfer tax and selling costs still apply. Commission % is an assumption."
    }

# ----------------------------------------------------------------------------
# 6. PATH PROJECTIONS
# ----------------------------------------------------------------------------
def project_paths(Y, params):
    """params: home_g, stock_g, infl, bill_g, a_rent_mo, occupy(bool), cash, park_months"""
    g = params["home_g"]; sg = params["stock_g"]; infl = params["infl"]; bg = params["bill_g"]
    n = max(HORIZONS)
    years = list(range(n + 1))
    t_from_2026 = [Y - BASE_YEAR + t for t in years]

    v = [A_VALUE_2026 * ((1 + g) ** dt) for dt in t_from_2026]
    av = [A_AV_2026 * (1.02 ** dt) for dt in t_from_2026]
    cap = [PROP19_CAP_2026 * ((1 + g) ** dt) for dt in t_from_2026]
    tax_occ  = [prop19_taxable(v[t], av[t], cap[t]) * A_RATE_IMPL for t in years]
    tax_full = [v[t] * A_RATE_IMPL for t in years]

    infl_f = [(1 + infl) ** t for t in years]
    # A fixed ops: insurance + sewer + water + electricity (electricity is negative = solar credit)
    a_ops = [( (A_INS_2026 + A_SEWER_YR + A_WATER_MO*12 + A_ELEC_MO*12) * infl_f[t]
               + v[t] * A_MAINT_PCT ) for t in years]
    b_tax = [B_TAX_2025 * (1.02 ** (Y - 2025 + t)) + (PROP_H_MF if (Y + t) >= 2027 else 0) for t in years]
    b_value = [B_VALUE_2026 * ((1 + g) ** (Y - BASE_YEAR + t)) for t in years]
    b_ops = [ (B_INS_2026 + B_WATER_MO*12 + B_ELEC_MO*12) * infl_f[t]
              + b_value[t] * B_MAINT_PCT for t in years]
    rent_b = [B_RENT_MO * 12 * ((1 + params.get("rent_g", 0.025)) ** t) for t in years]

    a_rent = params.get("a_rent_mo", 0)
    rent_a = [a_rent * 12 * ((1 + params.get("rent_g", 0.025)) ** t) for t in years]
    mgmt_a = [rent_a[t] * MGMT_PCT for t in years]

    # ---- common: Property B net cash flow (rent - B tax - B ops) in every path
    b_net_cf = [ rent_b[t] - b_tax[t] - b_ops[t] for t in years]

    # ---- SELL at Y, invest
    v0 = v[0]
    net0 = v0 * (1 - XFER_SC - SELL_COST_PCT) - RECORD_FEE
    port_sell = portfolio_path2(net0, sg, bg, 0, 0, n + 1)          # lump sum
    port_phase = portfolio_path2(net0, sg, bg, params.get("park_months", 24), 24, n + 1)
    sell_cf = list(b_net_cf)          # lives in B after sale; portfolio income taxed separately (flagged)
    sell_cum = []; _c = 0.0
    for _cf in sell_cf:
        _c += _cf; sell_cum.append(_c)

    # ---- LIVE path: occupy A (Prop 19 claimed), B fully rented (3rd unit = what-if, default 0),
    #      minus imputed rent = market rent forgone by occupying A (what-if input)
    third = params.get("b_third_unit_mo", 0) * 12
    imputed = [rent_a[t] for t in years]        # imputed-rent input: forgone market rent of A
    live_cf = [ b_net_cf[t] + third*infl_f[t] - tax_occ[t] - a_ops[t] - imputed[t] for t in years]
    live_cum = []; _c = 0.0
    for _cf in live_cf:
        _c += _cf; live_cum.append(_c)
    live_networth = [ v[t] * (1 - SELL_COST_PCT) + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + live_cum[t] for t in years]

    # ---- RENT path: live in B (2 units rented), rent A (full reassessment, no Prop 19), pay mgmt
    rent_cf = [ b_net_cf[t] + rent_a[t] - tax_full[t] - a_ops[t] - mgmt_a[t] for t in years]
    rent_cum = []; _c = 0.0
    for _cf in rent_cf:
        _c += _cf; rent_cum.append(_c)
    rent_networth = [ v[t] * (1 - SELL_COST_PCT) + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + rent_cum[t] for t in years]

    # ---- SELL path: proceeds invested + keep B
    sell_networth = [ port_sell[t] + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + sell_cum[t] for t in years]
    phase_networth = [ port_phase[t] + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + sell_cum[t] for t in years]

    # ---- MIXED: live 5y then sell (with §121 on post-death gain, capped 500k MFJ)
    mix_cf = [ live_cf[t] if t <= 5 else sell_cf[t] for t in years]
    mix = []; _c = 0.0
    for t in years:
        _c += mix_cf[t]
        if t <= 5:
            nw = v[t]*(1 - SELL_COST_PCT) + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + _c
        else:
            # sold at t=5: basis v0 (step-up); gain = v5-v0; §121 shelters min(gain,500k) if qualified
            v5 = v[5]
            gain = max(v5 - v0, 0)
            shelter = min(gain, SEC_121_MFJ)
            taxable = gain - shelter
            tax = taxable * (FED_LTCG_TOP + NIIT + CA_TOP_ALLIN)   # top rates — simplified, flagged
            proceeds = v5 * (1 - XFER_SC - SELL_COST_PCT) - RECORD_FEE - tax
            p = portfolio_path2(proceeds, sg, bg, 0, 0, t - 5)
            nw = p[-1] + B_VALUE_2026*((1+g)**(Y-BASE_YEAR+t)) + _c
        mix.append(nw)

    def summarize(cum_cf, nw, label, extra=None):
        d = {"path": label,
             "net_worth": {str(h): r10(nw[h]) for h in HORIZONS},
             "cum_net_cash_flow": {str(h): r10(sum(cum_cf[:h+1])) for h in HORIZONS},
             "annual_cash_flow_at_10": r10(cum_cf[10]) if n >= 10 else None,
             "series_nw": [r10(x) for x in nw],
             "series_cf": [r10(x) for x in cum_cf]}
        if extra: d.update(extra)
        return d

    out = {
        "inheritance_year": Y,
        "params": {k: (pct(vv,2) if isinstance(vv,float) and k.endswith(("_g",)) else vv) for k, vv in params.items()},
        "paths": [
            summarize(live_cf, live_networth, "LIVE in Property A (Prop 19 claimed)", {
                "property_tax_first_year": r10(tax_occ[0]),
                "reinvestment_risk": "None on the house (held); wealth concentrated in two Bay Area properties.",
                "liquidity": "Low — home equity not liquid without sale/HELOC.",
                "taxes_modeled": "Property tax (Prop 19 regime), no income tax unless later sale"}),
            summarize(rent_cf, rent_networth, "RENT Property A (full reassessment)", {
                "property_tax_first_year": r10(tax_full[0]),
                "reinvestment_risk": "None (rental held); landlord/tenant and vacancy risk instead.",
                "liquidity": "Low — rental equity not liquid.",
                "taxes_modeled": "Property tax (reassessed), management cost, rental income taxable (not netted here)"}),
            summarize(sell_cf, sell_networth, "SELL Property A → lump-sum stocks", {
                "net_proceeds_invested": r10(net0),
                "reinvestment_risk": "HIGH — full proceeds exposed to markets from day one (see Black Swan page).",
                "liquidity": "High — portfolio fully liquid.",
                "taxes_modeled": "Transfer tax + selling costs at sale; income tax ~$0 same-year (step-up); later portfolio income taxed"}),
            summarize(sell_cf, phase_networth, "SELL Property A → 24-mo Treasury park, then phase 24 mo", {
                "net_proceeds_invested": r10(net0),
                "reinvestment_risk": "MEDIUM — staged entry cuts single-date risk; may lag in V-shaped rebounds.",
                "liquidity": "High.",
                "taxes_modeled": "Same as lump-sum; treasury interest taxed as ordinary income annually"}),
            summarize(mix_cf, mix, "MIXED: live 5 years → sell", {
                "reinvestment_risk": "Delayed — markets engaged only after year 5.",
                "liquidity": "Low for 5 years, then high.",
                "taxes_modeled": "Prop 19 property tax ×5; sale: §121 excludes up to $500,000 gain (MFJ) if qualified; CA conforms"}),
        ],
        "series": {
            "years_post": years,
            "fmv_A": [r10(x) for x in v],
            "assessed_A": [r10(x) for x in av],
            "tax_occ": [r10(x) for x in tax_occ],
            "tax_full": [r10(x) for x in tax_full],
            "net_worth_live": [r10(x) for x in live_networth],
            "net_worth_rent": [r10(x) for x in rent_networth],
            "net_worth_sell": [r10(x) for x in sell_networth],
            "net_worth_phase": [r10(x) for x in phase_networth],
            "net_worth_mixed": [r10(x) for x in mix],
            "portfolio_lump": [r10(x) for x in port_sell],
            "portfolio_phase": [r10(x) for x in port_phase],
            "rentA_income": [r10(x) for x in rent_a],
        }
    }
    return out

# ----------------------------------------------------------------------------
# 7. BLACK SWAN ENTRY TESTS (historical)
# ----------------------------------------------------------------------------
def blackswan_entries():
    entries = []
    for start, label in [(1929,"1929 crash entry"), (1973,"1973–74 stagflation entry"),
                         (2000,"2000 dot-com peak entry"), (2008,"2008 GFC entry"),
                         (2020,"2020 COVID shock entry")]:
        row = {"start_year": start, "label": label, "strategies": []}
        for name, park, phase in [("Lump sum (day one)", 0, 0),
                                  ("Park 24 mo in T-bills, phase 24 mo", 24, 24),
                                  ("Park 36 mo in T-bills, phase 24 mo", 36, 24)]:
            vals, maxdd = hist_portfolio(start, 100_000, park, phase, 11)  # up to 10 yrs
            if not vals: continue
            row["strategies"].append({
                "strategy": name,
                "value_y5": r10(vals[4]) if len(vals) >= 5 else None,
                "value_y10": r10(vals[9]) if len(vals) >= 10 else None,
                "max_drawdown_pct": pct(maxdd, 1),
                "final_year_used": start + len(vals) - 1,
                "series": [r10(x) for x in vals],
            })
        # context: actual returns in the entry window
        ctx = []
        for k in range(0, 11):
            yr = start + k
            if yr in RET: ctx.append({"year": yr, "stock_pct": RET[yr][0], "bill_pct": RET[yr][1]})
        row["context"] = ctx
        entries.append(row)
    return entries

def regime_rows():
    return [
      {"regime": "Great Depression (1929–1932)", "window": "1929–1932",
       "stocks_cum_pct": round(((1+RET[1929][0]/100)*(1+RET[1930][0]/100)*(1+RET[1931][0]/100)*(1+RET[1932][0]/100)-1)*100,1),
       "bills_cum_pct": round(((1+RET[1929][1]/100)*(1+RET[1930][1]/100)*(1+RET[1931][1]/100)*(1+RET[1932][1]/100)-1)*100,1),
       "source": "damodaran", "note": "Four consecutive negative stock years; bills positive but tiny."},
      {"regime": "Stagflation (1973–1974)", "window": "1973–1974",
       "stocks_cum_pct": round(((1+RET[1973][0]/100)*(1+RET[1974][0]/100)-1)*100,1),
       "bills_cum_pct": round(((1+RET[1973][1]/100)*(1+RET[1974][1]/100)-1)*100,1),
       "source": "damodaran", "note": "Inflation averaged 11.3%/13.5%/10.3% in 1979–81 (BLS); bills beat stocks briefly."},
      {"regime": "Dot-com bust (2000–2002)", "window": "2000–2002",
       "stocks_cum_pct": round(((1+RET[2000][0]/100)*(1+RET[2001][0]/100)*(1+RET[2002][0]/100)-1)*100,1),
       "bills_cum_pct": round(((1+RET[2000][1]/100)*(1+RET[2001][1]/100)*(1+RET[2002][1]/100)-1)*100,1),
       "source": "damodaran", "note": "Three-year grind, not a one-day crash."},
      {"regime": "Global financial crisis (2008)", "window": "2008",
       "stocks_cum_pct": RET[2008][0], "bills_cum_pct": RET[2008][1],
       "source": "damodaran", "note": "Worst calendar year since 1931; recovery began 2009 (+25.94%)."},
      {"regime": "COVID shock (2020)", "window": "2020",
       "stocks_cum_pct": RET[2020][0], "bills_cum_pct": RET[2020][1],
       "source": "damodaran", "note": "Fastest bear market on record; calendar year still positive."},
    ]

# ----------------------------------------------------------------------------
# 8. MONTE CARLO DISTRIBUTION (seeded, reproducible)
# ----------------------------------------------------------------------------
def monte_carlo(Y=2045, n_sims=1000, horizon=30, seed=42):
    rng = random.Random(seed)
    g_mean, g_sd = STOCK_MEAN, STOCK_SD
    bundles = {"Sell A → 70/30 stocks/bills": [], "Hold A as rental (sell at end)": [], "Live in A (hold)": []}
    v0 = A_VALUE_2026 * ((1 + HOME_G["base"]) ** (Y - BASE_YEAR))
    net0 = v0 * (1 - XFER_SC - SELL_COST_PCT) - RECORD_FEE
    for _ in range(n_sims):
        s, b = net0 * 0.7, net0 * 0.3
        w_sell = []
        for t in range(horizon):
            rs = max(min(rng.gauss(g_mean, g_sd), 0.60), -0.60)
            rb = max(min(rng.gauss(BILL_G["base"], 0.01), 0.10), -0.02)
            s *= (1 + rs); b *= (1 + rb)
            w_sell.append(s + b)
        bundles["Sell A → 70/30 stocks/bills"].append(w_sell)

        rent_cf = 0.0
        vv_rent = v0
        fixed0 = A_INS_2026 + A_SEWER_YR + A_WATER_MO * 12 + A_ELEC_MO * 12   # 2026$ fixed ops
        for t in range(horizon):
            g_home_t = max(min(rng.gauss(HOME_G["base"], 0.03), 0.12), -0.15)
            vv_rent *= (1 + g_home_t)
            rent = A_RENT_FLOOR_MO * 12 * ((1 + INFL["base"]) ** t)
            costs = (vv_rent * (A_RATE_IMPL + A_MAINT_PCT)
                     + fixed0 * ((1 + INFL["base"]) ** t)
                     + rent * MGMT_PCT)
            rent_cf += (rent - costs)
        bundles["Hold A as rental (sell at end)"].append(vv_rent * (1 - SELL_COST_PCT) + rent_cf)

        w_live = []
        vv = A_VALUE_2026 * ((1 + HOME_G["base"]) ** (Y - BASE_YEAR))
        for t in range(horizon):
            g_home_t = max(min(rng.gauss(HOME_G["base"], 0.03), 0.12), -0.15)
            vv *= (1 + g_home_t)
        bundles["Live in A (hold)"].append(vv * (1 - SELL_COST_PCT))

    def pctile(series, p):
        xs = sorted(series); k = (len(xs) - 1) * p
        f = math.floor(k); c = math.ceil(k)
        return xs[f] if f == c else xs[f] * (c - k) + xs[c] * (k - f)

    out = {"horizon": horizon, "sims": n_sims, "seed": seed, "bundles": []}
    for name, vals in bundles.items():
        if name.startswith("Sell"):
            # per-year percentiles
            p10, p50, p90 = [], [], []
            for t in range(horizon):
                col = [w[t] for w in vals]
                p10.append(r10(pctile(col, .10))); p50.append(r10(pctile(col, .50))); p90.append(r10(pctile(col, .90)))
            out["bundles"].append({"name": name, "p10": p10, "p50": p50, "p90": p90,
                                   "end_p10": p10[-1], "end_p50": p50[-1], "end_p90": p90[-1]})
        else:
            v = [r10(pctile(vals, p)) for p in (.10, .50, .90)]
            out["bundles"].append({"name": name, "p10": [v[0]]*horizon, "p50": [v[1]]*horizon, "p90": [v[2]]*horizon,
                                   "end_p10": v[0], "end_p50": v[1], "end_p90": v[2],
                                   "note": "single end-point distribution (property held entire horizon)"})
    return out

# ----------------------------------------------------------------------------
# 9. STATIC TABLES (source-linked; null = unverified)
# ----------------------------------------------------------------------------
def tables():
    a_hist = [
      # user data rounded to $10; source = household
      {"year": 2026, "taxes": None, "assessment": r10(550_540), "chg": "+2%", "src": "household"},
      {"year": 2025, "taxes": r10(7_210), "assessment": r10(539_740), "chg": "+2%", "src": "household"},
      {"year": 2024, "taxes": r10(7_000), "assessment": r10(529_160), "chg": "+2%", "src": "household"},
      {"year": 2023, "taxes": r10(6_920), "assessment": r10(518_790), "chg": "+2%", "src": "household"},
      {"year": 2022, "taxes": r10(6_760), "assessment": r10(508_610), "chg": "+2%", "src": "household"},
      {"year": 2021, "taxes": r10(6_660), "assessment": r10(498_640), "chg": "+1%", "src": "household"},
      {"year": 2020, "taxes": r10(6_570), "assessment": r10(493_530), "chg": "+2%", "src": "household"},
      {"year": 2019, "taxes": r10(6_570), "assessment": r10(483_850), "chg": "+2%", "src": "household"},
      {"year": 2018, "taxes": r10(6_380), "assessment": r10(474_370), "chg": "+2%", "src": "household"},
      {"year": 2017, "taxes": r10(6_380), "assessment": r10(465_070), "chg": "+2%", "src": "household"},
      {"year": 2016, "taxes": r10(6_410), "assessment": r10(455_950), "chg": "+1.5%", "src": "household"},
      {"year": 2015, "taxes": r10(6_130), "assessment": r10(449_100), "chg": "+2%", "src": "household"},
      {"year": 2014, "taxes": r10(5_970), "assessment": r10(440_310), "chg": "+0.5%", "src": "household"},
    ]
    b_hist = [
      {"year": 2025, "taxes": r10(2_440), "assessment": r10(114_250), "chg": "+2%", "src": "household"},
      {"year": 2024, "taxes": r10(2_320), "assessment": r10(112_010), "chg": "+2%", "src": "household"},
      {"year": 2023, "taxes": r10(2_180), "assessment": r10(109_810), "chg": "+2%", "src": "household"},
      {"year": 2022, "taxes": r10(2_110), "assessment": r10(107_660), "chg": "+2%", "src": "household"},
      {"year": 2021, "taxes": r10(2_070), "assessment": r10(105_600), "chg": "+1%", "src": "household"},
      {"year": 2020, "taxes": r10(2_200), "assessment": r10(104_510), "chg": "+2%", "src": "household"},
      {"year": 2019, "taxes": r10(2_130), "assessment": r10(102_470), "chg": "+2%", "src": "household"},
      {"year": 2018, "taxes": r10(2_060), "assessment": r10(100_460), "chg": "+2%", "src": "household"},
      {"year": 2017, "taxes": r10(1_740), "assessment": r10(98_490), "chg": "+2%", "src": "household"},
      {"year": 2016, "taxes": r10(1_680), "assessment": r10(96_560), "chg": "+1.5%", "src": "household"},
    ]
    law_rows = [
      {"item": "Federal basic exclusion (deaths 2026)", "value": "$15,000,000", "src": "irs-rp2532", "status": "Enacted"},
      {"item": "Federal estate/GST top rate", "value": "40%", "src": "irs-706", "status": "Enacted"},
      {"item": "Annual gift exclusion 2026", "value": "$19,000", "src": "irs-rp2532", "status": "Enacted"},
      {"item": "Form 706 deadline", "value": "9 months after death (+6-month filing extension, Form 4768)", "src": "irs-706", "status": "Enacted"},
      {"item": "Portability (DSUE)", "value": "Elected on timely, complete Form 706; late relief ≤5 years (Rev. Proc. 2022-32)", "src": "irs-estgift", "status": "Enacted"},
      {"item": "California estate tax", "value": "$0 (R&T §13302 keys to repealed federal credit)", "src": "leginfo-13302", "status": "Enacted"},
      {"item": "California inheritance tax", "value": "$0 (repealed by Prop 6, 1982)", "src": "leginfo-13302", "status": "Enacted"},
      {"item": "Step-up in basis", "value": "FMV at date of death (or alternate valuation)", "src": "irs-p523", "status": "Enacted"},
      {"item": "Federal LTCG rates 2026", "value": "0% / 15% / 20% (+3.8% NIIT over $200k/$250k MAGI)", "src": "irs-rp2532", "status": "Enacted"},
      {"item": "CA treatment of capital gains", "value": "Taxed as ordinary income (no preferential rate)", "src": "ftb-capgain", "status": "Enacted"},
      {"item": "CA 1% surtax on income over $1,000,000", "value": "Behavioral Health Services Tax, Form 540 line 62 (was Mental Health Services Tax)", "src": "ftb-540i", "status": "Enacted"},
      {"item": "§121 primary-residence exclusion", "value": "$250,000 single / $500,000 MFJ; 2-of-5-year tests", "src": "irs-p523", "status": "Enacted"},
      {"item": "Prop 13", "value": "1% base + voter bonds; ≤2% factored value growth/yr", "src": "scc-assessor", "status": "Enacted"},
      {"item": "Prop 19 parent-child exclusion", "value": "Principal residence only; taxable = FBYV + excess above FBYV + cap; cap $1,044,586 (transfers 2026-02-16→2027-02-15)", "src": "boe-prop19", "status": "Enacted"},
      {"item": "Prop 19 filing windows", "value": "Homeowners' exemption ≤1 year of transfer; exclusion claim ≤3 years or before transfer to third party", "src": "boe-prop19", "status": "Enacted"},
      {"item": "SCC transfer tax (sale of Property A)", "value": "$0.55 per $500 = 0.11%; Property A's city adds NO city conveyance tax", "src": "scc-recorder", "status": "Enacted"},
      {"item": "SF transfer tax (if Property B ever sold)", "value": "0.50%–6.00% of entire value by tier ($1M–$5M = 0.75%)", "src": "sf-recorder", "status": "Enacted"},
      {"item": "SF Prop H parcel tax (Property B)", "value": "Multifamily ≤5,000 sqft: $249/yr from FY2027-28; CPI-adjusted from FY2028-29; expires 2042", "src": "sf-proph-text", "status": "Enacted (passed 2026-11-03, 74.42%)"},
      {"item": "SF Prop I transfer-tax change", "value": "Would have cut 5.5%/6% tiers for $10M+ property — DEFEATED", "src": "sf-results", "status": "Defeated (pre-certification)"},
      {"item": "SF secured tax rate FY2026-27", "value": "1.18162182%", "src": "sf-treasurer", "status": "Enacted"},
      {"item": "SF Rent Ordinance increase Mar 2026–Feb 2027", "value": "1.6% (60% of CPI) for covered units", "src": "sfrb", "status": "Enacted — official page not re-opened (flagged)"},
      {"item": "AB 1482 (statewide rent cap)", "value": "5% + local CPI, max 10%; SF 8.8% for Aug 2026–Jul 2027", "src": "sf-ab1482", "status": "Enacted"},
      {"item": "CA Initiative 25-0035 (60+ property tax exemption)", "value": "Would cut local revenue $12B–$20B/yr (LAO)", "src": "ag-init250035", "status": "DID NOT qualify for Nov 2026 ballot — watch 2028"},
      {"item": "H.R.601 Estate Tax Rate Reduction Act", "value": "Would reduce top estate rate", "src": "congress-hr601", "status": "Proposal — in committee"},
      {"item": "OBBBA (PL 119-21)", "value": "$15M exemption, no phase-out, indexed from 2027", "src": "irs-obbb", "status": "Enacted 2025-07-04"},
      {"item": "NEM 3.0 / Net Billing Tariff", "value": "New solar exports at avoided cost (CPUC D.22-12-056, eff. 2023-04-15)", "src": "cpuc-nbt", "status": "Enacted — decision PDF not re-opened (flagged)"},
    ]
    prop19_caps = [
      {"window": "2021-02-16 → 2023-02-15", "cap": 1_000_000, "src": "boe-prop19"},
      {"window": "2023-02-16 → 2025-02-15", "cap": 1_022_600, "src": "boe-prop19"},
      {"window": "2025-02-16 → 2027-02-15", "cap": 1_044_586, "src": "boe-prop19"},
      {"window": "2027-02-16 → 2029-02-15", "cap": None, "src": "boe-lta25009", "note": "Next biennial CA-HPI adjustment — amount not yet published; check BOE each February."},
    ]
    # Form 540 sensitivity (1% BHST) — rounded to $10
    sens = []
    for gain in (1_000_000, 3_000_000, 5_000_000, 10_000_000):
        # simplified: all income = gain (other income ignored — flagged)
        bhst = max(gain - 1_000_000, 0) * CA_BHST
        ca_ord = gain * CA_ORD_TOP                      # top marginal simplification
        fed = gain * (FED_LTCG_TOP + NIIT)
        sens.append({"gain": r10(gain),
                     "ca_bhst_1pct": r10(bhst),
                     "ca_ordinary_top_simplified": r10(ca_ord),
                     "fed_ltcg_niit_top_simplified": r10(fed),
                     "combined_top_simplified": r10(bhst + ca_ord + fed)})
    estate_rows = []
    for T in (10_000_000, 16_000_000, 25_000_000, 40_000_000):
        tax = max(T - BEA_2026, 0) * ESTATE_RATE
        estate_rows.append({"taxable_estate": r10(T), "bea_2026": r10(BEA_2026),
                            "federal_estate_tax": r10(tax), "effective_rate_on_excess": pct(ESTATE_RATE,0),
                            "src": ["irs-rp2532", "irs-706"]})
    cost_rows = [
      {"item": "Property A insurance (household estimate)", "value": r10(1500), "unit": "$/yr", "src": "household", "status": "Unverified — CA DOI statewide averages are higher; obtain quotes"},
      {"item": "Property B insurance (household estimate)", "value": r10(1500), "unit": "$/yr", "src": "household", "status": "Unverified — obtain landlord/DP-3 quotes"},
      {"item": "Property A water", "value": r10(125), "unit": "$/mo", "src": "household", "status": "Unverified range $100–$150"},
      {"item": "Property A sewer (Special district (Property A))", "value": r10(800), "unit": "$/yr", "src": "csd-ord135", "status": "Verified FY2025-26 ($802.14)"},
      {"item": "Property A electricity (solar net)", "value": r10(-15), "unit": "$/mo", "src": "household", "status": "Unverified: credits $10–$20/mo; NEM grandfathering must be confirmed"},
      {"item": "Property B water (all 3 units)", "value": r10(365), "unit": "$/mo", "src": "household", "status": "Unverified range $330–$400; SFPUC rates verified as mechanism"},
      {"item": "Property B electricity", "value": r10(50), "unit": "$/mo", "src": "household", "status": "Unverified range $30–$70"},
      {"item": "Property B rental income (2 units)", "value": r10(7150), "unit": "$/mo", "src": "household", "status": "Unverified — leases must be produced (open task)"},
      {"item": "Property A market rent", "value": None, "unit": "$/mo", "src": "hud-fmr", "status": "UNVERIFIED — model uses HUD FMR floor $3,604 (SF County 2-BR) only; Property A comps required"},
      {"item": "Property A maintenance", "value": None, "unit": "$/yr", "src": None, "status": "UNVERIFIED — model assumes 0.75% of value/yr (flagged assumption)"},
      {"item": "Property B maintenance", "value": None, "unit": "$/yr", "src": None, "status": "UNVERIFIED — model assumes 1.00% of value/yr (flagged assumption)"},
      {"item": "SF Prop H (multifamily floor)", "value": r10(249), "unit": "$/yr", "src": "sf-proph-text", "status": "Verified floor; final amount depends on building area (unknown)"},
      {"item": "CA DOI statewide avg premium (context)", "value": None, "unit": "$/yr", "src": "cdi-report", "status": "ZIP-level values in report — not extracted; look up both property ZIPs (internal)"},
    ]
    return {
      "property_a_tax_history": a_hist,
      "property_b_tax_history": b_hist,
      "law_rules": law_rows,
      "prop19_cap_schedule": [{"window": p["window"], "cap": r10(p["cap"]) if p["cap"] else None, "src": p["src"], **({"note": p["note"]} if "note" in p else {})} for p in prop19_caps],
      "form540_sensitivity": sens,
      "estate_tax_scenarios": estate_rows,
      "operating_costs": cost_rows,
      "rates": [
        {"item": "Property A implied all-in rate (household bill)", "value": f"{pct(A_RATE_IMPL,3)}%", "src": "household", "status": "Flagged — exceeds typical published TRA rates"},
        {"item": "Property B implied all-in rate (household bill)", "value": f"{pct(B_RATE_IMPL,3)}%", "src": "household", "status": "Flagged — vs official base 1.18162%; gap likely parcel taxes"},
        {"item": "Santa Clara County typical TRA example", "value": "1.1488%", "src": "scc-assessor", "status": "Verified (booklet example; actual TRA needs APN lookup)"},
        {"item": "SF secured rate FY2026-27", "value": "1.18162182%", "src": "sf-treasurer", "status": "Verified"},
        {"item": "SCC transfer tax", "value": "0.11% ($0.55/$500)", "src": "scc-recorder", "status": "Verified"},
        {"item": "SF transfer tax $1M–$5M tier", "value": "0.75% of entire value", "src": "sf-recorder", "status": "Verified"},
      ],
    }

# ----------------------------------------------------------------------------
# 10. TIMELINE / QUESTIONS / GLOSSARY / SUGGESTIONS / FLAGS
# ----------------------------------------------------------------------------
def timeline():
    return [
      {"when": "At death (est. 2040–2050)", "what": "Trust administration opens; date of death fixes step-up basis (FMV) and Prop 13/19 evaluation date", "src": "irs-p523", "kind": "process"},
      {"when": "Within 30 days of Form 706 due", "what": "Form 8971 basis reporting to heirs if 706 filed (heirs must use reported values)", "src": "irs-706", "kind": "deadline"},
      {"when": "9 months after death", "what": "Form 706 due (and any estate tax); Form 4768 extension must be filed by this date for +6 months to file", "src": "irs-706", "kind": "deadline"},
      {"when": "≤1 year of transfer", "what": "File homeowners' exclusion for Prop 19 (BOE-19-P pathway) — REQUIRED to keep parent-child base", "src": "boe-prop19", "kind": "deadline"},
      {"when": "≤3 years of transfer (or before transfer to third party)", "what": "File Proposition 19 intergenerational exclusion claim", "src": "boe-prop19", "kind": "deadline"},
      {"when": "Same tax year as inheritance", "what": "Model a sale first (this site does): step-up means ~$0 gain; transfer tax still due", "src": "irs-p523", "kind": "decision"},
      {"when": "Apr 15 following year", "what": "CA estimated tax / final return if sale or rental income occurred; Form 709 if gifts made", "src": "ftb-540i", "kind": "deadline"},
      {"when": "July 2 – Sept 15 (annual)", "what": "Santa Clara County assessment appeal window (BOE-305-AH); free informal Prop 8 review by Aug 8", "src": "scc-aab", "kind": "deadline"},
      {"when": "Nov 1 / Dec 10 & Feb 1 / Apr 10 (annual)", "what": "Santa Clara County secured tax installments (delinquency dates)", "src": "scc-assessor", "kind": "deadline"},
      {"when": "Dec 10 & Apr 10 (annual)", "what": "San Francisco secured tax installments", "src": "sf-treasurer", "kind": "deadline"},
      {"when": "Each Feb 16 (odd years)", "what": "BOE publishes next Prop 19 $1M cap adjustment (CA HPI)", "src": "boe-lta25009", "kind": "deadline"},
      {"when": "July 1, 2027", "what": "SF Prop H parcel tax begins (FY2027-28); CPI adjustments from FY2028-29; expires June 30, 2042", "src": "sf-proph-text", "kind": "law"},
      {"when": "Every December 3", "what": "SF Department of Elections certifies Nov 3 results (2026 certification due 2026-12-03)", "src": "sf-results", "kind": "deadline"},
      {"when": "Every January", "what": "Re-run this model with updated inputs; re-check federal/state/local sources (governance calendar)", "src": None, "kind": "process"},
      {"when": "Aug 4, 2027 (approx.)", "what": "Next CA initiative signature deadline cycle — watch for 60+ property tax exemption revival (25-0035 targeted 2028)", "src": "ag-init250035", "kind": "law"},
    ]

def questions():
    return [
      {"id":"Q1","q":"What is the date-of-death gross estate inventory, including non-probate assets and life insurance?","why":"Estate-tax exposure cannot be calculated from the inherited house alone. Include real estate, cash, investments, retirement accounts, business interests, jointly owned assets, and includible insurance; subtract debts only under applicable rules.","status":"MISSING — no estate total is available; the model's $0 cash baseline is not a household fact","how":"Ask the executor and estate attorney for a confidential inventory. Keep exact figures offline; the public model needs only an approved rounded range."},
      {"id":"Q2","q":"What taxable gifts, prior spouse portability (DSUE), trust ownership, and marital deductions apply?","why":"These items can materially change the exclusion available at death; the current-year federal exclusion alone does not establish whether estate tax is due.","status":"MISSING — no gift history, marital/ownership facts, or portability record supplied","how":"Attorney/CPA to review prior Forms 709 and 706, trust documents, ownership/title, and any DSUE election before estimating tax."},
      {"id":"Q3","q":"What federal estate-tax exclusion will apply in the actual year of death?","why":"The applicable exclusion and law may change before the expected inheritance window; the current-year amount is not a future guarantee.","status":"UNKNOWN — current law is a reference point only","how":"Re-check enacted federal law and IRS inflation adjustments each year and at the date of death; model the estate against low/base/high legal scenarios."},
      {"id":"Q4","q":"Does the heir intend to occupy Property A as a principal residence, and will they file the claim within 1 year?","why":"Prop 19 eligibility and filing are legal tests; separately, the household's genuine long-term occupancy plan determines whether choosing the living path is practical and consistent with its priorities.","status":"DECISION PENDING — legal eligibility and household intent are both open","how":"Before transfer, review the current BOE rules with the assessor/adviser and write down occupancy intent, duration assumptions, alternative housing costs, and the deadline; do not claim the exclusion if ineligible."},
      {"id":"Q5","q":"What is Property A's tax rate area (TRA) number, and what rate does the county publish for it?","why":"All property-tax projections hinge on the actual all-in TRA rate (household bill implies ~1.34%).","status":"MISSING — APN/TRA not held (privacy)","how":"Read TRA off any prior tax bill; look up in county tax rate book."},
      {"id":"Q6","q":"Why does Property B's bill imply ~2.14% when the official SF base rate is 1.18162%?","why":"Direct levies/parcel taxes explain part of the gap; errors are possible.","status":"FLAGGED","how":"Request parcel breakdown from SF Treasurer; compare to published direct-levy schedule."},
      {"id":"Q7","q":"What is the actual insurance premium (Property A and B) — and is Property B insured as a rental (DP-3/LL policy)?","why":"Household estimates (~$1,500) sit below CA DOI statewide averages; underinsurance is a tail risk.","status":"MISSING — quotes required","how":"Two broker quotes each; also pull ZIP-level CDI report figures for both property ZIPs (internal)."},
      {"id":"Q8","q":"What rent will Property A actually command?","why":"Rent path ranking is a floor until real comparables exist; HUD FMR is a voucher benchmark only.","status":"MISSING — model uses FMR floor","how":"Three licensed-comp appraisals/BPOs or a property-manager rent analysis."},
      {"id":"Q9","q":"Are Property B's leases written, assigned to the trust/heir, and compliant with SF Rent Ordinance registration?","why":"Lease terms, rent-control status and just-cause rules determine B's income durability.","status":"MISSING","how":"Produce all leases, registration certificates, and any banked-rent history."},
      {"id":"Q10","q":"Is Property A free of debt? Any liens?","why":"Debt must be repaid or assumed at transfer; changes every net-worth figure.","status":"ASSUMED none — flag if wrong","how":"Title report / trust inventory."},
      {"id":"Q11","q":"Is Property A on NEM 1.0/2.0 (grandfathered) or NEM 3.0?","why":"Solar economics differ ~5x on export credits; affects the +$10–$20/mo credit assumption.","status":"MISSING","how":"Utility interconnection records / permission-to-operate date."},
      {"id":"Q12","q":"Does the household prefer liquidity, income, or appreciation — and what drawdown is unacceptable?","why":"Pre-agreed preferences prevent reverse-engineering the answer from one projection.","status":"TO BE AGREED IN WRITING","how":"Sign the pre-commitment policy on the Suggestions page."},
      {"id":"Q13","q":"Could the estate need §6166 installment payments or life-insurance liquidity?","why":"Estate tax is due in 9 months in cash — illiquid real estate cannot pay it alone.","status":"MISSING","how":"Estate liquidity plan with counsel (briefing sheet lists the questions)."},
      {"id":"Q14","q":"Are there out-of-state heirs or property with ancillary-probate implications?","why":"Changes timelines and possibly state estate taxes (CA itself imposes none).","status":"MISSING","how":"Ask counsel about situs of assets and heir residences."},
    ]

def glossary():
    return [
      {"term":"Base year value (Prop 13)","def":"The value placed on property when it last changed ownership (or was newly built); grows at most 2% per year thereafter."},
      {"term":"Factored base year value","def":"Base year value after annual 2% inflation factors."},
      {"term":"Change in ownership","def":"A transfer that resets assessment to current market value unless an exclusion (like Prop 19) applies."},
      {"term":"Prop 19 value cap","def":"Parent-child exclusion protects taxable value only up to factored base year value + ~$1M (biennially adjusted); anything above is added to taxable value."},
      {"term":"Step-up in basis","def":"Inherited assets generally take a new tax basis equal to fair market value at death, wiping out pre-death gain for the heir."},
      {"term":"§121 exclusion","def":"Up to $250,000/$500,000 of gain on a principal residence can be excluded if the 2-of-5-year ownership and use tests are met."},
      {"term":"Form 706","def":"Federal estate tax return; also the vehicle for portability (DSUE) even when no tax is due."},
      {"term":"DSUE / portability","def":"A deceased spouse's unused exclusion transferred to the surviving spouse by filing a timely Form 706."},
      {"term":"Behavioral Health Services Tax","def":"California's 1% tax on taxable income above $1,000,000 (Form 540 line 62; formerly Mental Health Services Act)."},
      {"term":"NIIT","def":"3.8% federal net investment income tax on investment income once MAGI exceeds $200,000 (single) / $250,000 (joint)."},
      {"term":"Documentary transfer tax","def":"Tax due when real property changes hands — Santa Clara County charges 0.11%; San Francisco's tiered tax reaches 6%."},
      {"term":"Parcel tax","def":"A flat per-parcel charge (like SF Prop H) billed with property tax; not ad valorem."},
      {"term":"Mello-Roos / direct levies","def":"Special assessments for services/bonds that add to the property tax bill outside the 1% base."},
      {"term":"Reinvestment risk","def":"The risk that sale proceeds must be redeployed into markets at unfavorable prices — the mirror image of selling too early."},
      {"term":"Imputed rent","def":"The implicit rental value of living in a home you own — the benefit you forgo when you rent it out instead."},
      {"term":"NEM 3.0 (Net Billing Tariff)","def":"CPUC tariff crediting new solar exports at avoided cost rather than retail rate (effective 2023-04-15)."},
      {"term":"Vacancy decontrol","def":"SF rule allowing market rent reset when a tenant voluntarily vacates a covered unit."},
      {"term":"Black swan","def":"An extreme, hard-to-predict market event (1929, 2008) that invalidates baseline projections."},
      {"term":"Phased entry (dollar-cost averaging)","def":"Investing sale proceeds in tranches over months/years instead of all at once to reduce single-date timing risk."},
      {"term":"Liquidity ratio","def":"Liquid assets ÷ total net worth — how much of the estate can be turned to cash quickly."},
    ]

def suggestions():
    return [
      {"id":"S1","priority":"High","title":"Lock the occupancy decision in writing BEFORE the transfer","body":"Draft a one-page household policy: which path triggers under which conditions (cash size, market level, occupancy intent). Prevents reverse-engineering the answer from a single projection.","owner":"Household + attorney","status":"Proposed"},
      {"id":"S2","priority":"High","title":"Obtain independent valuations and rent comps","body":"Date-of-death appraisal (for basis and Prop 19), plus three rent comparables for Property A. Until then every 'rent' number on this site is a floor.","owner":"Executor / appraiser","status":"Proposed"},
      {"id":"S3","priority":"High","title":"Insurance audit for both properties","body":"Replace the ~$1,500 household guesses with quoted premiums (HO-3 for A; DP-3/landlord for B). Check CDI ZIP-level report for both property ZIPs (internal) context.","owner":"Household + broker","status":"Proposed"},
      {"id":"S4","priority":"High","title":"Estate liquidity plan if the estate may exceed the exclusion","body":"Identify cash/liquid assets covering potential 40% tax within 9 months; discuss §6166 and life-insurance options with counsel.","owner":"Attorney + CPA","status":"Proposed"},
      {"id":"S5","priority":"Medium","title":"Sign an investment policy statement for the proceeds now","body":"Write the allocation, phasing rules (24–36-month Treasury park), rebalancing, and drawdown limits BEFORE any money arrives.","owner":"Household","status":"Proposed"},
      {"id":"S6","priority":"Medium","title":"Annual re-run calendar","body":"Every January: re-run this model; every February 16: check BOE's new Prop 19 cap; every November: check ballot measures; annually verify insurance and rents.","owner":"Household","status":"Proposed"},
      {"id":"S7","priority":"Medium","title":"Add a 'Flagged for Review' triage routine","body":"When any flagged item is resolved (e.g., TRA found, comps obtained), update research/SOURCES.md, re-run model/build_model.py, and redeploy.","owner":"Site maintainer","status":"Proposed"},
      {"id":"S8","priority":"Medium","title":"Pre-agree the black-swan rule","body":"Decide now: if markets fall >30% within 12 months of selling, do we pause the phase-in, speed it up, or hold to schedule? Write it down.","owner":"Household","status":"Proposed"},
      {"id":"S9","priority":"Low","title":"Extend the model to monthly granularity","body":"Annual data smooths crashes; monthly series would sharpen the 1929/2008 entry tests.","owner":"Site maintainer","status":"Proposed"},
      {"id":"S10","priority":"Low","title":"Add per-TRA lookup helper","body":"Once the household shares a TRA number (not the address), pin the published rate into the data table with the county source link.","owner":"Household","status":"Proposed"},
      {"id":"S11","priority":"High","title":"Contain and audit the public GitHub history before claiming privacy is restored","body":"The repository and Pages are currently public; this shallow checkout cannot verify prior commits. First preserve an authorized backup, complete an offline scan of every historical commit and public artifact, agree whether to take the repository/site private or replace it with a clean sanitized history, then coordinate the history rewrite and check forks/caches. Do not force-rewrite shared main as an isolated session action.","owner":"Repository administrator + privacy reviewer","status":"Proposed — high urgency; not implemented"},
    ]

def flags():
    return [
      {"id":"F1","severity":"High","item":"Property A implied tax rate ~1.34% vs published typical TRA ~1.15–1.30%","detail":"Likely direct assessments/Mello-Roos, or a different TRA. Verify against parcel bill. Model uses the implied rate for continuity.","src":"household"},
      {"id":"F2","severity":"High","item":"Property B implied tax rate ~2.14% vs official 1.18162%","detail":"Gap ≈ parcel taxes/direct levies (SFUSD levies etc.) — obtain the bill breakdown.","src":"sf-treasurer"},
      {"id":"F3","severity":"High","item":"Cash inheritance amount undisclosed","detail":"All cash figures on this site are scenarios, not facts.","src":None},
      {"id":"F4","severity":"High","item":"Property A market rent unknown","detail":"HUD FMR floor $3,604 (SF County 2-BR) used as a labeled floor only; Property A comps required before ranking rent path on evidence.","src":"hud-fmr"},
      {"id":"F5","severity":"Medium","item":"Insurance estimates (~$1,500) below CA DOI statewide averages","detail":"Obtain quotes; CDI ZIP-level report holds both property ZIPs (internal) experience data (not extracted here).","src":"cdi-report"},
      {"id":"F6","severity":"Medium","item":"IRC §121(d)(11) statutory text not retrievable this session","detail":"The 2-year post-death tacking rule for inherited homes should be confirmed at uscode.house.gov or with counsel before relying on it.","src":"usc-121"},
      {"id":"F7","severity":"Medium","item":"Nov 2026 election results pre-certification","detail":"SF certification due 2026-12-03; CA results not certified. Treat Prop H pass / Prop I fail as highly likely but pending.","src":"sf-results"},
      {"id":"F8","severity":"Medium","item":"Assessment appeal and installment dates from county guidance","detail":"Official county pages not re-opened this session — verify at santaclaracounty.gov before diarizing.","src":"scc-aab"},
      {"id":"F9","severity":"Medium","item":"Broker/selling cost 5.5% and maintenance 0.75%/1.00% are assumptions","detail":"Not from official sources; adjust via what-if controls.","src":None},
      {"id":"F10","severity":"Low","item":"SF Prop H multifamily rate modeled at $249 floor","detail":"Final amount depends on building area (unknown); $0.195/sqft over 5,000 sqft could raise it.","src":"sf-proph-text"},
      {"id":"F11","severity":"Low","item":"FRED CPIAUCSL link not opened this session","reader":"Inflation history should be cross-checked directly at FRED.","src":"fred-cpi"},
      {"id":"F12","severity":"Low","item":"NEM 3.0 decision PDF not re-opened","detail":"Decision number D.22-12-056 and dates cross-checked via multiple secondary sources; confirm at cpuc.ca.gov.","src":"cpuc-nbt"},
      {"id":"F13","severity":"Low","item":"Third-unit rent for Property B left at $0 in base runs","detail":"Vacant-but-livable unit income unknown; add via what-if slider when comps exist.","src":None},
      {"id":"F14","severity":"Medium","item":"Property B depreciation history unknown (recapture exposure)","detail":"No placed-in-service dates, basis, or prior Form 4562 records held. Recapture table on the Data page is an illustration at assumed depreciation amounts only; obtain the depreciation schedule from the CPA before any sale of B.","src":None},
      {"id":"F15","severity":"High","item":"Path ranking is not tax-complete","detail":"SELL-path portfolio returns are pre-personal-income-tax and rental income tax is not netted; estate tax is not estimated because the full estate, prior gifts and portability facts are missing. These asymmetries may bias the apparent winner. Treat every ranking as provisional and obtain CPA/attorney calculations before relying on it.","src":["irs-i8960","ftb-capgain","irs-706"]},
      {"id":"F16","severity":"High","item":"Public repository and prior Git history not fully privacy-audited","detail":"GitHub reports this repository as public and the Pages site as built/public. This checkout is shallow, so prior commits cannot be inspected comprehensively here; a current-file scan does not scrub previous public commit objects, forks, caches, or third-party copies. No claim of historical scrubbing or complete containment is made. A coordinated history-rewrite/visibility decision and post-change verification are required before calling this resolved.","src":"repo-public"},
    ]

def questions_answers_front():
    """What would change the answer — first-screen content."""
    return [
      {"lever":"Full gross estate, taxable gifts and portability","current":"Unknown — no complete estate inventory or Form 709/706 history","changes":"This can reverse the current estate-tax headline. Include all probate and non-probate property, cash, investments, insurance, debts, marital deductions and any DSUE; the current-year exclusion is not a future threshold guarantee."},
      {"lever":"Cash and other inherited assets","current":"Unknown — model runs only illustrative cash scenarios","changes":"If liquid assets are large, the house decision is a smaller share of the estate; if the taxable estate exceeds the applicable year-of-death exclusion, tax and nine-month liquidity planning become central."},
      {"lever":"Will you occupy Property A long-term?","current":"Open decision","changes":"Occupancy + filing within 1 year preserves a capped Prop 19 base (saves roughly the cap amount × tax rate each year, ~$20k+/yr at 2045 values); not occupying triggers full FMV reassessment."},
      {"lever":"Real market rent for Property A","current":"FMR floor only","changes":"If comps come in well above the floor, RENT path climbs; if below, SELL/LIVE strengthen."},
      {"lever":"Where markets start when the house is sold","current":"Unknowable","changes":"A 1929-style entry destroys lump-sum proceeds; a V-shaped crash (2008) punishes slow phasing. This is why the phased-Treasury path exists."},
      {"lever":"Occupancy intent vs. SF rent control","current":"B generates $7,150/mo now","changes":"If B's leases end or rules tighten, LIVE-in-A becomes relatively more attractive (B income falls)."},
      {"lever":"Prop 19 cap at transfer date","current":"$1,044,586 for 2026–27 transfers","changes":"The cap re-adjusts each Feb 16; a higher cap at 2040s transfer dates widens the occupancy advantage."},
      {"lever":"Future law","current":"Enacted vs proposed tracked separately","changes":"CA 60+ exemption initiative (targeted 2028), federal estate-rate bills, or new SF transfer-tax measures could move the numbers materially."},
    ]

# ----------------------------------------------------------------------------
# 11. WRITE EVERYTHING
# ----------------------------------------------------------------------------
def write(name, obj):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, indent=1, allow_nan=False)
    print("wrote", name)

def main():
    # source registry (compact)
    write("sources.json", {k: {"t": v["t"], "u": v["u"], "o": v["o"], "k": v["k"], "v": v["v"]} for k, v in SOURCES.items()})
    write("tables.json", tables())
    write("timeline.json", timeline())
    write("questions.json", {"questions": questions(), "front": questions_answers_front()})
    write("glossary.json", glossary())
    write("suggestions.json", suggestions())
    write("flags.json", flags())

    # projections for each inheritance year (baseline params)
    proj = {}
    for Y in IN_YEARS:
        params = {"home_g": HOME_G["base"], "stock_g": STOCK_G["base"], "infl": INFL["base"],
                  "bill_g": BILL_G["base"], "a_rent_mo": A_RENT_FLOOR_MO, "park_months": 24,
                  "rent_g": 0.025, "b_third_unit_mo": 0, "cash": 0}
        proj[str(Y)] = project_paths(Y, params)
    write("projection.json", proj)

    # range runs (low/base/high) for sensitivity at 2045 + full stocks×homes grid
    sens = []
    grid = []
    for tag, hg, sg_, infl_ in [("low", HOME_G["low"], STOCK_G["low"], INFL["low"]),
                                ("base", HOME_G["base"], STOCK_G["base"], INFL["base"]),
                                ("high", HOME_G["high"], STOCK_G["high"], INFL["high"])]:
        p = {"home_g": hg, "stock_g": sg_, "infl": infl_, "bill_g": BILL_G["base"],
             "a_rent_mo": A_RENT_FLOOR_MO, "park_months": 24, "rent_g": 0.025,
             "b_third_unit_mo": 0, "cash": 0}
        pr = project_paths(2045, p)
        nw_by_path = {pp["path"]: pp["net_worth"] for pp in pr["paths"]}
        sens.append({"scenario": tag, "home_g": pct(hg), "stock_g": pct(sg_), "infl": pct(infl_),
                     "nw30": {k: v["30"] for k, v in nw_by_path.items()},
                     "nw": {k: v["30"] for k, v in nw_by_path.items()}})
        key = "SELL Property A → lump-sum stocks"
        livek = "LIVE in Property A (Prop 19 claimed)"
        rentk = "RENT Property A (full reassessment)"
        phasek = "SELL Property A → 24-mo Treasury park, then phase 24 mo"
        grid.append({"scenario": tag, "home_g": pct(hg), "stock_g": pct(sg_), "infl": pct(infl_),
                     **{f"{h}y": {"sell": nw_by_path[key][str(h)], "live": nw_by_path[livek][str(h)],
                                  "rent": nw_by_path[rentk][str(h)], "phase": nw_by_path[phasek][str(h)],
                                  "sell_minus_live": nw_by_path[key][str(h)] - nw_by_path[livek][str(h)],
                                  "sell_minus_rent": nw_by_path[key][str(h)] - nw_by_path[rentk][str(h)]}
                        for h in (10, 20, 30)}})
    # full matrix: stocks × homes (inflation at base), inherit 2045
    key = "SELL Property A → lump-sum stocks"
    livek = "LIVE in Property A (Prop 19 claimed)"
    rentk = "RENT Property A (full reassessment)"
    phasek = "SELL Property A → 24-mo Treasury park, then phase 24 mo"
    matrix = []
    for sg_m in (0.06, 0.085, 0.12):
        for hg_m in (0.01, 0.035, 0.055):
            p = {"home_g": hg_m, "stock_g": sg_m, "infl": INFL["base"], "bill_g": BILL_G["base"],
                 "a_rent_mo": A_RENT_FLOOR_MO, "park_months": 24, "rent_g": 0.025,
                 "b_third_unit_mo": 0, "cash": 0}
            pr = project_paths(2045, p)
            nb = {pp["path"]: pp["net_worth"] for pp in pr["paths"]}
            row = {"stocks": sg_m, "home": hg_m, "infl": INFL["base"]}
            for h in (10, 20, 30):
                row[f"at{h}"] = nb[key][str(h)] - nb[livek][str(h)]
                row[f"sell{h}"] = nb[key][str(h)]
                row[f"live{h}"] = nb[livek][str(h)]
                row[f"rent{h}"] = nb[rentk][str(h)]
                row[f"phase{h}"] = nb[phasek][str(h)]
            row["lead30"] = max([("SELL", nb[key]["30"]), ("LIVE", nb[livek]["30"]),
                                 ("RENT", nb[rentk]["30"]), ("PHASE", nb[phasek]["30"])],
                                key=lambda x: x[1])[0]
            matrix.append(row)
    write("sensitivity.json", {"runs": sens, "grid": grid, "matrix": matrix,
                               "stock_stats": {"mean_arith_pct": pct(STOCK_MEAN), "sd_pct": pct(STOCK_SD),
                                               "bill_mean_pct": pct(BILL_MEAN), "n": len(stocks),
                                               "src": "damodaran"}})

    # black swan
    write("blackswan.json", {"entries": blackswan_entries(), "regimes": regime_rows(),
                             "phasing_note": "Annual data; mid-year tranches earn half the year's return (approximation). "
                                             "Park yield assumed at bill-mean scenario rates for forward tests; historical tests use actual T-bill returns."})
    # Monte Carlo
    write("mc.json", monte_carlo())

    # constants for JS what-if lab
    write("model_constants.json", {
        "BASE_YEAR": 2026, "IN_YEARS": IN_YEARS, "A_VALUE_2026": r10(A_VALUE_2026),
        "B_VALUE_2026": r10(B_VALUE_2026), "A_AV_2026": r10(A_AV_2026),
        "A_RATE_IMPL": round(A_RATE_IMPL, 6), "B_RATE_IMPL": round(B_RATE_IMPL, 6),
        "SF_RATE": SF_RATE_2627, "SC_TYPICAL": SC_TYPICAL,
        "HOME_G": HOME_G, "STOCK_G": {k: pct(v) for k, v in STOCK_G.items()},
        "INFL": INFL, "BILL_G": BILL_G,
        "A_INS": r10(A_INS_2026), "B_INS": r10(B_INS_2026), "A_WATER_MO": r10(A_WATER_MO),
        "B_WATER_MO": r10(B_WATER_MO), "A_ELEC_MO": r10(A_ELEC_MO), "B_ELEC_MO": r10(B_ELEC_MO),
        "A_SEWER_YR": r10(A_SEWER_YR), "B_RENT_MO": r10(B_RENT_MO), "PROP_H_MF": r10(PROP_H_MF),
        "A_MAINT_PCT": A_MAINT_PCT, "B_MAINT_PCT": B_MAINT_PCT,
        "A_RENT_FLOOR_MO": r10(A_RENT_FLOOR_MO), "PROP19_CAP_2026": r10(PROP19_CAP_2026),
        "XFER_SC": XFER_SC, "RECORD_FEE": r10(RECORD_FEE), "SELL_COST_PCT": SELL_COST_PCT,
        "MGMT_PCT": MGMT_PCT, "SEC_121": r10(SEC_121_MFJ), "BEA": r10(BEA_2026),
        "ESTATE_RATE": ESTATE_RATE, "CA_TOP_ALLIN": CA_TOP_ALLIN, "FED_TOP_CG": FED_LTCG_TOP + NIIT,
        "HORIZONS": HORIZONS,
        "rounded": True,
    })
    # same-year sale table
    write("same_year_sale.json", [same_year_sale(Y, HOME_G["base"]) for Y in IN_YEARS])
    print("model build complete:", TODAY)

if __name__ == "__main__":
    main()
