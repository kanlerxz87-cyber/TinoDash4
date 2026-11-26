#!/usr/bin/env python3
"""Decision model: Property A (inherited) under eight paths, with Property B as context.

Standard library only, deterministic (seeded). Reads:
  data/inputs.json               owner figures, already rounded to $10
  data/returns_1928_2025.csv     annual S&P 500 total return and 3-month T-bill (academic record)
Writes:
  data/model_outputs.json        every published number (rounded to $10 or shown as a rate)

Choice rules are the ones written in DECISION_RULES.md before any output existed. This file
applies them; it does not change them.

Run:  python3 tools/model.py
"""
import csv
import json
import pathlib
import random
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = 20261126
N_MC = 2000          # Monte Carlo draws for the headline ranking
N_GRID = 200         # draws per sensitivity variant (smaller, same seed)
VAL_YEAR = 2026
TRANSFER_YEARS = [2040, 2050]
HORIZONS = [10, 20]

PATHS = {
    "LIVE": {"label": "Live in A (occupy, claim Prop 19)", "segs": [("live", None)], "deploy": None, "pure": True},
    "RENT": {"label": "Rent A (full reassessment)", "segs": [("rent", None)], "deploy": None, "pure": True},
    "SELL_LUMP": {"label": "Sell at transfer, invest lump sum", "segs": [("sell", None)], "deploy": ("lump",), "pure": True},
    "SELL_P24": {"label": "Sell, park 24 months in T-bills, phase in over 12", "segs": [("sell", None)], "deploy": ("park", 24, 12), "pure": False},
    "SELL_P36": {"label": "Sell, park 36 months in T-bills, phase in over 12", "segs": [("sell", None)], "deploy": ("park", 36, 12), "pure": False},
    "LIVE3_SELL": {"label": "Mixed: live 3 years, then sell", "segs": [("live", 3), ("sell", None)], "deploy": ("lump",), "pure": False},
    "RENT3_SELL": {"label": "Mixed: rent 3 years, then sell", "segs": [("rent", 3), ("sell", None)], "deploy": ("lump",), "pure": False},
    "LIVE3_RENT": {"label": "Mixed: live 3 years, then rent", "segs": [("live", 3), ("rent", None)], "deploy": None, "pure": False},
}

# Scenario sequences are taken from the historical record (see returns_1928_2025.csv).
CRASHES = {"bs1929": 1929, "bs2008": 2008, "bs1973": 1973, "bs2000": 2000}


def r10(x):
    """Round to the nearest $10, half up. None passes through."""
    if x is None:
        return None
    return int((Decimal(str(x)) / 10).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 10)


def pct(x, dp=2):
    return round(100 * x, dp)


def load_inputs():
    return json.loads((ROOT / "data/inputs.json").read_text())


def load_returns():
    rows = list(csv.DictReader((ROOT / "data/returns_1928_2025.csv").open()))
    years = [int(r["year"]) for r in rows]
    eq = [float(r["sp500_total_return_pct"]) / 100 for r in rows]
    bill = [float(r["tbill_3m_avg_pct"]) / 100 for r in rows]
    return years, eq, bill


def geo_mean(xs):
    p = 1.0
    for x in xs:
        p *= 1 + x
    return p ** (1 / len(xs)) - 1


def base_params(inp):
    a = inp["property_a"]
    hist = a["history"]
    av_2026 = hist[0]["assessed"]
    av_2025 = hist[1]["assessed"]
    tax_2025 = hist[1]["tax"]
    owner_rate = tax_2025 / av_2025           # owner's own bill divided by its assessed value
    water_mid = sum(a["water_monthly_range"]) / 2
    solar_mid = sum(a["solar_credit_monthly_range"]) / 2
    cpi = 0.023                                # CBO baseline CPI (S15)
    return {
        # --- owner-supplied (rounded to $10 in data/inputs.json)
        "mv0": a["value_estimate"]["value"],
        "av0": av_2026,                       # factored base for Prop 19 / Prop 13 (2026 roll)
        "ins0": a["insurance_annual_owner_estimate"],
        "water0_m": water_mid - solar_mid,     # net of solar credit, $ per month
        # --- statutory (verified)
        "cap0": 1044586,                       # BOE LTA 2025/009 (S03), valid 16 Feb 2025 - 15 Feb 2027
        "g13": min(cpi, 0.02),                 # Prop 13 growth cap: lesser of CPI or 2% (S10)
        "transfer_rate": 0.0011,               # $1.10 per $1,000 county documentary transfer tax (S13)
        "excl": 250000,                        # IRC 121 single; 500,000 joint (S08)
        # --- modelling assumptions (labelled on the site, not facts)
        "cpi": cpi,
        "hpa": cpi,                            # home-value growth = inflation (assumption)
        "rent_yield": 0.0375,                  # gross rent / value (assumption; no comparables)
        "vac": 0.05,
        "maint": 0.01,
        "rate": owner_rate,                    # owner-bill implied 1.3357% (flagged; see site)
        "sell_comm": 0.05,
        "sell_other": 0.005,
        "ord": 0.40,                           # combined ordinary rate on interest and rent (assumption)
        "ltcg": 0.20 + 0.038 + 0.093,          # federal 20% (S01 thresholds) + NIIT 3.8% (S19 not verified) + CA 9.3% (assumption)
        "recap": 0.25 + 0.038 + 0.093,         # unrecaptured 1250 gain 25% (S09 snippet) + NIIT + CA
        "drag": 0.005,                         # annual tax drag on equity returns (assumption)
        "bldg_share": 0.70,                    # depreciable share of value (assumption: needs appraisal)
        "life": 27.5,                          # residential rental recovery period (statute; not fetched)
        "living_commitment": inp["household"]["living_commitment_in_writing"],
        "comps": inp["household"]["verified_rental_comparables_for_A"],
    }


def variant(base, **kw):
    p = dict(base)
    p.update(kw)
    if "cpi" in kw and "g13" not in kw:
        p["g13"] = min(p["cpi"], 0.02)
    return p


def simulate(path, T, H, P, eq_seq, bill_seq):
    """Monthly simulation for one path. Returns nominal and real terminal values."""
    months = 12 * H
    cpi = P["cpi"]
    mv_T = P["mv0"] * (1 + P["hpa"]) ** (T - VAL_YEAR)
    av_base_T = P["av0"] * (1 + P["g13"]) ** (T - VAL_YEAR)
    cap_T = P["cap0"] * (1 + cpi) ** max(0, T - 2027)
    # Prop 19 new assessed value at transfer if the heir occupies (value above base+cap is added)
    av_live_T = max(av_base_T, mv_T - cap_T)
    # mode bounds
    bounds = []
    s = 0
    for mode, yrs in path["segs"]:
        e = months if yrs is None else min(months, s + 12 * yrs)
        bounds.append((mode, s, e))
        s = e
        if s >= months:
            break

    def mode_at(m):
        for mode, a, b in bounds:
            if a <= m < b:
                return mode
        return None

    eq = 0.0
    bill = 0.0
    imp = 0.0
    parked_initial = 0.0
    tranche = 0.0
    m_sale = None
    cur = None
    owned = False
    AV = 0.0
    basis = 0.0
    dep_taken = 0.0
    lived_months = 0
    sale_tax_total = 0.0
    prop_tax_total = 0.0
    imputed_total = 0.0
    deploy = path["deploy"]
    dep_rate = P["bldg_share"] / P["life"]
    sc_total = P["transfer_rate"] + P["sell_comm"] + P["sell_other"]

    def do_sale(m, mv_now):
        nonlocal eq, bill, owned, parked_initial, tranche, m_sale, sale_tax_total
        price = mv_now * (1 - sc_total)
        adj_basis = basis - dep_taken
        gain = price - adj_basis
        recap = min(dep_taken, max(0.0, gain))
        gain1 = max(0.0, gain - recap)
        excl = P["excl"] if lived_months >= 24 else 0
        taxable1 = max(0.0, gain1 - excl)
        tax = recap * P["recap"] + taxable1 * P["ltcg"]
        sale_tax_total += tax
        net = price - tax
        owned = False
        if deploy is None or deploy[0] == "lump":
            eq += net
        else:
            bill += net
            parked_initial = net
            tranche = net / deploy[2]
            m_sale = m

    for m in range(months):
        md = mode_at(m)
        if md is None:
            break
        mv_m = P["mv0"] * (1 + P["hpa"]) ** ((T - VAL_YEAR) + m / 12)
        if cur is None:
            cur = md
            owned = True
            if md in ("live", "sell"):
                AV = av_live_T if md == "live" else mv_T
            else:
                AV = mv_T
            basis = mv_T
        elif md != cur:
            if md == "rent" and cur == "live":
                # moved out: the Prop 19 exclusion ends; reassessed to market at the next lien date
                AV = mv_m
                basis = mv_m
                dep_taken = 0.0
            cur = md
        if cur == "sell" and owned:
            do_sale(m, mv_m)

        k = m // 12
        eq_ann = eq_seq[k % len(eq_seq)]
        bill_ann = bill_seq[k % len(bill_seq)]
        eq_net_m = (1 + eq_ann - P["drag"]) ** (1 / 12) - 1
        bill_net_m = (1 + bill_ann * (1 - P["ord"])) ** (1 / 12) - 1
        eq *= 1 + eq_net_m
        bill *= 1 + bill_net_m
        imp *= 1 + eq_net_m

        cash = 0.0
        if owned:
            AV *= (1 + P["g13"]) ** (1 / 12)
            infl = (1 + cpi) ** (m / 12)
            ptax = AV * P["rate"] / 12
            ins = P["ins0"] * infl / 12
            water = P["water0_m"] * infl
            maint = P["maint"] * mv_m / 12
            costs = ptax + ins + water + maint
            prop_tax_total += ptax
            if cur == "live":
                imputed = P["rent_yield"] * mv_m / 12
                imp += imputed
                imputed_total += imputed
                cash = -costs
                lived_months += 1
            elif cur == "rent":
                rent = P["rent_yield"] * mv_m * (1 - P["vac"]) / 12
                dep = P["bldg_share"] * basis / P["life"] / 12
                taxable = rent - costs - dep
                tax = max(0.0, taxable) * P["ord"]
                cash = rent - costs - tax
                dep_taken += dep
        # household cash flows (rent in, costs and tax out) go to the cash/T-bill account, not to
        # equities: a shortfall is funded at the bill rate instead of compounding at the equity return
        bill += cash

        # phased deployment out of T-bills into equities
        if deploy is not None and deploy[0] == "park" and m_sale is not None and bill > 0:
            since = m - m_sale
            if deploy[1] <= since < deploy[1] + deploy[2]:
                amt = min(tranche, bill)
                bill -= amt
                eq += amt

    if owned:
        # value any property still held at the end, as if sold then (fair comparison)
        mv_end = P["mv0"] * (1 + P["hpa"]) ** ((T - VAL_YEAR) + H)
        do_sale(months, mv_end)

    fin = eq + bill
    total = fin + imp
    defl = (1 + cpi) ** H
    return {
        "fin_real": fin / defl,
        "total_real": total / defl,
        "imputed_real": imp / defl,
        "sale_tax": sale_tax_total,
        "prop_tax_nominal": prop_tax_total,
        "imputed_nominal": imputed_total,
        "lived_months": lived_months,
    }


def pct_sorted(vals, q):
    v = sorted(vals)
    i = (len(v) - 1) * q
    lo = int(i)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


def monte_carlo(path, T, H, P, years_eq, years_bill, draws):
    res_fin, res_tot = [], []
    for seq in draws:
        eq_seq = [years_eq[i] for i in seq]
        bill_seq = [years_bill[i] for i in seq]
        r = simulate(path, T, H, P, eq_seq, bill_seq)
        res_fin.append(r["fin_real"])
        res_tot.append(r["total_real"])
    return res_fin, res_tot


def historical_seq(years, series, start_year, H):
    i = years.index(start_year)
    return [series[(i + k) % len(series)] for k in range(H)]


def summarise(vals):
    return {"median": r10(pct_sorted(vals, 0.5)), "p10": r10(pct_sorted(vals, 0.10)), "p90": r10(pct_sorted(vals, 0.90))}


def run_all(P, years, eq_hist_raw, bill_hist, n_mc, seed):
    eq_hist = [x + P.get("eq_adj", 0.0) for x in eq_hist_raw]   # equity stress shifts the whole record
    rng = random.Random(seed)
    idx_all = list(range(len(years)))
    out = {}
    eq_geo = geo_mean(eq_hist)
    fwd_bill = 0.032   # CBO 3-month average over the decade, secondary summary (S22)
    for T in TRANSFER_YEARS:
        for H in HORIZONS:
            # Monte Carlo draws: H annual pairs drawn with replacement from 1928-2025
            draws = [[rng.choice(idx_all) for _ in range(H)] for _ in range(n_mc)]
            block = {}
            for pid, path in PATHS.items():
                fin_list, tot_list = monte_carlo(path, T, H, P, eq_hist, bill_hist, draws)
                s_fin = summarise(fin_list)
                s_tot = summarise(tot_list)
                row = {
                    "label": path["label"],
                    "pure": path["pure"],
                    "mc_fin": s_fin,
                    "mc_total": s_tot,
                }
                # deterministic scenarios (real terminal value)
                base_eq = [eq_geo] * H
                base_bill = [fwd_bill] * H
                det = simulate(path, T, H, P, base_eq, base_bill)
                row["det_base"] = r10(det["fin_real"])
                row["det_base_total"] = r10(det["total_real"])
                row["imputed_real_base"] = r10(det["imputed_real"])
                row["prop_tax_nominal"] = r10(det["prop_tax_nominal"])
                row["imputed_nominal"] = r10(det["imputed_nominal"])
                row["sale_tax_base"] = r10(det["sale_tax"])
                for name, yr in CRASHES.items():
                    rr = simulate(path, T, H, P, historical_seq(years, eq_hist, yr, H), historical_seq(years, bill_hist, yr, H))
                    row[name] = r10(rr["fin_real"])
                eq5 = simulate(path, T, H, P, [0.05] * H, [fwd_bill] * H)
                row["stress_eq5"] = r10(eq5["fin_real"])
                reinv = simulate(path, T, H, P, base_eq, [fwd_bill] * min(3, H) + [0.01] * max(0, H - 3))
                row["reinvest_shock"] = r10(reinv["fin_real"])
                block[pid] = row
            out[f"{T}_{H}"] = {"T": T, "H": H, "paths": block}
    return out


def rules(block, P):
    """Pre-committed choice rules from DECISION_RULES.md, applied mechanically."""
    C = block["SELL_LUMP"]
    c_med = C["mc_fin"]["median"]
    c_p10 = C["mc_fin"]["p10"]
    c_worst = min(C[k] for k in CRASHES)
    eligible = {}
    removed = {}
    for pid, row in block.items():
        if pid in ("LIVE", "LIVE3_SELL", "LIVE3_RENT") and not P["living_commitment"]:
            removed[pid] = "Rule 3: no written commitment to occupy A within 12 months"
            continue
        if pid in ("RENT", "RENT3_SELL") and P["comps"] < 3:
            removed[pid] = "Rule 4: fewer than three verified rental comparables; reported as a floor only"
            continue
        eligible[pid] = row
    checks = {}
    passing = ["SELL_LUMP"]
    for pid in ("SELL_P24", "SELL_P36"):
        if pid not in eligible:
            continue
        row = eligible[pid]
        med = row["mc_fin"]["median"]
        p10 = row["mc_fin"]["p10"]
        worst = min(row[k] for k in CRASHES)
        guard = p10 >= c_p10 - 0.10 * abs(c_p10)                   # Rule 2
        phased_ok = worst >= c_worst and med >= c_med - 0.05 * abs(c_med)   # Rule 5
        beats = med > c_med * 1.02 if c_med > 0 else med > c_med     # Rule 8 tie band (2%)
        checks[pid] = {"guard_rule2": guard, "phase_rule5": phased_ok, "beats_by_more_than_2pct": beats,
                       "worst_black_swan": worst, "median": med}
        if guard and phased_ok and beats:
            passing.append(pid)
    choice = max(passing, key=lambda p: eligible[p]["mc_fin"]["median"] if p in eligible else -1e18)
    leader = max(block, key=lambda p: block[p]["mc_fin"]["median"])
    return {
        "choice": choice,
        "choice_label": block[choice]["label"],
        "unconstrained_leader": leader,
        "unconstrained_leader_label": block[leader]["label"],
        "eligible": sorted(eligible),
        "removed": removed,
        "checks": checks,
    }


def grid_variants(base, eq_geo):
    return [
        ("base", "Base case (as published)", {}),
        ("cpi_low", "Inflation 1.7% a year (range tested; not a CBO figure)", {"cpi": 0.017}),
        ("cpi_high", "Inflation 3.7% a year (range tested; not a CBO figure)", {"cpi": 0.037}),
        ("hpa_low", "Home values flat in nominal terms", {"hpa": 0.0}),
        ("hpa_high", "Home values +4% a year", {"hpa": 0.04}),
        ("rent_low", "Gross rent yield 3.0% (assumption)", {"rent_yield": 0.03}),
        ("rent_high", "Gross rent yield 4.5% (assumption)", {"rent_yield": 0.045}),
        ("tax_floor", "Tax rate at the published county floor 1.0412%", {"rate": 0.010412}),
        ("maint_high", "Maintenance 1.5% of value (assumption)", {"maint": 0.015}),
        ("ins_high", "Insurance $2,500 a year (assumption band)", {"ins0": 2500}),
        ("ord_high", "Ordinary tax rate 50.3% (stress case; top rate not verified, F-05)", {"ord": 0.503}),
        ("excl_high", "Living exclusion $500,000 (joint filers)", {"excl": 500000}),
        ("drag_high", "Equity tax drag 1.5% a year (assumption)", {"drag": 0.015}),
        ("eq_stress", "Equity return 5% a year (record shifted to a 5% geometric mean)", {"eq_adj": 0.05 - eq_geo}),
    ]


def main():
    inp = load_inputs()
    years, eq_hist, bill_hist = load_returns()
    base = base_params(inp)

    main_block = run_all(base, years, eq_hist, bill_hist, N_MC, SEED)
    picks = {}
    for key, blk in main_block.items():
        picks[key] = rules(blk["paths"], base)

    # Sensitivity: does the pick move when one input moves? (fewer draws, same seed)
    grid = []
    for vid, vlabel, changes in grid_variants(base, geo_mean(eq_hist)):
        P = variant(base, **changes)
        res = run_all(P, years, eq_hist, bill_hist, N_GRID, SEED)
        row = {"id": vid, "label": vlabel, "picks": {}}
        for key, blk in res.items():
            pk = rules(blk["paths"], P)
            row["picks"][key] = {"choice": pk["choice"], "leader": pk["unconstrained_leader"],
                                 "median_choice": blk["paths"][pk["choice"]]["mc_fin"]["median"]}
        grid.append(row)
    base_picks = {k: v["choice"] for k, v in picks.items()}
    moved = []
    for row in grid:
        flips = [k for k in base_picks if row["picks"][k]["choice"] != base_picks[k]]
        row["moved_in"] = flips
        row["moved"] = bool(flips)
        moved.append(row["id"] if flips else None)

    # Deterministic what-if table (no randomness): rent yield x home-value growth, 2050 + 20 years
    whatif = {"transfer_year": 2050, "horizon": 20, "rent_yields": [0.03, 0.0375, 0.045],
              "hpa": [0.0, 0.023, 0.04], "cells": []}
    for ry in whatif["rent_yields"]:
        for hp in whatif["hpa"]:
            P = variant(base, rent_yield=ry, hpa=hp)
            cell = {"rent_yield": ry, "hpa": hp, "paths": {}}
            for pid, path in PATHS.items():
                r = simulate(path, 2050, 20, P, [geo_mean(eq_hist)] * 20, [0.032] * 20)
                cell["paths"][pid] = r10(r["fin_real"])
            whatif["cells"].append(cell)

    # Distribution for the chart: real terminal value, 2050 transfer, 20-year horizon
    rng = random.Random(SEED + 1)
    draws = [[rng.choice(range(len(years))) for _ in range(20)] for _ in range(N_MC)]
    dist = {}
    for pid in ("SELL_LUMP", "SELL_P24", "SELL_P36", "LIVE", "RENT"):
        vals = []
        for seq in draws:
            r = simulate(PATHS[pid], 2050, 20, base, [eq_hist[i] for i in seq], [bill_hist[i] for i in seq])
            vals.append(r["fin_real"])
        vals.sort()
        lo, hi = vals[0], vals[-1]
        bins = 20
        width = (hi - lo) / bins if hi > lo else 1
        counts = [0] * bins
        for v in vals:
            j = min(bins - 1, int((v - lo) / width))
            counts[j] += 1
        dist[pid] = {"min": r10(lo), "max": r10(hi), "bin_width": r10(width),
                     "bins": [r10(lo + i * width) for i in range(bins)], "counts": counts}

    # Yearly projections, base case (nominal and real), Property A and Property B
    proj = []
    cpi = base["cpi"]
    a0 = inp["property_a"]
    b0 = inp["property_b"]
    bav = b0["history"][0]["assessed"]
    b_rate_statutory = 0.0118162182
    for y in range(VAL_YEAR, 2061):
        t = y - VAL_YEAR
        mv = base["mv0"] * (1 + base["hpa"]) ** t
        infl = (1 + cpi) ** t
        row = {"year": y}
        # Property A
        row["a_value"] = r10(mv)
        row["a_assessed_if_reassessed_2040"] = r10(base["mv0"] * (1 + base["hpa"]) ** 14) if y >= 2040 else r10(base["av0"] * (1 + base["g13"]) ** t)
        if y >= 2040:
            tt = y - 2040
            av_base = base["av0"] * (1 + base["g13"]) ** (2040 - VAL_YEAR)
            mv40 = base["mv0"] * (1 + base["hpa"]) ** 14
            cap40 = base["cap0"] * (1 + cpi) ** 13
            av_live = max(av_base, mv40 - cap40) * (1 + base["g13"]) ** tt
            av_full = mv40 * (1 + base["g13"]) ** tt
        else:
            av_live = base["av0"] * (1 + base["g13"]) ** t
            av_full = av_live
        row["a_assessed_live_prop19"] = r10(av_live)
        row["a_tax_live_prop19"] = r10(av_live * base["rate"])
        row["a_tax_full_reassessment"] = r10(av_full * base["rate"])
        row["a_insurance"] = r10(base["ins0"] * infl)
        row["a_water_net_annual"] = r10(base["water0_m"] * 12 * infl)
        row["a_maintenance_at_1pct"] = r10(base["maint"] * mv)
        row["a_imputed_rent_at_yield"] = r10(base["rent_yield"] * mv)
        # Property B (owned; owner-supplied income and costs; statutory SF rate on assessed value)
        bav_t = bav * (1.02) ** t
        row["b_value"] = r10(b0["value_estimate"]["value"] * (1 + base["hpa"]) ** t)
        row["b_assessed"] = r10(bav_t)
        row["b_tax_statutory_rate"] = r10(bav_t * b_rate_statutory)
        row["b_insurance"] = r10(base["ins0"] * infl)
        row["b_water_annual"] = r10(sum(b0["water_monthly_range"]) / 2 * 12 * infl)
        row["b_electricity_annual"] = r10(sum(b0["electricity_monthly_range"]) / 2 * 12 * infl)
        row["b_rent_income_annual"] = r10(b0["rent_monthly_total"] * 12 * infl)
        row["real_factor"] = round(1 / infl, 4)
        proj.append(row)

    # Breakevens: what would have to be true for living (or renting) to match a lump-sum sale
    def det_total(pid, P, T, H):
        return simulate(PATHS[pid], T, H, P, [geo_mean(eq_hist)] * H, [0.032] * H)["total_real"]

    def det_sell(P, T, H):
        return simulate(PATHS["SELL_LUMP"], T, H, P, [geo_mean(eq_hist)] * H, [0.032] * H)["fin_real"]

    def bisect(fn, lo, hi):
        flo = fn(lo)
        fhi = fn(hi)
        if flo * fhi > 0:
            return None
        for _ in range(60):
            mid = (lo + hi) / 2
            fm = fn(mid)
            if flo * fm <= 0:
                hi, fhi = mid, fm
            else:
                lo, flo = mid, fm
        return round((lo + hi) / 2, 5)

    breakeven = {}
    for T in TRANSFER_YEARS:
        for H in HORIZONS:
            key = f"{T}_{H}"
            breakeven[key] = {
                "live_rent_yield": bisect(lambda y: det_total("LIVE", variant(base, rent_yield=y), T, H) - det_sell(base, T, H), 0.0, 0.20),
                "rent_rent_yield": bisect(lambda y: det_total("RENT", variant(base, rent_yield=y), T, H) - det_sell(base, T, H), 0.0, 0.20),
                "live_hpa": bisect(lambda g: det_total("LIVE", variant(base, hpa=g), T, H) - det_sell(variant(base, hpa=g), T, H), -0.02, 0.10),
            }

    # Estate-tax headroom (federal basic exclusion; CA has no estate tax, see sources)
    known_re = inp["household"]["estate_tax_known_real_estate_total"]
    headroom = 15000000 - known_re

    out = {
        "_meta": {
            "generated_by": "tools/model.py",
            "seed": SEED,
            "monte_carlo_draws": N_MC,
            "sensitivity_draws": N_GRID,
            "valuation_year": VAL_YEAR,
            "transfer_years": TRANSFER_YEARS,
            "horizons_years": HORIZONS,
            "note": "All money values rounded to the nearest $10. Real = deflated by the base CPI assumption. Property B is held in every path and is shown as context only.",
        },
        "assumptions": {
            "cpi_base": base["cpi"],
            "home_value_growth": base["hpa"],
            "prop13_growth_cap": base["g13"],
            "prop19_cap_2025_2027": base["cap0"],   # statutory, printed exactly (BOE LTA 2025/009)
            "rate_owner_implied_pct": pct(base["rate"], 4),
            "rate_county_floor_pct": 1.0412,
            "rate_sf_b_statutory_pct": 1.18162182,
            "water_net_monthly": r10(base["water0_m"]),
            "insurance_annual": r10(base["ins0"]),
            "rent_yield": base["rent_yield"],
            "vacancy": base["vac"],
            "maintenance_rate": base["maint"],
            "sale_costs_pct": pct(0.0011 + base["sell_comm"] + base["sell_other"], 2),
            "transfer_tax_pct": pct(base["transfer_rate"], 3),
            "ordinary_rate_combined": base["ord"],
            "ltcg_rate_combined": round(base["ltcg"], 4),
            "recapture_rate_combined": round(base["recap"], 4),
            "equity_tax_drag": base["drag"],
            "building_share": base["bldg_share"],
            "exclusion_living": base["excl"],
            "equity_geo_mean_1928_2025_pct": pct(geo_mean(eq_hist), 2),
            "tbill_geo_mean_1928_2025_pct": pct(geo_mean(bill_hist), 2),
            "forward_bill_pct": 3.2,   # CBO By the Numbers (S23): 3-month bills 3.2% for 2027-2030
            "stress_equity_pct": 5.0,
            "living_commitment_in_writing": base["living_commitment"],
            "verified_rental_comparables": base["comps"],
        },
        "paths": {k: {"label": v["label"], "pure": v["pure"]} for k, v in PATHS.items()},
        "results": main_block,
        "picks": picks,
        "sensitivity": {"grid": grid, "moved_variants": [m for m in moved if m]},
        "whatif": whatif,
        "distribution": dist,
        "projections": proj,
        "breakeven": breakeven,
        "estate": {"federal_basic_exclusion": 15000000, "known_real_estate_owner_estimates": known_re,
                   "headroom_for_other_assets_before_debts_and_expenses": headroom,
                   "federal_rate_above_exclusion_pct": 40},
    }
    (ROOT / "data/model_outputs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print("wrote data/model_outputs.json")
    for key in picks:
        print(key, picks[key]["choice"], "| leader:", picks[key]["unconstrained_leader"], "| moved variants:",
              [r["id"] for r in grid if r["picks"][key]["choice"] != picks[key]["choice"]])


if __name__ == "__main__":
    main()
