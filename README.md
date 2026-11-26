# Inheritance decision dashboard

The current GitHub Pages publication is the root dashboard, built by Jekyll from `main` at `/`.
`_config.yml` excludes the alternate generated sites and source trees from the Pages artifact. Those
files still exist in the public GitHub repository and its history; a Jekyll exclusion is not access
control and is not a history purge.

| Surface | Where | Publication status |
| --- | --- | --- |
| Dashboard | Root `index.html`, other root pages, `assets/`, `data/`, and `brief.pdf` | Published by GitHub Pages |
| Decision workspace | `decision-workspace/` | Excluded from Pages; still visible in public GitHub source/history |
| Alternate model + site | `decision-model/`, `site/`, `model/`, `tools/`, `research/` | Excluded from Pages; still visible in public GitHub source/history |

**Privacy status: partial containment, not an anonymization guarantee.** The public dashboard uses
Property A/B labels and rounded, derived outputs, but outputs based on household inputs may still be
sensitive or linkable to public records. Rounding to the nearest $10 does not by itself prove
anonymity. The public repository and its earlier commits/PRs also remain outside the Pages exclusion
boundary. See [`PRIVACY_REMEDIATION.md`](PRIVACY_REMEDIATION.md) and [`PRIVACY_REVIEW.md`](PRIVACY_REVIEW.md).

## Dashboard (repository root)

The dashboard compares choices for an inherited property and an already-owned rental property:
sell, park and phase in, rent, live, and mixed paths. The one-page brief is `brief.pdf`; its
print-ready HTML version is `brief.html`.

**Start here:** `index.html` (the repository's GitHub Pages root).

```
python3 model/model.py              # requires local private/raw_inputs.json (gitignored)
python3 tools/build_site.py         # root pages from rounded data/model_outputs.json
python3 tools/build_brief_pdf.py    # brief.pdf (needs reportlab)
python3 tools/check_site.py         # strict; requires the ignored local private input file
python3 tools/check_site.py --public-only  # clean-checkout/CI checks; not privacy clearance
```

The public site build does not need the private input file. Default strict mode compares redacted
patterns from `private/raw_inputs.json` against repository text/PDF files and fails closed if the
inventory is missing or unreadable; matched values are never printed. `--public-only` deliberately
skips exact private-value comparison so clean CI can run without household inputs, while still
checking restricted-token hashes across the repository, direct-identifier patterns on Pages files,
and root-output integrity. That skip is not privacy clearance, and neither mode proves rounded
outputs anonymous. See `PRIVACY_REVIEW.md` and the root site's *Flagged for Review* page.

## Decision workspace (`decision-workspace/`)

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
by-product, not an input. This workspace is currently excluded from Pages; its files remain public
through the repository browser and Git history.

### The three rules it is built on

**1. Privacy needs a release boundary and a local comparison.** The root Pages build excludes
alternate trees through `_config.yml`, but that affects Pages only—not public GitHub source or
history. Default strict mode requires an ignored local `private/raw_inputs.json` and fails closed if
it is absent. `--public-only` logs that exact comparison was skipped so clean CI can run, but it is
not a privacy sign-off. Matched private values are withheld from checker output; rounded results may
still be linkable and must not be described as anonymous.

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

See `COORDINATION.md` for the task board, handoff log, and verification record. Open analysis
items are on the root site's *Flagged for Review* page. Privacy/history limitations are summarized
in `PRIVACY_REMEDIATION.md` and `PRIVACY_REVIEW.md`.

Not legal or tax advice. Not a privacy guarantee.
