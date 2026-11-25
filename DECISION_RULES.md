# Decision rules and draft investing policy

**Written:** 2026-11-25, before any model output was generated.
**Scope:** Property A (inherited, Santa Clara County) and Property B (already owned, San Francisco).
**Change control:** Any change to these rules after model output exists must be dated, justified, and logged in `COORDINATION.md`. The model may not change the rules; it only tests them.

## 1. Paths compared (same transfer dates and horizons)

| Code | Path | What it means |
|---|---|---|
| A | Live in Property A | Heir occupies A as principal residence within 1 year and claims the Prop 19 parent-child exclusion. |
| B | Rent Property A | A is let. No occupancy, so no Prop 19 exclusion; full reassessment. |
| C | Sell A, invest lump sum | Sell at transfer; invest net proceeds at once. |
| D | Sell A, phase proceeds | Sell at transfer; park proceeds in 3M–2Y Treasuries for 24–36 months, then phase into equities. |
| E | Mixed: occupy part, rent part | Occupied share gets the exclusion; rented share is reassessed. |
| F | Live N years, then sell | Occupy for N years (base 3), then sell. |

**Cases:** transfer years 2040 and 2050; horizons 10 and 20 years after transfer.

## 2. Choice criteria (fixed before results)

1. **Primary metric:** median real (CPI-deflated) net position at the horizon, across the scenario set and the Monte Carlo draws.
2. **Downside guard:** a path must keep its 10th-percentile real outcome within 10% of Path C's 10th percentile. Otherwise Path C is chosen.
3. **Live (A or F) is eligible only if** the household commits in writing to occupy A as its principal residence within 12 months. If that commitment is absent, A and F are removed from the choice set.
4. **Rent (B) is eligible only if** at least three verified rental comparables for A exist. Until then, B is reported as a **floor**, not a choice.
5. **Phased (D) beats lump sum (C) only if** D's worse black-swan outcome (1929-type or 2008-type) is at least C's worse black-swan outcome, and D's base median is within 5% of C's.
6. **Mixed (E) is chosen only if** it beats the best pure path on the primary metric and on the downside guard.
7. **Estate tax:** no federal estate-tax liability is assumed unless the total taxable estate is verified above the federal basic exclusion amount in the year of death. Other estate assets are unknown, so every result is conditional on that.
8. **Ties:** if two paths are within 2% on the primary metric, prefer the path with higher liquidity at transfer, then the lower regulatory-change exposure.

## 3. What would make the household choose each path

- **Choose A (Live):** written occupancy commitment; the economic value of living (including imputed rent) is at least the sale path's median; the 1-year Prop 19 filing timeline is achievable.
- **Choose B (Rent):** verified comparables show a gross rent yield at or above the model break-even; a landlord policy is quoted; the household accepts reassessment at full value.
- **Choose C (Sell, lump sum):** the sale path leads on the primary metric and the downside guard is met without phasing.
- **Choose D (Sell, phased):** the phased path passes Rule 5, and the household accepts 24–36 months of Treasury-level returns while it waits.
- **Choose E or F (Mixed):** Rule 6 is met, or the household prefers a stated occupancy schedule.

## 4. Pre-committed triggers that re-open the decision

- Any change to the Prop 19 indexed amount (next adjustment due 2027-02-16 per BOE LTA 2025/009).
- Any change to the federal basic exclusion amount or to step-up in basis.
- A verified change in Property A's assessed value or tax-rate-area rate.
- A verified market rent for Property A.
- A change in the household's occupancy plan.

## 5. Draft investing policy for sale proceeds (for attorney and CPA review)

*Draft. Not investment advice. No amounts are decided here.*

1. **Purpose:** hold sale proceeds for the household's stated goals; protect against forced sales in a downturn.
2. **Liquidity reserve:** hold an amount equal to [placeholder: months of household spending] in cash or Treasury bills. The amount is to be set by the household.
3. **Staging:** where phasing is chosen, move proceeds into equities in equal monthly tranches over 24 to 36 months (placeholder: period to be chosen before funds arrive).
4. **Diversification and rebalancing:** broad diversified index exposure; rebalance once per year to target weights set in advance.
5. **Drawdown rule:** do not sell equities to fund emergencies while the reserve is intact.
6. **Review:** annual review, aligned with the annual model re-run.
7. **Tax coordination:** the CPA confirms the holding structure and any trust or entity wrapper before funds are invested.
