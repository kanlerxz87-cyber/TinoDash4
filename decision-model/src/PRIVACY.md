# PRIVACY.md — Privacy model for this repository

**Status: binding on every file in this repo. Read before adding anything.**
**Last revised: 2026-11-26 by session `75bcd077` (supersedes the 2026-11-25 revision by `6d864338`).**

This repository is **public** and its GitHub Pages site is **public and indexed**. Therefore:

> **Nothing in this repository may contain personal information about the household, the
> decedent, the trust, the trustees, the properties, or the heirs — in any form that is
> specific enough to identify them.**

That is stricter than "no names". Addresses, assessor parcel numbers (APNs), exact assessed
values, exact tax bills, exact rent rolls, exact trust terms, **ZIP codes**, **neighbourhood
names**, and **city-plus-ZIP combinations** are all identifiers when combined with a dollar figure.

---

## 1. What must never appear here

| Category | Examples | Where it may live instead |
|---|---|---|
| Names | Household members, decedent, trustees, attorney, CPA, agent | Never collected by this repo |
| Street address / APN | Any parcel identifier | Private estate inventory (offline) |
| ZIP codes | Any five-digit postal code for either property | Placeholders `[ZIP-A]` and `[ZIP-B]` only |
| Neighbourhood names | Any sub-city locality for either property | "Property B's neighbourhood" |
| City-level location | City name paired with a ZIP, or with a dollar figure | "Santa Clara County" and "San Francisco" are the only location labels used |
| Exact assessed values & tax bills | The 13-year and 10-year series supplied by the household | Private model input file (offline); banded only |
| Account numbers | Trust tax ID, brokerage, escrow, loan | Never collected by this repo |
| Exact dates of death / birth | — | Offline |
| Trust document text | Distribution standards, powers, remainder terms | Offline, in the attorney's file |
| Tenant / lease details | Tenant names, unit rents per tenant, deposit amounts | Offline |
| Contact details | E-mail addresses, phone numbers | Never in content. Commit metadata is covered in §4. |

The published-site scan (`src/tools/check_site.py`) enforces the ZIP, neighbourhood and city-label
rules with hashed tokens, so the identifiers themselves do not have to be written into the checker.

## 2. Rounding policy (as requested, and hardened)

The household asked for **rounding to the nearest \$10**. That is implemented as the default:

* Every household-derived dollar figure rendered by the site is rounded to the **nearest \$10**.
* Every rate is rounded to **1 decimal place** (percent) or **2 decimals** where a 1-decimal
  rounding would hide a material step (transfer-tax tiers).
* **Published statutory thresholds are quoted exactly, on purpose.** Examples: the Prop 19
  allowance of \$1,044,586 (BOE Letter To Assessors 2025/009) and the federal filing threshold.
  Rounding them would make them wrong, and they are public law, not household data. They sit
  in `class="quote"` or `class="exact"` spans so the checker can tell them apart.
* Rounding to \$10 is **not, by itself, anonymising.** A figure rounded to \$10 plus a ZIP code and a
  market value is still a short search. For that reason ZIP codes and neighbourhood names were
  removed entirely (see §5), not rounded.

The reconciliation actually implemented:

* **The default build is `--round 10`.** That is what the household asked for, and it is what ships.
* **Parcel-unique figures are banded separately and structurally.** The two historic assessed values and
  the two historic tax bills never enter the model at full precision and are never rendered at full
  precision. They are carried as \$10,000 bands and as effective-rate ranges.

Stronger modes remain available:

```bash
python3 build.py --round 1000       # coarser market-value presentation
python3 build.py --round 10000      # coarsest: everything in $10,000 bands
```

## 3. What is published instead of private figures

| Private figure | Published as | Label |
|---|---|---|
| Property A value, Nov 2026 | `$3,100,000` | Household estimate — unverified |
| Property A assessed value, 2026 | band (see model) | From household series, banded |
| Property A tax bill | **effective-rate range** | Derived, banded |
| Property B value, Nov 2026 | `$1,800,000` | Household estimate — unverified |
| Property B assessed value, 2025 | band | From household series, banded |
| Property B tax bill | effective rate range | Derived — **flagged as anomalous** |
| Property B rent (2 units) | `$7,150/month` | Household figure |

Rounding a *market* estimate (a \$3.1M house, a \$7,150 rent) is not itself a privacy problem,
because thousands of parcels share that value. Rounding a *tax-assessed* figure is not enough, because
it is unique to one parcel. The distinction is applied throughout.

## 4. Git history — audit result (2026-11-26)

**The 2026-11-25 statement that "no personal data has ever been committed" was wrong and is withdrawn.**
An audit of the full history (`git log --all -S`, after `git fetch --unshallow`) found:

| Finding | Where it lives in history | Severity |
|---|---|---|
| Exact household assessed values and tax bills (unrounded) | `16b095d` (`data/inputs.json`, `docs/inputs.html`); `5026b1d` (`pages/executive-summary.html`) | **Critical** — parcel-unique |
| ZIP codes and city-plus-ZIP labels | `5026b1d`, `0d79d3a`, `e23a4ec`, `3e6c258`, `453c515`, `2e8a6db` and several later board commits | **High** — removed from current files, still in history |
| Neighbourhood name | `0d79d3a`, `3e6c258`, `453c515` | High — removed from current files, still in history |
| A personal e-mail address in commit author metadata | Many commits on `main` (author field, not content) | Medium — metadata, not site content |

**Status:** current files are scrubbed (this revision). History is **not** rewritten. A rewrite
requires a force-push to `main`, which this session is not permitted to perform, and it requires the
owner's explicit approval. The owner's decision, the exact commands, and the caveat that cached copies
and forks cannot be recalled are recorded in `COORDINATION.md` under session `75bcd077` (item P-3).

The rule for the future:

1. **Never commit a private figure, even transiently.** A "temporary" commit of an exact assessed value
   is a permanent disclosure.
2. Keep exact inputs in an **untracked** local file. `.gitignore` blocks `private/`, `*.private.json`,
   `*.private.csv`, `inventory.local.*`.
3. Keep author e-mail private with `git config user.email` set to the GitHub no-reply address for new commits.

## 5. Prior public-data exposure — containment checklist

The household has previously shared figures in conversation. Containment actions:

- [x] **Session 75bcd077 (2026-11-26):** ZIP codes, the neighbourhood name, and city-plus-ZIP labels removed
      from every generated page, the generator, the facts register, the README and this file. Replaced by
      `[ZIP-A]`, `[ZIP-B]`, "Santa Clara County", "San Francisco", and "Property A/B".
- [x] **Session 75bcd077:** the privacy checker now flags any ZIP, neighbourhood or city-plus-ZIP label by hashed token.
- [x] Exact *assessed* values and tax bills are not reproduced in current files (see §2–3).
- [x] No parcel identifiers are requested by any page or form on the site.
- [x] The site is **fully static**: no analytics, no third-party scripts, no cookies, no forms that post anywhere.
- [x] The optional what-if calculator runs **entirely in the browser**; values are never sent.
- [ ] **Owner decision (open):** whether to rewrite git history (§4). Until decided, the exact figures and
      ZIP codes remain visible in past commits of the public repository.
- [ ] **Owner decision (open):** whether the combination "Property A in Santa Clara County, inherited via trust,
      plus a three-unit building in San Francisco, with these dollar figures" is identifying enough to
      require `--round 100000` as the public default. The residual risk is recorded on the Flagged page.
- [ ] Confirm with the household whether the figures were ever posted publicly elsewhere
      (forum, social media, tax forum). **Open item — see `site/questions.html`.**

## 6. Threat model this does not cover

Rounding and coding protect against **casual discovery and search indexing**. They do not protect against an
adversary who already knows the household and reads the site. If that is a realistic threat, **do not publish
the site** — run the generator locally and keep the output in an untracked directory. GitHub Pages is public and
cannot be made private on a free plan; a private repo's Pages site is also public on most plans.

---

*Last reviewed: 2026-11-26 by session `75bcd077`.*
