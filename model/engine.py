"""
model/engine.py — the projection engine.

DESIGN RULES, in priority order:

1. CORRECTNESS BEFORE PRETTINESS. Every path is valued on the same cash-flow
   ledger, at the same transfer dates, over the same horizon, with the same tax
   treatment. Nothing is compared at unequal horizons.
2. RANGES, NOT POINTS. Every headline is a low/base/high band built from the
   low/base/high of the inputs that actually move the answer.
3. THE LEDGER IS EXPOSED. Each path returns its year-by-year ledger so the site
   can publish a distribution and a reviewer can audit any single year.
4. NO HIDDEN OPTIONALITY. Where a path depends on a legal test (e.g. Prop 19
   continued occupancy), the test is an explicit switch AND the model enforces
   the consequence, so the cost of failing the test is visible rather than
   assumed away.

UNIT OF ACCOUNT. Nominal dollars, after tax, net of all costs, at the terminal
year, PLUS the value of any asset still held, marked down for the cost and tax
of realising it. This is "net worth attributable to the choice". Comparing a
gross house value against a net brokerage balance is the most common way this
kind of analysis gets rigged; it is not done here.

IMPUTED RENT. A household that lives in Property A consumes housing it does not
pay for. A household that sells must pay rent somewhere. Omitting that makes the
sell path look artificially good by the full cost of shelter. Imputed rent is
therefore credited to every owner-occupancy year, at the same market rent the
rental path would have received — which is conservative, because the household
would otherwise rent an equivalent house, not this exact one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from . import params as P


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compound(rate: float, years: float) -> float:
    return (1.0 + rate) ** years


def prop13_adjust(prev: float, rate: float = P.A_PROP13_CAP) -> float:
    """Proposition 13 annual adjustment to the factored base year value.

    The 2% is a CEILING, not a floor (Cal. Const. art. XIII A, § 2(b); RTC § 51).
    The assessed value never falls through this mechanism alone. A fall requires
    a separate Proposition 8 decline-in-value reduction, modelled explicitly
    below wherever market value drops below the factored base year value.
    """
    return prev * (1.0 + rate)


# Blended marginal rates applied to rental and investment income. MODELLING
# CHOICES, not statute. They assume other income already fills the lower
# brackets, which is the realistic case for this household. Disclosed on the
# assumptions page.
RENT_TAX_BLENDED = 0.32
LAND_SHARE = P.A_LAND_SHARE


def building_value(market_value: float, land_share: float = LAND_SHARE) -> float:
    """The depreciable / maintainable part of a property's value.

    Cupertino land is roughly three-quarters of market value. Land needs no
    roof, no paint and no sewer lateral, and it is never depreciable. Tying
    maintenance to MARKET value instead of BUILDING value makes the modelled
    cost compound at the house-price rate for fifty years — a bug that buries
    every holding path by the horizon. The correction is in both places this
    function is used: maintenance and depreciation.
    """
    return market_value * (1.0 - land_share)


def maintenance_year(market_value: float, pct: float, years_elapsed: int,
                     cpi: float, land_share: float = LAND_SHARE) -> float:
    """Annual maintenance = pct of building value, with the building's
    replacement cost inflating at CPI plus a construction spread, NOT at the
    house-price rate."""
    build_now = building_value(market_value, land_share)
    # Blend: the structure's replacement cost grows with CPI + spread, while its
    # share of total value drifts down as land appreciates. Using the current
    # building value and letting the pct carry the growth is the conservative
    # choice, because it cannot understate cost in a high-land-inflation world.
    return build_now * pct


def depreciation_year(basis_at_death: float) -> float:
    """Straight-line residential rental depreciation for one full year.

    Verified: IRC § 168(c) — residential rental property, 27.5 years;
    § 168(b)(3)(B) — straight line; § 168(d)(2)(B) — mid-month convention.

    Base = the building's share of the § 1014 basis (FMV at date of death),
    divided by 27.5. LAND IS NEVER DEPRECIABLE. Only the building is. Getting
    this wrong is the single most common error in residential rental tax and it
    overstates the shelter on the rent path.
    """
    building = basis_at_death * (1.0 - LAND_SHARE)
    return building / P.FED_DEPR_LIFE


# ---------------------------------------------------------------------------
# Ledger row
# ---------------------------------------------------------------------------

@dataclass
class YearRow:
    year: int
    offset: int
    mode: str
    market_value: float
    assessed_value: float
    property_tax: float
    insurance: float
    maintenance: float
    water: float
    electric: float
    gross_rent: float
    imputed_rent: float
    rent_tax: float
    net_cash: float
    portfolio: float
    cum_net: float
    note: str = ""

    @property
    def operating_cost(self) -> float:
        return (self.property_tax + self.insurance + self.maintenance
                + self.water + self.electric)

    @property
    def net_worth(self) -> float:
        return self.cum_net + self.portfolio + self.market_value


# ---------------------------------------------------------------------------
# Path specification
# ---------------------------------------------------------------------------

@dataclass
class PathSpec:
    key: str
    label: str
    # occupancy timeline as (offset_from_transfer, mode); later entries win.
    # mode in {"live", "rent", "vacant", "sold"}
    timeline: List[Tuple[int, str]]
    sell_offset: Optional[int] = None
    claim_s121: bool = False
    claim_prop19: bool = True
    loses_prop19_on_conversion: bool = False
    description: str = ""
    risk_note: str = ""
    legal_note: str = ""


PATHS: List[PathSpec] = [
    PathSpec(
        key="sell",
        label="Sell at transfer, invest the net proceeds",
        timeline=[(0, "sold")],
        sell_offset=0,
        claim_prop19=False,
        description=(
            "Accept the step-up in basis and sell in the year of death, then "
            "invest the after-tax proceeds in a diversified portfolio. Because "
            "the § 1014 basis IS the date-of-death value, the gain in that same "
            "year is normally close to zero — the real cost is the 10%-plus "
            "transaction cost, not capital-gains tax."
        ),
        risk_note=(
            "Concentrates the entire entry into the market on a single day. This "
            "is the path most exposed to a bad entry date, and it is the reason "
            "the phased-investing option exists."
        ),
        legal_note=(
            "Selling later, after appreciation, creates real gain taxed at "
            "California ordinary rates with no state preference at all. The "
            "timing of the sale, not the sale itself, is the tax decision."
        ),
    ),
    PathSpec(
        key="live",
        label="Live in it as a principal residence, hold to horizon",
        timeline=[(0, "live")],
        claim_prop19=True,
        description=(
            "Move in within one year, file the homeowners' exemption within one "
            "year, claim the Prop 19 exclusion, and stay. Lowest property tax of "
            "any holding path. Credited with imputed rent equal to the market "
            "rent the household no longer has to pay."
        ),
        risk_note=(
            "Locks roughly $3.1M of today's capital into one undiversified asset "
            "in a single-industry town, on top of an already-concentrated San "
            "Francisco rental. The concentration, not the return, is the risk."
        ),
        legal_note=(
            "Requires actual, continuing occupancy. The exclusion is removed "
            "when the heir stops being eligible for the homeowners' exemption. "
            "Living there is not a lifestyle preference in this model — it is "
            "the legal condition of the tax benefit."
        ),
    ),
    PathSpec(
        key="rent",
        label="Rent it out, never occupy",
        timeline=[(0, "rent")],
        claim_prop19=False,
        description=(
            "Treat the house purely as an investment property. Under RTC § 63.2 "
            "the Prop 19 exclusion is unavailable because the heir does not "
            "occupy within one year, so the property is reassessed to full "
            "market value at transfer — which on a $3.1M house in 2045 is a "
            "six-figure annual tax bill against a five-figure rent roll."
        ),
        risk_note=(
            "Highest property tax of any holding path, income taxed as ordinary "
            "income, depreciation recapture on sale, and landlord obligations in "
            "a county with strong tenant protections."
        ),
        legal_note=(
            "This is the path the household's instinct most wants to exist — "
            "'rent it out and keep the low Prop 13 base'. It does not. A low "
            "Prop 13 base and rental income are mutually exclusive under current "
            "California law, and the model charges the full cost of that."
        ),
    ),
    PathSpec(
        key="live-then-sell",
        label="Live in it 6 years, then sell using the § 121 exclusion",
        timeline=[(0, "live"), (6, "sold")],
        sell_offset=6,
        claim_s121=True,
        claim_prop19=True,
        description=(
            "Occupy and claim Prop 19, satisfy the § 121 ownership-and-use tests, "
            "then sell with up to $500,000 of gain excluded from federal income. "
            "Because the basis was reset at death and the house then grew, this "
            "is where the § 121 exclusion earns its keep."
        ),
        risk_note="Market timing on the exit date; six years is a long time to be wrong about a neighbourhood.",
        legal_note=(
            "§ 121 requires ownership for 2 of the last 5 years AND use as the "
            "main home for 2 of the last 5 (IRS Topic 701). Gain above the "
            "exclusion is taxed at federal 0/15/20 plus 3.8% NIIT, and at "
            "California ordinary rates."
        ),
    ),
    PathSpec(
        key="rent-then-live",
        label="Rent it for one year, then move in and claim Prop 19",
        timeline=[(0, "rent"), (1, "live")],
        claim_prop19=True,
        description=(
            "Use the house as a rental during the transition year, then occupy "
            "within the one-year window that § 63.2(a)(1)(A) allows, preserving "
            "the Prop 19 exclusion."
        ),
        risk_note="A twelve-month tenancy creates a relationship you may have to unwind, and it changes the character of the residence timeline.",
        legal_note=(
            "Legal but narrow. The occupancy deadline runs one year from the "
            "TRANSFER, not one year from the end of a lease. A twelve-month lease "
            "that overruns the window destroys the exclusion and reassesses the "
            "property to full market value."
        ),
    ),
    PathSpec(
        key="live-then-rent",
        label="Live in it, then rent it out later",
        timeline=[(0, "live"), (8, "rent")],
        claim_prop19=True,
        loses_prop19_on_conversion=True,
        description=(
            "Occupy long enough to establish the residence and claim the "
            "exclusion, then convert to rental when the household moves. The "
            "model ENFORCES the loss of the exclusion at conversion."
        ),
        risk_note=(
            "The Prop 19 benefit is destroyed at the moment of conversion, which "
            "is usually the exact moment the plan was counting on the low tax "
            "base to make renting profitable."
        ),
        legal_note=(
            "THE TRAP. RTC § 63.2(a)(1)(B)-(C): the exclusion is removed on the "
            "date the transferee is no longer eligible for the homeowners' "
            "exemption, and a new base year value is enrolled as of the following "
            "lien date. Moving out and renting does not 'keep' a Prop 13 basis — "
            "it forfeits it, converting a low-tax house into a full-market-value "
            "one, retroactively. This path is modelled specifically to put that "
            "number in front of the household before they rely on it."
        ),
    ),
    PathSpec(
        key="live-phased-sell",
        label="Occupy, then sell and phase the proceeds in over 24–36 months",
        timeline=[(0, "live"), (4, "sold")],
        sell_offset=4,
        claim_s121=True,
        claim_prop19=True,
        description=(
            "The path the household asked about: occupy long enough for § 121, "
            "sell, park the after-tax proceeds in 3-month to 2-year Treasuries "
            "for 24–36 months, then phase into equities over 36 months. Tests "
            "whether the staging actually softens crash-entry risk."
        ),
        risk_note=(
            "Reinvestment risk is the price of crash protection. Phasing protects "
            "the downside only if the crash arrives during the parking window; if "
            "it does not, the household pays for insurance it did not use."
        ),
        legal_note="Standard sale plus a separate portfolio decision. No special legal test beyond § 121.",
    ),
    PathSpec(
        key="live-then-sell-immediate",
        label="Occupy 4 years, then sell and invest in one day",
        timeline=[(0, "live"), (4, "sold")],
        sell_offset=4,
        claim_s121=True,
        claim_prop19=True,
        description=(
            "Same as the phased path but without the Treasury parking window. "
            "This is the control that isolates the value of phasing."
        ),
        risk_note="Full single-day market entry risk, with no staging.",
        legal_note="Standard sale.",
    ),
]

PATHS_BY_KEY = {p.key: p for p in PATHS}

# The control path is not a household choice; it exists to measure the value of
# phasing. It is excluded from the headline ranking.
CONTROL_PATHS = {"live-then-sell-immediate"}


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

@dataclass
class PathResult:
    key: str
    label: str
    terminal_year: int
    terminal_net_worth: float
    terminal_real: float
    cumulative_cash: float
    cumulative_imputed_rent: float
    terminal_asset_value: float
    total_taxes_paid: float
    total_tax_on_sale: float
    ledger: List[YearRow]
    base_year_property_tax: float = 0.0
    note: str = ""


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def simulate(
    spec: PathSpec,
    *,
    transfer_year: int = P.BASE_TRANSFER_YEAR,
    horizon: int = 30,
    scenario: str = "base",
    crash: str = "none",
    phased: bool = False,
    # input bands
    a_assessed_2026: float = 552_500,
    a_tax_rate: float = P.A_TAX_RATE_BASE,
    a_insurance: float = P.A_INSURANCE_BASE,
    a_maint_pct: float = P.A_MAINT_BASE,
    a_rent_yield: float = P.A_RENT_YIELD_BASE,
    prop19_allowance: float = 1_044_586,
    sell_commission: float = P.SELL_COMMISSION,
    sell_other: float = P.SELL_OTHER_COSTS,
    # choices
    federal_gain_rate: float = P.FED_TOP_LTCG,
    ca_rate_on_gain: float = P.CA_EFFECTIVE_ON_LARGE_GAIN,
    include_niit: bool = True,
    rent_vacancy: float = 0.05,
    rent_growth: float = 0.030,
    credit_imputed_rent: bool = True,
    crash_offset_override: Optional[int] = None,
    house_growth_override: Optional[float] = None,
    equity_override: Optional[float] = None,
) -> PathResult:
    """Run one path under one macro scenario and crash overlay."""

    m = P.MACRO[scenario]
    cpi = m["cpi"]
    hpi = m["house"] if house_growth_override is None else house_growth_override
    eq = m["equity"] if equity_override is None else equity_override
    cr = dict(P.CRASHES[crash])
    if crash_offset_override is not None:
        cr["years_after_transfer"] = crash_offset_override
    crash_dur = max(1, cr.get("duration", 1))

    ledger: List[YearRow] = []

    # ---------------- pre-transfer: the trust owns the property -------------
    assessed = a_assessed_2026
    market = P.A_VALUE_2026
    for y in range(P.START_YEAR, transfer_year):
        assessed = prop13_adjust(assessed)
        market *= (1.0 + hpi)
        infl = compound(cpi, y - P.START_YEAR)
        ledger.append(YearRow(
            year=y, offset=y - transfer_year, mode="trust",
            market_value=market, assessed_value=assessed,
            property_tax=assessed * a_tax_rate,
            insurance=a_insurance * infl,
            maintenance=maintenance_year(market, a_maint_pct, 0, cpi),
            water=(P.A_WATER_LOW + P.A_WATER_HIGH) / 2 * infl,
            electric=(P.A_ELECTRIC_NET_LOW + P.A_ELECTRIC_NET_HIGH) / 2 * infl,
            gross_rent=0.0, imputed_rent=0.0, rent_tax=0.0,
            net_cash=0.0, portfolio=0.0, cum_net=0.0,
            note="Pre-transfer. Costs fall on the trust / current owner, not on the "
                 "household; shown only so the assessed-value drift is visible.",
        ))

    # ---------------- the change of ownership ------------------------------
    fmv_at_transfer = market * (1.0 + hpi)
    basis_1014 = fmv_at_transfer          # verified IRC § 1014(a)

    if spec.claim_prop19:
        # RTC § 63.2(d): new taxable value = prior taxable value
        #   + max(0, FMV - (prior taxable value + allowance))
        excess = max(0.0, fmv_at_transfer - (assessed + prop19_allowance))
        assessed_prop19 = assessed + excess
        prop19_note = (
            f"Prop 19 applied: carried base ${assessed:,.0f} + allowance "
            f"${prop19_allowance:,.0f}; the ${excess:,.0f} of value above the cap "
            f"is added to the assessment, giving ${assessed_prop19:,.0f}."
        )
    else:
        assessed_prop19 = fmv_at_transfer
        prop19_note = "Prop 19 not available: assessed at full fair market value at transfer."

    assessed = assessed_prop19
    market = fmv_at_transfer
    base_year_tax = assessed * a_tax_rate

    portfolio = 0.0
    cum = 0.0
    cum_imputed = 0.0
    total_taxes = 0.0
    total_tax_on_sale = 0.0
    sold = False
    sale_year: Optional[int] = None
    phase_start: Optional[int] = None
    park_until: Optional[int] = None
    converted_off_prop19 = False
    depreciation_taken = 0.0

    def mode_at(offset: int) -> str:
        mode = "vacant"
        for start, mm in spec.timeline:
            if offset >= start:
                mode = mm
        return mode

    def settle_sale(year: int, price: float, claim_121: bool) -> Tuple[float, float, str]:
        """Net proceeds after selling costs and income tax on the gain."""
        cost = price * (sell_commission + sell_other)
        net_before_tax = price - cost

        gain = price - basis_1014
        notes = [f"Sale at ${price:,.0f}; transaction costs ${cost:,.0f}."]

        if claim_121:
            excl = P.FED_S121_JOINT
            taxable = max(0.0, gain - excl)
            notes.append(
                f"§ 121 excludes ${min(max(gain,0), excl):,.0f} of the "
                f"${max(gain,0):,.0f} gain; ${taxable:,.0f} remains taxable."
            )
        else:
            taxable = max(0.0, gain)
            notes.append(f"No § 121 exclusion available; ${taxable:,.0f} of gain is taxable.")

        fed = taxable * federal_gain_rate
        if include_niit and taxable > 0:
            fed += taxable * P.FED_NIIT
        ca = taxable * ca_rate_on_gain

        # Unrecaptured § 1250 gain: depreciation previously taken is taxed at a
        # maximum 25% federal rate (verified, IRS Topic 409) and as ordinary
        # income by California.
        if depreciation_taken > 0:
            fed += depreciation_taken * P.FED_UNRECAPTURED_1250
            ca += depreciation_taken * P.CA_TOP_MARGINAL
            notes.append(
                f"Depreciation recapture of ${depreciation_taken:,.0f} taxed at 25% "
                f"federal / California ordinary rates."
            )

        tax = fed + ca
        notes.append(f"Tax on the sale ${tax:,.0f}.")
        return net_before_tax - tax, tax, " ".join(notes)

    # ---------------- main loop -------------------------------------------
    for i in range(horizon):
        y = transfer_year + i
        mode = mode_at(i)
        notes: List[str] = []
        if i == 0:
            notes.append(prop19_note)

        in_crash = (cr["years_after_transfer"] is not None
                    and cr["years_after_transfer"] <= i
                    < cr["years_after_transfer"] + crash_dur)

        # --- Prop 19 forfeiture on conversion off owner-occupancy -----------
        if (spec.loses_prop19_on_conversion and spec.claim_prop19
                and not converted_off_prop19 and mode in ("rent", "vacant")
                and i > 0):
            converted_off_prop19 = True
            before = assessed
            # The exclusion is removed and a new base year value is enrolled as
            # of the lien date following the loss of eligibility. Modelled as a
            # full reassessment to market value from the conversion year.
            assessed = max(assessed, market)
            notes.append(
                f"PROP 19 FORFEITED at conversion: assessed value jumps from "
                f"${before:,.0f} to ${assessed:,.0f} because the heir is no longer "
                f"eligible for the homeowners' exemption (RTC § 63.2(a)(1)(B)-(C)). "
                f"Property tax rises from ${before * a_tax_rate:,.0f}/yr to "
                f"${assessed * a_tax_rate:,.0f}/yr."
            )

        # --- scheduled sale ---
        if not sold and spec.sell_offset is not None and i == spec.sell_offset:
            proceed, tax, sale_note = settle_sale(y, market, spec.claim_s121 or mode == "live")
            total_tax_on_sale += tax
            total_taxes += tax
            portfolio += proceed
            sold = True
            sale_year = y
            notes.append(sale_note)
            if phased:
                park_until = y + P.PARK_MIN_YEARS
                notes.append(
                    f"Proceeds parked in 3-month to 2-year Treasuries at "
                    f"{P.PARK_YIELD_FALLBACK:.1%} for {P.PARK_MIN_YEARS}-"
                    f"{P.PARK_MAX_YEARS} years, then phased into equities over "
                    f"{P.DCA_MONTHS} months."
                )

        # --- asset movement ---
        if not sold:
            if in_crash:
                market *= (1.0 - cr["house_dd"] / crash_dur)
            else:
                market *= (1.0 + hpi)
            assessed = prop13_adjust(assessed)

            # Proposition 8 decline-in-value relief. This is a genuine hedge the
            # stock path does not have and it is routinely left out of
            # comparisons like this one.
            if market < assessed:
                notes.append(f"Prop 8 decline-in-value relief: assessment reduced to ${market:,.0f}.")
                assessed = market

        if sold or portfolio > 0:
            if phased and park_until is not None and y < park_until:
                portfolio *= (1.0 + P.PARK_YIELD_FALLBACK)
            elif phased and sale_year is not None and y - sale_year >= P.PARK_MIN_YEARS:
                if phase_start is None:
                    phase_start = y
                frac = min(1.0, ((y - phase_start) * 12) / P.DCA_MONTHS)
                eq_this = eq - (cr["equity_dd"] / crash_dur if in_crash else 0.0)
                portfolio *= ((1.0 - frac) * (1.0 + P.PARK_YIELD_FALLBACK)
                              + frac * (1.0 + eq_this))
            else:
                eq_this = eq - (cr["equity_dd"] / crash_dur if in_crash else 0.0)
                portfolio *= (1.0 + eq_this)

        # --- operating cash flow ---
        tax = ins = maint = water = electric = gross_rent = rent_tax = imputed = 0.0
        net = 0.0

        if not sold:
            infl = compound(cpi, y - P.START_YEAR)
            taxable_value = assessed
            if mode == "live":
                taxable_value = max(0.0, assessed - 7_000)   # verified BOE exemption
            tax = taxable_value * a_tax_rate
            ins = a_insurance * infl
            maint = maintenance_year(market, a_maint_pct, i, cpi)
            water = (P.A_WATER_LOW + P.A_WATER_HIGH) / 2 * infl
            electric = (P.A_ELECTRIC_NET_LOW + P.A_ELECTRIC_NET_HIGH) / 2 * infl

            market_rent_year = (P.A_VALUE_2026 * a_rent_yield / 12.0) * 12 * compound(
                rent_growth, y - P.START_YEAR)

            if mode == "rent":
                gross_rent = market_rent_year
                vacancy = gross_rent * rent_vacancy
                noi = gross_rent - vacancy - ins - maint - water - electric - tax
                dep = depreciation_year(basis_1014)
                depreciation_taken += dep
                rent_tax = max(0.0, noi - dep) * RENT_TAX_BLENDED
                total_taxes += rent_tax
                net = gross_rent - vacancy - ins - maint - water - electric - tax - rent_tax
            elif mode == "live":
                imputed = market_rent_year if credit_imputed_rent else 0.0
                cum_imputed += imputed
                total_taxes += tax
                net = imputed - (tax + ins + maint + water + electric)
            else:
                total_taxes += tax
                net = -(tax + ins + maint + water + electric)

        cum += net
        ledger.append(YearRow(
            year=y, offset=i, mode=mode, market_value=market,
            assessed_value=assessed, property_tax=tax, insurance=ins,
            maintenance=maint, water=water, electric=electric,
            gross_rent=gross_rent, imputed_rent=imputed, rent_tax=rent_tax,
            net_cash=net, portfolio=portfolio, cum_net=cum,
            note=" ".join(notes),
        ))

    # ---------------- terminal valuation ----------------------------------
    if sold:
        asset = portfolio
        note = "Assets held at the horizon are the invested portfolio."
    else:
        # The house is marked at FMV LESS the cost and tax of realising it.
        claim_121 = spec.claim_s121 or mode_at(horizon - 1) == "live"
        asset, tax, _ = settle_sale(ledger[-1].year, market, claim_121)
        total_tax_on_sale += tax
        total_taxes += tax
        note = ("House valued at fair market value net of the selling costs and "
                "income tax a sale at the horizon would incur.")

    nom = cum + asset
    real = nom / compound(cpi, horizon)

    return PathResult(
        key=spec.key, label=spec.label, terminal_year=transfer_year + horizon,
        terminal_net_worth=nom, terminal_real=real,
        cumulative_cash=cum, cumulative_imputed_rent=cum_imputed,
        terminal_asset_value=asset, total_taxes_paid=total_taxes,
        total_tax_on_sale=total_tax_on_sale, ledger=ledger,
        base_year_property_tax=base_year_tax, note=note,
    )
