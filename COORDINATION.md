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
| 1 | Privacy scrub / anonymization + $10 rounding of all figures | done (`9ca44509`) | `9ca44509` | `model/round.py`, `docs/data/*` |
| 2 | Build private estate inventory structure (placeholders only) | done (`9ca44509`) | `9ca44509` | `docs/estate-inventory.html`, `model/data/inventory.json` |
| 3 | Verify Prop 19 eligibility mechanics + allowance carry-forward | done (`9ca44509`) | `9ca44509` | `docs/prop19.html`, `docs/data/prop19.json` |
| 4 | Property-tax rate-area lookup (Santa Clara County, San Francisco) | done (`9ca44509`) | `9ca44509` | `docs/data/taxrates.json` |
| 5 | Prop 13 / 2% factor + assessed-value projection model | done (`9ca44509`) | `9ca44509` | `model/assessed.py` |
| 6 | Independent property & rental estimate protocol (comparables) | done (`9ca44509`) | `9ca44509` | `docs/comparables.html` |
| 7 | Depreciation & §1250 recapture model for Property B | done (`9ca44509`) | `9ca44509` | `model/depreciation.py` |
| 8 | Lease/local-rule verification (SF Rent Ordinance, Mom & Pop, AB 1482/SB 567) | done (`9ca44509`) | `9ca44509` | `docs/local-rules.html` |
| 9 | Documented investing policy statement (IPS) incl. phased-investing lane | done (`9ca44509`) | `9ca44509` | `docs/ips.html` |
| 10 | Black-swan / regime-switching scenario suite (1929, 2000, 2008, 2020, 1973) | done (`9ca44509`) | `9ca44509` | `model/blackswan.py`, `docs/black-swan.html` |
| 11 | Phased investing: park proceeds in 3M–2Y Treasuries 24–36 months | done (`9ca44509`) | `9ca44509` | `model/phased.py` |
| 12 | Tax-aware sensitivities on ranges (not round points) | done (`9ca44509`) | `9ca44509` | `model/sensitivity.py` |
| 13 | Federal/CA estate, income, gift, transfer-tax rules + deadlines timeline | done (`9ca44509`) | `9ca44509` | `docs/tax-rules.html`, `docs/timeline.html` |
| 14 | Mixed-path engine (live / rent / sell / 8 mixed paths, same dates & horizons) | done (`9ca44509`) | `9ca44509` | `model/paths.py`, `docs/paths.html` |
| 15 | Utility / insurance / maintenance cost tables (both buildings) | done (`9ca44509`) | `9ca44509` | `docs/costs.html`, `docs/data/costs.json` |
| 16 | Five-year maintenance & capital plan, both buildings | done (`9ca44509`) | `9ca44509` | `docs/capex.html` |
| 17 | Imputed-rent input for living paths | done (`9ca44509`) | `9ca44509` | `model/imputed.py` |
| 18 | §121 primary-residence exclusion for live-then-sell paths | done (`9ca44509`) | `9ca44509` | `model/gain.py` |
| 19 | Open questions / missing-information register + discovery suggestions | done (`9ca44509`) | `9ca44509` | `docs/questions.html`, `docs/data/questions.json` |
| 20 | Suggestions review board (choose before implementing) | done (`9ca44509`) | `9ca44509` | `docs/suggestions.html` |
| 21 | Executive summary + "what would change the answer" on first screen | done (`9ca44509`) | `9ca44509` | `docs/index.html` |
| 22 | One-page printable Attorney & CPA Briefing Sheet | done (`9ca44509`) | `9ca44509` | `docs/briefing.html` |
| 23 | Glossary + grouped navigation | done (`9ca44509`) | `9ca44509` | `docs/glossary.html`, `docs/assets/nav.js` |
| 24 | What-if controls (client-side recompute) | done (`9ca44509`) | `9ca44509` | `docs/whatif.html`, `docs/assets/whatif.js` |
| 25 | Legislation & ballot-measure watch (enacted vs proposed) | done (`9ca44509`) | `9ca44509` | `docs/watch.html` |
| 26 | Annual recheck protocol for extreme scenarios | done (`9ca44509`) | `9ca44509` | `docs/recheck.html` |
| 27 | Written pre-commitment: decision criteria fixed before figures | done (`9ca44509`) | `9ca44509` | `docs/framework.html` |
| 28 | Decision log (decision + date next to item) | done (`9ca44509`) | `9ca44509` | `docs/decision-log.html` |
| 29 | Distribution chart on projections | done (`9ca44509`) | `9ca44509` | `docs/projections.html`, `docs/assets/charts.js` |
| 30 | Flagged-for-review page (unverified items + source links) | done (`9ca44509`) | `9ca44509` | `docs/flagged.html` |
| 31 | Sources register (official links, accessed dates) | done (`9ca44509`) | `9ca44509` | `docs/sources.html`, `docs/data/sources.json` |
| 32 | Site build + GitHub Pages publish + PR to main | done (`9ca44509`) | `9ca44509` | `docs/*`, `.github/workflows/pages.yml` |

## Change requests on files owned by other sessions

_None yet._

## Conflict log

_None yet._

## Verification log (append-only)

Started below; each entry records what was checked, against which official source, and any irregularity.

## Ship log — where each task actually landed

The build consolidated the planned file layout: the site is generated at the repository root
(not `docs/`), and the model is five modules rather than one per task. Every numbered task above
is implemented; this is the mapping.

| # | Task | Landed in |
| --- | --- | --- |
| 1 | Privacy scrub, $10 rounding | `model/build.py` (`r10` + `scrub_str`, asserted), `model/site_lib.py` |
| 2 | Estate inventory | `model/inputs.py` (`PROPERTY_A`, `PROPERTY_B`), rendered on `model.html`, `costs.html` |
| 3 | Prop 19 mechanics + allowance carry-forward | `model/projections.py` (`prop19_scenarios`, one-time base at distribution), `tax-rules.html` |
| 4 | Tax rate-area lookup | `model/inputs.py` (`SCC-RATEBOOK`, `SF-TTC-RATE`), `flagged.html` F-1, `open-questions.html` Q-04 |
| 5 | Prop 13 2% factor + assessed projection | `model/projections.py` (`assessed_path`), `projections.html` |
| 6 | Comparables protocol | `model/site_pages2.py` (`comparables`), `data` contract, `comparables.html` |
| 7 | Depreciation & §1250 recapture | `model/engine.py` (`B_DEPR_BASIS`, `§1250` at 28.8%), `tax-rules.html` |
| 8 | Lease / local-rule verification | `model/registers.py` (`LAWS`: Rent Ordinance, Mom & Pop not modelled, AB 1482/SB 567, Prop U), `watch.html` |
| 9 | Investing policy statement | `model/inputs.py` (`PHASING`, `ECON`), `phased.html`, `framework.html` |
| 10 | Black-swan scenario suite | `model/history.py`, `model/projections.py` (`regime`, `rolling`), `black-swan.html` |
| 11 | Phased investing in Treasuries | `model/projections.py` (`phased_backtest`), `phased.html` |
| 12 | Tax-aware sensitivities on ranges | `model/engine.py` (`sensitivity_grid`, 162 cells), `what-if.html` |
| 13 | Estate/income/gift/transfer tax + deadlines | `model/inputs.py`, `model/engine.py` (`transfer_tax`, gain), `tax-rules.html`, `process.html` |
| 14 | Mixed-path engine | `model/engine.py` (`path_specs`, 12 paths, horizons 10/20/30), `paths.html` |
| 15 | Utility / insurance / maintenance tables | `model/inputs.py`, `model/projections.py` (`carry_costs`), `costs.html`, `projections.html` |
| 16 | Five-year capital plan | `costs.html` (capex section), `model/inputs.py` |
| 17 | Imputed rent for living paths | `model/engine.py` (`use_pv`, reported in its own column, never folded in silently) |
| 18 | §121 exclusion for live-then-sell | `model/engine.py` (2-of-5-years test), `tax-rules.html` |
| 19 | Open questions + discovery suggestions | `model/registers.py` (`QUESTIONS`, `SUGGESTIONS`), `open-questions.html` |
| 20 | Suggestions review board | `suggestions.html` (accept/reject persisted to `localStorage`) |
| 21 | Executive summary + "what would change the answer" | `model/site_pages.py` (`index`), first screen of `index.html` |
| 22 | One-page briefing sheet | `model/site_pages2.py` (`briefing`), `briefing.html` |
| 23 | Glossary + grouped navigation | `model/registers.py` (`GLOSSARY`), `site_lib.py` (`PAGES`, static nav), `glossary.html` |
| 24 | What-if controls | `assets/pages.js` (`wireWhatIf` over the published grid), `what-if.html` |
| 25 | Legislation & ballot watch | `model/registers.py` (`LAWS`), `watch.html` |
| 26 | Annual recheck protocol | `model/registers.py` (`RECHECK`), `recheck.html` |
| 27 | Pre-committed decision criteria | `model/registers.py` (`CRITERIA`), `framework.html` |
| 28 | Decision log | `model/registers.py` (`DECISION_LOG`), rendered on `recheck.html` |
| 29 | Distribution chart on projections | `assets/pages.js` (`hist`, `whisker`, `lines`, `rolling`), `projections.html`, `paths.html`, `index.html` |
| 30 | Flagged-for-review page | `model/registers.py` (`FLAGS`), `flagged.html` |
| 31 | Sources register | `model/inputs.py` (`SOURCES`), `sources.html` |
| 32 | Site build + Pages + PR | `model/site.py`, `model/site_lib.py`, `model/site_pages*.py`, root `*.html`, this PR |

## Verification log (appended)

| Checked | Against | Result |
| --- | --- | --- |
| Prop 19 rule set: who qualifies, $1M indexed allowance, factored base value, one-time cap at distribution, 26-month filing window | `boe.ca.gov/prop19` and BOE Letter to Assessors 2025/015 | modelled as read; the 2025/015 figures ($1,044,586 allowance, $468,412 after a prior $576,174 claim) are quoted from that document. Correction made during the build: the cap must not be re-applied every year. |
| Santa Clara County 1.00000% maximum levy and rate-area structure | county Controller-Treasurer rate book page | published rate retained; the household's bills imply ~1.33%, which is *not* reconcilable from the public rate book, so it is a flagged item (F-1) and the top open question (Q-04), not a modelled number. |
| San Francisco secured tax rate, transfer-tax tiers, Prop U parcel tax, Form 579 relocation table, Admin Code 1108 exemptions | `sftreasurer.org`, `sfasr.org`, `sf.gov`, `sfelections.org` certification | transfer tax confirmed as a **cliff**, not a marginal schedule (F-11); Prop U read from the official certification (approved 2026-11-03, 74.4%); the Form 579 table found covers notices served 2024-03-01 to 2025-02-28, so a later edition must exist and does not (F-9). |
| Step-up at death, sale-in-year-of-death gain, §121 2-of-5 test, §1250 recapture, rental-loss suspension, the CA 1% surtax threshold | `irs.gov` (559, 946, 409, 523), FTB Form 540 instructions | modelled as read; the $1,000,000 surtax threshold was not indexed in the booklet read here, which is disclosed on `tax-rules.html` rather than corrected by assumption. |
| Every published dollar figure | mechanical scan of all 20 `*.html`, `assets/data.js` and `data/*.json` | 0 amounts of $1,000+ that are not multiples of $10; sub-$100 rate cards (per-CCF water, per-$500 transfer tiers, recorder fees) are exact on purpose and labelled as rates. |
| Address / APN / account / phone / email leakage | pattern scan of the same set | no address, no parcel number, no email, no account number. Two hits reviewed and kept deliberately: the county office's published business number, and official election vote counts. The words "street", "avenue", "lane" and "apt" appear only inside ordinary words. |
| Link integrity | every internal `href` in every page | 0 broken internal links; all 20 pages present; all four `assets/` files referenced and on disk. |
| Template artifacts | scan for `{`, `None<`, escaped markup in output | clean. |
| Data contract | `assets/data.js` evaluated in a DOM stub | 162/162 sensitivity cells reachable from the what-if controls; 12 paths x 31 yearly rows with no `NaN`/`Infinity`; every grid cell carries `w`/`u`/`n`; `rows12` has 12 entries with a 21-point distribution each. |
| Rebuild determinism | `python3 model/build.py` then `python3 model/site.py` | exit 0, 20 pages, `assets/data.js` 229.9 KB, byte-stable across runs (seeded). |

## Handoff notes for the next session

1. **Do not "fix" the rate mismatch by picking a number.** Q-04 (the parcel's real rate area) is the
   single most valuable missing figure; until the household's own bill is read, `SCC-RATEBOOK`'s
   published 1.00000% is what the model uses and the ~1.33% implication is a flag, not an input.
2. **Do not re-cap Prop 19 annually.** `prop19_scenarios` snapshots the transfer-year values before
   the growth loop; a previous version applied the cap every year and inflated the saving.
3. **Rounding is enforced in two places.** `r10()` on numeric columns *and* `scrub_str()` on every
   string in the payload. If you add prose containing an amount, it is scrubbed at write time - so
   grep the built HTML after any change, do not eyeball the source.
4. **The source column is automatic.** `simple_table()` adds it when a builder does not declare its
   own `("...", "src")` header; `SRC(...)` sets page defaults. A table cannot be published unsourced,
   so there is no need to re-litigate per-page source footnotes.
5. **Rent paths are provisional.** Two of twelve paths rank on an owner-supplied rent, not on closed
   comparables. The comparables page is an intake sheet, deliberately blank; nothing on the site
   substitutes a portal estimate for a lease.
6. **No mortgage, no Mom & Pop exemption, no voucher-anchored rent** - each is a documented choice
   (Q-16, `tax-rules.html`, `comparables.html`), not an oversight.
7. **Rebuild, then re-verify.** The check scripts in the verification log above are cheap; run them
   after touching any builder, because the prose and the numbers are generated together.
