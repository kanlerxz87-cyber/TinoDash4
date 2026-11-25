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
