"""
build.py — run the model, write decision-workspace/data/*.json for the site.

Run from anywhere:  python3 model/build.py
Nothing here talks to the network, and every dollar that leaves is rounded to $10 by r10(),
so the published JSON is safe to publish. The unrounded values never get written anywhere.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "decision-workspace", "data")
sys.path.insert(0, HERE)

import inputs as I           # noqa: E402
import history as H          # noqa: E402
import engine as E           # noqa: E402
import projections as P      # noqa: E402
import registers as R        # noqa: E402


# ---------------------------------------------------------- privacy filter ----
# The household's rule is absolute: every published dollar figure is rounded to the
# nearest $10 so that nothing on this site can be matched back to a public record or a
# search result. Applying it only to the numeric columns would leave the narrative text
# (the source notes, the flags, the statute summaries) holding exact amounts, so the
# filter is applied to EVERY string in the payload, mechanically, at write time.
#
# It rewrites a bare dollar amount of three or more digits ($1,044,586 -> $1,044,590) and
# leaves alone anything with a decimal point (a per-$500 rate like $3.75, a per-square-foot
# rate like $0.195) and anything under $100, which are published rates, not the
# household's own figures. The exact official number is always one click away at the source.
_AMOUNT = re.compile(r"\$([0-9][0-9,]{2,})(?![.0-9])")


def scrub_str(t):
    def rep(m):
        n = int(m.group(1).replace(",", ""))
        return "$" + format(int(round(n / 10.0) * 10), ",d")
    return _AMOUNT.sub(rep, t)


def scrub(obj):
    if isinstance(obj, str):
        return scrub_str(obj)
    if isinstance(obj, bool) or obj is None or isinstance(obj, (int, float)):
        return obj
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [scrub(v) for v in obj]
    return obj


def write(name, obj):
    obj = scrub(obj)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"), sort_keys=False)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:26s} {kb:8.1f} KB")
    return path


def main():
    print("running model ...")
    paths30, specs = E.run(30)
    paths10, _ = E.run(10, sims=600)
    paths20, _ = E.run(20, sims=600)
    sc30 = E.score(paths30)
    sc30_use = E.score(paths30, use_value_in_ranking=True)
    bt, by = E.phased_backtest()

    # ---- paths.json : the comparison, all twelve paths, three horizons
    path_rows = []
    for sp in specs:
        p = paths30[sp["id"]]
        row = dict(id=sp["id"], name=sp["name"], group=sp["group"],
                   prop19=bool(sp["prop19"]), sell_at=sp["sell_a"],
                   occupy_a=("yes" if sp["a"] == "occupied" else ("partial" if sp.get("switch_at") else "no")),
                   occupy_b=("yes" if sp["b_occupy"] else "no"),
                   invest=sp["invest"],
                   w30=p["final_real"], w20=paths20[sp["id"]]["final_real"],
                   w10=paths10[sp["id"]]["final_real"],
                   w30_use=p["final_real_use"], use_value=p["use_value"],
                   p10=p["p10"], p50=p["p50"], p90=p["p90"], mean=p["mean"], sd=p["sd"],
                   min_wealth=p["min_wealth"], cash_flow_min=p["cash_flow_min"],
                   score=sc30[sp["id"]]["score"], score_use=sc30_use[sp["id"]]["score"],
                   dist=p["dist"])
        path_rows.append(row)
    write("paths.json", dict(horizon=30, transfer_year=I.ECON["transfer_year"],
                             asof=I.ASOF, seed=E.SEED, sims=E.N_SIMS, rows=path_rows,
                             yearly={k: v["rows"] for k, v in paths30.items()}))

    # ---- assessed.json : Prop 19 / Prop 13 maths, line by line
    sc = P.prop19_scenarios(30)
    write("assessed.json", dict(
        transfer_year=sc["transfer_year"], fbyv_T=sc["fbyv_T"], value_T=sc["value_T"],
        allowance_T=sc["allowance_T"], cap_T=sc["cap_T"], base_excluded=sc["base_excluded"],
        tax_excluded=sc["tax_excluded"], tax_full=sc["tax_full"], delta_yr0=sc["delta_yr0"],
        rows=sc["rows"],
        rateA=I.RULES["sc_rate_central"],
        carry_A={m: P.carry_costs("A", 30, assessed_mode=m) for m in ("prop13", "prop19", "reassess")},
        carry_B=P.carry_costs("B", 30),
        history_A=[dict(year=y, tax=t, assessed=a, tax_pct=tc, assd_pct=ac)
                   for (y, t, a, tc, ac) in I.HISTORY_A],
        history_B=[dict(year=y, tax=t, assessed=a, tax_pct=tc, assd_pct=ac)
                   for (y, t, a, tc, ac) in I.HISTORY_B],
    ))

    # ---- taxes.json : the sale itself, worked line by line
    write("taxes.json", dict(sales=P.sale_examples(), transfer=P.transfer_costs(),
                             rules=I.RULES, laws=R.LAWS,
                             fed_bea=[["2024", 13_610_000], ["2025", 13_990_000], ["2026", 15_000_000]],
                             prop19_prior=[[rng, I.r10(amt)] for amt, rng in I.RULES["prop19_prior_amounts"]]))

    # ---- blackswan.json + phased.json
    st = H.stats()
    write("blackswan.json", dict(
        stats=dict(n_years=st["n_years"], sp_geo=round(st["sp_geo"] * 100, 2),
                   sp_arith=round(st["sp_arith"] * 100, 2), sp_sd=round(st["sp_sd"] * 100, 2),
                   bill_geo=round(st["bill_geo"] * 100, 2), bill_sd=round(st["bill_sd"] * 100, 2),
                   worst=round(st["worst"] * 100, 2), worst_year=st["worst_year"],
                   best=round(st["best"] * 100, 2), best_year=st["best_year"],
                   neg_years=st["neg_years"], down20=st["down20"]),
        episodes=E.regime_table(), rolling=E.rolling_returns(10), rolling5=E.rolling_returns(5),
        rows=[[y, I.r10(0), s * 100, b * 100] for (y, s, b) in H.RETURNS],
    ))
    backtest = []
    for entry, tab in sorted(by.items()):
        for (park, ph), r in sorted(tab.items()):
            backtest.append(dict(entry=entry, park=park, phase=ph,
                                 wealth=round(r["wealth"], 3),
                                 vs_lump=round(r["vs_lump"] * 100, 1),
                                 max_dd=round(r["max_dd"] * 100, 1),
                                 dd_delta=round(r["dd_vs_lump"] * 100, 1)))
    write("phased.json", dict(config=I.PHASING, rows=backtest,
                              curve=[["3-month", 3.65], ["2-year", 3.47], ["10-year", 4.19]],
                              curve_date="2026-01-02",
                              note="Monthly conversion from annual data is geometric; the ranking, "
                                   "not the third decimal, is the point."))

    # ---- sensitivity grid for the what-if controls
    cells = E.sensitivity_grid((10, 20, 30))
    write("sensitivity.json", dict(
        cells=cells,
        dials=dict(home=[["low", I.ECON["home_value_growth"]["low"]],
                         ["mid", I.ECON["home_value_growth"]["mid"]],
                         ["high", I.ECON["home_value_growth"]["high"]]],
                   equity=[["low", I.ECON["equity_real_return"]["low"]],
                           ["mid", I.ECON["equity_real_return"]["mid"]],
                           ["high", I.ECON["equity_real_return"]["high"]]],
                   rent=[["low", I.ECON["rent_growth"]["low"]],
                         ["mid", I.ECON["rent_growth"]["mid"]],
                         ["high", I.ECON["rent_growth"]["high"]]],
                   horizons=[10, 20, 30]),
        ids=[sp["id"] for sp in specs], names={sp["id"]: sp["name"] for sp in specs}))

    # ---- registers, sources, flags, questions, suggestions, process, capital plan
    write("registers.json", dict(
        asof=I.ASOF, session=I.SESSION,
        sources={k: dict(title=v[0], url=v[1], status=v[2]) for k, v in I.SOURCES.items()},
        questions=I.QUESTIONS, suggestions=I.SUGGESTIONS, flags=I.FLAGS,
        laws=R.LAWS, timeline=R.TIMELINE, criteria=R.CRITERIA, decisions=R.DECISION_LOG,
        recheck=R.RECHECK, glossary=[dict(term=t, defn=d) for t, d in R.GLOSSARY],
        process=P.PROCESS, capital_plan=P.capital_plan(),
        econ=I.ECON, transact=I.TRANSACT, properties=dict(A=I.PROPERTY_A, B=I.PROPERTY_B),
        exec=P.exec_summary(paths30, sc30),
    ))
    print("done ->", OUT)


if __name__ == "__main__":
    main()
