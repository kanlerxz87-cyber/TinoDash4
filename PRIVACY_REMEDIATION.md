# Privacy containment status

**Status: partial containment; do not treat this as a history purge.**

## What this audit found

A repository review found multiple parallel, generated site trees. Some non-root artifacts still contain property-specific location labels and household-derived financial inputs, including directly rendered inputs and raw model constants. A previous privacy statement therefore overstated what was actually absent from the published artifacts. The maintained root dashboard has been configured as the only Pages output; the alternate generated trees and source/research files are excluded from the Jekyll build.

## What this change does

- Removes the `.nojekyll` bypass so GitHub Pages can apply `_config.yml` exclusions.
- Excludes the legacy/alternate site trees and model/source directories from the Pages artifact.
- Leaves the maintained root dashboard, its root assets, printable brief, and its public model-output data in the Pages artifact.
- Does **not** delete or rewrite existing Git objects, repository files, forks, caches, pull-request diffs, or previously served copies.

## Remaining exposure and limits

The GitHub repository itself remains a separate public surface from GitHub Pages. Excluding a directory from Jekyll does not remove it from GitHub's code browser, clone/download URLs, prior commits, forks, caches, or any copy already fetched by a third party. This checkout is based on one grafted commit, so the earlier pre-rounding commits are not available here to inspect or safely rewrite. A complete history scrub cannot be truthfully claimed from this branch. Rewriting the public default branch and asking GitHub to purge cached views would require a coordinated repository-administrator operation and may invalidate commit links or existing copies.

The user's request for a public Pages site and a guarantee that no household-derived information can be found in the public repository are in tension: a public repository exposes tracked source files independently of the Pages build. The currently implemented action limits what the website build publishes, but does not make the repository private or erase prior exposure.

## Verification and release gate

PR #19 was merged to `main`; the GitHub Pages Jekyll build and deploy completed successfully. The live root dashboard was fetched after deployment. Fetch attempts for the excluded alternate site paths failed, consistent with their exclusion; the Actions artifact itself could not be downloaded from this sandbox because its artifact blob host was inaccessible. Local checks pass: `python3 tools/build_site.py`, `python3 tools/check_site.py`, `node model/check_site.js`, and `git diff --check`. The private input file is absent, so the checker reports that its household-signature comparison was skipped; this is not a complete value-by-value privacy scan. The task remains **needs review** because tracked repository contents and older public history are still exposed.

## Recommended remediation sequence

1. Keep the Pages exclusions in place and recheck the deployed artifact after future changes.
2. Ask the repository owner to decide whether public repository visibility is compatible with the privacy requirement. Making it private can affect Pages availability and must be checked against the hosting plan.
3. If history removal is authorized, use a dedicated, reviewed history-rewrite and cache-removal plan across the default branch and all known refs; then check forks, PR diffs, Actions artifacts, Pages caches, and any downloaded copies. A force-push alone cannot recall copies already obtained by others.
4. For future household calculations, store raw inputs only in an offline or access-controlled private inventory and generate a publication export from synthetic/ranged inputs. Run a privacy scan on the final Pages artifact before every release.

This note intentionally avoids restating the exposed household values or exact property identifiers.
