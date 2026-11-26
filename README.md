# Inheritance decision dashboard

Two generated sites live in this repository, both published by the same Pages workflow. They were
built by different sessions from the same brief and were never reconciled, so read them as two
independent treatments of one question rather than as one product.

| Site | Where | How it is built |
| --- | --- | --- |
| Dashboard (root) | `index.html`, `pages/`, `assets/`, `data/` | `tools/build_site.py` from `data/model_outputs.json` |
| Decision workspace (archived, not tracked) | `private/archive/decision-workspace/` | `model/build.py` then `model/site.py` (20 pages) |
| Model + dashboard (archived, not tracked) | `private/archive/site/` | `model/build_model.py` then static HTML/JS; smoke-tested by `model/check_site.js` |

Both hold the household's figures only as rounded, anonymized output: every published dollar figure
is rounded to the nearest $10, and no address, parcel number or account number appears anywhere.

## Dashboard (repository root)

A privacy-first GitHub Pages site comparing paths for an inherited home (Property A) with an owned
rental (Property B): sell, park and phase in, rent, or live. Household figures are held internally
and never published; the site shows placeholders and results rounded to the nearest $10.

**Start here:** the dashboard is `index.html` (served at the repository's GitHub Pages address). A
printable one-page brief is `brief.pdf`; the print-ready HTML version is `brief.html`.

```
python3 model/model.py            # needs private/raw_inputs.json (gitignored, internal only)
python3 tools/build_site.py       # site from data/model_outputs.json and tools/content.py
python3 tools/build_brief_pdf.py  # brief.pdf (needs reportlab)
python3 tools/check_site.py       # root Pages-artifact privacy scan, row-link check, rounding, links
```

The site build does not need the private inputs. `check_site.py` scans the root Pages artifact (including
`brief.pdf`) for household signatures when the untracked private input file is available, and always
checks for forbidden identifiers, rounding, row sources, required content, and internal links. GitHub Pages
uses `_config.yml` to exclude alternate generated trees; repository contents remain independently public.

## Decision workspace (archived)

> Archived 2026-11-26: `decision-workspace/`, `decision-model/` and `site/` were untracked from git and moved to `private/archive/` (gitignored) because they contained household-specific figures and location labels. Their commands below now refer to that archive. Git history still contains earlier copies; see `PRIVACY_REMEDIATION.md`.


The same question modelled end to end: twelve paths (live / rent / sell / eight mixed) scored on one
set of assumptions, a 1,200-path block bootstrap over the 1928-2025 annual record, Prop 19 against
Prop 13 carry against full reassessment, and the open-questions, suggestions, flagged, comparables
and sources registers.

```
python3 model/build.py    # model -> decision-workspace/data/*.json
python3 model/site.py     # data + prose -> decision-workspace/*.html and assets/data.js
```

Standard library only, no network at run time, and deterministic: the Monte Carlo is seeded, so the
same tree always produces the same site. `model/site.py` runs the engine itself; the JSON is a
by-product, not an input. `decision-workspace/index.html` is the entry point (on Pages:
`/TinoDash4/decision-workspace/`).

### The three rules it is built on

**1. Privacy is mechanical, not careful.** Every household figure is rounded by `r10()`, and a
string-level scrubber rewrites any amount of three or more digits anywhere in the payload (notes,
captions, register text), so prose cannot leak an exact figure either. Published *rate cards* - a
per-CCF water charge, a per-$500 transfer-tax tier, a recorder's fee line - are left exact on
purpose, because they are public rates and not the household's numbers. `model/build.py` asserts both
directions at build time.

**2. A row without a source does not get published.** `simple_table()` appends a Source column to any
table whose builder did not declare one, so the invariant is enforced by the renderer rather than
remembered by the author. Links carry the document's short key and its verification status (`official`,
`academic`, `owner-supplied`, `unverified`). A figure with no official document behind it is shown as
`not verified`, never estimated.

**3. Narrative lives in code, not in HTML.** Every sentence quoting a number builds that number from the
model at write time, so the prose and the tables cannot drift apart. To change a statement, change the
constant and rebuild.

### Conventions worth knowing before editing

- Three tax systems are kept separate and never mixed in one table: estate tax at death, income tax on
  the gain, property tax on the assessment.
- No mortgage is modelled (open question Q-16). Adding one means a debt schedule in `engine.py`, not a
  new column.
- Rental losses are treated as suspended against rental income for a same-filing two-owner household.
- Marginal rates: CA ordinary 50.3% including the 1% mental-health surtax; federal LTCG 23.8% with NIIT;
  §1250 recapture 28.8% plus NIIT.
- Prop 19's factored base year value is set **once**, at the distribution of the estate, then grows at
  ≤2% a year. Re-capping it annually inflates the saving.
- Vacancy 5%; discount rate 3.5% real; `FINANCE_SPREAD = 0` because no financing is modelled.
- The Black-Swan and phased-investing pages are computed from the annual return record, so they move
  every January when the record gains a year.

## Coordination

See `COORDINATION.md` for the task board, handoff log, and verification record. Open items and
irregularities are on the *Flagged for Review* page of either site.

Not legal or tax advice.
