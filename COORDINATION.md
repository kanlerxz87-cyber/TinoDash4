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
| T-04 | Property data: Cupertino (95014) tax history, assessment, rates | done | session-1 | pages/cupertino.html |
| T-05 | Property data: San Francisco (94122) tax history, assessment, rates | done | session-1 | pages/sanfrancisco.html |
| T-06 | Insurance research: Cupertino primary residence & SF rental | done | session-1 | pages/cupertino.html, pages/sanfrancisco.html |
| T-07 | Utilities: water, electricity (solar) cost modeling | done | session-1 | pages/cupertino.html, pages/sanfrancisco.html |
| T-08 | Inheritance tax thresholds (federal/state) & Prop 19 analysis | done | session-1 | pages/inheritance.html |
| T-09 | Decision paths: live / rent / sell+reinvest modeling | done | session-1 | pages/paths.html |
| T-10 | Black swan economic conditions section | done | session-1 | pages/blackswan.html |
| T-11 | Maintenance & capital plan (5-year) for both buildings | done | session-1 | pages/cupertino.html, pages/sanfrancisco.html |
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
- Santa Clara County / Cupertino rate: ~1.1620% (Santa Clara County rates)
- Step-up in basis: IRS Topic 403; Capital gains: IRS Topic 409; Depreciation recapture: IRS Topic 414
- Like-kind exchange: IRS Topic 613; Primary residence exclusion: IRS Topic 701

**Flagged items (see pages/flagged.html):** User-provided property values ($3,100,000 Cupertino / $1,800,000 SF), tax rates need official confirmation, insurance quotes needed, Cupertino market rent needed, TRA lookup needed.

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
site. Properties are referred to as **Property A (Cupertino, Santa Clara County)** and **Property B (San Francisco)**.
Dollar figures are rounded to the nearest $10 for display and modelling output. Owner-provided figures are labelled as such.

## Log
- 2026-11-25 · bba2482b · Created board. Claimed T1–T4. T5 reserved for final integration.
- 2026-11-25 · bba2482b · Verification pass 1 complete (see `data/sources.json`, status `verified` vs `secondary`).
- 2026-11-25 · bba2482b · Model run (`model/model.py`, seeded). Corrected Prop 19 cap to the official $1,044,586 (S08). Wrote `data/flags.json` (F-01–F-08).
- 2026-11-25 · bba2482b · Site built (`build/build_site.py` → `docs/`, 13 pages). Internal links checked; privacy scan run. Claimed T5 for integration.
- Known gaps (not blocking merge, see Flagged): SFPUC unit-rate chunks, Cupertino TRA rate, HUD revised FY2026 FMRs, CDI page, MHST line, Fed SEP and minutes, Treasury step-up NPRM text, SB 974 text. Decision triggers were written after the first model run; the page says so.



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

- ZIP codes **95014** and **94122** appear in `index.html`, `pages/cupertino.html`, `pages/sanfrancisco.html`, `pages/briefing.html`, `pages/executive-summary.html`, `pages/flagged.html`, `pages/suggestions.html`, `docs/executive.html`, `docs/flagged.html`, `build/build_site.py`, `data/flags.json`, and this board.
- A neighbourhood name for Property B appears in `pages/sanfrancisco.html`.
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

