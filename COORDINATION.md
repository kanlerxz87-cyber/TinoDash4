# Coordination board

Shared task board for every agent session on this repository.

## Session and branch

- Owner session: `150580b0-tinodash4`
- Working branch: `arena/150580b0-tinodash4` (fixed for this session; based on `main` @ `fe3cad6`)
- Pull request target: `main` (see the PR section at the bottom once opened)

## Overlap notice (read first)

- Another session, `1277b9f1-tinodash4`, claimed an overlapping dashboard task on its own branch `arena/1277b9f1-tinodash4` (commit `654ac5d`). Its claimed files are `index.html`, `styles.css`, `app.js`, `README.md`, `COORDINATION.md`, `.nojekyll`.
- This session does not touch that branch. It does not create `session-<id>/<task>` branches, because the Arena branch is fixed for this session.
- To avoid file collisions, this session writes its site under `docs/` and its model under `tools/`. Root-level `index.html`, `styles.css`, and `app.js` are not created here.
- **Pages source change (2026-11-25, this session):** GitHub Pages was set to `main` / `/docs` so this session's site is served. The previous source was `main` / `/`. No root `index.html` existed on `main` when this was done. If the other session merges a root site, it must either move its site under `docs/` or agree a new source here, and log that below.
- Merge overlap is expected. Whichever branch reaches `main` first sets the site root. The other must rebase, and any conflict must be logged here before it is resolved.

## Task board

| # | Task | Status | Owner session | Branch | File scope |
|---|---|---|---|---|---|
| T1 | Repo review and irregularity log | partial: flagged register written (F01–F27); remaining verification listed as open items | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `COORDINATION.md`, `docs/flagged.html`, `docs/sources.html` |
| T2 | Decision rules and investing policy written before model output | done (2026-11-25) | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `DECISION_RULES.md` |
| T3 | Official-source research and source register | partial: 25 sources registered; several fetches failed and are flagged | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/content.js`, `docs/sources.html` |
| T4 | Decision model (paths A–F, Monte Carlo, black swan, phased investing, sensitivity, break-evens) | done as first version; re-run needed when flagged inputs are verified | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/model.js`, `docs/assets/model.js`, `docs/data/model.json` |
| T5 | Static site (landing, results, black swan, phased, estate, timeline, glossary, rules, what-if, flagged, suggestions, printable brief) | done as first version | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/build.js`, `tools/content.js`, `docs/*.html`, `docs/assets/*` |
| T6 | Privacy scan, link check, build check | done (privacy scan passes; external links listed, not fetched) | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/privacy_check.js`, `tools/check_links.js` |
| T7 | Integration: pull request to `main`, merge, GitHub Pages deploy check | in progress | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `README.md`, `COORDINATION.md` |

## Claims log

- 2026-11-25 — `150580b0-tinodash4` claimed T1–T7 on `arena/150580b0-tinodash4`. Scope limited to the files listed above.
- 2026-11-25 — Status correction: the first draft marked T1, T3–T7 "done" before the work was complete. Corrected above. Pages source changed to `/docs` (see overlap notice).

## Interpretations and changes (logged)

- 2026-11-25 — **F24:** DECISION_RULES.md Rule 3 names A and F. Path E (mixed) includes occupancy, so Rule 3 is also applied to E. Applied consistently in the model.
- 2026-11-25 — **F25:** Rule 8's second tie-break ("lower regulatory exposure") is interpreted as: sale paths before occupancy paths, and shorter parking before longer parking. Applied consistently.
- 2026-11-25 — Imputed rent is counted for the occupied share of paths A, E and F, per Rule 3 ("economic value of living, including imputed rent"). Financial-only results are in `docs/data/model.json`.
- 2026-11-25 — The Prop 19 base-year value is not in the workspace and was not invented. The model reassesses Property A at full value as the conservative fallback until it is entered (F08).
- 2026-11-25 — Pooled primary metric = median of six fixed scenarios plus Monte Carlo draws (Rule 1). Sale paths and the phased path are sensitive to the crash probability (F22); this is reported on the what-if page.

## Handoff / conflict log

- 2026-11-25 — Another session's claim (`1277b9f1-tinodash4`, see overlap notice) covers the same dashboard scope. No conflict has occurred yet: separate branches, and nothing has merged to `main` from that branch.

## Verification record (summary)

- Every value on the site carries an official-source link, or is marked **[F##]** (flagged) and listed on `docs/flagged.html`. Unverified values are not presented as verified.
- Dollar figures are rounded to the nearest $10 (user request).
- Full source register: `docs/sources.html`. Irregularities and unverified items: `docs/flagged.html`.
- Personal identifiers (addresses, ZIP codes, names, parcel numbers, contact details, assessed values, Property B rent figures) are excluded. `node tools/privacy_check.js` passes.
- Build: `node tools/build.js` regenerates `docs/`. Links: `node tools/check_links.js`.

## Open items after merge (not blocking)

- Verify all flagged items F01–F27 (see `docs/flagged.html`).
- Enter the Prop 19 base-year value (F08) and re-run the model.
- Obtain three rental comparables (F11) and an insurance quote (F10).
- Re-run yearly and on each trigger in DECISION_RULES.md §4.

## Pull request and merge

- PR and merge record: added below after the merge.
