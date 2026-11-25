# COORDINATION.md - task board

Session: `d4ff329e` · Branch: `arena/d4ff329e-tinodash4` (integration branch for this session) · Base: `fe3cad6` (main)

## Protocol used

- The session board protocol asks for per-task session branches (`session-<id>/<task>`). This session works on one branch only, as set by the session rules. All tasks were therefore committed to `arena/d4ff329e-tinodash4`, and that branch is the integration branch for the PR into `main`.
- No other session was active on this repository when this board was written, so no task claims conflicted. Conflicts, if any appear later, are logged below instead of editing another session's files.
- Pull before push; no force-pushes.

## Task board

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| T1 | Repo scaffold, data layer, build, Pages site | this session | done | `docs/` built by `scripts/build.js` |
| T2 | Decision model (7 paths; monthly; Monte Carlo; shocks; breakpoints) | this session | done | `model/model.js`; hand-checked SELL and LIVE mechanics |
| T3 | Criteria written before final figures | this session | done | `data/criteria.json`, dated 2026-11-25 (after discarded draft test runs; disclosed) |
| T4 | Property tax history: Cupertino 2014-2026, SF 2016-2025 | this session | partial | SF FY2026-27 verified; history rows blank (F24, F25) |
| T5 | Insurance research (both properties) | this session | blocked | CDI primary dataset not reached; values blank (F05, F06) |
| T6 | Federal estate/gift/income thresholds with projections | this session | partial | $15M verified; standard-deduction conflict (F09) |
| T7 | California taxes (brackets; no estate tax confirmation) | this session | partial | bracket conflict (F10); state estate tax secondary (F28) |
| T8 | Prop 19 / Prop 13 / Prop H analysis | this session | partial | allowance and BOE primary not read (F03, F04); Prop H text not read (F15) |
| T9 | Depreciation and recapture; transfer tax and recording | this session | partial | county fees verified; Pub 544 ch. 3 not read (F26) |
| T10 | Black-swan economic section (separate) | this session | done | stylised shocks; regime model assumptions |
| T11 | Federal bills tracking | this session | partial | metadata only; rate conflict (F11) |
| T12 | Anonymised inventory; no personal information on site | this session | done | placeholders only; ZIPs withheld |
| T13 | Flagged for Review and Suggestions pages | this session | done | 28 flags; suggestions not applied |
| T14 | Git history privacy | owner decision | open | existing commit shows a personal email (F21); not rewritten without approval |
| T15 | Pages deployment from `docs/` | this session | pending | set Pages source to main /docs after merge; confirm deploy |
| T16 | Integration PR into main, merge, record | this session | pending | recorded below after merge |

## Conflict log

- None between sessions. Internal conflicts in source values are listed in the Flagged for Review page (F08, F09, F10, F11, F12, F13, F15, F16).

## Decisions (dated)

- 2026-11-25: Decision criteria fixed (`data/criteria.json`). Written after discarded draft test runs, before the final figures were generated. Disclosed on the criteria page.
- 2026-11-25: Recording fee uses $92 (first page less $10 when transfer tax applies; includes $75 SB2). Corrected from $167 after reading the fee schedule.
- 2026-11-25: Cupertino treated as outside Measure E pending official city-boundary confirmation (F08).
- 2026-11-25: Recommendation is conditional on flagged inputs (F01, F02, F05, F07).

## Deployment and PR record

- PR: pending (to be filled in before merge)
- Merge: pending
- Pages: pending
