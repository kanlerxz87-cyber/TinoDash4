# Coordination board

Shared task board for every session working on this repository.
Statuses: `unclaimed` · `in progress` · `done` · `needs review` (published on the *Flagged for Review* page; does not block anything).

## Session constraints (read first)

- **One branch per session.** This session works only on `arena/8c530ff4-tinodash4` (session `8c530ff4`), branched from `main` at `fe3cad6`. Per-task `session-<id>/<task>` branches and a separate integration branch were requested by the household, but the platform only permits work on the current branch, so all tasks are integrated on this single branch. This is the integration session for its own work.
- **Overlapping remote branch observed.** `origin/arena/1277b9f1-tinodash4` (another Arena session, `1277b9f1`) exists with its own `COORDINATION.md` claiming the same overall dashboard task and files (`index.html`, `styles.css`, `app.js`, `README.md`, `COORDINATION.md`, `.nojekyll`). This session did **not** read-modify, push to, or merge that branch. When it is reconciled with `main`, expect conflicts in `index.html`, `README.md`, `COORDINATION.md`, and `.nojekyll`; the owner of that branch must resolve them without discarding either session's work.
- **Privacy.** The household's raw figures live only in `private/` (gitignored, never committed or published). The site uses figures rounded to the nearest $10 and placeholder names (Property A = Property A (Santa Clara County), Property B = San Francisco). `tools/check_site.py` fails the build if any raw figure appears in the published files.
- **No history rewrite.** Git history was not rewritten. See the *Flagged for Review* page (item on commit author e-mail in the base commit).

## Task board

| Task | Status | Owner session | Branch | File scope | Notes |
|---|---|---|---|---|---|
| Repo review + irregularities log | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` | `COORDINATION.md`, `README.md`, `.gitignore`, `data/irregularities.json` | Base repo is a placeholder README; flags logged on Flagged page |
| Official-source research register (tax, legal, market, rent, utilities) | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/content.py` (sources and rows) | Every row has a source link; unverified values left blank and flagged |
| Estate / decision model (paths, taxes, ranges, what-if, black swan, phased test) | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` | `model/model.py`, `data/model_outputs.json` | Deterministic grid + Monte Carlo distribution |
| Site generator, pages, print brief | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/build_site.py`, `assets/*`, generated `*.html`, `brief.pdf` | GitHub Pages serves `main` at `/` |
| Verification, privacy scan, link check | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/check_site.py` | Must pass before PR |
| Pull request, merge, Pages deploy confirmation | unclaimed | `8c530ff4` | `arena/8c530ff4-tinodash4` → `main` | `COORDINATION.md` (log only) | Recorded after merge |

## Handoff log

- 2026-11-25 · `8c530ff4` · Claimed all tasks above on `arena/8c530ff4-tinodash4`. No other session's files were edited.

## Verification record

Filled in as each task completes (sources, checks run, irregularities). See the *Sources* and *Flagged for Review* pages for the live register.
