# Privacy review — 2026-11-26

**Status: partial containment; not privacy-cleared.** This review does not repeat household amounts,
addresses, contact details, or parcel identifiers. A successful build or hygiene scan is not a release
approval and is not a guarantee of anonymity.

## Current publication boundary

- GitHub Pages is configured for a legacy root build from `main` at `/`.
- The root `_config.yml` excludes alternate site and model trees from the Pages artifact. `.nojekyll`
  must remain absent so Jekyll can apply those exclusions.
- A historical Pages build for the containment revision reported `built`; the related verification run
  completed. This confirms the reported build status, **not** the contents of the deployed artifact.
  The artifact file-list download could not be completed from this environment, so deployed paths remain
  unverified here.
- Jekyll exclusions limit Pages output only. They do not restrict public GitHub source, previous
  commits, pull-request diffs, other refs, forks, caches, Actions artifacts, or copies.

## Findings and limits

1. **Pages exclusion is not repository privacy.** Earlier repository reviews found household-derived
   material in alternate model/site trees. Those paths remain accessible through public Git even when
   excluded from Pages. This change does not remove those files or purge earlier history.
2. **The root dashboard contains rounded, derived projections.** They use household-provided model
   assumptions and may be linkable to public records. Rounding to $10 does not establish anonymity.
   Direct unit/lease details in the root facts and brief are now marked held internally, but the
   projections remain household-derived.
3. **History was not rewritten.** Public commits include author contact metadata and earlier versions
   of exposed material. A current-tree edit cannot remove prior commit objects or copies. This session
   did not rewrite shared history.
4. **The current-tree privacy gate has two modes.** Default strict mode requires the ignored local
   `private/raw_inputs.json` and fails closed if it is absent or unreadable. `--public-only` skips exact
   private-input matching so CI can run without household values; it still scans repository text for
   restricted-token hashes and checks direct-identifier patterns and structural integrity on the root
   Pages surface. The explicit skip is not a privacy sign-off.
5. **The exact-pattern comparison is intentionally limited.** It checks selected unrounded numeric
   inputs, sufficiently long text inputs, and explicit private location-code inputs; $10-multiple
   values are excluded because public outputs are deliberately rounded. It cannot certify that those
   rounded or derived outputs are non-identifying. The ignored input file is absent from this checkout,
   so that comparison has not been run here.
6. **Current review entries were sanitized, not the history.** Household-derived amounts were removed
   from the current coordination board and root irregularities register. Earlier commits may still
   contain them; the limitations in item 3 apply.
7. **The one-page PDF is part of the public surface.** Its page count, links, and privacy caveat are
   checked with the root HTML and data artifacts.

## Recommended next actions

- Keep raw household inputs in an access-controlled, ignored local file or offline inventory; never
  commit them or place them in a public artifact.
- If the no-household-data publication rule is absolute, replace personalized public outputs with
  synthetic examples or broad non-household ranges and retain calculations based on actual inputs
  offline.
- Ask the repository owner to decide whether public repository visibility is compatible with the
  privacy requirement. A smaller Pages artifact does not make GitHub source private.
- Before treating containment as complete, inspect the actual Pages artifact file list and deployed
  URLs after the next deployment.
- If history remediation is authorized, coordinate it across the default branch, all refs, PRs, forks,
  caches, Actions artifacts, and Pages copies. A force-push cannot recall copies already obtained.
  This session does not rewrite shared history.

## Verification record

- Historical Pages API metadata reported a legacy build from `main` at `/`; the related Actions runs
  completed successfully. The artifact's file list was not independently inspected.
- The current worktree rebuilt 18 root navigation pages and regenerated the one-page `brief.pdf`.
  A second CI-style root build produced no diff in tracked HTML/assets/irregularity output; staged and
  unstaged `git diff --check` both passed.
- `python3 tools/check_site.py --public-only` passed: repository restricted-token scan, 23 Pages files
  scanned for direct-identifier patterns, $10 rounding, 212/212 sourced table rows, internal links,
  Jekyll exclusions, and the one-page PDF with 15 clickable source links. The checker explicitly
  reports that exact private-input matching was skipped.
- Default `python3 tools/check_site.py` failed closed as expected because the ignored private input is
  absent. No private baseline was added to the repository.
- `python3 model/build_model.py` completed without changing tracked `site/data`; `node
  model/check_site.js` passed the renderer smoke checks.
- The artifact file-list check remains incomplete because the Actions artifact download redirected to a
  host that this execution environment does not permit.

No tax, estate, or legal conclusion is made in this privacy review.
