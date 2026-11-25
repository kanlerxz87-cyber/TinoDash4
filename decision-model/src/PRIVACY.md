# PRIVACY.md — Privacy model for this repository

**Status: binding on every file in this repo. Read before adding anything.**

This repository is **public** and its GitHub Pages site is **public and indexed**. Therefore:

> **Nothing in this repository may contain personal information about the household, the
> decedent, the trust, the trustees, the properties, or the heirs — in any form that is
> specific enough to identify them.**

That is a stricter rule than "no names". Addresses, assessor parcel numbers (APNs), exact
assessed values, exact tax bills, exact rent rolls, and exact trust terms are all identifiers
when combined with a ZIP code and a dollar figure.

---

## 1. What must never appear here

| Category | Examples | Where it may live instead |
|---|---|---|
| Names | Household members, decedent, trustees, attorney, CPA, agent | Never collected by this repo |
| Street address / APN | Any parcel identifier | Private estate inventory (offline, `templates/`) |
| Exact assessed values & tax bills | The 13-year and 10-year series supplied by the household | Private model input file (offline) |
| Account numbers | Trust tax ID, brokerage, escrow, loan | Never collected by this repo |
| Exact dates of death / birth | — | Offline |
| Trust document text | Distribution standards, powers, remainder terms | Offline, in the attorney's file |
| Tenant / lease details | Tenant names, unit rents per tenant, deposit amounts | Offline |

## 2. Rounding policy (as requested, and hardened)

The household asked for **rounding to the nearest \$10**. That is implemented as the default:

* Every dollar figure rendered by the site is rounded to the **nearest \$10**.
* Every rate is rounded to **1 decimal place** (percent) or **2 decimals** where a 1-decimal
  rounding would hide a material step (transfer-tax tiers).
* No figure is ever rendered with more precision than the source supports.

**However, rounding to \$10 is not, by itself, anonymising for this dataset.** A factored base
year value rounded to the nearest \$10, combined with a ZIP code and a market value, is still a
short search. Only about a dozen 95014 parcels have that combination.

The reconciliation actually implemented:

* **The default build is `--round 10`.** That is what the household asked for, and it is what
  ships: all market values, rents, costs, taxes and projections render to the nearest \$10.
* **Parcel-unique figures are banded separately and structurally.** The two historic *assessed
  values* and the two historic *tax bills* never enter the model at full precision and are never
  rendered at full precision. They are carried as \$10,000 bands (`545,000–560,000`;
  `110,000–120,000`) and as effective-rate ranges. Rounding is not relied on to protect them.

The distinction, stated plainly: rounding a *market* estimate to \$10 protects nothing and is
also unnecessary, because thousands of parcels share it. Rounding a *tax-assessed* figure protects
nothing either, because a \$10 band is still unique to one parcel. So the second category is
banded by construction rather than by the display layer, and the display layer simply honours the
household's \$10 instruction everywhere else.

Stronger modes remain available:

```bash
python3 build.py --round 1000       # coarser market-value presentation
python3 build.py --round 10000      # coarsest: everything in $10,000 bands
```

## 3. What is published instead of private figures

Replace private figures with **household-supplied estimates**, clearly labelled:

| Private figure | Published as | Label |
|---|---|---|
| Cupertino value Nov 2026 | `$3,100,000` | Household estimate — unverified |
| Cupertino assessed value 2026 | `$550,000–$560,000` band | From household series, banded |
| Cupertino tax bill | **effective-rate range** `1.2%–1.4%` | Derived, banded |
| SF value Nov 2026 | `$1,800,000` | Household estimate — unverified |
| SF assessed value 2025 | `$110,000–$120,000` band | From household series, banded |
| SF tax bill | effective rate `2.0%–2.2%` | Derived — **flagged as anomalous** |
| SF rent (2 units) | `$7,150/month` → rounded `$7,150` | Household figure |

Rounding a *market* estimate (a \$3.1M house, a \$7,150 rent) does not create a privacy problem,
because thousands of parcels share it. Rounding a *tax-assessed* figure does, because it is
unique to one parcel. The distinction is applied throughout.

## 4. Pre-history / git hygiene

The repository was created with a single `Initial commit` whose only content was an 11-byte
`README.md`. **No personal data has ever been committed.** Verified in this session:

```text
fe3cad6 Initial commit        (README.md, 11 bytes: "# TinoDash4")
```

There is therefore no pre-rounding history to scrub — the first version of every data file in
this repository is already the rounded version. The rule for the future:

1. **Never commit a private figure, even transiently.** Git history is forever; a "temporary"
   commit of an exact assessed value is a permanent disclosure.
2. Keep exact inputs in an **untracked** local file. `.gitignore` blocks
   `private/`, `*.private.json`, `*.private.csv`, `inventory.local.*`.
3. If a private figure is ever committed by mistake, the fix is **history rewrite of that
   branch and force-push, then a GitHub support request to purge cached objects** — a normal
   `git rm` commit does **not** remove it. Log the incident in `COORDINATION.md`.

## 5. Prior public-data exposure — containment checklist

The household has previously shared figures in conversation. Containment actions:

- [x] Exact values are not reproduced in this repository (see §2).
- [x] No parcel identifiers are requested by any page or form on the site.
- [x] The site is **fully static**: no analytics, no third-party scripts, no fonts fetched from
      a CDN, no cookies, no forms that post anywhere. A visitor cannot be profiled, and there is
      no server-side log of their inputs.
- [x] The optional what-if calculator runs **entirely in the browser**; values are never sent.
- [ ] Confirm with the household whether the figures were ever posted publicly elsewhere
      (Reddit, Bogleheads, a tax forum). **Open item — see `site/questions.html`.**
- [ ] Consider whether the *combination* "Cupertino 95014, \$3.1M, inherited via trust,
      plus a 3-unit Outer Sunset property" is itself identifying in a small community. If so,
      switch the committed default to `--round 100000`. **Open item.**

## 6. Threat model this does not cover

Rounding and coding protect against **casual discovery and search indexing**. They do not
protect against an adversary who already knows the household and reads the site. If that is a
realistic threat, **do not publish the site** — run the generator locally and keep the output
in the untracked `site-private/` directory. GitHub Pages is public and cannot be made private
on a free plan; a private repo's Pages site is also public on most plans.

---

*Last reviewed: 2026-11-25 by session `6d864338`.*
