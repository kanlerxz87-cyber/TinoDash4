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
- Merge overlap is expected. Whichever branch reaches `main` first sets the site root. The other must rebase, and any conflict must be logged here before it is resolved.

## Task board

| # | Task | Status | Owner session | Branch | File scope |
|---|---|---|---|---|---|
| T1 | Repo review and irregularity log | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `COORDINATION.md`, `docs/flagged.html`, `docs/sources.html` |
| T2 | Decision rules and investing policy written before model output | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `DECISION_RULES.md` |
| T3 | Official-source research and source register | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/content.js`, `docs/sources.html` |
| T4 | Decision model (paths, mixed paths, black swan, phased investing, Monte Carlo, sensitivity) | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/model.js`, `docs/assets/model.js`, `docs/data/model.json` |
| T5 | Static site (landing, category pages, tables, timeline, glossary, suggestions, flagged page, printable brief) | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/build.js`, `tools/content.js`, `docs/*.html`, `docs/assets/*` |
| T6 | Privacy scan, link check, build check | done | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `tools/privacy_check.js`, `tools/check_links.js` |
| T7 | Integration: pull request to `main`, merge, GitHub Pages deploy check | in progress | `150580b0-tinodash4` | `arena/150580b0-tinodash4` | `README.md`, `COORDINATION.md` |

## Claims log

- 2026-11-25 — `150580b0-tinodash4` claimed T1–T7 on `arena/150580b0-tinodash4`. Scope limited to the files listed above.

## Handoff / conflict log

- 2026-11-25 — Another session's claim (`1277b9f1-tinodash4`, see overlap notice) covers the same dashboard scope. No conflict has occurred yet because the work is on separate branches and nothing has merged to `main`.

## Verification record (summary)

- Every value on the site carries an official-source link, or is marked **unverified** and left out of the verified tables.
- Dollar figures are rounded to the nearest $10 (user request).
- Full source register: `docs/sources.html`. Irregularities and unverified items: `docs/flagged.html`.
- Personal identifiers (addresses, ZIP codes, names, APNs, contact details) are excluded. Properties are shown as "Property A (Santa Clara County)" and "Property B (San Francisco)".
