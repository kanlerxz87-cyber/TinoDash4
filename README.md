# Inheritance decision analysis (TinoDash4)

A privacy-first, source-checked comparison of paths for an inherited Cupertino-area house against an existing San Francisco property. Published as a static GitHub Pages site from `docs/`.

## What is here

- `model/model.js` - the decision model (pure JavaScript; used by the build and by the browser what-if page). Monthly simulation of seven paths, Monte Carlo over market regimes, stylised 1929/2008 entry shocks, and breakpoints.
- `data/` - source registry (`sources.json`), table rows with status (`tables.json`), flagged items (`flags.json`), timeline, glossary, anonymised inventory, criteria written before modelling (`criteria.json`), suggestions.
- `scripts/build.js` - builds every page in `docs/` and `docs/results.json`. Run `node scripts/build.js`.
- `scripts/app.js`, `scripts/style.css` - browser what-if controls and styles (copied into `docs/`).
- `docs/` - the published site (GitHub Pages).
- `COORDINATION.md` - task board and deployment record.

## Rules applied

- Personal information is excluded from the site; the household is described with placeholders (Property A, Property B).
- Every dollar figure is rounded to the nearest $10.
- A value that cannot be verified is left blank and listed on the Flagged for Review page; the model never infers a missing value.
- Each table row links to its source and carries a status (primary, secondary, owner, assumption, blank, conflict, preliminary).

## Build

```
node model/model.js   # loads without output
node scripts/build.js
```

Not tax, legal or investment advice. Consult an attorney and a CPA before acting on any path.
