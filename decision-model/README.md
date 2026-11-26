# Inherited-Home Decision Model

A privacy-first decision dashboard for one household question: **given a house in Santa Clara County
that will be inherited sometime between 2040 and 2050, and a three-unit rental building already
owned in San Francisco, what is the right thing to do with the house?**

Published site: **https://kanlerxz87-cyber.github.io/TinoDash4/decision-model/site/**

Everything here is anonymised. The two properties are **Property A** (Santa Clara County) and
**Property B** (San Francisco). There are no addresses, parcel numbers, owner names or
exact assessed values anywhere in this directory — see [src/PRIVACY.md](src/PRIVACY.md), which is
a binding rule for anything committed, not a disclaimer.

> This is one of several independent analyses in this repository. Everything it needs is inside
> this directory, and it writes to nothing outside it. It does not modify the integrated site at
> the repo root (owned by a later integration session) or any other session's output.

---

## Read this first

If you are the household, open the site and read **index.html** top to bottom. The first content
block is *what would change the answer* — written down before the figures, on purpose, so the
conclusion cannot be reverse-engineered from a projection.

If you are the attorney or the CPA, print **briefing-sheet.html**. It is one page, letter size,
and it is designed to be marked up in a meeting.

---

## What the model says

Under base assumptions — transfer in 2045, 30-year horizon, nominal, after tax, after transaction
costs, with imputed rent credited to every year of ownership — **selling at transfer and
diversifying wins**, by about $22.9M over holding and $24.8M over renting.

Two findings matter more than the headline:

1. **The Proposition 19 exclusion is worth far less than inherited-base folklore implies** for a
   2045 transfer (~$0.56M of terminal net worth, about 2.5% of the gap). The exclusion is a *cap*
   on reassessment, not an exemption from it, and by 2045 the house has grown far past the cap.
2. **Phasing the proceeds into the market only pays if a crash arrives in the first three years.**
   After that it is a pure cost of about −$2.8M (−7.3%). It is insurance, and it is worth buying
   only if the household would otherwise panic.

Neither of those is an opinion. Both are re-runnable:

```bash
cd src
python3 -c "from model import runner; print(runner.prop19_value())"
python3 -c "from model import runner; print(runner.phased_compare())"
```

---

## Layout

```
src/
  model/
    params.py    every number the model uses, with its source ID and status
    engine.py    one simulation: a path, a scenario, a horizon -> a ledger
    runner.py    comparisons, sensitivities, black-swan overlays, phasing analysis
  data/
    facts.json   the fact registry. status in {verified, secondary, unverified}
  sitegen.py     renders 21 static HTML pages. no framework, no JS needed
  assets/
    style.css    screen + print stylesheet
  tools/
    check_site.py  the gate: links, anchors, sources, personal-data smells, rounding
  build.py       build -> check -> publishable
  PRIVACY.md     the rule, not a disclaimer
site/            the built site (this is what GitHub Pages serves)
```

## Build

```bash
cd src
python3 build.py                       # build into ../site/, then check it
python3 build.py --round 1000          # coarser rounding
python3 tools/check_site.py ../site    # check without building
```

`build.py` refuses to finish if the checker finds an error. That is deliberate: this site is
public, and publishing an unchecked build is the one mistake here that cannot be undone.

No dependencies beyond the Python 3 standard library. No npm, no bundler, no build step that
needs the network.

### A note on `--out`

`sitegen.py` wipes its output directory before writing. During development, `--out ..` was passed
by mistake and deleted the working tree. The build now refuses to wipe any directory that is not
empty and does not already look like a previous build of this site. The guard is there because
the failure actually happened, not as defensive boilerplate.

## Rounding

All dollar figures are rounded to the nearest **$10**, as the household asked. A $10 step is
*not* anonymising for a market value, so parcel-unique **assessed values and tax bills are banded
to $10,000 by construction in `data/facts.json`**, not by the display layer. Statutory figures
that are exact by law (the $1,044,586 Prop 19 allowance, the $15,000,000 federal exclusion) stay
exact, because rounding a tax threshold would print a number that is not the law.
[src/PRIVACY.md](src/PRIVACY.md) explains the reasoning in full.

## Sources

Every row on the site carries a link to an official source, or says plainly that no official
source was located. Facts are tagged `verified`, `secondary` or `unverified` in
`data/facts.json`; the `unverified` ones are collected on **flagged.html** so they can be argued
with in one place rather than hunted for.

**Nothing here is legal, tax or investment advice.** It is a model, built to be wrong in public
so the wrong parts can be found. It is designed to be re-run annually — see the suggestions page
for the schedule.

## Known gaps, stated rather than hidden

- **reinvestment.html** — the equity/Treasury spread is an assumption, not an observation. It
  needs a forward-looking capital-market estimate from a named source.
- **decision-log.html** — ships empty. A decision log filled in by the person who built the model
  is not a decision log.
- **Household (`HH-*`) figures are all unverified** and printed as such. They are the household's
  own estimates, and the model is only as good as they are.
- **The 2045 Prop 19 allowance is unpublished.** It is modelled as three growth scenarios, and no
  single number is quoted for it.
