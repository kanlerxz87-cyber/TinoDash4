"""
engine.py — the decision model. Deterministic core + block-bootstrap Monte Carlo.

Reproduce with:  cd model && python3 engine.py            (prints a summary)
                 cd model && python3 build_site.py         (writes the site data + pages)

Framing decisions, stated so a reviewer can attack them rather than discover them:
  1. All paths share one transfer year and one horizon, so every comparison is like-for-like.
  2. Wealth accumulation is the ranking objective. The *use value* of the housing the household
     consumes (imputed rent on whatever owned unit they occupy) is computed and reported as a
     separate column and as an optional ranking adjustment - never folded silently into wealth.
     Occupying Property A consumes a $3.1M house's rental value; occupying a unit at Property B
     consumes much less. That difference is a lifestyle fact, not a return, so it is shown, not hidden.
  3. Taxes are computed at top marginal rates (the household is assumed to stay there), on ranges.
  4. Rental losses are treated as SUSPENDED (no offset against other income): the passive-activity
     rules and the $100k-$150k phase-out make that the likely answer. Flagged as an assumption.
  5. No mortgage is modelled on either building (none was reported). If one exists, the ranking
     can change: see question Q-16 and the "debt" row on /model.html.
  6. Nothing in this file is a "verified fact". The verified facts are the rule parameters it
     reads from inputs.py, each with its source and status.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inputs import PROPERTY_A, PROPERTY_B, RULES, ECON, TRANSACT, PHASING, r10  # noqa: E402
import history  # noqa: E402

SEED = 20261125
N_SIMS = 1200
BLOCK = 3

FED_ORD_TOP = 0.370
FED_LTCG = RULES["fed_ltcg_top"] + RULES["niit"]      # 20% + 3.8%
FED_1250 = RULES["fed_1250_cap"] + RULES["niit"]       # 25% + 3.8%
CA_TOP = RULES["ca_top"] + RULES["ca_bhst"]            # 12.3% + 1%
MARG_ORD = FED_ORD_TOP + CA_TOP                        # 50.3%
PORTF_YIELD = 0.015
PORTF_TAX = FED_LTCG + CA_TOP
DISC = ECON["discount_rate"]
FINANCE_SPREAD = 0.00   # opportunity-cost convention: the household account earns/costs bills
SURPLUS_TO_EQUITY = False  # what-if toggle: banked rental surplus invested in the index
B_DEPR_BASIS = 600_000      # ASSUMPTION (unverified): depreciable basis of Property B
B_RESID_BASIS = 700_000     # ASSUMPTION (unverified): B's income-tax basis for the terminal calc
OTHER_PARCEL_A = 0.0        # SCVWD parcel charges left at zero and flagged (see F-12)


# ------------------------------------------------------------ Prop 19 maths ----
def prop19_taxable_value(fbyv, market, allowance):
    cap = fbyv + allowance
    excess = max(0.0, market - cap)
    return fbyv + excess, cap, excess


def prop19_allowance_at(year, base_year=2026, base=RULES["prop19_indexed_amount"], growth=0.02):
    """Carry the published amount forward. Indexing rule (FHFA HPI, biennial) is official;
    the 2%/yr used for future years is our assumption and is flagged."""
    return base * (1 + growth) ** (year - base_year)


def assessed_series(base_av, market_at_transfer, excluded, years):
    start = base_av if excluded else market_at_transfer
    out, v = [], start
    for _ in range(years + 1):
        out.append(v)
        v *= (1 + RULES["prop13_factor_cap"])
    return out


# ---------------------------------------------------------------- the paths ----
def path_specs():
    return [
        dict(id="P-01", name="Live in A; B keeps two tenants, third unit vacant",
             group="live", a="occupied", b_occupy=False, b_rent_vacant=False,
             sell_a=None, prop19=True, invest=dict(policy="lump", park=0, phase=1)),
        dict(id="P-02", name="Live in A; also let B's vacant unit",
             group="live", a="occupied", b_occupy=False, b_rent_vacant=True,
             sell_a=None, prop19=True, invest=dict(policy="lump", park=0, phase=1)),
        dict(id="P-03", name="Live in B's vacant unit; let the whole of A",
             group="rent", a="rented", b_occupy=True, b_rent_vacant=False,
             sell_a=None, prop19=False, invest=dict(policy="lump", park=0, phase=1)),
        dict(id="P-04", name="Live in A 3 years (Prop 19 claimed), sell, move to B",
             group="mixed", a="occupied", b_occupy=False, b_rent_vacant=False,
             sell_a=3, prop19=True, invest=dict(policy="phase", park=24, phase=24),
             switch_to="occupied_b"),
        dict(id="P-05", name="Sell in the year of the death; invest at once (lump sum)",
             group="sell", a="sold", b_occupy=True, b_rent_vacant=False,
             sell_a=0, prop19=False, invest=dict(policy="lump", park=0, phase=1)),
        dict(id="P-06", name="Sell at death; 24 months in 3M-2Y Treasuries, 24-month phase-in",
             group="stage", a="sold", b_occupy=True, b_rent_vacant=False,
             sell_a=0, prop19=False, invest=dict(policy="phase", park=24, phase=24)),
        dict(id="P-07", name="Sell at death; 36 months parked, 36-month phase-in",
             group="stage", a="sold", b_occupy=True, b_rent_vacant=False,
             sell_a=0, prop19=False, invest=dict(policy="phase", park=36, phase=36)),
        dict(id="P-08", name="Let A for 10 years, then sell (never a principal residence)",
             group="rent", a="rented", b_occupy=True, b_rent_vacant=False,
             sell_a=10, prop19=False, invest=dict(policy="phase", park=12, phase=12)),
        dict(id="P-09", name="Live in A 12 years (Prop 19 + section 121), then sell; move to B",
             group="mixed", a="occupied", b_occupy=False, b_rent_vacant=False,
             sell_a=12, prop19=True, invest=dict(policy="phase", park=12, phase=12)),
        dict(id="P-10", name="A as a permanent rental, sold at year 30",
             group="rent", a="rented", b_occupy=True, b_rent_vacant=False,
             sell_a=30, prop19=False, invest=dict(policy="lump", park=0, phase=1)),
        dict(id="P-11", name="Live in A 2 years, let it 8, sell at year 10",
             group="mixed", a="occupied", b_occupy=False, b_rent_vacant=True,
             sell_a=10, prop19=True, invest=dict(policy="phase", park=24, phase=24),
             switch_to="rented", switch_at=2),
        dict(id="P-12", name="Hold A vacant as a legacy/fallback; live in B, let both B units",
             group="hold", a="vacant", b_occupy=True, b_rent_vacant=False,
             sell_a=None, prop19=False, invest=dict(policy="lump", park=0, phase=1)),
    ]


def _mode_at(spec, y):
    mode = spec["a"]
    if spec.get("switch_at") is not None and y >= spec["switch_at"]:
        mode = spec.get("switch_to", mode)
    if spec["sell_a"] is not None and y >= spec["sell_a"]:
        mode = "sold"
    return mode


def _occupied_A(spec, y):
    return _mode_at(spec, y) == "occupied"


def annual_rate(econ_sp_x, y):
    return econ_sp_x[y] if isinstance(econ_sp_x, (list, tuple)) else econ_sp_x


# ------------------------------------------------------------------ the sim ----
def simulate(spec, horizon, econ, detailed=False, rent_mult=1.0):
    home_g, rent_g, infl, spx, bill = econ
    T = ECON["transfer_year"]
    A, B = PROPERTY_A, PROPERTY_B
    rateA, rateB = RULES["sc_rate_central"], RULES["sf_rate_central"]
    allow = prop19_allowance_at(T)

    vA = float(A["value_2026"])
    vB = float(B["value_2026"])
    for _ in range(T - 2026):
        vA *= (1 + home_g)
        vB *= (1 + home_g)
    vA_T, vB_T = vA, vB

    fbyv_T = A["assessed_2026"] * (1 + RULES["prop13_factor_cap"]) ** (T - 2026)
    new_av, cap, excess = prop19_taxable_value(fbyv_T, vA_T, allow)
    avA = assessed_series(new_av, vA_T, spec["prop19"], horizon)
    avB = B["assessed_2025"] * (1 + RULES["prop13_factor_cap"]) ** (T - 2025)

    basis_A = vA_T                        # IRC s.1014 step-up at the date of death
    depr_taken = 0.0
    depr_B = B_DEPR_BASIS / RULES["depr_life_resid"]

    ins_A = 2_400.0
    ins_B = 3_000.0
    water_A = sum(A["water_mo"]) / 2.0
    elec_A = sum(A["electric_mo_net"]) / 2.0
    maint_A_pct = sum(A["maintenance_pct_of_value"]) / 2.0
    maint_B_pct = sum(B["maintenance_pct_of_value"]) / 2.0
    rent_A0 = sum(A["rent_mo_range"]) / 2.0 * rent_mult
    rent_B_vac0 = sum(B["vacant_unit_rent_mo"]) / 2.0
    rent_B = float(B["rent_roll_mo"]) * 12
    mgmt_A = sum(A["property_mgmt_pct"]) / 2.0
    mgmt_B = sum(B["property_mgmt_pct"]) / 2.0

    portfolio = 0.0
    cost_basis = 0.0
    pending = 0.0
    park_left = phase_left = 0.0
    phase_amt = 0.0
    sale_done = False
    rows = []
    min_wealth = None
    use_pv = 0.0
    acct = 0.0
    capex_add = 0.0

    for y in range(horizon + 1):
        year = T + y
        mode = _mode_at(spec, y)
        # does the household occupy a unit of Property B this year?
        occupying_B = spec["b_occupy"] or (spec.get("switch_to") == "occupied_b"
                                          and spec["sell_a"] is not None and y >= spec["sell_a"])
        vA_y = vA_T * (1 + home_g) ** y
        tax_A_y = avA[y] * rateA + OTHER_PARCEL_A * (1 + 0.02) ** y
        ins_A_y = ins_A * (1 + max(infl, ECON["insurance_growth"]["mid"])) ** y
        water_A_y = water_A * (1 + infl) ** y
        elec_A_y = elec_A * (1 + infl) ** y
        maint_A_y = maint_A_pct * vA_y
        rent_A_y = rent_A0 * 12 * (1 + min(rent_g, RULES["ab1482_cap"][1])) ** y
        tax_B_y = avB * (1 + RULES["prop13_factor_cap"]) ** y * rateB \
            + RULES["sf_prop_h_multifamily_base"] * (1 + 0.02) ** y

        cash = 0.0
        if mode == "occupied":
            cash -= (tax_A_y + ins_A_y + water_A_y + elec_A_y + maint_A_y)
            use_pv += (rent_A0 * 12 * (1 + rent_g) ** y) / ((1 + DISC) * (1 + infl)) ** y
        elif mode == "vacant":
            cash -= (tax_A_y + ins_A_y + water_A_y + elec_A_y + maint_A_y * 0.45)
        elif mode == "rented":
            gross = rent_A_y * 0.95
            opex = tax_A_y + ins_A_y + water_A_y + elec_A_y + maint_A_y + mgmt_A * gross
            noi = gross - opex
            dnow = (basis_A * 0.75) / RULES["depr_life_resid"]
            taxable = max(0.0, noi - dnow)
            cash += noi - taxable * MARG_ORD
            depr_taken += min(dnow, max(0.0, noi))
            capex_add += maint_A_y * 0.35

        b_rent = rent_B * (1 + min(rent_g, RULES["ab1482_cap"][1])) ** y
        if spec["b_rent_vacant"]:
            b_rent += rent_B_vac0 * 12 * (1 + min(rent_g, RULES["ab1482_cap"][1])) ** y
        b_cost = (sum(B["water_mo"]) / 2.0 * (1 + infl) ** y
                  + sum(B["electric_mo"]) / 2.0 * (1 + infl) ** y
                  + ins_B * (1 + max(infl, 0.05)) ** y
                  + maint_B_pct * vB_T * (1 + home_g) ** y
                  + tax_B_y + mgmt_B * b_rent)
        b_noi = b_rent - b_cost
        b_tax = max(0.0, b_noi - depr_B) * MARG_ORD
        cash += b_noi - b_tax
        if occupying_B:
            use_pv += (rent_B_vac0 * 12 * 0.9 * (1 + rent_g) ** y) / ((1 + DISC) * (1 + infl)) ** y

        if (not sale_done) and spec["sell_a"] is not None and y == spec["sell_a"]:
            t = TRANSACT["A"]
            costs = vA_y * (t["commission_pct"] + t["seller_concessions_pct"]
                            + t["dtt_pct"] + t["prep_pct"]) + t["closing_flat"]
            net = vA_y - costs
            adj_basis = basis_A + capex_add - depr_taken
            gain = max(0.0, net - adj_basis)
            occ5 = sum(1 for k in range(max(0, y - 4), y + 1) if _occupied_A(spec, k))
            excl = min(RULES["sec121_single"], gain) if (occ5 >= 2 and spec["a"] == "occupied") else 0.0
            taxable_gain = max(0.0, gain - excl)
            rec = min(depr_taken, taxable_gain)
            tax = rec * FED_1250 + (taxable_gain - rec) * FED_LTCG + taxable_gain * CA_TOP
            pending = net - tax
            if spec["invest"]["policy"] == "phase":
                park_left = spec["invest"]["park"] / 12.0
                phase_left = max(spec["invest"]["phase"] / 12.0, 1e-9)
                phase_amt = pending / phase_left if phase_left > 1e-6 else pending
            else:
                portfolio += pending
                cost_basis += pending
                pending = 0.0
            sale_done = True
        elif mode == "occupied" or mode == "vacant":
            capex_add += maint_A_y * 0.35

        if pending > 0:
            pending *= (1 + max(annual_rate(bill, y), -0.02))
            if park_left > 0:
                park_left -= 1.0
            elif phase_left > 0:
                step = min(phase_amt, pending)
                pending -= step
                portfolio += step
                cost_basis += step
                phase_left -= 1.0
            if park_left <= 0 and phase_left <= 0 and pending > 0:
                portfolio += pending
                cost_basis += pending
                pending = 0.0

        # ---- path cash flow runs through the household account at the bill rate ----
        # (opportunity-cost convention: deficits are funded from, and surpluses banked into,
        #  short-dated bills. The what-if page can instead route surpluses into the index.)
        r_acct = max(annual_rate(bill, y), -0.02) + FINANCE_SPREAD
        acct = acct * (1 + r_acct) + cash
        if SURPLUS_TO_EQUITY and acct > 0 and portfolio >= 0:
            growth_part = acct * annual_rate(spx, y)
            portfolio += acct
            cost_basis += acct
            acct = 0.0
            portfolio += growth_part * 0.0
        if portfolio > 0:
            income = portfolio * PORTF_YIELD
            growth = (portfolio - income) * annual_rate(spx, y)
            portfolio += income + growth - income * PORTF_TAX


        ownA = 0.0 if mode == "sold" else vA_y
        total = portfolio + pending + ownA + vB_T * (1 + home_g) ** y + acct
        min_wealth = total if min_wealth is None else min(min_wealth, total)

        if detailed:
            g = mode == "sold"        # once sold there is no assessment, no rent and no upkeep
            rows.append(dict(year=year, mode=mode, valueA=None if g else r10(vA_y),
                             assessedA=None if g else r10(avA[y]),
                             taxA=None if g else r10(tax_A_y),
                             upkeepA=None if g else r10(ins_A_y + water_A_y + elec_A_y + maint_A_y),
                             rentA=None if g else r10(rent_A_y), cashA=r10(cash),
                             noiB=r10(b_noi), taxB=r10(tax_B_y), bOcc=("yes" if occupying_B else "no"),
                             portfolio=r10(portfolio + pending), wealth=r10(total)))

    def liquidate(value, basis, primary, depr=0.0):
        t = TRANSACT["A"]
        costs = value * (t["commission_pct"] + t["prep_pct"] + t["dtt_pct"]) + t["closing_flat"]
        gain = max(0.0, value - costs - basis)
        excl = min(RULES["sec121_single"], gain) if primary else 0.0
        taxable = max(0.0, gain - excl)
        rec = min(depr, taxable)
        tax = rec * FED_1250 + (taxable - rec) * FED_LTCG + taxable * CA_TOP
        return value - costs - tax

    mode_end = _mode_at(spec, horizon)
    vA_end = vA_T * (1 + home_g) ** horizon
    resid = liquidate(vA_end, basis_A + capex_add - depr_taken,
                      spec["a"] == "occupied", depr_taken) if mode_end != "sold" else 0.0
    b_end = liquidate(vB_T * (1 + home_g) ** horizon, B_RESID_BASIS, False)
    unreal = max(0.0, portfolio - cost_basis)
    final = portfolio + pending + resid + b_end + acct - unreal * (FED_LTCG + CA_TOP)
    infl_tot = (1 + infl) ** horizon
    real = final / infl_tot
    pv = real / (1 + DISC) ** horizon
    return dict(id=spec["id"], final_nominal=final, final_real=real,
                use_value_pv=use_pv,
                pv_real=pv, pv_with_use=pv + use_pv,
                min_wealth_real=min_wealth / infl_tot,
                cash_flow_min=min([r["cashA"] for r in rows], default=0.0) if detailed else 0.0,
                acct=acct,
                rows=rows if detailed else None, portfolio=portfolio, resid=resid)


def econ_draw(rng, horizon):
    """Block bootstrap (contiguous 3-year blocks) of the historical annual series, so the
    sequence of returns - not just the average - is real. Home-value growth, rent growth and
    inflation are drawn per simulation from the assumption ranges in inputs.py."""
    yrs = history.YEARS
    n = len(yrs)
    spx_seq, bill_seq = [], []
    while len(spx_seq) < horizon + 1:
        start = rng.randrange(0, n - BLOCK)
        for j in range(BLOCK):
            y = yrs[start + j]
            spx_seq.append(history.SPX[y])
            bill_seq.append(history.BILL[y])
    spx_seq = spx_seq[:horizon + 1]
    bill_seq = bill_seq[:horizon + 1]
    regime = rng.choice([1.0, 1.0, 1.0, 1.25, 0.75])   # mild regime multiplier, fat-but-not-silly tails
    spx_seq = [max(-0.60, min(0.70, r * regime)) for r in spx_seq]
    home = max(-0.03, min(0.12, rng.gauss(ECON["home_value_growth"]["mid"], 0.021)))
    infl = max(-0.01, min(0.09, rng.gauss(ECON["inflation"]["mid"], 0.011)))
    rent = max(-0.01, min(0.10, rng.gauss(ECON["rent_growth"]["mid"], 0.018)))
    return home, rent, infl, spx_seq, bill_seq


def deterministic_econ(home=None, rent=None, infl=None, spx=None, bill=None, horizon=30):
    h = ECON["home_value_growth"]["mid"] if home is None else home
    r = ECON["rent_growth"]["mid"] if rent is None else rent
    i = ECON["inflation"]["mid"] if infl is None else infl
    s = (ECON["equity_real_return"]["mid"] + i) if spx is None else spx
    b = ECON["tbill_return"]["mid"] if bill is None else bill
    return h, r, i, s, b


def run(horizon=30, sims=N_SIMS):
    rng = random.Random(SEED)
    specs = path_specs()
    det = deterministic_econ(horizon=horizon)
    out = {}
    for sp in specs:
        base = simulate(sp, horizon, det, detailed=True)
        draws = sorted(simulate(sp, horizon, econ_draw(rng, horizon))["final_real"] for _ in range(sims))
        q = lambda p: draws[min(len(draws) - 1, int(p * len(draws)))]
        out[sp["id"]] = dict(
            id=sp["id"], name=sp["name"], group=sp["group"],
            final_real=r10(base["final_real"]), final_real_use=r10(base["pv_with_use"]),
            use_value=r10(base["use_value_pv"]), pv_real=r10(base["pv_real"]),
            min_wealth=r10(base["min_wealth_real"]),
            p10=r10(q(0.10)), p50=r10(q(0.50)), p90=r10(q(0.90)),
            dist=[r10(draws[min(len(draws) - 1, int(i / 20 * len(draws)))]) for i in range(21)],
            mean=r10(sum(draws) / len(draws)),
            sd=r10(math.sqrt(sum((x - sum(draws) / len(draws)) ** 2 for x in draws) / len(draws))),
            rows=base["rows"], cash_flow_min=r10(base["cash_flow_min"]),
        )
    return out, specs


def score(paths, use_value_in_ranking=False):
    """Documented, pre-committed scoring so the recommendation is auditable.
    0.50 * median real terminal wealth (normalised) + 0.25 * 10th percentile + 
    0.15 * downside resilience + 0.10 * liquidity / reversibility judgement."""
    key = "final_real_use" if use_value_in_ranking else "final_real"
    vals = [p[key] for p in paths.values()]
    lo, hi = min(vals), max(vals)
    rngv = max(1.0, hi - lo)
    p10 = [p["p10"] for p in paths.values()]
    plo, phi = min(p10), max(p10)
    prng = max(1.0, phi - plo)
    out = {}
    for pid, p in paths.items():
        wealth = (p[key] - lo) / rngv
        down = (p["p10"] - plo) / prng
        spread = 1.0 - abs(p["p90"] - p["p10"]) / max(1.0, abs(p["p90"]) + abs(p["p10"]))
        liq = 1.0 if p["cash_flow_min"] > -60_000 else 0.5
        out[pid] = dict(score=round(100 * (0.50 * wealth + 0.25 * down + 0.15 * spread + 0.10 * liq), 1),
                        wealth=round(wealth, 3), down=round(down, 3),
                        spread=round(spread, 3), liq=liq)
    return out


# ---------------------------------------------------- Black-swan / phasing ----
def phased_backtest(years=30):
    """Compare 'invest everything on day one' with 'park in bills, then phase into equities'.

    Annual history is converted to a monthly path geometrically ((1+r)^(1/12)); that is a
    simplification and is stated as such on the page. The ranking and the sign of the result,
    not the third decimal, are what this is for.
    """
    res = []
    for entry in PHASING["crash_entries"]:
        yrs = [y for y in range(entry, entry + years + 1) if y in history.SPX]
        for park in PHASING["park_months"]:
            for ph in PHASING["phase_in_months"]:
                w = peak = trough = 1.0
                worst_depth = 0.0
                running_peak = 1.0
                for k, y in enumerate(yrs):
                    m0 = k * 12
                    invested = 1.0 if m0 >= park + ph else (
                        0.0 if m0 < park else (m0 - park) / float(ph))
                    r_m = ((1 + history.SPX[y]) ** invested) * ((1 + history.BILL[y]) ** (1 - invested)) - 1
                    w *= (1 + r_m)
                    running_peak = max(running_peak, w)
                    dd = w / running_peak - 1.0
                    worst_depth = min(worst_depth, dd)
                    trough = min(trough, w)
                res.append(dict(entry=entry, park=park, phase=ph, wealth=w,
                                max_dd=worst_depth, years=len(yrs)))
    by_entry = {}
    for r in res:
        by_entry.setdefault(r["entry"], {})[(r["park"], r["phase"])] = r
    for entry, tab in by_entry.items():
        lump = tab[(0, 1)]
        for k, r in tab.items():
            r["vs_lump"] = r["wealth"] / lump["wealth"] - 1.0
            r["dd_vs_lump"] = r["max_dd"] - lump["max_dd"]
    return res, by_entry


def regime_table():
    """Documented episodes, computed from the annual series rather than quoted from memory."""
    out = []
    episodes = [(1929, 1932, "Great Depression"), (1973, 1974, "First oil shock / stagflation"),
                (2000, 2002, "dot-com"), (2007, 2009, "Global financial crisis"),
                (2020, 2020, "Pandemic"), (2021, 2022, "Inflation shock + rate hikes"),
                (1937, 1938, "1937 recession"), (1987, 1987, "Black Monday"),
                (2008, 2009, "Bear-market entry with zero cash yields")]
    for a, b, label in episodes:
        eq = 1.0
        bi = 1.0
        for y in range(a, b + 1):
            if y in history.SPX:
                eq *= (1 + history.SPX[y])
                bi *= (1 + history.BILL[y])
        out.append(dict(label=label, span=f"{a}-{b}", eq=(eq - 1) * 100, bill=(bi - 1) * 100,
                        eq_years=b - a + 1))
    return out


def rolling_returns(window=10):
    yrs = history.YEARS
    vals = []
    for i in range(0, len(yrs) - window):
        p = 1.0
        for y in yrs[i:i + window]:
            p *= (1 + history.SPX[y])
        vals.append((p ** (1.0 / window) - 1) * 100)
    vals_sorted = sorted(vals)
    return dict(window=window, n=len(vals), lo=round(vals_sorted[int(0.05 * len(vals))], 2),
                med=round(vals_sorted[len(vals) // 2], 2), hi=round(vals_sorted[int(0.95 * len(vals))], 2),
                minv=round(vals_sorted[0], 2), maxv=round(vals_sorted[-1], 2),
                pct_negative=round(100.0 * sum(1 for v in vals if v < 0) / len(vals), 1),
                series=[[yrs[i], round(v, 2)] for i, v in enumerate(vals)])


if __name__ == "__main__":
    paths, specs = run(30)
    sc = score(paths)
    bt, by = phased_backtest()
    import json
    print(json.dumps(dict(stats=history.stats(),
                          rolling=rolling_returns(10),
                          ranking=sorted(sc.items(), key=lambda kv: -kv[1]["score"])[:4],
                          paths={k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                                 for k, v in paths.items()},
                          backtest={str(e): {f"{k[0]}m/{k[1]}m": round(v["vs_lump"] * 100, 1)
                                             for k, v in tab.items()}
                                    for e, tab in list(by.items())[:4]}), indent=1)[:4000])


# ------------------------------------------------------------- what-if grid ----
def sensitivity_grid(horizons=(10, 20, 30)):
    """Exact grid over the what-if dials. Published so the browser does a lookup rather than a
    re-derivation: every number the sliders show was computed here, in Python, from inputs.py.

    Dials: home-value growth x equity REAL return x rent growth x Prop 19 obtained (yes/no)
           x horizon. Prop 19 'no' strips the exclusion from every path that would have claimed
           it, which is how the exclusion gets stress-tested as a policy choice, not a fact.
    """
    cells = []
    hg, eg, rg = (ECON["home_value_growth"], ECON["equity_real_return"], ECON["rent_growth"])
    for hkey in ("low", "mid", "high"):
        for ekey in ("low", "mid", "high"):
            for rkey in ("low", "mid", "high"):
                for p19 in (True, False):
                    for hz in horizons:
                        econ = deterministic_econ(home=hg[hkey], rent=rg[rkey],
                                                  spx=eg[ekey] + ECON["inflation"]["mid"],
                                                  horizon=hz)
                        row = {}
                        for sp in path_specs():
                            sp2 = dict(sp)
                            if not p19:
                                sp2["prop19"] = False
                            r = simulate(sp2, hz, econ)
                            row[sp["id"]] = dict(w=r10(r["pv_real"]), u=r10(r["pv_with_use"]),
                                                 n=r10(r["final_nominal"]))
                        cells.append(dict(home=hkey, equity=ekey, rent=rkey, prop19=p19,
                                          horizon=hz, values=row))
    return cells


def break_even_rent(rival="P-05", target="P-08", horizon=20, lo=0.2, hi=3.0):
    """Multiplier on the owner's rent estimate at which `target` ties `rival` on real terminal
    wealth, found by bisection. Published as 'what the rent would have to be'."""
    det = deterministic_econ(horizon=horizon)
    sp_t = [x for x in path_specs() if x["id"] == target][0]
    sp_r = [x for x in path_specs() if x["id"] == rival][0]
    base_r = simulate(sp_r, horizon, det)["final_real"]
    f = lambda mult: simulate(sp_t, horizon, det, rent_mult=mult)["final_real"] - base_r
    if f(hi) < 0:
        return None
    for _ in range(40):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def rent_gap(horizon=20, target="P-08", rival="P-05"):
    mult = break_even_rent(rival, target, horizon)
    base = sum(PROPERTY_A["rent_mo_range"]) / 2.0
    if mult is None:
        return dict(found=False, base_month=r10(base))
    return dict(found=True, base_month=r10(base), mult=round(mult, 3),
                need_month=r10(base * mult), need_year=r10(base * mult * 12),
                premium=round(mult - 1.0, 3))


def rent_diagnostics(horizon=20):
    """What the rent path has to earn to be worth it, at the modelled transfer year.

    Expressed three ways so it can be checked against real listings: gross yield on value,
    the rent that covers the carrying cost, and the rent whose net operating income equals
    what the same money earns in short Treasuries after tax.
    """
    T = ECON["transfer_year"]
    A = PROPERTY_A
    home = ECON["home_value_growth"]["mid"]
    infl = ECON["inflation"]["mid"]
    price = float(A["value_2026"]) * (1 + home) ** (T - 2026)
    rent0 = sum(A["rent_mo_range"]) / 2.0 * 12
    rate = RULES["sc_rate_central"]
    tax = price * rate                       # full reassessment: the rental case
    ins = 2400.0 * (1 + max(infl, ECON["insurance_growth"]["mid"])) ** (T - 2026)
    water = sum(A["water_mo"]) / 2.0 * (1 + infl) ** (T - 2026)
    elec = sum(A["electric_mo_net"]) / 2.0 * (1 + infl) ** (T - 2026)
    maint = sum(A["maintenance_pct_of_value"]) / 2.0 * price
    mgmt = sum(A["property_mgmt_pct"]) / 2.0
    opex = tax + ins + water + elec + maint
    noi = rent0 * 0.95 - opex
    t = TRANSACT["A"]
    net_proceeds = price * (1 - t["commission_pct"] - t["seller_concessions_pct"] - t["dtt_pct"]
                            - t["prep_pct"]) - t["closing_flat"]
    safe = ECON["tbill_return"]["mid"] * (1 - (FED_ORD_TOP + CA_TOP) * 0.55)
    need_noi = net_proceeds * safe
    need_rent = (need_noi + opex) / 0.95
    depr = (price * 0.75) / RULES["depr_life_resid"]
    return dict(
        transfer_year=T, price=r10(price), rent_month=r10(rent0 / 12), rent_year=r10(rent0),
        gross_yield=round(100 * rent0 / price, 2), tax=r10(tax), insurance=r10(ins),
        water=r10(water), electric=r10(elec), maintenance=r10(maint), mgmt_pct=round(100 * mgmt, 1),
        opex=r10(opex), noi=r10(noi), noi_after_tax=r10(noi if noi <= depr else noi - (noi - depr) * MARG_ORD),
        net_proceeds=r10(net_proceeds), safe_yield=round(100 * safe, 2),
        need_noi=r10(need_noi), need_rent_year=r10(need_rent), need_rent_month=r10(need_rent / 12),
        break_even_rent=r10(opex / 0.95), break_even_month=r10(opex / 0.95 / 12),
        depreciation_year=r10(depr),
        vs_owner_estimate=round(100 * (need_rent / rent0 - 1), 1),
    )
