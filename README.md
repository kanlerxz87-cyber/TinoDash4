# Household Legacy decision dashboard

A privacy-first, static decision-support site for comparing inherited-home paths without publishing family identifiers or precise property / financial facts. The public dashboard uses neutral aliases (`Property A` / `Property B`), blank inputs for unverified values, official source links, and rounded calculator outputs.

## Local preview

Open `index.html` directly, or serve this directory with any static web server, for example:

```sh
python3 -m http.server 8000 --bind 0.0.0.0
```

The what-if calculator runs entirely in the browser. It does not use cookies, analytics, local storage, a server, external fonts, or network requests to submit inputs. Refresh the page to clear the form. Do not enter personal identifiers or sensitive account details.

## Publish with GitHub Pages

The GitHub Actions workflow in `.github/workflows/pages.yml` publishes the root directory after changes reach `main` (or can be run manually). It requires GitHub Pages to be configured for GitHub Actions in repository settings.

## Important limits

- This is not legal, tax, financial, investment, appraisal, insurance, or property-management advice.
- Current law is not a forecast of law in 2040–2050. Recheck official sources at transfer and filing dates.
- No supplied exact home value, ZIP, street address, property-tax history, rent, utility bill, or personal identity is reproduced.
- The calculator uses user-entered assumptions and tax estimates; it does not compute tax liability, Prop 19 eligibility, depreciation recapture, local transfer tax, or probability distributions.
- The 2026 San Francisco Measure H result is preliminary as of the last source check (November 25, 2026); confirm certification and implementation before modeling any parcel charge.

See [COORDINATION.md](COORDINATION.md) for the task log and verification record.
