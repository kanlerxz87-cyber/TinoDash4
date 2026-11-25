# TinoDash4 — inherited-property decision workspace

A decision model and a static site for one question: *what should be done with the inherited
Cupertino house (Property A), given the household already owns a three-unit building in San
Francisco (Property B)?* The transfer is modelled at 2045. Twelve paths — live in it, rent it,
sell it at the death, sell it later, move into B, stage the proceeds — are scored on the same
assumptions, and every number on the site is generated from those assumptions rather than typed.

Nothing here is financial or legal advice. It is a workspace that makes the assumptions, the
governing rules and the open questions explicit enough to be argued with.

## Run it

No dependencies beyond CPython 3.11+ (standard library only) and no network access at run time.

```bash
python3 model/build.py    # model -> data/*.json (privacy-scrubbed, safe to publish)
python3 model/site.py     # data + prose -> *.html and assets/data.js (20 pages)
open index.html           # or: python3 -m http.server -d . 8000
```

Both scripts are deterministic: the 1,200-simulation Monte Carlo is seeded, so the same tree
always produces the same site. `model/site.py` runs the engine itself; it does not read
`data/*.json`, which is why the JSON is a by-product rather than an input.

## Layout

| Path | What it is |
| --- | --- |
| `model/inputs.py` | every constant, rate, threshold and source key |
| `model/engine.py` | the twelve path definitions, the year-by-year walk, taxes, Monte Carlo |
| `model/projections.py` | projections, Prop 19 comparison, carrying costs, rent diagnostics |
| `model/registers.py` | the non-numeric registers: laws, deadlines, criteria, open questions, flags, glossary |
| `model/history.py` | the 1928-2025 annual return series used by the risk pages |
| `model/build.py` | writes `data/*.json` |
| `model/site.py` | writes the site |
| `model/site_lib.py` | page chrome, formatters, the source-link renderer, the privacy filter |
| `model/site_pages.py`, `model/site_pages2.py` | the page builders |
| `assets/` | the stylesheet and the (deliberately small) scripts the built site loads |
| `data/` | generated JSON, published so a reviewer can check a number without running anything |

`*.html` at the root and `assets/data.js` are build output and are not committed. The published
site is rebuilt in CI — see `.github/workflows/pages.yml` — and served from the `site` branch.

## The three rules this project is built on

**1. Privacy is mechanical, not careful.** Every published dollar figure that belongs to the
household is rounded to $10 by `r10()`, and a string-level scrubber rewrites any amount of three
or more digits found anywhere in the payload (notes, captions, register text) so that no prose
can leak an exact figure either. Published *rate cards* — a per-CCF water charge, a per-$500
transfer-tax tier, a recorder's fee schedule line — are deliberately left exact, because they are
public rates and not the household's numbers. The build asserts both of these.

**2. A row without a source does not get published.** `simple_table()` adds a Source column to any
table that did not build its own, so the invariant is enforced by the renderer. Links carry the
document's short key and its verification status (`official`, `academic`, `owner-supplied`,
`unverified`). A figure that could not be read from an official document in this pass is shown as
`not verified` rather than estimated; there are no placeholders.

**3. Narrative lives in code, not in HTML.** Every sentence that quotes a number builds that
number from the model at write time, so the prose and the tables cannot drift apart. To change a
statement, change the constant and rebuild.

## Conventions worth knowing before editing

- Three tax systems are kept separate and never mixed in one table: estate tax at death, income
  tax on the gain, property tax on the assessment.
- No mortgage is modelled (open question Q-16). Adding one means adding a debt schedule to
  `engine.py`, not a new column.
- Rental losses are treated as suspended against rental income for a same-filing two-owner
  household, not as a current-year offset.
- Marginal rates used: CA ordinary 50.3% including the 1% mental-health surtax; federal LTCG
  23.8% including NIIT; §1250 recapture 28.8% plus NIIT.
- Prop 19's factored base year value is set **once**, at the distribution of the estate, and then
  grows at ≤2% a year. It is not re-capped each year — that mistake inflates the saving.
- Vacancy is 5%; the discount rate is 3.5% real; `FINANCE_SPREAD = 0` because no financing is
  modelled.
- The Black-Swan and phased-investing pages are computed from the 1928-2025 annual record, so they
  change every January when the record gains a year.

## Recheck cadence

`recheck.html` lists the ten documents that must be re-read, with what each one moves. Until
Property A's own tax bill, deed and preliminary title report are read, the values carried here are
derived from the household's memory of the bills, and the flagged register says so.
