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
| Repo review + irregularities log | done | `8c530ff4` | `arena/8c530ff4-tinodash4` | `COORDINATION.md`, `README.md`, `.gitignore`, `data/irregularities.json` | Base repo is a placeholder README; flags logged on Flagged page |
| Official-source research register (tax, legal, market, rent, utilities) | done (secondary items labelled) | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/content.py` (sources and rows) | Every row has a source link; unverified values left blank and flagged |
| Estate / decision model (paths, taxes, ranges, what-if, black swan, phased test) | done | `8c530ff4` | `arena/8c530ff4-tinodash4` | `model/model.py`, `data/model_outputs.json` | Deterministic grid + Monte Carlo distribution |
| Site generator, pages, print brief | done (brief.pdf via ReportLab) | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/build_site.py`, `assets/*`, generated `*.html`, `brief.pdf` | GitHub Pages serves `main` at `/` |
| Verification, privacy scan, link check | done (all checks pass) | `8c530ff4` | `arena/8c530ff4-tinodash4` | `tools/check_site.py` | Must pass before PR |
| Pull request, merge, Pages deploy confirmation | in progress | `8c530ff4` | `arena/8c530ff4-tinodash4` → `main` | `COORDINATION.md` (log only) | Recorded after merge |

## Handoff log

- 2026-11-25 · `8c530ff4` · Claimed all tasks above on `arena/8c530ff4-tinodash4`. No other session's files were edited.
- 2026-11-25 · `8c530ff4` · Model v2: fixed a double count in the phase-in and rent paths (earlier first-run numbers withdrawn). Household inputs moved out of `model/model.py` into the gitignored `private/` folder; the published output keeps rounded results only. Commit `91c0097`.
- 2026-11-25 · `8c530ff4` · Content audit: household figures, tax-history rows and unverified legislation details removed or replaced by placeholders and blanks; SF Measure H confirmed as the parcel tax (official results page) and Measure I as the transfer-tax change that failed on the preliminary count. Commit `e100ca2`.
- 2026-11-25 · `8c530ff4` · Site, checks and brief built (`cbdd66b`). Gate: privacy scan (77 patterns, including `brief.pdf`), 1,934 money values rounded to $10, 202 of 202 table rows linked, all internal links resolve. A planted-value test confirmed the scan fails when a household figure appears.
- 2026-11-25 · `8c530ff4` · Found a personal e-mail address in the author field of the base commit on `main` (`fe3cad6`). History was not rewritten; logged on the Flagged for Review page for your decision.

## Verification record

- **Primary sources opened in this session (FETCHED):** IRS IR-2025-103; IRS What's new (estate and gift tax); FTB 2025 Form 540-ES instructions; Federal Register FR Doc 2026-17891 (FY 2027 FMR notice); HUD FMR landing page; U.S. Treasury November 2026 par yields; SF Department of Elections November 3, 2026 preliminary results (Measure H 74.42% yes; Measure I 48.38% yes).
- **Excerpt only (EXCERPT):** CBO Budget and Economic Outlook 2026–2036; San Jose Water AL 628 (rates from Jul 1, 2026).
- **Secondary (SECONDARY; official link given for checking):** Prop 19 allowance and Prop 13 factor (BOE letters); IRS Publications 523, 527, 544; Form 706; Rev. Proc. 2022-32; 2027 federal exclusion; SF transfer-tax tiers (conflicting, left blank); Santa Clara transfer tax; insurance averages (none confirmed, left blank).
- **Not verified (UNVERIFIED, left blank):** city transfer tax; Property A and B insurance premiums; SF transfer-tax tiers; FY 2027 county fair market rents; bill numbers and text of the reported federal proposals; the Prop 19 move-out reading.
- **Household figures:** held in `private/` only. Not in the repository's published files; the privacy scan enforces this.
- **Checks:** `python3 tools/check_site.py` passes on the committed tree (privacy scan, rounding to $10, every table row linked, internal links, required pages).

Irregularities: see `data/irregularities.json` and the *Flagged for Review* page (19 items).
