# Household Legacy decision dashboard

A privacy-first, static decision-support site for comparing paths for an anticipated inherited home alongside an already-owned property. The public dashboard uses neutral aliases (`Property A` / `Property B`), blank inputs for unverified values, official source links, and rounded calculator outputs.

## Local preview

Open `index.html` directly, or serve this directory with a static server:

```sh
python3 -m http.server 8000 --bind 0.0.0.0
```

The scenario calculator runs in the browser. It does not use cookies, analytics, local storage, a server, external fonts, or network requests to submit inputs. Refresh to clear entries. Do not enter personal identifiers or sensitive account details.

## Publish with GitHub Pages

The workflow in `.github/workflows/pages.yml` uploads only the static root site after changes reach `main` (or on manual dispatch). Configure GitHub Pages to use GitHub Actions. Verify a successful Actions deployment before sharing a live URL.

## Privacy and legacy-history notice

Earlier committed versions of this repository contained property-specific details and financial inputs in legacy pages and data files. Those files were removed from the current tree, but their previous commits may remain visible in GitHub history, caches, forks, or clones. The current dashboard does not reproduce those values. See [COORDINATION.md](COORDINATION.md) for the privacy finding and limitations. A current-tree deletion does not purge old commit history or third-party copies.

## Important limits

- Not legal, tax, financial, investment, appraisal, insurance, or property-management advice.
- Current law is not a forecast of law in 2040–2050. Recheck official sources at transfer and filing dates.
- No private parcel identifier or owner-specific property value, rent, utility bill, or tax history is published in the current site.
- The calculator uses user-entered assumptions and tax estimates; it does not compute tax liability, Prop 19 eligibility, depreciation recapture, local transfer tax, or probability distributions.
- The 2026 San Francisco Measure H result was preliminary as of the last source check (November 25, 2026); confirm certification and implementation before modeling any parcel charge.
