# COORDINATION.md — Shared Task Board

Repo: `TinoDash4` · Purpose: privacy-first decision workspace for the **Property A (Cupertino /
Santa Clara County)** inheritance decision, evaluated against the already-owned
**Property B (San Francisco / Outer Sunset)**.

## Rules of the board

1. Claim a task by writing your session ID and file scope here, then commit and push the claim immediately.
2. Never start a task another session has claimed. Work on branch `session-<id>/<task>`.
3. Keep scopes non-overlapping. Shared outputs (`docs/index.html`, `docs/assets/nav.js`,
   `model/data/*.json`) are touched only by the integration session.
4. Need a file owned by someone else? Log a request below instead of editing it.
5. `git pull --rebase` before every push. Small, frequent commits.
6. If a claim is >60 minutes old with no commits, another session may take over and note the handoff.
7. Statuses: `unclaimed` · `in progress` · `needs review` (published on Flagged for Review; non-blocking) · `done`.

## Sessions

| Session ID | Branch | Started | Notes |
| --- | --- | --- | --- |
| `9ca44509` | `arena/9ca44509-tinodash4` | 2026-11-25T13:30Z | Full-scope build; sole active session at start (repo contained only `README.md`, 1 commit, `fe3cad6`). |

## Task board

| # | Task | Status | Owner | Scope (files) |
| --- | --- | --- | --- | --- |
| 1 | Privacy scrub / anonymization + $10 rounding of all figures | in progress | `9ca44509` | `model/round.py`, `docs/data/*` |
| 2 | Build private estate inventory structure (placeholders only) | in progress | `9ca44509` | `docs/estate-inventory.html`, `model/data/inventory.json` |
| 3 | Verify Prop 19 eligibility mechanics + allowance carry-forward | in progress | `9ca44509` | `docs/prop19.html`, `docs/data/prop19.json` |
| 4 | Property-tax rate-area lookup (Santa Clara County, San Francisco) | in progress | `9ca44509` | `docs/data/taxrates.json` |
| 5 | Prop 13 / 2% factor + assessed-value projection model | in progress | `9ca44509` | `model/assessed.py` |
| 6 | Independent property & rental estimate protocol (comparables) | in progress | `9ca44509` | `docs/comparables.html` |
| 7 | Depreciation & §1250 recapture model for Property B | in progress | `9ca44509` | `model/depreciation.py` |
| 8 | Lease/local-rule verification (SF Rent Ordinance, Mom & Pop, AB 1482/SB 567) | in progress | `9ca44509` | `docs/local-rules.html` |
| 9 | Documented investing policy statement (IPS) incl. phased-investing lane | in progress | `9ca44509` | `docs/ips.html` |
| 10 | Black-swan / regime-switching scenario suite (1929, 2000, 2008, 2020, 1973) | in progress | `9ca44509` | `model/blackswan.py`, `docs/black-swan.html` |
| 11 | Phased investing: park proceeds in 3M–2Y Treasuries 24–36 months | in progress | `9ca44509` | `model/phased.py` |
| 12 | Tax-aware sensitivities on ranges (not round points) | in progress | `9ca44509` | `model/sensitivity.py` |
| 13 | Federal/CA estate, income, gift, transfer-tax rules + deadlines timeline | in progress | `9ca44509` | `docs/tax-rules.html`, `docs/timeline.html` |
| 14 | Mixed-path engine (live / rent / sell / 8 mixed paths, same dates & horizons) | in progress | `9ca44509` | `model/paths.py`, `docs/paths.html` |
| 15 | Utility / insurance / maintenance cost tables (both buildings) | in progress | `9ca44509` | `docs/costs.html`, `docs/data/costs.json` |
| 16 | Five-year maintenance & capital plan, both buildings | in progress | `9ca44509` | `docs/capex.html` |
| 17 | Imputed-rent input for living paths | in progress | `9ca44509` | `model/imputed.py` |
| 18 | §121 primary-residence exclusion for live-then-sell paths | in progress | `9ca44509` | `model/gain.py` |
| 19 | Open questions / missing-information register + discovery suggestions | in progress | `9ca44509` | `docs/questions.html`, `docs/data/questions.json` |
| 20 | Suggestions review board (choose before implementing) | in progress | `9ca44509` | `docs/suggestions.html` |
| 21 | Executive summary + "what would change the answer" on first screen | in progress | `9ca44509` | `docs/index.html` |
| 22 | One-page printable Attorney & CPA Briefing Sheet | in progress | `9ca44509` | `docs/briefing.html` |
| 23 | Glossary + grouped navigation | in progress | `9ca44509` | `docs/glossary.html`, `docs/assets/nav.js` |
| 24 | What-if controls (client-side recompute) | in progress | `9ca44509` | `docs/whatif.html`, `docs/assets/whatif.js` |
| 25 | Legislation & ballot-measure watch (enacted vs proposed) | in progress | `9ca44509` | `docs/watch.html` |
| 26 | Annual recheck protocol for extreme scenarios | in progress | `9ca44509` | `docs/recheck.html` |
| 27 | Written pre-commitment: decision criteria fixed before figures | in progress | `9ca44509` | `docs/framework.html` |
| 28 | Decision log (decision + date next to item) | in progress | `9ca44509` | `docs/decision-log.html` |
| 29 | Distribution chart on projections | in progress | `9ca44509` | `docs/projections.html`, `docs/assets/charts.js` |
| 30 | Flagged-for-review page (unverified items + source links) | in progress | `9ca44509` | `docs/flagged.html` |
| 31 | Sources register (official links, accessed dates) | in progress | `9ca44509` | `docs/sources.html`, `docs/data/sources.json` |
| 32 | Site build + GitHub Pages publish + PR to main | in progress | `9ca44509` | `docs/*`, `.github/workflows/pages.yml` |

## Change requests on files owned by other sessions

_None yet._

## Conflict log

_None yet._

## Verification log (append-only)

Started below; each entry records what was checked, against which official source, and any irregularity.
