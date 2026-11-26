"""
model/runner.py — turns the engine into the tables the site publishes.

Produces:
  * the low / base / high band per path, at the same transfer year and horizon
  * the full path x crash grid (this is the "black swan" section)
  * the phased-vs-immediate comparison, with reinvestment risk alongside
  * the sensitivity grid (which input moves the answer, and by how much)
  * the year-by-year ledger for the distribution chart
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import params as P
from . import engine as E


# ---------------------------------------------------------------------------
# Bands
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Band:
    low: Dict[str, float]
    base: Dict[str, float]
    high: Dict[str, float]

    def at(self, name: str) -> Dict[str, float]:
        return getattr(self, name)


# The low/base/high sets are built from the inputs that actually move the
# answer. Ordering is deliberate: the LOW case is the one least favourable to
# holding property (high tax, high insurance, high maintenance, low rent), and
# the HIGH case is the one most favourable. This means the band is not a
# confidence interval, it is a pair of adversarial cases. That is more useful.
INPUTS = Band(
    low=dict(
        a_assessed_2026=560_000, a_tax_rate=P.A_TAX_RATE_HIGH,
        a_insurance=P.A_INSURANCE_HIGH, a_maint_pct=P.A_MAINT_HIGH,
        a_rent_yield=P.A_RENT_YIELD_LOW, prop19_allowance=1_044_586,
        sell_commission=0.055, sell_other=0.012,
        ca_status="single", ca_other_income=0.0,
    ),
    base=dict(
        a_assessed_2026=552_500, a_tax_rate=P.A_TAX_RATE_BASE,
        a_insurance=P.A_INSURANCE_BASE, a_maint_pct=P.A_MAINT_BASE,
        a_rent_yield=P.A_RENT_YIELD_BASE, prop19_allowance=1_044_586,
        sell_commission=P.SELL_COMMISSION, sell_other=P.SELL_OTHER_COSTS,
        ca_status=P.CA_DEFAULT_STATUS, ca_other_income=P.CA_OTHER_TAXABLE_INCOME,
    ),
    high=dict(
        a_assessed_2026=545_000, a_tax_rate=P.A_TAX_RATE_LOW,
        a_insurance=P.A_INSURANCE_LOW, a_maint_pct=P.A_MAINT_LOW,
        a_rent_yield=P.A_RENT_YIELD_HIGH, prop19_allowance=1_300_000,
        sell_commission=0.045, sell_other=0.008,
        ca_status=P.CA_DEFAULT_STATUS, ca_other_income=P.CA_OTHER_TAXABLE_INCOME,
    ),
)

# The Prop 19 allowance in 2040-2050 is unpublished. Modelled as an explicit
# scenario band rather than a guess. See facts.json CA-PROP19-ALLOWANCE-FUTURE.
PROP19_FUTURE = {
    "2pct_to_2045": 1_044_586 * (1.02 ** 18),
    "3pct_to_2045": 1_044_586 * (1.03 ** 18),
    "4p5pct_to_2045": 1_044_586 * (1.045 ** 18),
}


def band_for(path_key: str, **kw) -> Dict[str, object]:
    """Run one path across the three input bands and return low/base/high."""
    spec = E.PATHS_BY_KEY[path_key]
    out = {}
    for name in ("low", "base", "high"):
        r = E.simulate(spec, **INPUTS.at(name), **kw)
        out[name] = r
    return out


# ---------------------------------------------------------------------------
# The headline table: all paths, same dates, same horizon
# ---------------------------------------------------------------------------

def headline(transfer_year: int = P.BASE_TRANSFER_YEAR,
             horizon: int = 30,
             scenario: str = "base") -> List[Dict[str, object]]:
    rows = []
    for spec in E.PATHS:
        b = band_for(spec.key, transfer_year=transfer_year,
                     horizon=horizon, scenario=scenario)
        rows.append(dict(
            key=spec.key,
            label=spec.label,
            low=b["low"].terminal_net_worth,
            base=b["base"].terminal_net_worth,
            high=b["high"].terminal_net_worth,
            real_base=b["base"].terminal_real,
            cash_base=b["base"].cumulative_cash,
            asset_base=b["base"].terminal_asset_value,
            tax_on_sale=b["base"].total_tax_on_sale,
            taxes_total=b["base"].total_taxes_paid,
            description=spec.description,
            risk_note=spec.risk_note,
            legal_note=spec.legal_note,
        ))
    rows.sort(key=lambda r: r["base"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Black swan grid
# ---------------------------------------------------------------------------

def crash_grid(transfer_year: int = P.BASE_TRANSFER_YEAR,
               horizon: int = 30,
               scenario: str = "base") -> Dict[str, object]:
    """Every path x every crash overlay, base inputs only, no phasing."""
    out = {"paths": [p.key for p in E.PATHS],
           "crashes": list(P.CRASHES.keys()),
           "labels": {k: v["label"] for k, v in P.CRASHES.items()},
           "cells": {}}
    for ck in P.CRASHES:
        row = {}
        for spec in E.PATHS:
            r = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                           scenario=scenario, crash=ck, **INPUTS.base)
            row[spec.key] = r.terminal_net_worth
        out["cells"][ck] = row
    return out


# ---------------------------------------------------------------------------
# Phased investing: the household's explicit request
# ---------------------------------------------------------------------------

def phased_compare(transfer_year: int = P.BASE_TRANSFER_YEAR,
                   horizon: int = 30,
                   scenario: str = "base",
                   path_key: str = "sell") -> Dict[str, object]:
    """Immediate lump sum vs 24-36 month Treasury parking, across every crash.

    Run on the `sell` path by default, because that is the path that actually
    faces a single-day entry into the market. Phasing a sale that happens four
    years after the transfer protects nothing that matters — the crash lands at
    the transfer, not at the sale.

    The point is NOT that phasing wins. The point is to show, for each crash
    shape, what phasing bought and what it cost:

      * crash inside the parking window -> phasing protects
      * no crash                        -> phasing costs the equity premium
      * stocks and bonds fall together  -> phasing does not protect at all and
                                           the cost is a pure loss (2022 shape)

    A twenty-year profile follows the grid, because two years is a very short
    window against a fifty-year holding period.
    """
    spec = E.PATHS_BY_KEY[path_key]
    out = {"path": path_key, "rows": [], "profile": [], "crashes": list(P.CRASHES.keys())}

    for ck in P.CRASHES:
        imm = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                         scenario=scenario, crash=ck, phased=False, **INPUTS.base)
        ph = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                        scenario=scenario, crash=ck, phased=True, **INPUTS.base)
        delta = ph.terminal_net_worth - imm.terminal_net_worth
        out["rows"].append(dict(
            crash=ck,
            label=P.CRASHES[ck]["label"],
            immediate=imm.terminal_net_worth,
            phased=ph.terminal_net_worth,
            delta=delta,
            pct=(delta / imm.terminal_net_worth) if imm.terminal_net_worth else 0.0,
            verdict=_verdict(delta, abs(imm.terminal_net_worth)),
        ))

    # --- crash TIMING is the whole ballgame -----------------------------
    # If every crash is assumed to arrive one year after the transfer, then any
    # parking window longer than the crash duration "works" by construction.
    # That is a tautology, not a finding. The honest version varies WHEN the
    # crash arrives, because a 24-36 month window only protects a crash that
    # lands inside it. The baseline below is the key number.
    out["timing"] = []
    for arrival in (1, 2, 3, 5, 8, 12):
        row = {"arrival": arrival}
        for ck in ("1929", "2008", "2022"):
            imm = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                             scenario=scenario, crash=ck, phased=False,
                             crash_offset_override=arrival, **INPUTS.base)
            ph = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                            scenario=scenario, crash=ck, phased=True,
                            crash_offset_override=arrival, **INPUTS.base)
            row[ck] = ph.terminal_net_worth - imm.terminal_net_worth
        out["timing"].append(row)

    # How the answer changes with the length of the parking window, holding the
    # crash wave fixed. This is the "reinvestment risk beside the headline".
    saved_min = P.PARK_MIN_YEARS
    for park in (0, 1, 2, 3, 4, 5, 7, 10):
        row = {"park_years": park}
        for ck in ("none", "1929", "2008", "1973", "2022"):
            P.PARK_MIN_YEARS = max(0, park)
            r = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                           scenario=scenario, crash=ck,
                           phased=(park > 0), **INPUTS.base)
            row[ck] = r.terminal_net_worth
        out["profile"].append(row)
    P.PARK_MIN_YEARS = saved_min

    return out


def _verdict(delta: float, scale: float) -> str:
    if scale == 0:
        return "—"
    pct = delta / scale
    if pct > 0.005:
        return "phasing helped"
    if pct < -0.005:
        return "phasing cost money"
    return "a wash"


# ---------------------------------------------------------------------------
# Reinvestment risk: what the parking window must beat
# ---------------------------------------------------------------------------

def reinvestment_risk(park_years: int = 2,
                      equity: float = 0.065,
                      treasury: float = 0.045) -> Dict[str, float]:
    """The annual hurdle the parking window gives up, and the break-even.

    Reinvestment risk here means: while the money sits in Treasuries, it earns
    the Treasury yield instead of the equity total return. If equities do not
    crash during the window, the household has paid the spread for nothing.
    The spread is the insurance premium. Annualised, it is equity - treasury.
    """
    spread = equity - treasury
    premium_paid = (1.0 + equity) ** park_years - (1.0 + treasury) ** park_years
    # A crash of size D inside the window is worth avoiding if
    # (1-D)*(1+treasury)^n > (1+equity)^n  ->  D > 1 - ((1+e)/(1+t))^n
    breakeven_dd = 1.0 - ((1.0 + equity) / (1.0 + treasury)) ** park_years
    return dict(park_years=park_years, equity=equity, treasury=treasury,
                annual_spread=spread, premium_paid=premium_paid,
                breakeven_drawdown=breakeven_dd)


# ---------------------------------------------------------------------------
# Real sensitivities — every number computed by re-running the model
# ---------------------------------------------------------------------------

def sensitivity(transfer_year: int = P.BASE_TRANSFER_YEAR, horizon: int = 30) -> List[Dict]:
    """Re-run the model with one input changed at a time.

    Every figure on the site's sensitivity tables comes from here. Nothing is
    computed by arithmetic shortcut off a headline number, because a shortcut
    is how a projection acquires numbers that the model never produced.
    """
    base = {}
    for spec in E.PATHS:
        base[spec.key] = E.simulate(spec, transfer_year=transfer_year,
                                    horizon=horizon, scenario="base",
                                    **INPUTS.base).terminal_net_worth

    def delta(label, path_key, **kw):
        r = E.simulate(E.PATHS_BY_KEY[path_key], transfer_year=transfer_year,
                       horizon=horizon, scenario="base", **kw).terminal_net_worth
        return r - base[path_key]

    out = []

    # 1. Appraised value ±10%
    for sign, name in ((0.90, "−10%"), (1.10, "+10%")):
        out.append(dict(
            label=f"Appraised value {name}", path="sell",
            delta=_value_shock(sign, "sell", transfer_year, horizon),
            comment="The sale price is also the basis and the portfolio principal",
        ))

    # 2. Prop 19 forfeited at year 8 (the live-then-rent trap)
    out.append(dict(
        label="Occupancy forfeited in year 8", path="live-then-rent",
        delta=base["live-then-rent"] - base["live"],
        comment="Not a shock: this is the actual difference between the two paths",
    ))

    # 3. Macro regime swing
    for sc in ("stagflation", "japan", "household-productivity", "tech-bust"):
        s = E.simulate(E.PATHS_BY_KEY["sell"], transfer_year=transfer_year,
                       horizon=horizon, scenario=sc, **INPUTS.base).terminal_net_worth
        h = E.simulate(E.PATHS_BY_KEY["live"], transfer_year=transfer_year,
                       horizon=horizon, scenario=sc, **INPUTS.base).terminal_net_worth
        out.append(dict(
            label=f"Regime: {P.MACRO[sc]['label']}", path="sell vs live",
            delta=s - h,
            comment="Gap between selling and holding under this regime",
        ))

    return out


def _value_shock(factor: float, path_key: str,
                 transfer_year: int, horizon: int) -> float:
    """Change the 2026 market value and every downstream consequence."""
    spec = E.PATHS_BY_KEY[path_key]
    saved = P.A_VALUE_2026
    try:
        P.A_VALUE_2026 = saved * factor
        import importlib
        from . import engine as _e
        r = _e.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                        scenario="base", **INPUTS.base)
    finally:
        P.A_VALUE_2026 = saved
    base_r = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                        scenario="base", **INPUTS.base)
    return r.terminal_net_worth - base_r.terminal_net_worth


def prop19_value(transfer_year: int = P.BASE_TRANSFER_YEAR, horizon: int = 30) -> Dict:
    """What the Proposition 19 exclusion is actually worth, in the model.

    Computed, not asserted: run the hold path with the exclusion and without it,
    same everything else. This is the number that the one-year occupancy
    deadline is worth.
    """
    spec = E.PATHS_BY_KEY["live"]
    with_ex = E.simulate(spec, transfer_year=transfer_year, horizon=horizon,
                         scenario="base", **INPUTS.base)
    saved = spec.claim_prop19
    try:
        object.__setattr__(spec, "claim_prop19", False) if False else None
        spec2 = E.PathSpec(**{**spec.__dict__, "claim_prop19": False})
        without = E.simulate(spec2, transfer_year=transfer_year, horizon=horizon,
                             scenario="base", **INPUTS.base)
    finally:
        pass

    # Undiscounted property tax over the horizon in each case
    tax_with = sum(r.property_tax for r in with_ex.ledger if r.offset >= 0)
    tax_without = sum(r.property_tax for r in without.ledger if r.offset >= 0)
    return dict(
        net_worth_with=with_ex.terminal_net_worth,
        net_worth_without=without.terminal_net_worth,
        difference=with_ex.terminal_net_worth - without.terminal_net_worth,
        tax_with=tax_with, tax_without=tax_without,
        tax_difference=tax_without - tax_with,
        assessed_with=with_ex.ledger[len([r for r in with_ex.ledger if r.offset < 0])].assessed_value,
        assessed_without=without.ledger[len([r for r in without.ledger if r.offset < 0])].assessed_value,
    )
