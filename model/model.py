"""
Inheritance decision model: Property A (inherited) with Property B (owned) as context.

Rules set by the household (2026-11-25):
  * Every money figure is rounded to the nearest $10 before it is shown.
  * Every input is tagged: FETCHED/EXCERPT (official source opened), SECONDARY (secondary source,
    official link for checking), USER (household figure, held in private/, never published),
    DERIVED (computed), ASSUMPTION (analyst choice, adjustable).
  * Household figures are read from private/raw_inputs.json (gitignored). They are never written
    to data/ and never shown on the site; only rounded results derived from them are published.
  * All paths are compared at the same transfer year T and the same horizon H. Terminal values
    are liquidated after tax, so liquid and illiquid paths compare on the same footing.
  * Results are in real 2026 dollars (2% CPI deflator).

Run:  python3 model/model.py   -> writes data/model_outputs.json. Standard library only.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "model_outputs.json")
BASE_YEAR = 2026


def r10(x):
    """Round to nearest $10 (household rule)."""
    return int(round(x / 10.0) * 10)


# ---------------------------------------------------------------------------
# Inputs (see tools/content.py for the source and status of each row)
# ---------------------------------------------------------------------------
# Household figures live in private/raw_inputs.json (gitignored). Loaded here, never committed.
PRIVATE = os.path.join(HERE, "..", "private", "raw_inputs.json")
if not os.path.exists(PRIVATE):
    raise SystemExit("private/raw_inputs.json is required (internal only, gitignored).")
_RAW = json.load(open(PRIVATE))
_A = _RAW["propertyA"]
A_VALUE_2026 = r10(_A["est_value_nov2026"])          # USER estimate Nov 2026 (not an appraisal)
A_AV_2025 = r10(_A["tax_assessment"]["2025"])        # USER assessment history
A_AV_2026 = r10(_A["tax_assessment"]["2026"])        # USER projection row
A_TAX_2025 = r10(_A["property_tax"]["2025"])         # USER property tax
EFF_RATE = A_TAX_2025 / A_AV_2025               # DERIVED effective rate (tax / assessed value)
ALLOW_2026 = 1044590                            # SECONDARY BOE allowance $1,044,586, rounded to $10
PROP13_FACTOR = 0.02                            # SECONDARY 2026-27 inflation factor 1.02 (cap is 2%)
CPI = 0.02                                      # EXCERPT: CBO PCE inflation 2.0% by 2030

INSURANCE_A = _RAW["insurance_guess_annual_a"]  # USER guess, UNVERIFIED (no official figure found)
WATER_A = sum(_A["water_monthly_range"]) / 2 * 12  # USER range per month, midpoint x 12
SOLAR_CREDIT_A = sum(_A["solar_monthly_credit_range"]) / 2 * 12  # USER range per month, midpoint x 12 (NEM 3.0 risk)
MAINT_A = 0.006                    # ASSUMPTION: 0.6% of value per year
RENT_YIELD_A = 0.0325              # ASSUMPTION: gross rent 3.25% of value (no comps yet)
VACANCY = 0.05                     # ASSUMPTION
MARGINAL_TAX = 0.40                # ASSUMPTION: combined rate on rental income and interest
DEP_BUILDING_SHARE = 0.70          # ASSUMPTION: building share of value (no appraisal yet)
DEP_YEARS = 27.5                   # SECONDARY IRS residential rental recovery period (Pub 527 to check)
SELL_COMMISSION = 0.025            # ASSUMPTION (not a verified rate)
SELL_ESCROW_TITLE = 0.005          # ASSUMPTION
COUNTY_DTT = 1.10 / 1000           # SECONDARY: Santa Clara County $1.10 per $1,000
FED_LTCG = 0.238                   # SECONDARY 20% + 3.8% NIIT (top rates; IRS Rev. Proc. 2025-32 to check)
CA_RATE = 0.133                    # SECONDARY 12.3% + 1% Behavioral Health Services Tax (surcharge: FTB 540-ES, FETCHED)
RECAPTURE_RATE = 0.25              # SECONDARY maximum rate on unrecaptured Sec. 1250 gain (IRS Pub 527 to check)
SEC121_EXCLUSION = 250000          # SECONDARY single filer (MFJ: $500,000; IRS Pub 523 to check)
EQUITY_W = 0.60                    # ASSUMPTION: 60/40 portfolio
BOND_YIELD = 0.044                 # EXCERPT anchor: CBO 10-year Treasury 4.4% (2031-35)
PARK_YIELD = 0.035                 # ASSUMPTION: 3M-2Y Treasury parking; spot 3M 4.36%, 2Y 4.63%
EQUITY_TAX_DRAG = 0.005            # ASSUMPTION per year
LIQUIDATION_TAX = 0.25             # ASSUMPTION: tax on embedded portfolio gains at liquidation

APPRECIATION = {"low": 0.000, "base": 0.025, "high": 0.045}    # ASSUMPTION (Property A nominal)
EQUITY_RETURN = {"low": 0.040, "base": 0.065, "high": 0.085}   # ASSUMPTION (equity nominal)
CREDIT_CHOICES = [0.0, 0.5, 1.0]   # share of imputed rent counted as saved cash in living years
TRANSFER_YEARS = [2040, 2045, 2050]
HORIZONS = [10, 20]

PATHS = {
    "S":      "Sell at transfer; invest proceeds in one lump sum",
    "SP24":   "Sell at transfer; park in 3M-2Y Treasuries 24 months; phase into stocks over 12 months",
    "SP36":   "Sell at transfer; park in 3M-2Y Treasuries 36 months; phase into stocks over 12 months",
    "R":      "Rent long-term (not occupied); sell at horizon",
    "L":      "Live in it long-term (primary residence); sell at horizon",
    "L2S":    "Mixed: live 2 years, then sell",
    "L5S":    "Mixed: live 5 years, then sell",
    "R10S":   "Mixed: rent 10 years, then sell",
    "L5R_B":  "Mixed: live 5 years, then rent (move-out reading B: base = value at transfer)",
    "L5R_A":  "Mixed: live 5 years, then rent (move-out reading A: base = Prop 19 base carried)",
}
PARK_MONTHS = {"SP24": 24, "SP36": 36}


def fbyv(years):
    """Factored base-year value of the parent's assessment (Prop 13 factor per year)."""
    return A_AV_2026 * (1 + PROP13_FACTOR) ** years


def prop19_base(fmv_T, T):
    """Taxable value after a qualifying Prop 19 family-home transfer.
    New value = factored base + any market value above (factored base + allowance).
    The allowance grows with the factor (ASSUMPTION; BOE adjusts it every two years)."""
    y = T - BASE_YEAR
    base = fbyv(y)
    limit = base + ALLOW_2026 * (1 + PROP13_FACTOR) ** y
    return base if fmv_T <= limit else base + (fmv_T - limit)


def sale_tax(fmv_s, fmv_T, dep_accum, lived_last60):
    """Net proceeds and tax on a sale. Basis = value at transfer (step-up, IRC 1014) less depreciation."""
    net = fmv_s * (1 - SELL_COMMISSION - SELL_ESCROW_TITLE - COUNTY_DTT)
    gain = net - (fmv_T - dep_accum)
    recap = min(max(gain, 0.0), dep_accum)
    rest = max(gain - recap, 0.0)
    excl = min(rest, SEC121_EXCLUSION) if lived_last60 >= 24 else 0.0
    tax = recap * (RECAPTURE_RATE + CA_RATE) + max(rest - excl, 0.0) * (FED_LTCG + CA_RATE)
    return net, tax


def simulate(path, T, H, g, mu, credit, yearly_g=None, yearly_mu=None):
    """Simulate one path monthly from transfer (month 0) to horizon (month 12H).
    g: annual appreciation (constant unless yearly_g given); mu: annual equity return (or yearly_mu).
    credit: share of imputed rent saved as cash in living months (ASSUMPTION choice).
    Returns real 2026 dollars, rounded to $10."""
    months = H * 12
    fmv_T = A_VALUE_2026 * (1 + g) ** (T - BASE_YEAR)
    tv_p19 = prop19_base(fmv_T, T)
    tv_full = fmv_T

    # Schedule per path: months when living, sale month, taxable base, parking months
    sched = {
        "S":     dict(live_to=0, sell_at=0, base=tv_full, rent_from=None),
        "SP24":  dict(live_to=0, sell_at=0, base=tv_full, rent_from=None),
        "SP36":  dict(live_to=0, sell_at=0, base=tv_full, rent_from=None),
        "R":     dict(live_to=0, sell_at=None, base=tv_full, rent_from=0),
        "L":     dict(live_to=None, sell_at=None, base=tv_p19, rent_from=None),
        "L2S":   dict(live_to=24, sell_at=24, base=tv_p19, rent_from=None),
        "L5S":   dict(live_to=60, sell_at=60, base=tv_p19, rent_from=None),
        "R10S":  dict(live_to=0, sell_at=120, base=tv_full, rent_from=0),
        "L5R_B": dict(live_to=60, sell_at=None, base=tv_full, rent_from=60),
        "L5R_A": dict(live_to=60, sell_at=None, base=tv_p19, rent_from=60),
    }[path]
    live_to = months if sched["live_to"] is None else min(sched["live_to"], months)
    sell_at = sched["sell_at"]
    base_taxable = sched["base"]
    rent_from = sched["rent_from"]
    pm = PARK_MONTHS.get(path, 0)

    m_port_fixed = None
    port = 0.0       # invested pool
    contrib = 0.0    # cumulative deposits into the pool (for liquidation tax basis)
    park = 0.0       # parked cash (3M-2Y Treasuries)
    fmv = fmv_T
    dep_accum = 0.0
    lived = []       # 1 if living that month, else 0 (for Sec. 121 look-back)
    sold = False
    m_park = (1 + PARK_YIELD * (1 - MARGINAL_TAX)) ** (1 / 12) - 1

    def m_port_for(mu_y):
        ann = EQUITY_W * mu_y + (1 - EQUITY_W) * BOND_YIELD * (1 - MARGINAL_TAX)
        return (1 + ann) ** (1 / 12) - 1 - EQUITY_TAX_DRAG / 12

    # ----- Sale at transfer (t = 0) for paths that sell immediately -----
    if sell_at == 0:
        net, tax = sale_tax(fmv_T, fmv_T, 0.0, 0)
        proceeds = net - tax
        if pm:
            park = proceeds
        else:
            port = proceeds
        contrib = proceeds
        sold = True

    m_port = m_port_for(mu)
    for t in range(1, months + 1):
        k = (t - 1) // 12  # year index
        if yearly_g is not None:
            g_m = (1 + yearly_g[k]) ** (1 / 12) - 1
        else:
            g_m = (1 + g) ** (1 / 12) - 1
        fmv = fmv * (1 + g_m)
        if yearly_mu is not None:
            m_port = m_port_for(yearly_mu[k])
        elif (t - 1) % 12 == 0:
            m_port = m_port_for(mu)

        # ----- Property cash flows while owned -----
        if not sold:
            infl = (1 + PROP13_FACTOR) ** (t / 12)
            ptax_m = EFF_RATE * base_taxable * (1 + PROP13_FACTOR) ** (t / 12) / 12
            ins_m = INSURANCE_A * infl / 12
            water_m = WATER_A * infl / 12
            maint_m = MAINT_A * fmv / 12
            solar_m = SOLAR_CREDIT_A * infl / 12
            costs_m = ins_m + water_m + maint_m + ptax_m - solar_m
            if t <= live_to:
                saved = credit * RENT_YIELD_A * fmv / 12   # avoided rent kept as cash
                flow = saved - costs_m
                lived.append(1)
            elif rent_from is not None and t > rent_from:
                rent_m = RENT_YIELD_A * fmv * (1 - VACANCY) / 12
                dep_m = DEP_BUILDING_SHARE * fmv_T / (DEP_YEARS * 12)
                dep_accum += dep_m
                taxable = rent_m - ins_m - water_m - maint_m - ptax_m - dep_m
                flow = rent_m - costs_m - MARGINAL_TAX * taxable   # after-tax net rent
                lived.append(0)
            else:
                flow = -costs_m   # owned but neither lived in nor rented (not used by the paths above)
                lived.append(0)
            # Net cash flows are deposits (or withdrawals) that form the cost basis of the pool
            port += flow
            contrib += flow

        # ----- Parked cash and phase-in (SP24, SP36) -----
        if park > 0:
            if t <= pm:
                park *= (1 + m_park)
            elif t <= pm + 12:
                remaining = pm + 12 - (t - 1)
                buy = park / remaining
                park -= buy          # moves existing money; basis already counted at sale
                port += buy
                park *= (1 + m_park)
            else:
                park *= (1 + m_park)
        if port != 0:
            port *= (1 + m_port)

        # ----- Scheduled sale -----
        if not sold and sell_at is not None and t == sell_at:
            lived_last60 = sum(lived[-60:])
            net, tax = sale_tax(fmv, fmv_T, dep_accum, lived_last60)
            port += net - tax
            contrib += net - tax
            sold = True

    # ----- Horizon liquidation for paths still holding the house -----
    if not sold:
        lived_last60 = sum(lived[-60:])
        net, tax = sale_tax(fmv, fmv_T, dep_accum, lived_last60)
        port += net - tax
        contrib += net - tax

    port += park
    gain = max(port - contrib, 0.0)
    liquid_nominal = port - LIQUIDATION_TAX * gain
    real = liquid_nominal / ((1 + CPI) ** H)
    return r10(real)


# ---------------------------------------------------------------------------
# Grids, break-evens, black-swan test, Monte Carlo, projections
# ---------------------------------------------------------------------------
def run_grid():
    grid = []
    for T in TRANSFER_YEARS:
        for H in HORIZONS:
            for ap_key, g in APPRECIATION.items():
                for eq_key, mu in EQUITY_RETURN.items():
                    for c in CREDIT_CHOICES:
                        results = {p: simulate(p, T, H, g, mu, c) for p in PATHS}
                        grid.append({"T": T, "H": H, "appreciation": ap_key, "equity": eq_key,
                                     "credit": c, "results": results})
    return grid


def breakeven(path_a, path_b, key, lo, hi, base):
    """Find the value of one input where two paths tie (bisection). None if no sign change."""
    def diff(x):
        kw = dict(base)
        kw[key] = x
        return simulate(path_a, kw["T"], kw["H"], kw["g"], kw["mu"], kw["c"]) - \
               simulate(path_b, kw["T"], kw["H"], kw["g"], kw["mu"], kw["c"])
    f_lo, f_hi = diff(lo), diff(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(50):
        mid = (lo + hi) / 2
        f_mid = diff(mid)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return round((lo + hi) / 2, 4)


def crash_test():
    """Stock-only stylised test. Sale and the crash peak are at month 0 for 'start=0'.
    Depth and peak-to-trough/recovery durations are VERIFIED-secondary facts used as shape only:
      1929-type: -86.2% over ~32 months (Sep 1929 to Jun 1932), back to peak after ~300 months.
      2008-type: -56.8% over ~17 months (Oct 2007 to Mar 2009), back to peak after ~66 months.
    Values are index multiples of the amount invested at month 0 (nominal)."""
    scenarios = {
        "1929-type": {"depth": 0.862, "down": 32, "recover": 300},
        "2008-type": {"depth": 0.568, "down": 17, "recover": 66},
        "No crash": {"depth": 0.0, "down": 1, "recover": 1},
    }
    m_eq = (1 + EQUITY_RETURN["base"]) ** (1 / 12) - 1 - EQUITY_TAX_DRAG / 12
    m_park = (1 + PARK_YIELD * (1 - MARGINAL_TAX)) ** (1 / 12) - 1
    horizon = 240

    def index_path(sc, start):
        lvl = [1.0]
        for t in range(1, horizon + 1):
            if sc["depth"] == 0 or t <= start:
                lvl.append((1 + m_eq) ** t)
                continue
            pre = (1 + m_eq) ** start
            tr = t - start
            trough = pre * (1 - sc["depth"])
            if tr <= sc["down"]:
                lvl.append(pre * (1 - sc["depth"]) ** (tr / sc["down"]))
            elif tr <= sc["recover"]:
                frac = (tr - sc["down"]) / (sc["recover"] - sc["down"])
                lvl.append(trough * (pre / trough) ** frac)
            else:
                lvl.append(pre * (1 + m_eq) ** (tr - sc["recover"]))
        return lvl

    def phased(idx, pm, horizon_m):
        park_val, units = 1.0, 0.0
        for t in range(1, horizon_m + 1):
            if t <= pm:
                park_val *= (1 + m_park)
            elif t <= pm + 12:
                buy = park_val / (pm + 12 - (t - 1))
                park_val -= buy
                units += buy / idx[t]
                park_val *= (1 + m_park)
            else:
                park_val *= (1 + m_park)
        return park_val + units * idx[horizon_m]

    out = {}
    for name, sc in scenarios.items():
        for start in [0, 12, 24, 36]:
            idx = index_path(sc, start)
            out[f"{name}|{start}"] = {
                "lump_10y": round(idx[120], 4),
                "lump_20y": round(idx[240], 4),
                "phase24_10y": round(phased(idx, 24, 120), 4),
                "phase24_20y": round(phased(idx, 24, 240), 4),
                "phase36_10y": round(phased(idx, 36, 120), 4),
                "phase36_20y": round(phased(idx, 36, 240), 4),
                "depth_pct": round(sc["depth"] * 100, 1),
            }
    return out


def monte_carlo(T=2045, H=20, credit=0.0, n=2000, seed=20261125):
    """Distribution of real terminal values, 2026 dollars.
    ASSUMPTION distributions (not sourced): annual equity return ~ N(6.5%, 15%);
    annual Property A appreciation ~ N(2.5%, 4%). Common random numbers across paths."""
    rng = random.Random(seed)
    res = {p: [] for p in PATHS}
    for _ in range(n):
        yg = [rng.gauss(APPRECIATION["base"], 0.04) for _ in range(H)]
        ym = [rng.gauss(EQUITY_RETURN["base"], 0.15) for _ in range(H)]
        for p in PATHS:
            res[p].append(simulate(p, T, H, APPRECIATION["base"], EQUITY_RETURN["base"], credit,
                                   yearly_g=yg, yearly_mu=ym))
    summary = {}
    for p, vals in res.items():
        s = sorted(vals)
        pct = lambda q: s[int(q * (len(s) - 1))]
        summary[p] = {"p10": r10(pct(0.10)), "p50": r10(pct(0.50)), "p90": r10(pct(0.90)),
                      "mean": r10(sum(s) / len(s))}
    hist = {}
    for p in ("S", "R", "L"):
        lo, hi = min(res[p]), max(res[p])
        width = (hi - lo) / 20 or 1
        counts = [0] * 20
        for v in res[p]:
            counts[min(int((v - lo) / width), 19)] += 1
        hist[p] = {"lo": r10(lo), "width": r10(width), "counts": counts}
    return {"summary": summary, "histogram": hist, "n": n, "seed": seed}


def projection_table(T=2045):
    """Year-by-year base-case projection for Property A, 2027-2070 (nominal). Household costs omitted."""
    rows = []
    g = APPRECIATION["base"]
    for year in range(2027, 2071):
        yrs = year - BASE_YEAR
        value = A_VALUE_2026 * (1 + g) ** yrs
        if year < T:
            tv_live = tv_rent = fbyv(yrs)
        else:
            fmv_T = A_VALUE_2026 * (1 + g) ** (T - BASE_YEAR)
            tv_live = prop19_base(fmv_T, T) * (1 + PROP13_FACTOR) ** (year - T)
            tv_rent = fmv_T * (1 + PROP13_FACTOR) ** (year - T)
        rows.append({
            "year": year,
            "market_value": r10(value),
            "assessed_no_transfer": r10(fbyv(yrs)),
            "taxable_if_living_prop19": r10(tv_live),
            "taxable_if_rented": r10(tv_rent),
            "property_tax_if_living": r10(tv_live * EFF_RATE),
            "property_tax_if_rented": r10(tv_rent * EFF_RATE),
        })
    return rows


def run_all():
    base = {"T": 2045, "H": 20, "g": APPRECIATION["base"], "mu": EQUITY_RETURN["base"], "c": 0.0}
    base_results = {p: simulate(p, 2045, 20, base["g"], base["mu"], 0.0) for p in PATHS}
    be = {
        "credit_for_live_to_tie_sell": breakeven("L", "S", "c", 0.0, 1.0, base),
        "equity_for_rent_to_tie_sell": breakeven("R", "S", "mu", 0.0, 0.15, base),
        "appreciation_for_rent_to_tie_sell": breakeven("R", "S", "g", -0.02, 0.15, base),
        "appreciation_for_live_credit0_to_tie_sell": breakeven("L", "S", "g", -0.02, 0.15, base),
    }
    return {
        "meta": {
            "generated_for_date": "2026-11-25",
            "transfer_years": TRANSFER_YEARS,
            "horizons_years": HORIZONS,
            "base_case": {"transfer_year": 2045, "horizon_years": 20,
                          "appreciation": APPRECIATION["base"], "equity_return": EQUITY_RETURN["base"],
                          "imputed_credit": 0.0},
            "rounding": "Nearest $10. Real = 2026 dollars (2% deflator).",
        },
        "derived_inputs_note": "Household inputs are private; only rounded results are published.",
        "paths": PATHS,
        "base_results_real_2026": base_results,
        "breakevens": be,
        "grid": run_grid(),
        "crash_test": crash_test(),
        "monte_carlo": monte_carlo(),
        "projection_base": projection_table(2045),
    }


if __name__ == "__main__":
    data = run_all()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print("wrote", os.path.normpath(OUT))
    for p, v in data["base_results_real_2026"].items():
        print(f"{p:7s} {v:>14,}")
    print("breakevens:", data["breakevens"])
