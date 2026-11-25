# TinoDash4 — inheritance decision analysis

Privacy-first analysis of an inherited property (Property A, Santa Clara County) versus an owned rental (Property B, San Francisco).
All figures are rounded to the nearest $10 and shown in 2026 dollars. Personal information is not published.

- `docs/` — static site for GitHub Pages (generated; do not hand-edit)
- `build/build_site.py` — builds `docs/` from `data/`
- `model/model.py` — projection model; writes `data/projections.json`
- `data/` — inputs, sources, flags
- `COORDINATION.md` — shared task board

Rebuild: `python3 model/model.py && python3 build/build_site.py`

Not legal or tax advice.

---

## Estate decision model (session 150580b0)

A separate decision model compares paths for Property A (inherited, Santa Clara County) and Property B (San Francisco): live, rent, sell, phased sale, mixed, or live then sell.

- Site: `estate-model/` (13 pages; open `estate-model/index.html`).
- Model: `tools/model.js` (also copied to `estate-model/assets/model.js` for the browser what-if page).
- Build: `node tools/build.js` writes `estate-model/*.html` and `estate-model/data/model.json`.
- Checks: `node tools/privacy_check.js` (this session's files) and `node tools/check_links.js`.
- Rules fixed before model output: `DECISION_RULES.md`.
- Figures are rounded to the nearest $10. Unverified values are flagged on `estate-model/flagged.html`.
