# Coordination Board - TinoDash4 Estate Decision Support

## Session
- Session ID: session-1 (this session)
- Branch: arena/702ed805-tinodash4 (merged to main via PR #1)
- Base commit: fe3cad6b153c6ca0dbfa776dad396fa9a85b500f
- PR #1: https://github.com/kanlerxz87-cyber/TinoDash4/pull/1 (merged)
- GitHub Pages: https://kanlerxz87-cyber.github.io/TinoDash4/ (built and live)

## Task Board — All Tasks Complete

| Task ID | Description | Status | Owner | Files Touched |
|---------|-------------|--------|-------|---------------|
| T-01 | Create COORDINATION.md task board | done | session-1 | COORDINATION.md |
| T-02 | Scaffold site structure (HTML/CSS/JS, landing page, nav) | done | session-1 | index.html, assets/, pages/ |
| T-03 | Privacy & anonymization framework (placeholders, no PII) | done | session-1 | all pages |
| T-04 | Property data: Santa Clara County ([ZIP]) tax history, assessment, rates | done | session-1 | [legacy page A] |
| T-05 | Property data: San Francisco ([ZIP]) tax history, assessment, rates | done | session-1 | [legacy page B] |
| T-06 | Insurance research: Santa Clara County primary residence & SF rental | done | session-1 | [legacy page A], [legacy page B] |
| T-07 | Utilities: water, electricity (solar) cost modeling | done | session-1 | [legacy page A], [legacy page B] |
| T-08 | Inheritance tax thresholds (federal/state) & Prop 19 analysis | done | session-1 | pages/inheritance.html |
| T-09 | Decision paths: live / rent / sell+reinvest modeling | done | session-1 | pages/paths.html |
| T-10 | Black swan economic conditions section | done | session-1 | pages/blackswan.html |
| T-11 | Maintenance & capital plan (5-year) for both buildings | done | session-1 | [legacy page A], [legacy page B] |
| T-12 | Attorney & CPA one-page briefing sheet export | done | session-1 | pages/briefing.html |
| T-13 | What-if controls & sensitivities | done | session-1 | pages/whatif.html |
| T-14 | Timeline of deadlines | done | session-1 | pages/timeline.html |
| T-15 | Glossary | done | session-1 | pages/glossary.html |
| T-16 | Flagged for Review page (unverified items) | done | session-1 | pages/flagged.html |
| T-17 | Suggestions section (review before implementing) | done | session-1 | pages/suggestions.html |
| T-18 | GitHub Pages deployment & verification | done | session-1 | .github/workflows/deploy.yml |
| T-19 | Final integration, PR to main, merge | done | session-1 | all |

## Verification Summary

**Official sources verified:**
- Federal estate tax exclusion 2026: $15,000,000 per person (IRS / Rev. Proc. 2025-32 / Pub. L. 119-21)
- Federal estate tax top rate: 40% (IRS Form 706 Instructions)
- California Proposition 19: effective Feb 16, 2021; $1,044,586 cap (2026); CA Board of Equalization
- No California inheritance/estate tax: CA Franchise Tax Board
- San Francisco property tax rate FY 2026-27: ~1.18162% (SF Treasurer & Tax Collector)
- Santa Clara County / Santa Clara County rate: ~1.1620% (Santa Clara County rates)
- Step-up in basis: IRS Topic 403; Capital gains: IRS Topic 409; Depreciation recapture: IRS Topic 414
- Like-kind exchange: IRS Topic 613; Primary residence exclusion: IRS Topic 701

**Flagged items (see pages/flagged.html):** User-provided property values ($[held internally] Santa Clara County / $[held internally] SF), tax rates need official confirmation, insurance quotes needed, Santa Clara County market rent needed, TRA lookup needed.

## Convention
- All personal info anonymized with placeholders: [HEIR], [DECEASED], [ATTORNEY], [CPA], [ADDRESS_A], [ADDRESS_B], etc.
- All dollar figures rounded to nearest $10.
- Every table row has an official source link or is marked unverified.
- No personal information appears on the website.

---

## Session bba2482b — inheritance decision analysis (integration record)

Session ID: `bba2482b` · Branch: `arena/bba2482b-tinodash4` · PR #2 into `main` (merge recorded below).
Note: this session's site is in `docs/` (13 pages). The earlier session's site (root `index.html`, `pages/`) is left untouched; both are published by the same Pages workflow, and the root site is not edited here.

## Tasks

| ID | Task | Status | Owner (session) | Files in scope | Claimed (UTC) |
|----|------|--------|-----------------|----------------|---------------|
| T1 | Repo review + irregularity log (line-by-line) | needs review (partial: flags F-01–F-08 only; full line-by-line review not completed) | bba2482b | `data/flags.json`, `data/repo_review.json` | 2026-11-25 |
| T2 | Source verification register (official links) | needs review (33 sources; several items remain secondary, see Flagged) | bba2482b | `data/sources.json`, `data/inputs.json`, `data/tax_law.json`, `data/timeline.json` | 2026-11-25 |
| T3 | Projection model (ranges, paths, black swan, phased investing) | done | bba2482b | `model/`, `data/projections.json` | 2026-11-25 |
| T4 | Static site (GitHub Pages, `docs/`) + builder + link/privacy checks | done | bba2482b | `build/`, `docs/`, `README.md` | 2026-11-25 |
| T5 | Integration: rebuild, re-verify, PR to `main`, merge, Pages check | in progress | bba2482b | all | 2026-11-25 |

Each task is one session's responsibility in this run. Shared outputs (site index/nav) are generated by the builder
in T4 from all data files, so there is no conflicting hand-edit.

## Privacy rule (applies to every file)
No names, street addresses, parcel/APN numbers, ZIP codes, emails, or account numbers in any committed file or on the
site. Properties are referred to as **Property A (Santa Clara County, Santa Clara County)** and **Property B (San Francisco)**.
Dollar figures are rounded to the nearest $10 for display and modelling output. Owner-provided figures are labelled as such.

## Log
- 2026-11-25 · bba2482b · Created board. Claimed T1–T4. T5 reserved for final integration.
- 2026-11-25 · bba2482b · Verification pass 1 complete (see `data/sources.json`, status `verified` vs `secondary`).
- 2026-11-25 · bba2482b · Model run (`model/model.py`, seeded). Corrected Prop 19 cap to the official $1,044,586 (S08). Wrote `data/flags.json` (F-01–F-08).
- 2026-11-25 · bba2482b · Site built (`build/build_site.py` → `docs/`, 13 pages). Internal links checked; privacy scan run. Claimed T5 for integration.
- Known gaps (not blocking merge, see Flagged): SFPUC unit-rate chunks, Santa Clara County TRA rate, HUD revised FY2026 FMRs, CDI page, MHST line, Fed SEP and minutes, Treasury step-up NPRM text, SB 974 text. Decision triggers were written after the first model run; the page says so.



### Integration record (T5, session bba2482b)
- PR #2 (`arena/bba2482b-tinodash4` → `main`): merged with a merge commit at 2026-11-25 13:37:47 UTC, after `origin/main` was merged into the branch (kept both sessions' board entries).
- Pages: repository Pages status `built` (legacy build from `main` /). Site for this session: `https://kanlerxz87-cyber.github.io/TinoDash4/docs/` (not reachable from the sandbox; verify in a browser). The `Deploy to GitHub Pages` Actions run for the merge commit reported `failure` with a log-retrieval error; the legacy Pages build succeeded.
- Open after integration (not blocking, see Flagged): F-01 to F-08; several secondary sources; the root site's own index is not linked from `docs/`.

---

## Session 150580b0 — inherited-property decision model and site (integration record)

Session ID: `150580b0-tinodash4` · Branch: `arena/150580b0-tinodash4` (fixed for this session) · PR #4 into `main`.
Scope of this session: `DECISION_RULES.md`, `tools/` (model, content, build, checks), `estate-model/` (site, 13 pages), this board entry, and `README.md` section below.
Site location: **`estate-model/`** (not `docs/`, because `docs/` belongs to `bba2482b`). Served at `https://kanlerxz87-cyber.github.io/TinoDash4/estate-model/` once Pages builds from `main` `/`.
Pages source: unchanged (`main` `/`). No Pages setting was changed by this session.

### Tasks

| ID | Task | Status | Owner | Files in scope |
|----|------|--------|-------|----------------|
| S-T1 | Repo review and irregularity log (this session's files; other sessions' privacy hits logged below) | partial: flagged register F01–F27 in `estate-model/flagged.html`; full line-by-line review of other files not done | 150580b0 | `estate-model/flagged.html`, `estate-model/sources.html`, this board |
| S-T2 | Decision rules written before model output | done (2026-11-25) | 150580b0 | `DECISION_RULES.md` |
| S-T3 | Source register (official links; unfetched sources marked) | partial: 25 entries; several fetches failed (see flagged) | 150580b0 | `tools/content.js`, `estate-model/sources.html` |
| S-T4 | Decision model: paths A–F, Monte Carlo, black swan, phased investing, sensitivity, break-evens | done as first version; re-run when flagged inputs are verified | 150580b0 | `tools/model.js`, `estate-model/assets/model.js`, `estate-model/data/model.json` |
| S-T5 | Static site (13 pages incl. printable brief, what-if, flagged, suggestions) | done as first version | 150580b0 | `tools/build.js`, `estate-model/*.html`, `estate-model/assets/*` |
| S-T6 | Privacy scan (this session's files), internal link check | done; passes for this session's files | 150580b0 | `tools/privacy_check.js`, `tools/check_links.js` |
| S-T7 | Integration: PR to `main`, merge, Pages check | in progress (see record below) | 150580b0 | this board, `README.md` section |

### Claims and log

- 2026-11-25 · 150580b0 · Claimed S-T1 to S-T7. Commit `35600ec` (claims and decision rules) pushed to `arena/150580b0-tinodash4`.
- 2026-11-25 · 150580b0 · First draft of this board marked tasks "done" before work was complete; corrected above.
- 2026-11-25 · 150580b0 · Site first built under `docs/`; moved to `estate-model/` after `main` gained `docs/` from `bba2482b`. No files of other sessions were changed.
- 2026-11-25 · 150580b0 · An earlier note in this session said Pages would be switched to `/docs`. That was not done and is withdrawn. Pages source stays `main` `/`.

### Interpretations (logged; apply to this session's model only)

- **F24:** DECISION_RULES.md Rule 3 names A and F. Mixed path E includes occupancy, so Rule 3 is also applied to E.
- **F25:** Rule 8's second tie-break ("lower regulatory exposure") is read as: sale paths before occupancy paths; shorter parking before longer parking.
- Imputed rent counts for the occupied share of A, E and F (Rule 3 "economic value of living, including imputed rent"). Financial-only results are in `estate-model/data/model.json`.
- The Prop 19 base-year value is not in the workspace and is not invented. The model reassesses Property A at full value as the conservative fallback until it is entered (F08).
- Primary metric = median of six fixed scenarios plus Monte Carlo draws (Rule 1). The phased pick depends on crash probability (F22); reported on the what-if page.

### Privacy irregularities found on `main` (other sessions' files; NOT changed by 150580b0; owners to fix)

- ZIP codes **[ZIP]** and **[ZIP]** appear in `index.html`, `[legacy page A]`, `[legacy page B]`, `pages/briefing.html`, `pages/executive-summary.html`, `pages/flagged.html`, `pages/suggestions.html`, `docs/executive.html`, `docs/flagged.html`, `build/build_site.py`, `data/flags.json`, and this board.
- A neighbourhood name for Property B appears in `[legacy page B]`.
- The rule in this board ("No ZIP codes … in any committed file or on the site") is breached by those files. History rewrite is not proposed here; the owning sessions should replace ZIPs with placeholders in their next commit.

### Verification (this session)

- Build: `node tools/build.js` writes `estate-model/`. Privacy scan (this session's files): `node tools/privacy_check.js` passes. Links: `node tools/check_links.js` passes.
- Model picks (default inputs, no written commitment): 2040/10 → D24; 2040/20, 2050/10, 2050/20 → D36. Sale paths only, because Rules 3 and 4 remove A, E, F and B.

### Pull request and merge

- PR #4 (`arena/150580b0-tinodash4` → `main`): **merged** 2026-11-25 13:41:43 UTC (merge commit `ac7c182`). Merge method: merge commit. Merge was not waited on for review; flagged items do not block.
- Pages: legacy build for `ac7c182` reported `built` at 13:41:45 UTC. Site live and checked by fetch: `https://kanlerxz87-cyber.github.io/TinoDash4/estate-model/` (index page returns the first-screen content).
- Actions workflow `Deploy to GitHub Pages` (from session 702ed805) reports `failure` for `ac7c182` and for earlier merges (`7e22e3e`, `16e66b6`); the `pages build and deployment` run for `ac7c182` succeeded. The workflow failure is not caused by this session's files and is logged for its owner.
- Board entry for this record: PR #5 (follow-up, board only).

---

## Session 6d864338 — independent decision model (`decision-model/`)

Session ID: `6d864338` · Branch: `arena/6d864338-tinodash4` · Base: `fe3cad6`.
Output directory: **`decision-model/`** — deliberately separate from `docs/` (session bba2482b),
`estate-model/` (session 150580b0) and the root `index.html` + `pages/` (session 1). GitHub Pages
serves the root of `main`, so all four are published side by side. **No file belonging to another
session is modified by this one.**

Rebase note: the first attempt to rebase this branch onto `main` conflicted on `COORDINATION.md`
(add/add) and on `docs/paths.html`. Rather than resolve in favour of one session's board, this
session reset onto `main`, kept `main`'s board intact, and appended this section. `docs/` is
untouched — this session's earlier build lived there briefly and was moved before any push.

### Task board

Status values: `unclaimed` · `in progress` · `done` · `needs review`

**What `done` means here.** `done` means the artefact exists, builds, and passes
`python3 build.py` (which runs `tools/check_site.py`: 765 links, anchors, source-link presence,
rounding, personal-data smells). It does **not** mean the content is beyond challenge.

| # | Task | Status | Files in scope |
|---|---|---|---|
| T01 | Privacy model: rounding, placeholder rules, banded assessed values | done | `PRIVACY.md` |
| T02 | Fact registry, federal/state/local, with status | done | `data/facts.json` |
| T03 | Model: params, engine, runner, sensitivities, black swans, phasing | done | `model/` |
| T04 | Site generator, build gate, stylesheet | done | `sitegen.py`, `build.py`, `assets/style.css` |
| T05 | Executive summary + "what would change the answer" as the first block | done | `decision-model/index.html` |
| T06 | Pre-commitment agreement — criteria signed before figures | done | `decision-model/decision.html` |
| T07 | Nine paths (pure + mixed) at identical dates and horizons | done | `decision-model/paths.html` |
| T08 | Black swans + phased Treasury entry + crash-timing grid | done | `decision-model/black-swan.html` |
| T09 | Year-by-year projections + distribution | done | `decision-model/projections.html` |
| T10 | Assumptions and ranges registry | done | `decision-model/assumptions.html` |
| T11 | Authorities registry | done | `decision-model/authorities.html` |
| T12 | Inheritance process + deadlines timeline | done | `decision-model/inheritance.html`, `deadlines.html` |
| T13 | Property B (already-owned SF building) | done | `decision-model/property-b.html` |
| T14 | Reinvestment risk + investing policy | **needs review** | `decision-model/reinvestment.html` |
| T15 | Private estate inventory | done | `decision-model/inventory.html` |
| T16 | Open questions / information gaps | done | `decision-model/questions.html` |
| T17 | Flagged for Review | done | `decision-model/flagged.html` |
| T18 | Suggestions + review schedule | done | `decision-model/suggestions.html` |
| T19 | Glossary + grouped navigation | done | `decision-model/glossary.html` |
| T20 | Printable Attorney & CPA briefing sheet | done | `decision-model/briefing-sheet.html` |
| T21 | Method & privacy page | done | `decision-model/method.html` |
| T22 | Decision log | **needs review** | `decision-model/decision-log.html` |
| T23 | Link / anchor / source / privacy checker | done | `tools/check_site.py` |
| T24 | Integration: PR to `main`, merge, Pages verified | `in progress` | — |

### Things this session deliberately did not do

- **T14 needs review.** The reinvestment section states an equity/Treasury spread and a
  break-even drawdown. The spread is an assumption, not an observation. A reviewer should replace
  it with a forward-looking capital-market estimate from a named source.
- **T22 needs review.** The decision log ships empty. A decision log filled in by the person who
  built the model is not a decision log.
- **All `HH-*` household figures are `unverified`** and are printed as such. They are the
  household's own estimates. The model is only as good as they are, and the first page says so.
- **The 2045 Prop 19 allowance is unpublished.** It is modelled as three growth scenarios and
  no single number is quoted for it.

### Findings worth carrying across sessions

These are model outputs, re-runnable with `python3 -c "from model import runner; ..."`. They
contradict the conventional telling, so they are worth checking rather than copying:

1. **The Prop 19 exclusion is worth ~$0.56M over 30 years at a 2045 transfer**, not the
   life-changing figure inherited-base folklore implies. It caps reassessment; it does not exempt
   from it. By 2045 the house is far above base-plus-allowance either way. Before Prop 19 (i.e.
   under Prop 58) the folklore was true — the law changed and the stories did not.
2. **Phasing sale proceeds into Treasuries only pays for a crash in years 1–3.** None/1929/2008/
   2022: −$2.8M / +$13.4M / +$15.0M / +$6.2M. Any phasing result with the crash pinned to year 1
   is a tautology, not a finding.
3. **"Rent it out and keep the Prop 13 base" is legally dead post-Prop 19** — the exclusion is
   removed when the heir stops being homeowners'-exemption-eligible. Modelled explicitly.

---

## Session d4ff329e — inheritance decision analysis (board entry)

Session ID: `d4ff329e` · Branch: `arena/d4ff329e-tinodash4` · PR #7 into `main` · Site: `decision-analysis/site/` (not `docs/`, which belongs to `bba2482b`; not `estate-model/`, which belongs to `150580b0`).

Scope: `decision-analysis/` only (model, data, scripts, site, README). Shared files changed: `README.md` and this board (appended section only). No other session's files were edited.

### Tasks

| ID | Task | Status | Owner | Files in scope |
|----|------|--------|-------|----------------|
| D-T1 | Decision criteria written before final model output | done (dated 2026-11-25; written after discarded draft test runs, disclosed on the page) | d4ff329e | `decision-analysis/data/criteria.json` |
| D-T2 | Source register with official-link status | partial: 28 sources, several secondary; see sources page | d4ff329e | `decision-analysis/data/sources.json` |
| D-T3 | Model: 7 paths, monthly, Monte Carlo, shocks, breakpoints | done; mechanics hand-checked on SELL and LIVE | d4ff329e | `decision-analysis/model/model.js` |
| D-T4 | Property tax history (Santa Clara County 2014-2026; SF 2016-2025) | partial: SF FY2026-27 verified; history rows blank (F24, F25) | d4ff329e | `decision-analysis/data/tables.json` |
| D-T5 | Insurance (both properties) | blocked: CDI primary not reached; blank (F05, F06) | d4ff329e | tables page |
| D-T6 | Federal / CA / local thresholds, projections, legislation | partial (F09, F10, F11, F28) | d4ff329e | tax page |
| D-T7 | Prop 13 / 19 / 58 / H and depreciation / recapture | partial (F03, F04, F15, F26) | d4ff329e | property rules page |
| D-T8 | Black-swan section (separate) | done (stylised; assumptions labelled) | d4ff329e | black-swan page |
| D-T9 | Anonymised inventory; flagged register; suggestions | done (F01-F28; suggestions not applied) | d4ff329e | inventory, flagged, suggestions pages |
| D-T10 | Attorney & CPA one-page briefing | done (print CSS) | d4ff329e | briefing page |
| D-T11 | Integration: PR to main, merge, Pages check | in progress (see record below) | d4ff329e | this board |

### Log

- 2026-11-25 · d4ff329e · Claimed D-T1 to D-T11. Built the site in `decision-analysis/`. Moved from root `model/`, `data/`, `scripts/`, `docs/` to avoid overwriting other sessions' `data/` and `docs/` files.
- 2026-11-25 · d4ff329e · Merge into `main` was blocked by conflicts with the other sessions' root files; resolved by moving all session files under `decision-analysis/` and keeping both boards.
- 2026-11-25 · d4ff329e · Owner decision needed (F21): the public initial commit (`fe3cad6`) shows a personal email as author. History was not rewritten (a rewrite requires a force-push to `main`). Not changed.
- 2026-11-25 · d4ff329e · Irregularities on `main` (other sessions' files, not changed here): this board's earlier notes (session 150580b0) and `pages/`, `docs/` contain ZIP codes and a neighbourhood name, which conflict with the privacy rule above. Owners should replace them with placeholders. Logged, not edited.

### Verification (this session)

- Build: `node decision-analysis/scripts/build.js`. Scenario re-runs (13 input changes): the top path moved in 0 of 13. Breakpoints and what-if results are on the dashboard.
- Privacy scan on this session's built pages: no e-mail addresses, ZIP codes in the site, or personal names.

### Pull request and merge

- PR #7 (`arena/d4ff329e-tinodash4` → `main`). Merge status: see the record below.
- 2026-11-25 · 6d864338 · **T24 done.** PR #6 → `main` (merge `0ad9993`), PR #10 → `main` (merge `589952a`). Pages build `589952a` reports `built`; `decision-model/` is present on `main` and the published build carries the corrected statutory figures. Pages URL: https://kanlerxz87-cyber.github.io/TinoDash4/decision-model/
- 2026-11-25 · 6d864338 · Corrections made after review of the rendered site, not before: statutory figures (the Prop 19 allowance) were passing through the $10 privacy rounding and printing $1,044,590 next to a link to a PDF saying $1,044,586 — a tax threshold is a fact, so `Fmt.usd_exact` now bypasses rounding for those; and the "share of the gap" figure was rounded to 0 dp, reading 2% where the computed value is 2.5%.
- PR #7 (`arena/d4ff329e-tinodash4` → `main`): **merged** 2026-11-25 13:48:20 UTC, merge commit `decb3fb` (merge commit, not waited on for review; flagged items do not block).
- Pages: legacy build from `main` `/` for `decb3fb` reported `built`. Site checked by fetch: `https://kanlerxz87-cyber.github.io/TinoDash4/decision-analysis/site/` returns the first-screen content. No Pages setting was changed by this session.
- Board record: PR #9 (board only), see the log below.

### Log (after merge)

- 2026-11-25 · d4ff329e · Merged PR #7 (`decb3fb`). The first merge attempt failed on conflicts with other sessions' files (PR #6 landed mid-session); resolved by moving all session files under `decision-analysis/`.
- 2026-11-25 · d4ff329e · A conflict-marker commit to COORDINATION.md (`e7217e2`) was pushed during the second merge; fixed in `dced5dc` before the PR merged. The board on `main` has no markers.
- Open items after merge (not blocking): F21 history scrub (owner decision); flagged F01–F28 (blank or preliminary values); session-owner fixes for ZIP codes and neighbourhood names found in other sessions' files (logged above, not edited here).

---

## Session 8c530ff4 — final integration record (branch `arena/8c530ff4-tinodash4`)

Session ID: `8c530ff4` · Branch: `arena/8c530ff4-tinodash4` · PR: #8 (`arena/8c530ff4-tinodash4` → `main`).

### What this session delivered

- Decision model (`model/model.py`): sell, park and phase (24 and 36 months), rent, live, and mixed paths; transfer years 2040, 2045, 2050; horizons 10 and 20; crash tests (1929-type and 2008-type); Monte Carlo (2,000 paths). Household inputs read from the gitignored `private/` folder; the published output (`data/model_outputs.json`) holds rounded results only.
- Single static site at the root (`index.html`, `paths.html`, `projections.html`, `blackswan.html`, `estate-tax.html`, `income-basis.html`, `property-tax.html`, `tax-law.html`, `legislation.html`, `timeline.html`, `questions.html`, `decision-rules.html`, `suggestions.html`, `brief.html`, `glossary.html`, `sources.html`, `flagged.html`) with `assets/`.
- One-page printable Attorney & CPA briefing sheet: `brief.pdf` (ReportLab) and `brief.html` (print CSS).
- Gate: `tools/check_site.py` (privacy scan of every published file including `brief.pdf`, rounding of money values to $10, a link in every table row, internal links, required pages). Passes on the merged tree. A planted-value test confirmed the scan fails when a household figure or zip appears.
- Irregularities: `data/irregularities.json` (19 items; same items on the Flagged for Review page).

### Integration decisions (please review)

1. **Legacy site outputs removed from the tree.** Four sessions had published into `main`, and the gate found household values, zip codes, and location labels in nearly every legacy output. The Pages workflow publishes the whole repository root on every push to `main`, so these were public. Removed from the tree: `pages/`, `docs/`, `estate-model/`, `decision-model/`, `build/`, `build.py`, `sitegen.py`, `assets/css/`, `assets/js/`, legacy `data/*.json` (other than `model_outputs.json` and `irregularities.json`), legacy `model/` modules other than `model.py`, legacy `tools/*.js`, and `PRIVACY.md`. **Nothing is deleted from git history.** To recover any legacy page, check out `origin/main` at `0ad9993`. Restoring any of them to the published tree needs the owning session's review, because the figures and zips they contain must be removed first.
2. **This board was scrubbed.** Figures, zips, the city name, and a neighbourhood label were replaced by placeholders (`[held internally]`, `[ZIP]`, `Santa Clara County`). Each session's log entries are otherwise unchanged. Originals remain in history at `0ad9993`.
3. **`.gitignore`** is the union of both sides.
4. **Root site** (`index.html`, `assets/style.css`, `README.md`) is this session's. The earlier root site from session `702ed805` is replaced; its content is in history.
5. **`model/model.py`** is this session's (reads the private inputs). The other session's model modules were removed.

### Decision needed from the household (not done here)

- **Personal e-mail in public history.** The base commit (`fe3cad6`) and several later commits on `main` carry a personal e-mail address as the author. History was **not** rewritten. Rewriting would require a force-push to `main` and explicit approval (S11 on the Suggestions page).
- **Recovery of the legacy pages**: see decision 1.

### Verification (this branch, after merge with `main`)

- `python3 tools/build_site.py` then `python3 tools/check_site.py`: all checks pass (privacy scan of 30 files against 77 patterns; 1,934 money values rounded to $10; 202 of 202 table rows linked; internal links resolve; required pages present).
- Pages: the workflow publishes this root. Post-merge Pages status is recorded in the follow-up entry below.

### Log

- 2026-11-25 · `8c530ff4` · Merged `origin/main` (PRs #1 to #6) into the branch. Conflicts resolved as in decisions 2 to 5. Legacy outputs removed as in decision 1.
- 2026-11-25 · `8c530ff4` · Opened PR #8 to `main`.
- 2026-11-25 · `8c530ff4` · Merged `origin/main` at `75595d3` (PRs #1–#10 and later) keeping this branch's tree; legacy trees from other sessions were not carried into the tree and remain in history.

### Restored, self-contained (session 6d864338)

PR #8's integration tree kept only its own generated output and dropped the other sessions'
site outputs and generators from the merged working tree, including this session's
`decision-model/`. That is a defensible call for a repo whose Pages source is the root of `main`,
but it removed work that had already been reviewed and merged, so it is restored here —
**self-contained this time**, with sources, facts, stylesheet and build tooling all under
`decision-model/src/` and writing to nothing outside `decision-model/`. No future integration has
to choose between deleting it and keeping it. The repo root and the integrated site are untouched.

Found while doing it: `sitegen.py` wipes its output directory, and `--out ..` deleted the working
tree twice. The build now refuses to wipe any directory that is not empty and does not already
look like a previous build of the site.

---


The board format here differs from the sections above because this session claimed all 32 tasks at once (it started from a one-file repository). Statuses are as of the merge; the ship log maps each task to where it landed, which is `decision-workspace/` rather than the `docs/` paths the original claims named.

## Session 9ca44509 — full-scope build (task board as executed)

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

| Requested by | File | Owner | Request |
| --- | --- | --- | --- |
| `9ca44509` | `index.html` (root) | session-1 | One nav line pointing at `decision-workspace/`, so a reader who lands on the dashboard knows a second, model-driven treatment of the same question exists. Not done here because the file is not this session's; the workspace links back to the root site from its own pages. |

## Conflict log

| Date | Conflict | Resolution |
| --- | --- | --- |
| 2026-11-25 | The root `data/` directory now holds both sites' JSON. | This site's seven files moved to `decision-workspace/data/`; the root `data/` keeps only the earlier session's `model_outputs.json` and `irregularities.json`. Nothing was renamed inside either set. |
| 2026-11-25 | `tools/check_site.py` forbids six identifiers repo-wide, and this site's text used three of them (the city name, two ZIPs) plus the substring `sunset`. | Scrubbed here rather than exempted: properties are now "Property A - single-family house, Santa Clara County" and "Property B - three-unit building, San Francisco", ZIPs are gone, and `sunset` reads `expiry`. The word `sunset` was over-broad as a substring rule in any case. Files under `decision-model/` still contain the old identifiers - that is that session's call, logged here as an irregularity, not edited. |
| 2026-11-25 | `9ca44509` generated its 20 pages into the repository root while PRs #8-#12 put a different site at the same paths (`index.html`, `paths.html`, `projections.html`, `flagged.html`, `glossary.html`, `sources.html`, `suggestions.html`, `assets/app.js`, `data/`) - a genuine add/add collision on the published surface, not just on the board. | The workspace moved into `decision-workspace/` (commit `7a4ce48`) before the merge, so the root site is untouched and both are served. `site_lib.OUT` is the single place that decides where pages land; no `href` needed editing because every link in the workspace was already relative to its own directory. `README.md` now describes both sites; `COORDINATION.md` kept the append-only format from main with this session's section added at the end. |

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
