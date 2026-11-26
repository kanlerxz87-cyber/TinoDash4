# Privacy and publication notice

This repository and its GitHub Pages site are public. Property A and Property B are placeholders; no street address, parcel/APN, owner name, account number, tenant name, or postal code is intentionally included in the generated pages.

## Limits of the current protection

The model includes rounded, owner-supplied property estimates and general property characteristics in tracked source/data and in the public pages. Rounding to $10 does **not** make property-linked figures anonymous. Local jurisdiction names and official-source links also narrow the geography because the analysis covers local tax and housing rules. Treat the published model as public information, not as a private record.

The checked-in output is a static site. Its what-if controls run in the browser; they do not send values to a server. That does not prevent copying, indexing, screenshots, or access to GitHub's public source files and history.

## Controls currently used

- Use Property A / Property B placeholders; do not add personal names, addresses, APNs, parcel documents, birth dates, account identifiers, tenant identities, or lease-level records.
- Omit postal codes and hyper-local neighborhood names from site prose.
- Round household-supplied money figures to the requested $10 display step, and label them as unverified unless supported by an official record. Rounding is a formatting convention, not a privacy guarantee.
- Keep unverified inputs and legal uncertainties on the Flagged for Review page. Do not present owner estimates as official values.

## History and prior exposure

The checked-out repository is shallow at the current integration commit. It does not contain enough prior commits to verify the statement that the public Git history is free of pre-rounding inputs. This checkout also cannot remove data from earlier public commits, forks, caches, screenshots, or search indexes. A history-wide audit and any GitHub-side purge require a separately authorized repository-history operation; a normal follow-up commit cannot erase old objects.

The current branch includes a Jekyll configuration that excludes alternate generated sites and source directories from the Pages artifact; its deployed effect is still pending verification by the integration owner. Repository source files and history remain public on GitHub. This privacy pass removes postal codes and hyper-local neighborhood labels from the legacy `decision-model` site, but does not claim that all public source history or all property-linked estimates are private.

## Before adding or publishing new data

1. Do not commit private inventories, trust text, addresses, assessment notices, tax bills, leases, or exact parcel records.
2. Keep any detailed inventory and exact-value model offline and access-controlled. Do not add a private input file to Git.
3. Before a future public publish, run `python3 tools/check_site.py`. If `private/raw_inputs.json` is absent, the exact-value comparison is explicitly **skipped**; that run is not a full privacy verification.
4. If even the rounded estimates or local jurisdiction labels are sensitive, do not publish this model on public GitHub Pages; use a private, access-controlled deployment instead.

This notice is a candid statement of current limitations, not a promise that publication is risk-free.
