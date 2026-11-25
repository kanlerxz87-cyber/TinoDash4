"""Projection model for the inheritance decision (Property A = Cupertino inheritance;
Property B = San Francisco, already owned).

Monthly engine, all nominal USD internally; outputs are deflated to 2026 dollars and rounded
to the nearest $10. Every run is deterministic except the Monte Carlo block, which uses a fixed seed.

Run:  python3 model/model.py   -> writes data/projections.json
"""
import json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INP = json.load(open(os.path.join(ROOT, "data", "inputs.json")))
OUT = os.path.join(ROOT, "data", "projections.json")
TRANSFER_YEARS = [2040, 2045, 2050]
HORIZONS = [5, 10, 20]
ORIGIN_YEAR = 2026            # Nov 2026 valuation date
IMPUTED_B_UNIT = 3600         # HUD 2BR SF FMR $3,604 rounded to $10 (benchmark, S13)

# Which side of each range is "adverse" to household wealth (used by the downside/upside sets).
ADVERSE_HIGH = {"A_insurance","A_water_mo","A_maint_pct","A_vacancy","A_sell_cost","A_rate_owner",
                "B_vacancy","B_water_mo","B_elec_mo","B_insurance","B_maint_pct","marg_rate",
                "ltcg_fed","ca_cg","inv_drag","A_recording_fee","B_third_unit_dummy"}
ADVERSE_LOW = {"A_value","B_value","A_rent_fmr3","A_elec_income_mo","B_third_unit","eq_mu","treas_3m",
               "real_app","real_rent","sec121","eq_weight_dummy"}


def r10(x):
    return int(round(x / 10.0)) * 10


def inp(i):
    return next(x for x in INP["inputs"] if x["id"] == i)


def params(case="base"):
    """Return flat parameter dict. case in base/downside/upside/low/high (single-input sensitivities use low/high)."""
    p = {}
    for x in INP["inputs"]:
        base = x["base"]
        if x["id"] in ("A_basis_cap",):
            p[x["id"]] = x["low"]
            continue
        if case == "base":
            v = base
        elif case == "downside":
            v = x["high"] if x["id"] in ADVERSE_HIGH else (x["low"] if x["id"] in ADVERSE_LOW else base)
        elif case == "upside":
            v = x["low"] if x["id"] in ADVERSE_HIGH else (x["high"] if x["id"] in ADVERSE_LOW else base)
        else:
            v = base
        p[x["id"]] = v
    # Sensitivity cases are handled by the caller via override dicts.
    return p


def with_overrides(p, ov):
    q = dict(p)
    q.update(ov)
    return q


# ---------- scenario definitions (named what-if sets) ----------
SCENARIOS = {
    "base": {"label": "Base case", "case": "base", "ov": {}, "desc": "Central inputs; owner figures where supplied; assumptions as documented."},
    "downside": {"label": "Downside (all adverse ends)", "case": "downside", "ov": {}, "desc": "Every input set to the end of its range that hurts household wealth."},
    "upside": {"label": "Upside (all favourable ends)", "case": "upside", "ov": {}, "desc": "Every input set to the end of its range that helps household wealth."},
    "stagflation": {"label": "1970s-style stagflation", "case": "base",
                    "ov": {"cpi_near": 5.5, "cpi_long": 3.5, "real_app": -1.0, "eq_mu": 4.0, "treas_3m": 5.0, "real_rent": 0.0},
                    "desc": "Inflation 5.5% for 2027-2029 then 3.5%; stocks 4%; cash 5%; housing 1 point below inflation in real terms."},
    "lost_decade": {"label": "Lost decade (flat stocks, 10 years)", "case": "base",
                    "ov": {"eq_mu_early": 1.0, "eq_early_years": 10},
                    "desc": "Stock return 1% a year for the first 10 years after transfer, then base case."},
    "crash_1929": {"label": "1929-style crash at transfer", "case": "base",
                   "ov": {"eq_shock": [[0, 36, -0.87]], "house_shock": [[0, 36, -0.30]], "treas_3m": 2.5},
                   "desc": "Stocks fall 87% over 36 months from transfer (Fed History reports -89% 1929-1932; calibrated approximately). Housing -30% over 3 years (ASSUMED analogue). Cash falls to 2.5% (deflation response)."},
    "crash_2008": {"label": "2008-style crash at transfer", "case": "base",
                   "ov": {"eq_shock": [[0, 17, -0.57]], "house_shock": [[0, 24, -0.30]]},
                   "desc": "Stocks fall 57% over 17 months from transfer (Fed History: S&P 500 -57%, Oct 2007-Mar 2009). Housing -30% over 24 months (Fed History: about -30%)."},
    "rate_cut": {"label": "Reinvestment shock: cash yields fall to 2.5%", "case": "base",
                 "ov": {"treas_3m_schedule": [[12, 48, 2.5]]},
                 "desc": "Short-term yields fall to 2.5% for three years, starting one year after transfer. Tests reinvestment risk of cash parked for 24-36 months."},
    "step_up_cap": {"label": "Reported step-up cap (UNVERIFIED proposal)", "case": "base",
                    "ov": {"use_basis_cap": True},
                    "desc": "Basis capped at $3,000,000 at death (reported Treasury proposal; not law; text not located)."},
    "pre_prop19": {"label": "Illustrative: Prop 19 repealed (pre-2021 rules)", "case": "base",
                   "ov": {"pre_prop19": True},
                   "desc": "Illustrative only (the 2026 repeal initiative did not qualify per S29). Heir keeps the factored base year value regardless of occupancy."},
}

PATHS = {
    "LIVE_A": {"label": "Live in Property A (Prop 19 claimed)", "type": "pure", "occupy_until": None, "rent_from": None, "sale": None, "prop19": True, "phased": False, "b_third_from": 0, "b_third_to": None},
    "RENT_A": {"label": "Rent Property A at market", "type": "pure", "occupy_until": None, "rent_from": 0, "sale": None, "prop19": False, "phased": False, "b_third_from": None, "b_third_to": None},
    "SELL_A": {"label": "Sell Property A now, invest in one lump", "type": "pure", "occupy_until": None, "rent_from": None, "sale": 0, "prop19": False, "phased": False, "b_third_from": None, "b_third_to": None},
    "LIVE_THEN_SELL": {"label": "Live 2 years, then sell (mixed)", "type": "mixed", "occupy_until": 24, "rent_from": None, "sale": 24, "prop19": True, "phased": False, "b_third_from": 0, "b_third_to": 24},
    "LIVE_THEN_RENT": {"label": "Live 5 years, then rent (mixed)", "type": "mixed", "occupy_until": 60, "rent_from": 60, "sale": None, "prop19": True, "phased": False, "b_third_from": 0, "b_third_to": 60},
    "RENT_THEN_SELL": {"label": "Rent 10 years, then sell (mixed)", "type": "mixed", "occupy_until": None, "rent_from": 0, "sale": 120, "prop19": False, "phased": False, "b_third_from": None, "b_third_to": None},
    "SELL_A_PHASED": {"label": "Sell now, park 2-3 yrs in 3M-2Y Treasuries, then phase into stocks (mixed)", "type": "mixed", "occupy_until": None, "rent_from": None, "sale": 0, "prop19": False, "phased": True, "b_third_from": None, "b_third_to": None},
}


def cpi_y(p, y):
    return p["cpi_near"] if y <= 2029 else p["cpi_long"]


def pre_growth(p, T):
    """Factors from Nov 2026 to Jan 1 of transfer year T (annual steps)."""
    v = rent = ins = water = 1.0
    idx = 1.0
    for y in range(2027, T + 1):
        c = cpi_y(p, y) / 100
        v *= (1 + c + p["real_app"] / 100)
        rent *= (1 + c + p["real_rent"] / 100)
        ins *= (1 + c)
        idx *= (1 + c)
    return {"V": v, "rent": rent, "ins": ins, "idx": idx}


def deflator(p, year):
    idx = 1.0
    for y in range(2027, year + 1):
        idx *= (1 + cpi_y(p, y) / 100)
    return idx


def in_sched(m, sched):
    """Return list of (start, dur, total) applicable; monthly factor helper."""
    return [s for s in (sched or []) if s[0] <= m < s[0] + s[1]]


def run_path(p, path, T, H, phased_override=None):
    """Monthly simulation from transfer (month 0 = Jan of year T) to horizon T+H. Returns metrics dict."""
    spec = PATHS[path]
    M = H * 12
    pg = pre_growth(p, T)
    V0 = p["A_value"] * pg["V"] / 1.0            # value at transfer (owner base scaled by growth)
    # Base value at transfer scaled to the owner's Nov-2026 estimate band
    rate_A = p["A_rate_owner"] if not p.get("use_official_rate") else p["A_rate_official"]
    fbyv_T = p["A_fbyv_2026"] * (1.02 ** (T - ORIGIN_YEAR))
    cap = p["A_prop19_cap"]
    rent_T = p["A_rent_fmr3"] * pg["rent"]
    ins_T = p["A_insurance"] * pg["ins"]
    water_T = p["A_water_mo"] * 12 * pg["ins"]
    elec_T = p["A_elec_income_mo"] * 12 * pg["ins"]
    b_third = p["B_third_unit"]
    basis_T = min(V0, p["A_basis_cap"]) if p.get("use_basis_cap") else V0
    dep_basis = V0 * p["bldg_share"]
    dep_per_month = dep_basis / p["dep_years"] / 12
    phased = spec["phased"] if phased_override is None else phased_override
    park = p["park_months"]
    phase_m = p["phase_months"]

    # property taxable base at transfer
    if p.get("pre_prop19"):
        base_factor_T = fbyv_T
    elif spec["prop19"]:
        base_factor_T = max(fbyv_T, V0 - cap)
    else:
        base_factor_T = V0
    base_T = base_factor_T

    cash_b = 0.0     # cash bucket (Treasuries, park)
    port_b = 0.0     # invested bucket
    tax_total = 0.0
    imputed_total = 0.0
    rent_income_total = 0.0
    sold = False
    proceeds = 0.0
    dep_taken = 0.0
    phase_start = park
    phase_per = None
    eq_w = p["eq_weight"]
    drag = p["inv_drag"] / 100

    # Initial sale-at-transfer for pure sell paths
    if spec["sale"] == 0:
        # sale at transfer: costs + tax (no gain -> no tax)
        price = V0
        cost = price * p["A_sell_cost"] + price * p["A_dtt"] / 100 + p["A_recording_fee"]
        gain = price - cost - basis_T
        tax = max(0, gain) * (p["ltcg_fed"] + p["niit"] + p["ca_cg"]) / 100 if gain > 0 else 0
        proceeds = price - cost - tax
        tax_total += tax
        sold = True
        if phased:
            cash_b = proceeds
        else:
            port_b = proceeds

    V = V0
    taxable = base_T
    for m in range(M):
        yr = T + m // 12
        # --- growth of property value (annual steps applied monthly)
        c = cpi_y(p, yr) / 100
        if not sold or spec["sale"] is None:
            pass
        ann_app = c + p["real_app"] / 100
        if p.get("eq_shock") is not None or p.get("house_shock") is not None:
            pass
        V *= (1 + ann_app) ** (1 / 12)
        # house shock
        for s0, d, tot in in_sched(m, p.get("house_shock")):
            V *= (1 + tot) ** (1 / (12 * 1.0 * 1)) if False else 1.0
        if p.get("house_shock"):
            for s0, d, tot in p["house_shock"]:
                if s0 <= m < s0 + d:
                    V *= (1 + tot) ** (1 / d)
        # rent growth
        rent_m = rent_T * ((1 + c + p["real_rent"] / 100) ** (m / 12))
        ins_m = ins_T * ((1 + c) ** (m / 12)) / 12
        water_m = (water_T / 12) * ((1 + c) ** (m / 12))
        elec_m = (elec_T / 12) * ((1 + c) ** (m / 12))

        # --- rates by scenario
        treas = p["treas_3m"]
        for s0, d, r in (p.get("treas_3m_schedule") or []):
            if s0 <= m < d:
                treas = r
        # equity monthly return
        eq_ann = p["eq_mu"]
        if p.get("eq_early_years") and m < p["eq_early_years"] * 12:
            eq_ann = p["eq_mu_early"]
        r_e = (1 + eq_ann / 100) ** (1 / 12) - 1
        for s0, d, tot in (p.get("eq_shock") or []):
            if s0 <= m < s0 + d:
                r_e = (1 + tot) ** (1 / d) - 1
        r_b = (1 + treas / 100) ** (1 / 12) - 1
        r_port = eq_w * r_e + (1 - eq_w) * r_b - drag / 12
        r_cash = r_b

        # --- property ownership phases
        owns = not sold
        occupying = owns and (spec["occupy_until"] is None or m < spec["occupy_until"])
        renting = owns and spec["rent_from"] is not None and m >= spec["rent_from"]
        if spec["sale"] is not None and m == spec["sale"] and spec["sale"] > 0 and owns:
            # sale at a later month
            price = V
            cost = price * p["A_sell_cost"] + price * p["A_dtt"] / 100 + p["A_recording_fee"]
            gain = price - cost - basis_T - dep_taken
            excl = min(max(gain, 0), p["sec121"]) if (spec["occupy_until"] and spec["prop19"]) else 0.0
            taxable_gain = max(0, gain - excl)
            dep_part = min(max(gain, 0), dep_taken)
            tax = dep_part * (p["recapture"] + p["niit"] + p["ca_cg"]) / 100 \
                + max(0, taxable_gain - dep_part) * (p["ltcg_fed"] + p["niit"] + p["ca_cg"]) / 100
            tax_total += tax
            proceeds = price - cost - tax
            sold = True
            owns = False
            occupying = False
            renting = False
            if phased:
                cash_b += proceeds
            else:
                port_b += proceeds

        # --- property cash flows and taxes while owned
        prop_cf = 0.0
        if owns:
            # property tax on taxable base (Prop 8 decline: cannot exceed market)
            if p.get("pre_prop19"):
                tax_base = min(base_T * (1.02 ** (m / 12)), V) if False else base_T * (1.02 ** (m / 12))
            elif spec["prop19"] and occupying or (spec["prop19"] and not sold):
                tax_base = min(base_T * (1.02 ** (m / 12)), max(fbyv_T, V - cap))
            else:
                tax_base = min(base_T * (1.02 ** (m / 12)), V)
            ptax_m = tax_base * (rate_A / 100) / 12
            maint_m = V * (p["A_maint_pct"] / 100) / 12
            cost_m = ins_m + water_m + ptax_m + maint_m - elec_m
            prop_cf -= cost_m
            if renting:
                gross = rent_m * (1 - p["A_vacancy"])
                dep_m = dep_per_month if m >= (spec["rent_from"] or 0) else 0.0
                dep_taken += dep_m
                ti = gross - cost_m - dep_m
                tax_m = ti * p["marg_rate"] / 100
                prop_cf += gross - tax_m
                tax_total += tax_m
                rent_income_total += gross
            if occupying:
                imputed_total += rent_m / 1.0 * (1.0 if True else 0)
        else:
            pass

        # --- B third-unit rent while owner-unit is vacated (LIVE paths)
        b_cf = 0.0
        if spec["b_third_from"] is not None and m >= spec["b_third_from"] and (spec["b_third_to"] is None or m < spec["b_third_to"]):
            g = b_third * (1 - p["B_vacancy"]) * ((1 + c) ** (m / 12))
            b_tax = g * p["marg_rate"] / 100
            b_cf = g - b_tax
            tax_total += b_tax

        # --- imputed rent for owner-occupied home (non-cash): B unit if not living in A
        if not occupying:
            imputed_total += IMPUTED_B_UNIT * ((1 + c) ** (m / 12))

        # --- cash flows into accounts
        flow = prop_cf + b_cf
        if phased and sold and cash_b > 0 or (phased and sold and phase_per is None and m < park):
            pass
        # phased: park in cash bucket then phase
        if phased and sold:
            cash_b *= (1 + r_cash)
            if m >= park and m < park + phase_m:
                move = cash_b * (1.0 / (park + phase_m - m))
                cash_b -= move
                port_b += move
            port_b *= (1 + r_port)
            port_b += 0
            if flow:
                port_b += flow
        else:
            port_b *= (1 + r_port)
            port_b += flow
        if not sold:
            pass

    # horizon-end liquidation-equivalent for property still held
    liquid = cash_b + port_b
    prop_equity = 0.0
    if not sold:
        price = V
        cost = price * p["A_sell_cost"] + price * p["A_dtt"] / 100 + p["A_recording_fee"]
        gain = price - cost - basis_T - dep_taken
        excl = min(max(gain, 0), p["sec121"]) if (spec["occupy_until"] is not None or spec["prop19"]) and spec["occupy_until"] and spec["occupy_until"] >= 24 else 0.0
        taxable_gain = max(0, gain - excl)
        dep_part = min(max(gain, 0), dep_taken)
        tax = dep_part * (p["recapture"] + p["niit"] + p["ca_cg"]) / 100 + max(0, taxable_gain - dep_part) * (p["ltcg_fed"] + p["niit"] + p["ca_cg"]) / 100
        prop_equity = price - cost - tax
        # tax on hypothetical liquidation is not added to tax_total (it is a what-if liquidation)
    total = liquid + prop_equity
    idx = deflator(p, T + H)
    out = {
        "cash_real": r10(liquid / idx),
        "property_real": r10(prop_equity / idx),
        "total_real": r10(total / idx),
        "imputed_real": r10(imputed_total / idx),
        "taxes_real": r10(tax_total / idx),
        "liquid_share_pct": round(100 * liquid / total, 1) if total > 0 else 0.0,
        "rent_income_real": r10(rent_income_total / idx),
        "total_incl_imputed_real": r10((total + imputed_total) / idx),
    }
    return out


def run_all():
    res = {}
    for sname, s in SCENARIOS.items():
        base_p = params(s["case"])
        base_p = with_overrides(base_p, s["ov"])
        if s["ov"].get("use_basis_cap"):
            base_p["use_basis_cap"] = True
        if s["ov"].get("pre_prop19"):
            base_p["pre_prop19"] = True
        res[sname] = {}
        for T in TRANSFER_YEARS:
            res[sname][str(T)] = {}
            for H in HORIZONS:
                res[sname][str(T)][str(H)] = {pn: run_path(base_p, pn, T, H) for pn in PATHS}
    return res


def ranking(cell):
    return sorted(cell.keys(), key=lambda k: -cell[k]["total_real"])


def sensitivities(T=2045, H=10):
    """One-at-a-time low/high for each input. Reports whether the top path changes."""
    basep = params("base")
    base_top = ranking({k: run_path(basep, k, T, H) for k in PATHS})[0]
    rows = []
    for x in INP["inputs"]:
        if x["id"] in ("A_basis_cap",) or x["low"] == x["high"]:
            continue
        outs = {}
        for side in ("low", "high"):
            q = dict(basep)
            q[x["id"]] = x[side]
            cell = {k: run_path(q, k, T, H) for k in PATHS}
            top = ranking(cell)[0]
            outs[side] = {"top": top, "top_total": cell[top]["total_real"],
                          "LIVE_A": cell["LIVE_A"]["total_real"], "RENT_A": cell["RENT_A"]["total_real"],
                          "SELL_A": cell["SELL_A"]["total_real"]}
        rows.append({"id": x["id"], "label": x["label"], "low_value": x["low"], "high_value": x["high"],
                     "top_at_low": outs["low"]["top"], "top_at_high": outs["high"]["top"],
                     "flips_top_path": outs["low"]["top"] != base_top or outs["high"]["top"] != base_top,
                     "LIVE_A_low": outs["low"]["LIVE_A"], "LIVE_A_high": outs["high"]["LIVE_A"],
                     "RENT_A_low": outs["low"]["RENT_A"], "RENT_A_high": outs["high"]["RENT_A"],
                     "SELL_A_low": outs["low"]["SELL_A"], "SELL_A_high": outs["high"]["SELL_A"]})
    rows.sort(key=lambda r: (not r["flips_top_path"]))
    return base_top, rows


def blackswan_entry_test(T=2045, H=10):
    """Lump sale-and-invest vs phased entry under a 1929-style and a 2008-style crash.
    Compares: lump entry at transfer when the crash starts at transfer; phased entry with the crash
    starting at transfer (investor still parked); phased entry with the crash starting when phase-in begins."""
    out = {}
    for name, sched in (("crash_1929", [[0, 36, -0.87]]), ("crash_2008", [[0, 17, -0.57]])):
        q = with_overrides(params("base"), {"eq_shock": sched})
        lump = run_path(q, "SELL_A", T, H)["total_real"]
        phased_crash_now = run_path(q, "SELL_A_PHASED", T, H)["total_real"]
        q2 = with_overrides(params("base"), {"eq_shock": [[int(q["park_months"]), 36 if name == 'crash_1929' else 17, sched[0][2]]]})
        phased_crash_at_entry = run_path(q2, "SELL_A_PHASED", T, H)["total_real"]
        base_lump = run_path(params("base"), "SELL_A", T, H)["total_real"]
        base_phased = run_path(params("base"), "SELL_A_PHASED", T, H)["total_real"]
        out[name] = {
            "lump_crash_at_transfer": lump,
            "phased_crash_at_transfer": phased_crash_now,
            "phased_crash_during_phase_in": phased_crash_at_entry,
            "lump_no_crash": base_lump,
            "phased_no_crash": base_phased,
        }
    return out


def reinvestment_risk(T=2045, H=10):
    """Annual income lost per $1,000,000 parked for the park period if 3M yields fall to 2.5%."""
    p = params("base")
    base_yield = p["treas_3m"]
    per_1m = 1_000_000 * (base_yield - 2.5) / 100
    return {"base_yield_pct": base_yield, "shock_yield_pct": 2.5,
            "annual_income_lost_per_1m_r": r10(per_1m),
            "park_months_base": p["park_months"]}


def monte_carlo(T=2045, H=20, n=5000, seed=20261125):
    """Stochastic stock returns (normal, base mean and vol) with a 5%/yr chance of a -35% year.
    Compares lump-sum vs phased investment of the same after-tax proceeds (no property risk)."""
    rnd = random.Random(seed)
    p = params("base")
    pg = pre_growth(p, T)
    V0 = p["A_value"] * pg["V"]
    # Proceeds at transfer from the deterministic sale-at-transfer engine
    dt = p["A_dtt"] / 100
    price = V0
    cost = price * p["A_sell_cost"] + price * dt + p["A_recording_fee"]
    proceeds = price - cost
    M = H * 12
    park = int(p["park_months"]); phase_m = int(p["phase_months"])
    eq_w = p["eq_weight"]; drag = p["inv_drag"] / 100; r_b_a = p["treas_3m"] / 100
    idx = deflator(p, T + H)
    lump_vals, phased_vals = [], []
    for _ in range(n):
        yr_ret = []
        for y in range(H + 1):
            if rnd.random() < 0.05:
                yr_ret.append(-0.35)
            else:
                yr_ret.append(rnd.gauss(p["eq_mu"] / 100, p["eq_vol"] / 100))
        # lump
        port = proceeds
        cash = 0.0
        for m in range(M):
            ye = yr_ret[m // 12]
            r_e = (1 + ye) ** (1 / 12) - 1
            r_port = eq_w * r_e + (1 - eq_w) * ((1 + r_b_a) ** (1 / 12) - 1) - drag / 12
            port *= (1 + r_port)
        lump_vals.append((port) / idx)
        # phased
        cash = proceeds; port = 0.0
        for m in range(M):
            ye = yr_ret[m // 12]
            r_e = (1 + ye) ** (1 / 12) - 1
            r_cash = (1 + r_b_a) ** (1 / 12) - 1
            r_port = eq_w * r_e + (1 - eq_w) * r_cash - drag / 12
            cash *= (1 + r_cash)
            if park <= m < park + phase_m:
                move = cash / (park + phase_m - m)
                cash -= move
                port += move
            port *= (1 + r_port)
        phased_vals.append((port + cash) / idx)
    def pct(xs, q):
        s = sorted(xs); return s[int(q * (len(s) - 1))]
    lump_vals_s = sorted(lump_vals)
    phased_vals_s = sorted(phased_vals)
    # histogram (20 bins) over combined range in real dollars
    lo = min(lump_vals_s[0], phased_vals_s[0]); hi = max(lump_vals_s[-1], phased_vals_s[-1])
    bins = 20
    step = (hi - lo) / bins if hi > lo else 1
    hist = {"lump": [0] * bins, "phased": [0] * bins}
    for v in lump_vals:
        hist["lump"][min(bins - 1, int((v - lo) / step))] += 1
    for v in phased_vals:
        hist["phased"][min(bins - 1, int((v - lo) / step))] += 1
    edges = [r10(lo + i * step) for i in range(bins + 1)]
    prob_phased_better = sum(1 for a, b in zip(lump_vals, phased_vals) if b > a) / n
    return {
        "transfer_year": T, "horizon_years": H, "runs": n, "seed": seed,
        "assumptions": {"equity_mu_pct": p["eq_mu"], "equity_vol_pct": p["eq_vol"], "crash_prob_per_year": 0.05,
                        "crash_return_pct": -35, "park_months": park, "phase_months": phase_m},
        "proceeds_real_at_transfer": r10(proceeds / deflator(p, T)),
        "lump": {"p10": r10(pct(lump_vals, 0.10)), "p50": r10(pct(lump_vals, 0.50)), "p90": r10(pct(lump_vals, 0.90))},
        "phased": {"p10": r10(pct(phased_vals, 0.10)), "p50": r10(pct(phased_vals, 0.50)), "p90": r10(pct(phased_vals, 0.90))},
        "prob_phased_beats_lump_pct": round(100 * prob_phased_better, 1),
        "histogram": {"edges": edges, "lump": hist["lump"], "phased": hist["phased"]},
    }


def yearly_tables(T=2045, years=40):
    """Base-case property A and B year-by-year values and tax lines (nominal and 2026 dollars)."""
    p = params("base")
    rows = []
    VA = p["A_value"]; fbyv = p["A_fbyv_2026"]; bill_B = p["B_bill_2025"]; assess_B = p["B_assessed_2025"]
    VB = p["B_value"]
    for k, y in enumerate(range(ORIGIN_YEAR, ORIGIN_YEAR + years + 1)):
        if y > ORIGIN_YEAR:
            c = cpi_y(p, y) / 100
            VA *= (1 + c + p["real_app"] / 100)
            VB *= (1 + c + p["real_app"] / 100)
        factor_A = 1.02 ** (y - ORIGIN_YEAR)
        taxable_fbyv = fbyv * factor_A
        taxable_rent = VA if y >= T else taxable_fbyv
        taxable_live_post = max(taxable_fbyv, VA - p["A_prop19_cap"]) if y >= T else taxable_fbyv
        rows.append({
            "year": y,
            "A_value_nominal": r10(VA),
            "A_value_real2026": r10(VA / deflator(p, y)),
            "A_assessed_if_no_transfer": r10(taxable_fbyv),
            "A_taxable_if_rented_or_sold_T": r10(taxable_rent),
            "A_taxable_if_prop19_occupied": r10(taxable_live_post),
            "A_tax_if_prop19_owner_rate": r10(taxable_live_post * p["A_rate_owner"] / 100),
            "A_tax_if_reassessed_owner_rate": r10(taxable_rent * p["A_rate_owner"] / 100),
            "B_value_nominal": r10(VB),
            "B_assessed": r10(assess_B * (1.02 ** (y - 2025))),
            "B_tax_bill_owner": r10(bill_B * (1.02 ** (y - 2025))),
            "B_tax_bill_official_rate": r10(assess_B * (1.02 ** (y - 2025)) * p["B_rate_official"] / 100),
        })
    return rows


def main():
    res = run_all()
    base_top_sens, sens = sensitivities(2045, 10)
    bs = blackswan_entry_test(2045, 10)
    rr = reinvestment_risk()
    mc = monte_carlo(2045, 20)
    # recommendation check across scenario sets (T=2045, H=10 and H=20; total real wealth)
    rec = {}
    for H in ("10", "20"):
        tops = {s: ranking(res[s]["2045"][H])[0] for s in SCENARIOS}
        rec[H] = {"top_by_scenario": tops, "moved": len(set(tops.values())) > 1,
                  "base_top": tops["base"]}
    # base-case table
    base_cells = {str(T): {str(H): res["base"][str(T)][str(H)] for H in HORIZONS} for T in TRANSFER_YEARS}
    out = {
        "generated_for": "2026-11-25",
        "rounding": "Nearest $10 (display and output).",
        "real_dollars": "All outputs in 2026 dollars unless labelled nominal.",
        "transfer_years": TRANSFER_YEARS, "horizons_years": HORIZONS,
        "paths": {k: {"label": v["label"], "type": v["type"]} for k, v in PATHS.items()},
        "scenarios": {k: {"label": v["label"], "desc": v["desc"]} for k, v in SCENARIOS.items()},
        "results": res,
        "base_by_transfer": base_cells,
        "sensitivity": {"transfer_year": 2045, "horizon": 10, "base_top_path": base_top_sens, "rows": sens},
        "blackswan_entry_test": bs,
        "reinvestment_risk": rr,
        "monte_carlo": mc,
        "recommendation_check": rec,
        "yearly_base": yearly_tables(2045, 40),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", OUT)
    print("base top 2045/10:", ranking(res["base"]["2045"]["10"]))
    print("base top 2045/20:", ranking(res["base"]["2045"]["20"]))
    print("recommendation moved (H=10):", rec["10"]["moved"], rec["10"]["top_by_scenario"])
    print("recommendation moved (H=20):", rec["20"]["moved"], rec["20"]["top_by_scenario"])


if __name__ == "__main__":
    main()
