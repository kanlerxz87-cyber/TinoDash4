"""
projections.py — the yearly projection tables the site renders, plus the pieces of the
comparison that are not part of the Monte Carlo (deadlines, capital plan, process steps).

Everything dollar-denominated leaves through r10(). Anything with no official source is
None (rendered as "not verified") rather than a guess.
"""
from inputs import (PROPERTY_A, PROPERTY_B, RULES, ECON, TRANSACT, HISTORY_A, HISTORY_B,
                    SOURCES, r10)


def carry_costs(prop="A", years=30, start_year=None, home=None, infl=None, rate=None,
                assessed_mode="prop13"):
    """assessed_mode: 'prop13' (exclusion applies, base keeps factoring), 'prop19' (excess
    reassessment on top of the factored base), 'reassess' (no exclusion - full market value)."""
    """Annual carrying cost of one building, split into the lines the household asked for:
    value, assessed value, property tax, insurance, water, electric, maintenance."""
    home = ECON["home_value_growth"]["mid"] if home is None else home
    infl = ECON["inflation"]["mid"] if infl is None else infl
    P = PROPERTY_A if prop == "A" else PROPERTY_B
    start_year = ECON["transfer_year"] if start_year is None else start_year
    rate = RULES["sc_rate_central"] if prop == "A" else RULES["sf_rate_central"]
    base_av = (P["assessed_2026"] if prop == "A" else P["assessed_2025"])
    val = P["value_2026"]
    out = []
    lead = start_year - 2026
    v = float(val) * (1 + home) ** lead
    fbyv = float(base_av) * (1 + RULES["prop13_factor_cap"]) ** lead
    allow = RULES["prop19_indexed_amount"] * (1.02) ** lead
    if prop == "A" and assessed_mode == "reassess":
        av = v
    elif prop == "A" and assessed_mode == "prop19":
        av = fbyv + max(0.0, v - (fbyv + allow))
        allow = RULES["prop19_indexed_amount"] * (1.02) ** lead
        av = fbyv + max(0.0, v - (fbyv + allow))
    else:
        av = fbyv if prop == "A" else float(base_av) * (1 + RULES["prop13_factor_cap"]) ** lead
    g_ins = max(infl, ECON["insurance_growth"]["mid"])
    allow = allow if prop == "A" and assessed_mode == "prop19" else 0.0
    for i in range(years + 1):
        tax = av * rate
        ins = (2400.0 if prop == "A" else 3000.0) * (1 + g_ins) ** (i + lead)
        wat = (sum(P["water_mo"]) / 2.0) * (1 + infl) ** (i + lead)
        ele = (sum(P.get("electric_mo_net", P.get("electric_mo", (0, 0)))) / 2.0) * (1 + infl) ** (i + lead)
        mnt = (P["maintenance_pct_of_value"][0] + P["maintenance_pct_of_value"][1]) / 2.0 * v
        prop_h = (RULES["sf_prop_h_multifamily_base"] * (1 + 0.02) ** i) if prop == "B" else 0.0
        out.append(dict(year=start_year + i, value=r10(v), assessed=r10(av),
                        tax=r10(tax + prop_h), insurance=r10(ins), water=r10(wat),
                        electric=r10(ele), maintenance=r10(mnt),
                        total=r10(tax + prop_h + ins + wat + ele + mnt)))
        v *= (1 + home)
        # the new base is fixed at the transfer (one-time), then factors at the Prop 13 rate
        av *= (1 + RULES["prop13_factor_cap"])
    return out


def prop19_scenarios(years=30, home=None, allowance_growth=0.02):
    """The three assessed-value futures for Property A, on the same market path.

    Prop 19 is a ONE-TIME event: the new base is fixed on the day of distribution
    (prior factored base + the excess above the cap) and from then on it grows at the
    Prop 13 factor like any other base. Models that re-apply the cap every year - and
    some published calculators do - overstate the future bill, because they let the
    excess keep chasing the market value."""
    home = ECON["home_value_growth"]["mid"] if home is None else home
    T = ECON["transfer_year"]
    A = PROPERTY_A
    fbyv = float(A["assessed_2026"])
    val = float(A["value_2026"])
    allow = RULES["prop19_indexed_amount"]
    for _ in range(T - 2026):                     # grow everything to the transfer year
        fbyv *= (1 + RULES["prop13_factor_cap"])
        val *= (1 + home)
        allow *= (1 + allowance_growth)
    cap = fbyv + allow
    base_excluded = fbyv + max(0.0, val - cap)     # fixed at transfer, forever
    allow_T, cap_T, excess_T, fbyv0, val0 = allow, cap, max(0.0, val - cap), fbyv, val
    rows = []
    fb, v, base19, basefull = fbyv, val, base_excluded, val
    for i in range(years + 1):
        year = T + i
        rows.append(dict(year=year, market=r10(v),
                         keep13_assessed=r10(fb), keep13_tax=r10(fb * RULES["sc_rate_central"]),
                         prop19_assessed=r10(base19), prop19_tax=r10(base19 * RULES["sc_rate_central"]),
                         reassess_assessed=r10(basefull),
                         reassess_tax=r10(basefull * RULES["sc_rate_central"]),
                         allowance=r10(allow), cap=r10(cap),
                         excess=r10(excess_T) if i == 0 else None))
        fb *= (1 + RULES["prop13_factor_cap"])
        v *= (1 + home)
        base19 *= (1 + RULES["prop13_factor_cap"])
        basefull *= (1 + RULES["prop13_factor_cap"])
        allow *= (1 + allowance_growth)
        cap = fb + allow
    return dict(rows=rows, transfer_year=T, fbyv_T=r10(fbyv0), value_T=r10(val0),
                allowance_T=r10(allow_T), cap_T=r10(cap_T), excess_T=r10(excess_T),
                base_excluded=r10(base_excluded),
                tax_excluded=r10(base_excluded * RULES["sc_rate_central"]),
                tax_full=r10(val0 * RULES["sc_rate_central"]),
                delta_yr0=r10((val0 - base_excluded) * RULES["sc_rate_central"]))


def gain_table(spec_id, sale_year_offset, market_at_sale, basis, depr=0.0, primary=False,
               capital_add=0.0, hold_years=0):
    """One sale, worked line by line, so a CPA can check it."""
    t = TRANSACT["A"]
    costs = market_at_sale * (t["commission_pct"] + t["seller_concessions_pct"] + t["dtt_pct"]
                              + t["prep_pct"]) + t["closing_flat"]
    net = market_at_sale - costs
    adj = basis + capital_add - depr
    gain = max(0.0, net - adj)
    excl = min(RULES["sec121_single"], gain) if primary else 0.0
    taxable = max(0.0, gain - excl)
    rec = min(depr, taxable)
    fed = rec * 0.25 + (taxable - rec) * (RULES["fed_ltcg_top"] + RULES["niit"])
    ca = taxable * (RULES["ca_top"] + RULES["ca_bhst"])
    return dict(spec=spec_id, year=sale_year_offset, price=r10(market_at_sale),
                costs=r10(costs), net=r10(net), basis=r10(basis), capital_add=r10(capital_add),
                depreciation=r10(depr), adjusted_basis=r10(adj), gain=r10(gain),
                exclusion=r10(excl), taxable_gain=r10(taxable), recapture=r10(rec),
                fed_tax=r10(fed), ca_tax=r10(ca), total_tax=r10(fed + ca),
                net_after_tax=r10(net - fed - ca),
                effective_rate=round(100 * (fed + ca) / gain, 1) if gain else 0.0,
                hold_years=hold_years)


def sale_examples():
    """Worked examples: sell in year 0 vs year 10 vs never-sell, at the mid growth path."""
    T = ECON["transfer_year"]
    A = PROPERTY_A
    home = ECON["home_value_growth"]["mid"]
    v0 = float(A["value_2026"]) * (1 + home) ** (T - 2026)
    basis = v0                                   # s.1014 step-up = FMV at death (assumed)
    ex = []
    for off, primary, label in [(0, True, "Sell in the year of the death"),
                                (3, True, "Live 3 years (Prop 19 claimed), then sell"),
                                (10, False, "Rent 10 years, then sell"),
                                (12, True, "Live 12 years, then sell"),
                                (30, False, "Rent 30 years, then sell")]:
        price = v0 * (1 + home) ** off
        depr_years = 0 if primary else off
        basis_A_val = price
        dep = (basis_A_val * 0.75 / RULES["depr_life_resid"]) * depr_years if depr_years else 0.0
        # depreciation is on the stepped-up basis for the rented years
        dep = ((v0 * (1 + home) ** 0) * 0.75 / RULES["depr_life_resid"]) * depr_years if depr_years else 0.0
        cap = 0.006 * v0 * 0.35 * off
        ex.append(dict(label=label, **gain_table("A", T + off, price, v0, depr=dep,
                                                 primary=primary, capital_add=cap, hold_years=off)))
    return ex


def transfer_costs():
    """Price the transaction itself in both markets, per the household's request."""
    A, B = PROPERTY_A, PROPERTY_B
    a = float(A["value_2026"])
    b = float(B["value_2026"])
    dtt_a = a / 500.0 * RULES["sc_dtt_per_500"]
    tiers = RULES["sf_dtt_tiers"]
    rate_b = tiers[-1][1]
    for ceil_, r in tiers:
        if b <= ceil_:
            rate_b = r
            break
    dtt_b = b / 500.0 * rate_b
    return dict(
        A=dict(price=r10(a), dtt=r10(dtt_a), dtt_note="county only (0.11%); no city "
             "add-on identified - see F-11 note in the register",
             recording=r10(92), recording_note="$102 first page less the $10 fraud-fee offset when DTT "
             "applies, + $3 per additional page (4 pages assumed)",
             commission=r10(a * TRANSACT["A"]["commission_pct"]),
             concessions=r10(a * TRANSACT["A"]["seller_concessions_pct"]),
             prep=r10(a * TRANSACT["A"]["prep_pct"]),
             total=r10(a * (TRANSACT["A"]["commission_pct"] + TRANSACT["A"]["seller_concessions_pct"]
                           + TRANSACT["A"]["dtt_pct"] + TRANSACT["A"]["prep_pct"]) + 90),
             pct_of_price=round(100 * (TRANSACT["A"]["commission_pct"] + TRANSACT["A"]["seller_concessions_pct"]
                                       + TRANSACT["A"]["dtt_pct"] + TRANSACT["A"]["prep_pct"]), 1),
             src="SCC-RECORDER-FEES"),
        B=dict(price=r10(b), dtt=r10(dtt_b), dtt_note=f"SF tier ${rate_b:.2f} per $500 applied to the "
             "whole consideration (a cliff, not a marginal rate)",
             recording=r10(0), recording_note="documents subject to SF transfer tax are exempt from the "
             "recording fee",
             commission=r10(b * TRANSACT["B"]["commission_pct"]),
             concessions=r10(b * TRANSACT["B"]["seller_concessions_pct"]),
             prep=r10(b * TRANSACT["B"]["prep_pct"]),
             total=r10(b * (TRANSACT["B"]["commission_pct"] + TRANSACT["B"]["seller_concessions_pct"]
                            + TRANSACT["B"]["dtt_pct"] + TRANSACT["B"]["prep_pct"])),
             pct_of_price=round(100 * (TRANSACT["B"]["commission_pct"] + TRANSACT["B"]["seller_concessions_pct"]
                                       + TRANSACT["B"]["dtt_pct"] + TRANSACT["B"]["prep_pct"]), 1),
             src="SF-TRANSFER-TAX"))


def capital_plan():
    """5-year maintenance / capital plan for both buildings, from the owner's stated ranges.
    Costs are ranges because a single number would be invented."""
    A, B = PROPERTY_A, PROPERTY_B
    def pct(v, lo, hi):
        return (r10(v * lo), r10(v * hi))
    rows = [
        dict(building="A", item="Roof (asphalt shingle, 20-25 year life)",
             trigger="age, not calendar", cost=(r10(18_000), r10(45_000)),
             why="The single most common surprise on an inherited house. Inspect before deciding anything.",
             src=None, status="inspection required"),
        dict(building="A", item="Sewer line scope + camera", trigger="once, before any sale",
             cost=(r10(600), r10(2_500)), why="Clay lateral failure on a 1960s single-family house is a "
             "$20k+ event and a sale blocker.", src=None, status="action required"),
        dict(building="A", item="Solar: inverter / battery, panel warranty status",
             trigger="inverter ~12-15 yr", cost=(r10(2_000), r10(8_000)),
             why="The zero electric bill depends on this system and its tariff vintage (Q-18).",
             src=None, status="owner to confirm"),
        dict(building="A", item="Routine upkeep (paint, gutters, landscape, appliances)",
             trigger="annual", cost=pct(float(A["value_2026"]), A["maintenance_pct_of_value"][0],
                                        A["maintenance_pct_of_value"][1]),
             why="Owner's stated range: 0.4%-0.8% of value per year, lighter than Property B.",
             src="owner", status="owner-supplied"),
        dict(building="A", item="Earthquake / water backup insurance uplift", trigger="at renewal",
             cost=(r10(1_200), r10(4_000)), why="The $1,500 owner figure is one line, not a quote (F-3).",
             src=None, status="unverified"),
        dict(building="B", item="Unit 3 habitability / permit status", trigger="before any OMI or sale",
             cost=(None, None), why="If the third livable unit is unpermitted, the rent attributable to it "
             "is not financeable and the insurer may not cover it. Cost cannot be stated until the permit "
             "record is pulled.", src=None, status="record search required"),
        dict(building="B", item="Routine upkeep (3 units, common areas, stairwells)", trigger="annual",
             cost=pct(float(B["value_2026"]), B["maintenance_pct_of_value"][0], B["maintenance_pct_of_value"][1]),
             why="Owner's stated range: 1.2%-2.0% of value per year.", src="owner", status="owner-supplied"),
        dict(building="B", item="Rent Board / AB 1482 compliance and OMI paperwork", trigger="before a "
             "possession attempt", cost=(r10(2_000), r10(9_000)), why="Petitions, notices, and a "
             "relocation payment if a protected tenant is involved (L-17).", src="SF-RELO",
             status="legal advice required"),
        dict(building="B", item="Water heater, boiler, roof (multi-unit ages differ per unit)",
             trigger="inspection", cost=(r10(6_000), r10(30_000)), why="Tenanted units defer maintenance; "
             "that deferral lands on the owner all at once.", src=None, status="inspection required"),
    ]
    return rows


PROCESS = [
    dict(step=1, title="Before the death - the trust route",
         body="Nothing in this list requires probate if the house is titled in the trust. Confirm with "
              "the estate attorney that Property A is in the trust NOW, that the trust is revocable and "
              "the settlor is the occupant, and who the successor trustees are. If the house is not in "
              "the trust, the timeline below is optimistic by 12-18 months.",
         src=None),
    dict(step=2, title="At the death - documents to obtain",
         body="Certified death certificates (several), the trust instrument and any amendments, the "
              "trailer/assignment of personal property, the property's most recent tax bill and "
              "assessment record, the mortgage statement (if any), the insurance policy, and the utility "
              "accounts. Everything else follows from these.", src="IRS-559"),
    dict(step=3, title="Valuation - the single most load-bearing document",
         body="Commission a written, dated appraisal of Property A at the date of death (and of the "
              "contents if material). It sets income-tax basis, the Form 706 number if one is filed, and "
              "the Prop 19 excess calculation. Get it from a licensed appraiser, not an estate agent's "
              "market analysis, and keep the unrounded copy offline.", src="BOE-P19"),
    dict(step=4, title="Estate tax decision",
         body="Add the gross estate plus post-1976 taxable gifts. If it exceeds the threshold for the "
              "year of death ($15,000,000 for 2026), Form 706 is due nine months after death, on "
              "extension via Form 4768. Even when no tax is due, file 706 if portability of a prior "
              "spouse's unused exclusion is wanted.", src="IRS-ESTATE"),
    dict(step=5, title="Distribution and the change in ownership",
         body="The trustee's distribution to the beneficiary is the property-tax event. File the change "
              "in ownership statement (BOE-502-D) within 150 days. Expect supplemental bills afterwards - "
              "they are for the part-year, not a mistake.", src="SCC-RATEBOOK"),
    dict(step=6, title="Property tax: two claims, two deadlines",
         body="If the heir will live there: (a) file for the homeowners' exemption within ONE year, and "
              "(b) file the BOE-19-P parent-child claim within THREE years (or before any transfer to a "
              "third party). Miss (a) and (b) is void. If the heir will rent it, do not file them - the "
              "exclusion is unavailable and the value reassesses in full.", src="BOE-P19"),
    dict(step=7, title="Insurance and utilities from the date of distribution",
         body="Notify the insurer (vacancy changes the policy), re-title the utility accounts, and if "
              "the solar system is leased/PPA find out whether the contract is assignable before listing.",
         src=None),
    dict(step=8, title="Choose a path against the written criteria",
         body="Not against the projection. The criteria on /framework.html were agreed before the numbers; "
              "score each path against them, then look at the money. Record the choice and the date in the "
              "decision log.", src=None),
    dict(step=9, title="If selling: price, then stage, then invest per the IPS",
         body="Decide the 1031 question in writing BEFORE listing. Then follow the investment policy - "
              "the Treasury parking lane and the phase-in calendar - which was agreed while there was "
              "nothing to argue about.", src="IRS-544"),
    dict(step=10, title="After: re-run once a year",
         body="/recheck.html and /watch.html. The transfer may be 15+ years away; the rules in this "
              "workspace will not all still be true in 2045, and some will have changed by 2028.", src=None),
]


def exec_summary(paths, scores):
    """The first-screen content, generated from the run so it can never drift from the model."""
    ranked = sorted(scores.items(), key=lambda kv: -kv[1]["score"])
    top = ranked[0][0]
    return dict(ranked=[dict(id=k, **v, name=paths[k]["name"],
                             final_real=paths[k]["final_real"],
                             final_real_use=paths[k]["final_real_use"],
                             p10=paths[k]["p10"], p90=paths[k]["p90"]) for k, v in ranked],
                top=top)
