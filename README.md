# Inheritance decision dashboard

A privacy-first GitHub Pages site comparing paths for an inherited home (Property A) with an owned rental (Property B): sell, park and phase in, rent, or live. Household figures are held internally and never published; the site shows placeholders and results rounded to the nearest $10.

**Start here:** the dashboard is `index.html` (served at the repository's GitHub Pages address). A printable one-page brief is `brief.pdf`; the print-ready HTML version is `brief.html`.

## Rebuild

```
python3 model/model.py          # needs private/raw_inputs.json (gitignored, internal only)
python3 tools/build_site.py     # site from data/model_outputs.json and tools/content.py
python3 tools/build_brief_pdf.py  # brief.pdf (needs reportlab)
python3 tools/check_site.py     # privacy scan, row-link check, rounding, links; must pass before publishing
```

The site build does not need the private inputs. `check_site.py` scans every published file (including `brief.pdf`) for household values, zip codes, and location labels. It fails the build if any are found.

## Coordination

See `COORDINATION.md` for the task board, handoff log, and verification record. Open items and irregularities are on the *Flagged for Review* page.

Not legal or tax advice.
