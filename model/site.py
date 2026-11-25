"""
site.py — build the context once, render every page, and write the JSON the browser needs.

  cd model && python3 site.py

Charts and the what-if controls read assets/data.js, which is generated here from the same
run as the prose - so a number can never disagree between the sentence and the SVG.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import inputs as I  # noqa: E402
import history as H  # noqa: E402
import engine as E  # noqa: E402
import projections as P  # noqa: E402
import site_pages as PG  # noqa: P04 - page builders  # noqa: E402
import site_pages2 as PG2  # noqa: E402
from site_lib import r10, write, scrub_str  # noqa: E402


def robustness(cells, ids):
    """How often does each path win across the published grid?"""
    ranks = {i: [] for i in ids}
    firsts = {i: 0 for i in ids}
    top3 = {i: 0 for i in ids}
    for c in cells:
        vals = sorted(((v["w"], k) for k, v in c["values"].items()), reverse=True)
        for pos, (v, k) in enumerate(vals):
            ranks[k].append(pos + 1)
            if pos == 0:
                firsts[k] += 1
            if pos < 3:
                top3[k] += 1
    out = []
    for k in ids:
        rs = sorted(ranks[k])
        med = rs[len(rs) // 2]
        n = len(cells)
        if firsts[k] == n:
            note = "wins in every published scenario - the ranking does not depend on the dials"
        elif firsts[k] == 0:
            note = "never first anywhere in the grid; it survives only as a preference, not a return"
        elif top3[k] / n > 0.8:
            note = "top three almost everywhere - robust, but not the leader"
        else:
            note = f"first in {100 * firsts[k] // n}% of scenarios - genuinely dial-dependent"
        out.append(dict(id=k, first=firsts[k], top3=top3[k], med=med, worst=max(rs), n=n, note=note))
    out.sort(key=lambda r: (-r["first"], r["med"]))
    return out


def main():
    print("running model (seeded, " + str(E.N_SIMS) + " simulations per path) ...")
    paths30, specs = E.run(30)
    paths20, _ = E.run(20, sims=600)
    paths10, _ = E.run(10, sims=600)
    sc = E.score(paths30)
    sc_use = E.score(paths30, use_value_in_ranking=True)
    bt, by = E.phased_backtest()
    cells = E.sensitivity_grid((10, 20, 30))
    ids = [s["id"] for s in specs]
    prop19 = P.prop19_scenarios(30)
    carry = {mode: dict(rows=P.carry_costs("A", 30, assessed_mode=mode))
             for mode in ("prop13", "prop19", "reassess")}
    carryB = P.carry_costs("B", 30)
    rd = E.rent_diagnostics()

    # how much the staging lane costs, and how sensitive the keep paths are to house prices
    stage_cost = 100 * (1 - paths30["P-06"]["final_real"] / paths30["P-05"]["final_real"])
    mid = [c for c in cells if (c["home"], c["equity"], c["rent"], c["prop19"], c["horizon"])
           == ("mid", "mid", "mid", True, 30)][0]
    lo = [c for c in cells if (c["home"], c["equity"], c["rent"], c["prop19"], c["horizon"])
          == ("low", "mid", "mid", True, 30)][0]
    hi = [c for c in cells if (c["home"], c["equity"], c["rent"], c["prop19"], c["horizon"])
          == ("high", "mid", "mid", True, 30)][0]
    keep = [k for k in ids if specs[ids.index(k)]["sell_a"] is None]
    home_sens = ("%.0f%% to %.0f%% swings in terminal wealth across the growth dial"
                 % (100 * (lo["values"][keep[0]]["n"] / mid["values"][keep[0]]["n"] - 1),
                    100 * (hi["values"][keep[0]]["n"] / mid["values"][keep[0]]["n"] - 1)))

    ctx = dict(paths30=paths30, paths20=paths20, paths10=paths10, sc=sc, sc_use=sc_use, specs=specs,
               prop19=prop19, carry=carry, carryB=carryB, sales=P.sale_examples(),
               transfer=P.transfer_costs(), capital=P.capital_plan(), process=P.PROCESS,
               by=by, bt=bt, curve=[["3-month", 3.65], ["2-year", 3.47], ["10-year", 4.19]],
               stats=H.stats(), regime=E.regime_table(), rolling=E.rolling_returns(10),
               rent_diag=rd, robust=robustness(cells, ids),
               grid_dials=dict(home=[("low", "%.1f%%" % (100 * I.ECON["home_value_growth"]["low"])),
                                     ("mid", "%.1f%%" % (100 * I.ECON["home_value_growth"]["mid"])),
                                     ("high", "%.1f%%" % (100 * I.ECON["home_value_growth"]["high"]))],
                               equity=[("low", "%.1f%%" % (100 * I.ECON["equity_real_return"]["low"])),
                                       ("mid", "%.1f%%" % (100 * I.ECON["equity_real_return"]["mid"])),
                                       ("high", "%.1f%%" % (100 * I.ECON["equity_real_return"]["high"]))],
                               rent=[("low", "%.1f%%" % (100 * I.ECON["rent_growth"]["low"])),
                                     ("mid", "%.1f%%" % (100 * I.ECON["rent_growth"]["mid"])),
                                     ("high", "%.1f%%" % (100 * I.ECON["rent_growth"]["high"]))]),
               stage_cost=stage_cost, home_sens=home_sens,
               yearly={k: v["rows"] for k, v in paths30.items()},
               cells=cells, ids=ids,
               short=PG.SHORT)

    print("writing pages ...")
    # Each page declares what its tables rest on; simple_table() adds a Source column filled from
    # this whenever a table does not build its own, so an unsourced table cannot be published.
    import site_lib as L
    L.SRC("model")
    write("index.html", PG.index(ctx))
    L.SRC("model")
    write("paths.html", PG.paths(ctx))
    L.SRC("model")
    write("projections.html", PG.projections(ctx))
    L.SRC("SCC-RATEBOOK", "BOE-P19", "IRS-559", "SF-TRANSFER-TAX")
    write("tax-rules.html", PG.tax_rules(ctx))
    L.SRC("owner", "SCC-RECORDER-FEES", "SFELECT-RRP", "SFPUC-RATES")
    write("costs.html", PG.costs(ctx))
    write("process.html", PG.process(ctx))
    L.SRC("DAMO")
    write("black-swan.html", PG.black_swan(ctx))
    L.SRC("DAMO", "UST-DAILY")
    write("phased.html", PG.phased(ctx))
    L.SRC("model", "DAMO")
    write("what-if.html", PG.what_if(ctx))
    L.SRC("CALEG", "BOE-P19", "SF-ORD-1342")
    write("watch.html", PG2.watch(ctx))
    L.SRC("owner")
    write("recheck.html", PG2.recheck(ctx))
    L.SRC("owner")
    write("open-questions.html", PG2.open_questions(ctx))
    L.SRC("owner", "model")
    write("suggestions.html", PG2.suggestions(ctx))
    L.SRC("owner")
    write("flagged.html", PG2.flagged(ctx))
    L.SRC("owner", "ZILLOW")
    write("comparables.html", PG2.comparables(ctx))
    L.SRC("model")
    write("sources.html", PG2.sources(ctx))
    L.SRC("model", "owner")
    write("framework.html", PG2.framework(ctx))
    L.SRC("model", "owner")
    write("briefing.html", PG2.briefing(ctx))
    L.SRC("model")
    write("glossary.html", PG2.glossary(ctx))
    L.SRC("model")
    write("model.html", PG2.model(ctx))

    # ---- assets/data.js : everything the browser renders or recomputes
    data = dict(
        asof=I.ASOF, seed=E.SEED, sims=E.N_SIMS, transfer_year=I.ECON["transfer_year"],
        horizon=30, ids=ids, short=PG.SHORT,
        paths={k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in paths30.items()},
        w10={k: v["final_real"] for k, v in paths10.items()},
        w20={k: v["final_real"] for k, v in paths20.items()},
        yearly=ctx["yearly"],
        rows12=[dict(id=k, name=v["name"], w30=v["final_real"], w30_use=v["final_real_use"],
                    p10=v["p10"], p50=v["p50"], p90=v["p90"], dist=v["dist"], group=v["group"],
                    score=sc[k]["score"]) for k, v in paths30.items()],
        prop19=prop19, carryA=carry, carryB=carryB, rent_diag=rd,
        cells=cells,
        dials=dict(home=["low", "mid", "high"], equity=["low", "mid", "high"], rent=["low", "mid", "high"]),
        rolling=ctx["rolling"], stats=ctx["stats"], regime=ctx["regime"],
        backtest=[dict(entry=e["entry"], park=e["park"], phase=e["phase"], wealth=e["wealth"],
                       vs_lump=e["vs_lump"], max_dd=e["max_dd"], dd_delta=e["dd_vs_lump"])
                  for e in bt if e["entry"] in by],
    )

    def roundtrip(o):
        """belt and braces: run the published blob through the same text filter as the pages"""
        return json.loads(scrub_str(json.dumps(o)))

    payload = json.dumps(roundtrip(data), separators=(",", ":"))
    path = os.path.join(ROOT, "assets", "data.js")
    with open(path, "w") as f:
        f.write("/* generated by model/site.py from the seeded run - do not hand-edit */\n"
                "window.TINO_DATA = " + payload + ";\n")
    print(f"  {'assets/data.js':22s} {os.path.getsize(path)/1024:7.1f} KB")
    print("done.")


if __name__ == "__main__":
    main()
