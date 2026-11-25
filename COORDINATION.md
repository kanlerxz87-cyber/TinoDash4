# Coordination and verification record

## Current tracked task

| Task | Status | Owner session | Branch | Scope |
|---|---|---|---|---|
| Privacy-first inheritance decision dashboard, local-only scenario calculator, evidence register, flagged review, five-year planning worksheets, printable brief, Pages configuration and privacy cleanup | in progress pending GitHub checks | `1277b9f1-tinodash4` | `arena/1277b9f1-tinodash4` | Root site (`index.html`, `flagged.html`, `styles.css`, `app.js`), README, Pages workflow, current-tree privacy cleanup, this record |

Arena assigns this session to one fixed branch. The requested separate session branches and separate integration branch were not used. Existing merged work from earlier sessions was reviewed; material with private or traceable property facts was removed from the current tracked tree. No personal/property identifiers or owner-specific asset figures are reproduced in this record.

## Privacy finding and remediation

Reviews of successive incoming `main` trees found multiple legacy generated sites, data files, model outputs, build scripts and a workflow that published the repository root. The legacy material included property/location details, owner-provided financial figures, calculations and unverified derived claims. All non-root legacy site/model/data artifacts and the old publisher have been removed from the current tree. The replacement dashboard uses only Property A / Property B aliases, blank user-entered inputs, official sources, and no user-data submission or storage. The active Pages workflow stages only the static deliverables (`index.html`, `flagged.html`, `styles.css`, `app.js`, `.nojekyll`), excluding this coordination record and README.

**Important history limitation:** these prior files were already committed on `main` before this session rebased. Deleting them from the current tree does not erase their prior GitHub commits, cached copies, forks, clones, or search-engine records. This session did not rewrite shared `main` history or attempt cache removal. A repository owner should review GitHub visibility and, if history redaction is needed, coordinate a repository-wide purge and cache requests; that may affect collaborators and cannot guarantee third-party deletion. The current feature branch's deletion diff may itself reference old lines in GitHub's compare view.

## Source and fact review

Official sources were consulted while preparing the current root dashboard on November 25, 2026. The evidence table links each factual row directly to an official government source; unknown amounts remain blank / flagged rather than inferred. Principal sources and scope:

- California BOE Proposition 13 assessment rules: <https://boe.ca.gov/pdf/pub800-10.pdf>; Proposition 19: <https://www.boe.ca.gov/prop19/>; Santa Clara TRA map: <https://www.boe.ca.gov/maps/SantaClaraCo.htm>.
- California Revenue and Taxation Code §13301: <https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=13301.>.
- IRS 2026 Form 706 instructions: <https://www.irs.gov/instructions/i706>; Pub. 551 basis: <https://www.irs.gov/publications/p551>; Pub. 17 income: <https://www.irs.gov/publications/p17>; Pub. 523 home-sale exclusion: <https://www.irs.gov/publications/p523>; Pub. 544 sale/exchange treatment: <https://www.irs.gov/pub/irs-pdf/p544.pdf>.
- California FTB personal income-tax and capital-gain references: <https://www.ftb.ca.gov/forms/2025/2025-540-booklet.html>; <https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html>.
- San Francisco Treasurer property-tax information: <https://sftreasurer.org/property/secured-property-taxes>; SF Rent Board petitions: <https://www.sf.gov/landlord-petitions-and-passthroughs>; 2026 voter pamphlet: <https://media.api.sf.gov/documents/N26_EN_VIP.pdf>; SFE results: <https://www.sfelections.org/results/20261103/index.html>. The November 25 dashboard states Measure H results were preliminary and does not treat them as certified.
- TreasuryDirect marketable securities: <https://www.treasurydirect.gov/marketable-securities/>; IRS Pub. 550: <https://www.irs.gov/publications/p550>.
- California Contractors State License Board consumer resources: <https://www.cslb.ca.gov/Consumers/>.
- California Department of Insurance consumer resources: <https://www.insurance.ca.gov/01-consumers/>.

No private parcel-level tax rate, property value, insurance premium, rent, or property cost is presented as verified. Property-specific assessments, records and documents must be obtained privately from the relevant assessor, recorder, insurer, property manager, attorney and CPA. Recheck law and rates near transfer and filing dates.

## Verification completed

- `node --check app.js` passed.
- Calculator smoke-tested with synthetic test-only inputs in a Node DOM stub: six common-horizon pathways, Property B horizon equity, configurable multi-year post-shock recovery, missing-input handling, invalid recovery selector, low/high ordering, negative-equity rejection and reset behavior.
- HTML audit across `index.html` and `flagged.html`: no duplicate IDs or broken fragment links; every factual table / worksheet data row links directly to an official source.
- Form audit: all required calculator input controls are referenced; no unused calculator field remains.
- `git diff --check` passed after the current cleanup.
- Local HTTP server returned 200 for `/`, `/styles.css`, `/app.js`, `/flagged.html` and `/.nojekyll`.
- A token scan of the current public tree for selected exact legacy locations/figures found no matches. This narrow scan is not proof against every identifying combination.
- Pages workflow staging is limited to the public static files; it does not upload README or COORDINATION.md.
- No actual browser visual, assistive-technology, or end-to-end test has been performed.

## Unresolved and explicitly flagged

The site is a non-probabilistic sensitivity aid, not a forecast, legal/tax engine, recommendation, investment-policy prescription or historical replay of 1929/2008. It models one user-entered equity drawdown and a user-selected 1/3/5/10-year recovery-return assumption, then flat annual assumptions; low/base/high combinations are not probability distributions. Property B is assumed retained in all paths; its horizon value less entered horizon debt is included before B sale costs/tax. It requires private verified date-matched inputs before any comparison could support a household decision. Unknowns include date-of-death value, current valuations, title/trust and basis, Prop 19 eligibility, debt, prior gifts/portability, leases and unit legality, SF occupancy/lease implications, depreciation schedules, parcel classification and tax bills (including Measure H certification / implementation), rent comparables, insurance, utilities, five-year capital plans, transaction costs, tax estimates, estate liquidity needs and investment policy.

## GitHub publication

The root site is static and needs GitHub Pages configured for GitHub Actions. This session has not yet verified a pull request, merge, Actions run or deployed URL. Do not state that the current dashboard is live until the deployment workflow completes successfully and the deployed page is checked. The old workflow was removed to prevent it from publishing the deleted legacy trees.
