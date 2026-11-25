# TinoDash4: inherited-property decision (privacy-first)

A static decision-analysis site comparing paths for an inherited home in Santa Clara County (Property A) and an existing home in San Francisco (Property B): live, rent, sell, phased sale, mixed, or live then sell.

- Site: `docs/` (served by GitHub Pages from `main` / `/docs`).
- Model: `tools/model.js` (also copied to `docs/assets/model.js` for the in-browser what-if page).
- Build: `node tools/build.js` writes `docs/*.html` and `docs/data/model.json`.
- Checks: `node tools/privacy_check.js` (personal identifiers) and `node tools/check_links.js` (internal links).
- Rules written before results: `DECISION_RULES.md`.
- Coordination board and log: `COORDINATION.md`.

Published figures are rounded to the nearest $10. Every verified value links to an official source. Unverified values are flagged on `docs/flagged.html`. Nothing on the site is personal advice.
