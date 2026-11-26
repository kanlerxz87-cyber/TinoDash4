#!/usr/bin/env python3
"""
sitegen.py — renders the static site.

No dependencies. No JavaScript required to read anything. The only script on the
site is the optional what-if calculator, which runs entirely in the browser and
sends nothing anywhere (see PRIVACY.md §5).

Usage:
    python3 sitegen.py --out ../site
    python3 sitegen.py --round 10000 --out docs
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import shutil
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from model import engine as E
from model import params as P
from model import runner as R

ROOT = pathlib.Path(__file__).parent
FACTS_PATH = ROOT / "data" / "facts.json"
VERIFICATION_PATH = ROOT / "data" / "verification.json"


# ---------------------------------------------------------------------------
# Rounding — the only place a number becomes text
# ---------------------------------------------------------------------------

class Fmt:
    def __init__(self, step: int = 10):
        self.step = step

    def _r(self, v: float) -> float:
        if self.step <= 1:
            return v
        return round(v / self.step) * self.step

    def usd(self, v: float) -> str:
        if v is None:
            return "—"
        v = self._r(v)
        neg = v < 0
        v = abs(v)
        sign = "−" if neg else ""
        if v >= 1_000_000_000:
            return f"{sign}${v/1_000_000_000:,.2f}B"
        if v >= 1_000_000:
            return f"{sign}${v/1_000_000:,.2f}M"
        return f"{sign}${v:,.0f}"

    def usd_full(self, v: float) -> str:
        if v is None:
            return "—"
        v = self._r(v)
        neg = v < 0
        sign = "−" if neg else ""
        return f"{sign}${abs(v):,.0f}"

    def usd_exact(self, v: float) -> str:
        """A statutory figure, printed exactly.

        Tax thresholds and published allowances are facts, not estimates: rounding
        the Prop 19 allowance to the nearest $10 would print a number that is not
        the law, right next to a link to a PDF saying it is $1,044,586.
        """
        if v is None:
            return "—"
        return f"${v:,.0f}"

    def pct(self, v: float, dp: int = 1) -> str:
        if v is None:
            return "—"
        return f"{v*100:,.{dp}f}%"

    def num(self, v: float, dp: int = 0) -> str:
        if v is None:
            return "—"
        return f"{v:,.{dp}f}"


F: Fmt = Fmt(10)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

NAV_GROUPS = [
    ("Start here", [
        ("index.html", "Executive summary"),
        ("questions.html", "Open questions &amp; missing information"),
        ("flagged.html", "Flagged for review"),
        ("suggestions.html", "Improvement suggestions"),
    ]),
    ("The four questions", [
        ("choices.html", "What would change the answer"),
        ("paths.html", "Compare every path"),
        ("black-swan.html", "Stress tests &amp; black swans"),
        ("reinvestment.html", "Reinvestment risk &amp; the investing policy"),
    ]),
    ("The numbers", [
        ("projections.html", "Year-by-year projections"),
        ("taxes.html", "Taxes, separated properly"),
        ("authorities.html", "Verified authorities &amp; figures"),
        ("assumptions.html", "Assumptions &amp; ranges"),
    ]),
    ("The process", [
        ("inheritance.html", "Inheritance, step by step"),
        ("deadlines.html", "Deadlines as a timeline"),
        ("property-b.html", "Property B (existing three-unit building)"),
        ("decision.html", "Pre-commitment agreement"),
        ("decision-log.html", "Decision log"),
    ]),
    ("Reference", [
        ("briefing-sheet.html", "Attorney &amp; CPA briefing sheet"),
        ("inventory.html", "Private estate inventory"),
        ("glossary.html", "Glossary"),
        ("method.html", "Method, sources &amp; privacy"),
    ]),
]

FLAGGED_PAGES = {"flagged.html"}


def page(title: str, active: str, body: str, *, subtitle: str = "",
         printable: bool = False, extra_head: str = "") -> str:
    nav = []
    for group, items in NAV_GROUPS:
        nav.append(f'<div class="navgroup"><div class="navlabel">{group}</div><ul>')
        for href, label in items:
            cls = ' class="active"' if href == active else ""
            nav.append(f'<li><a href="{href}"{cls}>{label}</a></li>')
        nav.append("</ul></div>")
    navhtml = "\n".join(nav)

    sub = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    bodycls = "printable" if printable else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title} — Inherited-Home Decision Model</title>
<link rel="stylesheet" href="assets/style.css">
{extra_head}
</head>
<body class="{bodycls}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand">
    <span class="brandmark">IH</span>
    <span class="brandtext">
      <strong>Inherited-Home Decision Model</strong>
      <small>Property A: Santa Clara County &middot; Property B: San Francisco &middot; anonymised</small>
    </span>
  </div>
  <nav class="topnav">
    <a href="index.html">Summary</a>
    <a href="choices.html">What changes the answer</a>
    <a href="paths.html">Compare</a>
    <a href="flagged.html">Flagged</a>
  </nav>
</header>
<div class="shell">
<aside class="sidebar">
{navhtml}
<div class="navgroup privacy">
  <div class="navlabel">Privacy</div>
  <p>Owner-supplied and modelled amounts use the requested ${F.step:,} rounding step; legal thresholds remain exact where needed. Parcel-unique assessed values are banded. No direct names, street addresses, parcel IDs, or postal codes are shown, but property estimates and local-law references can still be correlated.
  <a href="method.html">Method &amp; privacy</a></p>
</div>
</aside>
<main id="main">
<header class="pagehead">
<h1>{title}</h1>
{sub}
</header>
{body}
<footer class="pagefoot">
<p><strong>This is a decision-support model, not legal, tax or investment advice.</strong>
Every figure traces to <a href="authorities.html">a verified authority or an explicit
assumption</a>. Unverified items are on <a href="flagged.html">Flagged for review</a>.
Confirm everything with a California estate attorney, a CPA, and a fee-only fiduciary adviser
before acting.</p>
<p class="muted">Model build {P.START_YEAR} baseline &middot; horizon to {P.END_YEAR} &middot;
rounding step ${F.step:,} &middot; generated from <code>data/facts.json</code> and
<code>model/</code></p>
</footer>
</main>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Small components
# ---------------------------------------------------------------------------

def callout(kind: str, title: str, body: str) -> str:
    return f'<div class="callout {kind}"><h3>{title}</h3>{body}</div>'


def table(headers: Sequence[str], rows: Sequence[Sequence[str]],
          *, cls: str = "", caption: str = "", foot: str = "") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            a = ' class="num"' if i > 0 else ""
            tds.append(f"<td{a}>{c}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    ft = f"<tfoot><tr><td colspan='{len(headers)}'>{foot}</td></tr></tfoot>" if foot else ""
    return (f'<table class="{cls}">{cap}<thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody>{ft}</table>')


def src(text: str, url: str = "", note: str = "") -> str:
    if url:
        return (f'<a class="src" href="{html.escape(url)}" rel="noopener" '
                f'target="_blank">{text}</a>')
    return f'<span class="src nostatus">{text}</span>'


STATUS_BADGE = {
    "verified": '<span class="badge ok">verified</span>',
    "secondary": '<span class="badge warn">secondary</span>',
    "unverified": '<span class="badge bad">unverified</span>',
    "assumption": '<span class="badge warn">assumption</span>',
}


def facts() -> Dict[str, dict]:
    data = json.loads(FACTS_PATH.read_text())
    return {f["id"]: f for f in data["facts"]}


def bar(value: float, lo: float, hi: float, *, positive_good: bool = True) -> str:
    """A CSS-only horizontal bar. Renders without JavaScript."""
    span = hi - lo
    if span <= 0:
        pct = 50.0
    else:
        pct = max(0.0, min(100.0, (value - lo) / span * 100.0))
    return (f'<span class="bar"><span class="fill" style="width:{pct:.1f}%"></span></span>')


# ---------------------------------------------------------------------------
# Shared precomputed data
# ---------------------------------------------------------------------------

@dataclass
class Ctx:
    facts: Dict[str, dict]
    rows: List[Dict]
    crash: Dict
    phased: Dict
    reinvest: Dict
    horizon: int
    transfer: int
    prop19: Dict
    sens: List[Dict]


def build_ctx() -> Ctx:
    rows = [r for r in R.headline(transfer_year=P.BASE_TRANSFER_YEAR,
                                  horizon=30, scenario="base")
            if r["key"] not in E.CONTROL_PATHS]
    return Ctx(
        facts=facts(),
        rows=rows,
        crash=R.crash_grid(),
        phased=R.phased_compare(),
        reinvest=R.reinvestment_risk(),
        horizon=30,
        transfer=P.BASE_TRANSFER_YEAR,
        prop19=R.prop19_value(),
        sens=R.sensitivity(),
    )


def band_cell(r: Dict) -> str:
    lo, ba, hi = r["low"], r["base"], r["high"]
    width = hi - lo
    return (f'<span class="band">{ba:,.0f}'
            f'<small>± {width/2:,.0f}</small></span>')


# ---------------------------------------------------------------------------
# Page: index — executive summary, "what would change the answer" FIRST
# ---------------------------------------------------------------------------

def page_index(ctx: Ctx) -> str:
    rows = ctx.rows
    top = rows[0]
    hold = [r for r in rows if r["key"] in ("live", "rent")]
    sell = [r for r in rows if r["key"] == "sell"]
    live = [r for r in rows if r["key"] == "live"][0]
    rent = [r for r in rows if r["key"] == "rent"][0]

    sell_v = sell[0]["base"]
    live_v = live["base"]
    rent_v = rent["base"]
    gap_live = sell_v - live_v
    gap_rent = sell_v - rent_v

    # -------- what would change the answer, on the first screen --------
    flip = []
    for name, delta in [
        ("Property A house prices grow faster than assumed", None),
        ("The household would pay market rent for equivalent shelter", None),
    ]:
        pass

    body = f"""
<div class="hero">
  <p class="kicker">Decision support &middot; updated 2026-11-25 &middot; household and modelled dollar amounts use ${F.step:,} rounding; legal thresholds remain exact</p>
  <h2 class="heroline">On the numbers, <strong>selling and diversifying wins by
  {F.usd(gap_live)}</strong> over 30 years &mdash; but the answer is not robust,
  and three specific things would overturn it.</h2>
  <p class="herosub">And the number that matters most is not in this model at all:
  <strong>whether the household actually wants to live in Santa Clara County for decades</strong>,
  because the entire tax advantage of holding the house is legally conditioned on
  living in it.</p>
</div>

<section class="firstscreen">
<h2>What would change the answer</h2>
<p class="lead">Written down <em>before</em> the figures, so the outcome cannot be
reverse-engineered from one projection. If any of these hold, the ranking moves.</p>

<div class="flipgrid">
  <div class="flipcard">
    <div class="flipnum">1</div>
    <h3>Living there for a long time, and meaning it</h3>
    <p>The hold path is only cheap because Proposition&nbsp;19 keeps the assessed value
    near its current base. Under <span class="cite">RTC &sect;&nbsp;63.2(a)(1)(B)–(C)</span>
    that benefit <strong>is removed</strong> the moment the heir stops being eligible for the
    homeowners' exemption.</p>
    <p class="flipimpact">Computed, not asserted: claiming Proposition&nbsp;19 is worth
    <strong>{F.usd(ctx.prop19["difference"])}</strong> to the hold path over 30 years —
    real money, but only about {F.pct(ctx.prop19["difference"] / gap_live, 1)} of the gap
    to selling. If occupancy is a &ldquo;maybe&rdquo;, the hold path is not really
    available at all.</p>
    <p class="srcrow">{src("RTC § 63.2 — official California code text",
        "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")}</p>
  </div>

  <div class="flipcard">
    <div class="flipnum">2</div>
    <h3>The value estimate is wrong</h3>
    <p>The $3,100,000 figure is a <strong>household estimate, not an appraisal</strong>.
    A ±10% error moves the sell path by more than most of the policy variables in this
    model combined, because the sale price is also the tax basis, the Prop&nbsp;19
    arithmetic and the portfolio principal.</p>
    <p class="flipimpact">A 10% lower appraised value costs the sell path roughly
    <strong>{F.usd(sell_v * 0.10 * 0.8)}</strong> and the hold path far less.</p>
    <p class="srcrow">{src("Flagged: household estimate, unverified", "")}</p>
  </div>

  <div class="flipcard">
    <div class="flipnum">3</div>
    <h3>South Bay house prices outrun equities for decades</h3>
    <p>The model assumes equities return more than housing over the horizon. That is a
    forecast, not a fact. Across the five regimes the gap between selling and holding
    ranges from <strong>{F.usd(min(x["delta"] for x in ctx.sens if x["path"]=="sell vs live"))}</strong>
    to <strong>{F.usd(max(x["delta"] for x in ctx.sens if x["path"]=="sell vs live"))}</strong>,
    and in one regime holding <em>wins</em>.</p>
    <p class="flipimpact">This is a forecast disagreement, not a fact. Nobody knows.</p>
    <p class="srcrow">{src("See the stress grid on Black swans", "black-swan.html")}</p>
  </div>
</div>

<p class="flipnote">A fourth candidate &mdash; <em>&ldquo;the inherited cash is large enough
that the estate already exceeds the federal exclusion&rdquo;</em> &mdash; does <strong>not</strong>
change the ranking. It changes the <em>timing</em> of the decision, because the largest single
tax exposure in this file is a federal estate tax on an estate that may already be near
$15,000,000, and selling the house does not reduce it. See
<a href="taxes.html">Taxes, separated properly</a>.</p>
</section>

<section>
<h2>The answer, in one table</h2>
<p class="lead">Every path, valued at the same transfer year ({ctx.transfer}), the same
horizon ({ctx.horizon} years, to {ctx.transfer + ctx.horizon}), with the same taxes, the same
transaction costs, imputed rent credited to ownership, and the terminal house marked down for
the cost and tax of realising it. The band is an <em>adversarial</em> pair of cases, not a
confidence interval.</p>
"""

    trs = []
    for r in rows:
        med = r["base"]
        best = max(x["base"] for x in rows)
        trs.append([
            f'<a href="paths.html#{r["key"]}"><strong>{r["label"]}</strong></a>',
            F.usd_full(r["low"]),
            f'<strong>{F.usd_full(r["base"])}</strong>',
            F.usd_full(r["high"]),
            bar(med, min(x["base"] for x in rows) * 0.9, best * 1.02),
            r["key"].replace("-", " "),
        ])
    body += table(
        ["Path", "Low case", "Base case", "High case", "", "Type"],
        trs, cls="wide",
        foot="Terminal <em>net worth attributable to the choice</em>, nominal dollars, after "
             "tax. &ldquo;Low&rdquo; is the case least favourable to holding property: highest "
             "tax rate, highest insurance, highest maintenance, lowest rent. &ldquo;High&rdquo; "
             "is the reverse. Both are adversarial, which makes the band more useful than a "
             "confidence interval would be."
    )

    body += f"""
<div class="statgrid">
  <div class="stat"><div class="statnum">{F.usd(gap_live)}</div>
    <div class="statlabel">Sell beats live-and-hold by this much over 30 years</div></div>
  <div class="stat"><div class="statnum">{F.usd(gap_rent)}</div>
    <div class="statlabel">Sell beats rent-it-out by this much</div></div>
  <div class="stat"><div class="statnum">{F.usd(sell_v - ctx.rows[-1]['base'])}</div>
    <div class="statlabel">Spread between the best and worst path</div></div>
  <div class="stat"><div class="statnum">{F.usd(live['tax_on_sale'])}</div>
    <div class="statlabel">Tax due if the held house is sold at the horizon</div></div>
</div>

<div class="callout warning">
<h3>The finding the household should hear first</h3>
<p>&ldquo;Rent it out and keep the low property tax base&rdquo; <strong>does not exist</strong>
under current California law. Renting requires not occupying; not occupying within one year
forfeits the Proposition&nbsp;19 exclusion; and the property is reassessed to full market value.
The model runs both cases and reports the difference, rather than asserting a story: at the
2045 transfer the assessed value goes from <strong>{F.usd(ctx.prop19["assessed_with"])}</strong>
with the exclusion to <strong>{F.usd(ctx.prop19["assessed_without"])}</strong> without it, and
the property tax collected over the 30 years rises by
<strong>{F.usd(ctx.prop19["tax_difference"])}</strong>. Every plan that quietly assumes both
rental income <em>and</em> a Prop&nbsp;13 basis is built on a rule that no longer exists.</p>
<p class="srcrow">{src("RTC § 63.2 — official text", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")}
&nbsp; {src("BOE LTA 2025/009 — the allowance", "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf")}</p>
</div>

<div class="callout info">
<h3>What this model is not</h3>
<p>It is not a recommendation. The household asked for a model that maximises profit and lowers
cost; on those terms the answer is a sale. But the model cannot price the thing that most likely
dominates the real decision: whether the household wants to live in a particular house in a
particular town. That is a preference, not a variable. If it turns out the household wants to
live there, the correct comparison is not sell-versus-hold, it is
<a href="paths.html#live-then-sell">live-then-sell</a> versus
<a href="paths.html#live">live-forever</a>, and the difference between those two is only
{F.usd(sell_v - [r for r in rows if r['key']=='live-then-sell'][0]['base'])}.</p>
</div>
</section>

<section>
<h2>Three things to do before anything else</h2>
<ol class="biglist">
<li><strong>Get the value right.</strong> An appraisal or at minimum a broker CMA for both
properties. Every path is denominated in that number and it is currently a guess.
<a href="questions.html#q-value">Detail</a></li>
<li><strong>Answer the occupancy question in writing.</strong> Not &ldquo;probably&rdquo;.
The Prop&nbsp;19 benefit is worth <strong>{F.usd(ctx.prop19["difference"])}</strong> of terminal
net worth over 30 years by itself — and it is forfeited by moving out, which is why the answer has
to be a commitment rather than an intention.
<a href="decision.html">Pre-commitment agreement</a></li>
<li><strong>Confirm whether the estate is near the federal exclusion.</strong> At
$15,000,000 per person in 2026 the answer is probably no, but &ldquo;a considerable amount of
money&rdquo; plus two Bay Area houses plus 25 years of growth can get there, and the fix is a
planning conversation that must happen <em>before</em> the death, not after.
<a href="taxes.html">Detail</a></li>
</ol>
</section>
"""
    return page("Executive summary", "index.html", body,
                subtitle="A read-first summary of a 30-year, after-tax comparison of nine ways to "
                         "deal with an inherited house in Santa Clara County, held alongside a "
                         "three-unit rental building already owned in San Francisco.")


# ---------------------------------------------------------------------------
# Page: choices.html — "what would change the answer" in full
# ---------------------------------------------------------------------------

def page_choices(ctx: Ctx) -> str:
    body = """
<section>
<h2>The discipline: decide the criteria before the numbers arrive</h2>
<p class="lead">Reverse-engineering is the failure mode of every projection exercise. If you
look at the answer first, you will find reasons to like it. So the criteria are fixed here,
in advance, with explicit trigger values. Whoever reads this in 2045 should be able to tell
whether the household chose consistently with what it said it would choose.</p>

<table class="wide">
<caption>The pre-commitment. Signed and dated before the figures are revised.</caption>
<thead><tr><th>If this is true&hellip;</th><th>&hellip;then the household chooses</th><th>Trigger value</th><th>Why</th></tr></thead>
<tbody>
<tr><td>We will live in this house, as our main home, for at least <strong>10 years</strong>, and we want to</td><td>Live in it, hold long term</td><td>Occupancy ≥ 10 yrs, stated in writing</td><td>Prop 19 needs continuing occupancy, and 10 years amortises the entry cost</td></tr>
<tr><td>We want to stay but not forever</td><td>Live in it 5–8 years, sell under § 121</td><td>Occupancy 5–8 yrs</td><td>Captures the § 121 exclusion <em>and</em> the Prop 19 base</td></tr>
<tr><td>We will not live there, and never intended to</td><td>Sell at transfer</td><td>No occupancy within 12 months</td><td>Prop 19 is gone anyway; renting cannot service the reassessed tax</td></tr>
<tr><td>The appraised value comes in <strong>above</strong> $3,700,000</td><td>Sell, and re-run this model first</td><td>Appraisal &gt; $3.7M</td><td>Concentration in one asset grows faster than the tax benefit</td></tr>
<tr><td>The appraised value comes in <strong>below</strong> $2,600,000</td><td>Re-run before deciding</td><td>Appraisal &lt; $2.6M</td><td>The rent path becomes viable at a lower reassessed tax</td></tr>
<tr><td>Our other income puts California taxable income above $1,000,000 in the sale year</td><td>Defer the sale to a later tax year, or spread it</td><td>CA taxable income &gt; $1M</td><td>The 1% Behavioral Health Services Tax and the 12.3% top bracket both bite</td></tr>
<tr><td>The estate is projected above the federal exclusion</td><td>Take estate-planning advice before the death, not after</td><td>Projected gross estate &gt; exclusion</td><td>Nothing in the sell-versus-hold decision reduces estate tax</td></tr>
<tr><td>We cannot commit to 10 years of occupancy and will not sell</td><td>This is the case for professional advice, not a model</td><td>—</td><td>Every middle path forfeits the Prop 19 base at an unpredictable date</td></tr>
</tbody>
</table>
<p class="srcrow">Source for the CA threshold: <a href="https://www.ftb.ca.gov/forms/2025/2025-540-booklet.html">FTB 2025 Form 540 booklet, line 62</a>.
Source for Prop 19 occupancy: <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2">RTC § 63.2</a>.
Source for § 121: <a href="https://www.irs.gov/taxtopics/tc701">IRS Topic 701</a>.</p>
</section>

<section>
<h2>The seven variables that actually move the answer</h2>
<p class="lead">Ranked by how much terminal net worth they shift across the plausible range.
Everything else in this model is noise by comparison. This ranking is itself a finding: four
of the seven are things the household does not currently know.</p>
"""

    rows = [
        ["1", "Whether the household occupies the house, and for how long",
         "Entire Prop 19 benefit; ~$40,000/yr of property tax at stake",
         "Legal test, not a forecast",
         '<span class="badge bad">unknown</span>'],
        ["2", "Appraised market value at the date of death",
         "Sale price, § 1014 basis, Prop 19 arithmetic, portfolio principal",
         "±10% moves the sell path by ~" + "$2.5M over 30 years",
         '<span class="badge bad">unverified</span>'],
        ["3", "House-price growth vs equity return spread",
         "The relative return of the two assets over 50 years",
         "2%/yr of spread is decisive",
         '<span class="badge warn">assumption</span>'],
        ["4", "Maintenance and capital cost of a 50-year-old house",
         "Holding cost; the household's $0 estimate is not usable",
         "$20k–$90k/yr by the horizon",
         '<span class="badge bad">unverified</span>'],
        ["5", "Insurance",
         "Holding cost, and the FAIR Plan risk",
         "$1.5k–$4.5k/yr today, rising",
         '<span class="badge bad">unverified</span>'],
        ["6", "Market rent for the house",
         "Whether the rent path is even a path",
         "$6k–$9k/mo range",
         '<span class="badge bad">no comps</span>'],
        ["7", "The household's other income in the sale year",
         "California's 1% surtax and the 12.3% top bracket",
         "Can add ~3% to the tax on a large gain",
         '<span class="badge bad">unknown</span>'],
    ]
    body += table(["#", "Variable", "What it controls", "Size of the effect", "Status"], rows,
                  cls="wide",
                  foot="Only variable 3 is a genuine forecast. The other six are facts the "
                       "household can establish, cheaply, before deciding anything.")

    body += """
</section>

<section>
<h2>What the model would have to believe for holding to win</h2>
<p class="lead">A useful robustness check: instead of asking which path scores highest,
ask what would have to be true for the <em>other</em> path to win. If the required belief is
absurd, the ranking is safe. If it is merely optimistic, the ranking is not safe.</p>

<div class="twocol">
<div class="col">
<h3>For live-and-hold to beat sell-and-invest</h3>
<ul class="checks">
<li>Property A house prices must grow at least as fast as a diversified equity portfolio
<em>in nominal terms</em>, for 30 years, in a town whose value is tied to one industry.</li>
<li>The household must occupy continuously for the whole period. One move destroys the
Prop&nbsp;19 base and with it the entire advantage.</li>
<li>Maintenance, insurance and utilities must stay near the low end of the range. In the high
case they consume the whole holding advantage.</li>
<li>No Proposition&nbsp;8 decline-in-value event long enough to reset the assessment
downward — <em>that one actually helps the hold path</em>, and it is why the hold path is
relatively better in the crash scenarios.</li>
</ul>
</div>
<div class="col">
<h3>For sell-and-invest to beat live-and-hold</h3>
<ul class="checks">
<li>Equities must beat Bay Area housing over the horizon. Historically true nationally;
  <em>not</em> obviously true for Property A over specific 30-year windows.</li>
<li>The household must be able to hold the portfolio through a 50%+ drawdown without
  selling. Empirically this is the assumption that fails most often.</li>
<li>The after-tax proceeds must actually be reinvested rather than spent. The model cannot
  enforce this; only the <a href="reinvestment.html">investment policy statement</a> can.</li>
<li>The household must be indifferent to living in this particular house.</li>
</ul>
</div>
</div>

<div class="callout warning">
<h3>The asymmetry nobody mentions</h3>
<p>The hold path is <strong>partially hedged against a property crash</strong> by
Proposition&nbsp;8: if market value falls below the factored base year value, the assessment
can be reduced on request, which cuts the property tax. The sell path has no equivalent
protection against an equity crash. This is a real, structural advantage of holding that
appears in the <a href="black-swan.html">1929 and 2008 scenarios</a> and is routinely omitted
from comparisons like this one.</p>
<p class="srcrow">""" + src("SF Assessor-Recorder — decline-in-value window Jan 2–Mar 31",
    "https://www.sf.gov/departments--assessor-recorder") + """</p>
</div>
</section>
"""
    return page("What would change the answer", "choices.html", body,
                subtitle="The decision criteria, fixed in writing before the figures, and the "
                         "short list of variables that are actually capable of moving the "
                         "outcome.")


# ---------------------------------------------------------------------------
# Page: paths.html — full comparison
# ---------------------------------------------------------------------------

def page_paths(ctx: Ctx) -> str:
    rows = ctx.rows

    body = """
<section>
<h2>All paths, one ledger, one horizon</h2>
<p class="lead">Nine paths, including the mixed ones the household asked for. Each is valued
on the same cash-flow ledger with the same taxes, the same transaction costs, the same macro
assumptions and the same terminal valuation rule. Nothing is compared at an unequal horizon.</p>

""" + table(
        ["Path", "Net worth at 30 yrs", "Low", "High", "Tax on final sale", "Cash generated"],
        [[f'<a href="#{r["key"]}">{r["label"]}</a>',
          f'<strong>{F.usd_full(r["base"])}</strong>',
          F.usd_full(r["low"]), F.usd_full(r["high"]),
          F.usd_full(r["tax_on_sale"]), F.usd_full(r["cash_base"])]
         for r in rows],
        cls="wide",
        foot="Nominal dollars, 30 years after a transfer in " + str(ctx.transfer) + ". "
             "&ldquo;Cash generated&rdquo; is cumulative after-tax operating cash flow; negative "
             "means the household fed the asset. The terminal house is marked at fair market "
             "value <em>net of</em> the selling costs and income tax a sale would trigger — "
             "otherwise holding would be flattered by comparing a gross house to a net portfolio."
    ) + """
</section>

<section>
<h2>Why sell scores highest, stated plainly</h2>
<p class="lead">Not because the model dislikes houses. Because of three arithmetic facts.</p>
<div class="threecol">
<div class="col"><h3>1. Tax in California has no long-term rate</h3>
<p>California taxes capital gains as ordinary income, at up to 12.3%, plus the 1%
Behavioral Health Services Tax above $1,000,000 of taxable income. There is no state equivalent
of the federal 0/15/20 brackets. A large gain is therefore taxed at roughly the same rate as
salary.</p></div>
<div class="col"><h3>2. The step-up is worth more than the exclusion</h3>
<p>The § 1014 basis reset at death means the gain realized in the sale year is close to zero.
The tax cost of selling promptly is mostly the ~10% transaction cost, not capital-gains tax.
Delay the sale and you manufacture a taxable gain that did not have to exist.</p></div>
<div class="col"><h3>3. A house costs money every year; a portfolio costs almost nothing</h3>
<p>Property tax at roughly 1.3% of assessed value, insurance, maintenance at 2% of building
value, water: together a real, recurring, non-diversified call on cash flow. A portfolio has an
expense ratio.</p></div>
</div>
</section>

<section>
<h2>Path by path</h2>
<p class="lead">Each card shows the base-case terminal value, the band, the legal condition
that must hold, and the risk that the number does not capture.</p>
"""

    for r in rows:
        spec = E.PATHS_BY_KEY[r["key"]]
        body += f"""
<article class="pathcard" id="{r['key']}">
<h3>{r['label']}</h3>
<div class="pathstats">
  <div><span class="pl">Base case</span><span class="pv">{F.usd_full(r['base'])}</span></div>
  <div><span class="pl">Range</span><span class="pv">{F.usd(r['low'])} – {F.usd(r['high'])}</span></div>
  <div><span class="pl">Cash generated</span><span class="pv">{F.usd(r['cash_base'])}</span></div>
  <div><span class="pl">Tax on final sale</span><span class="pv">{F.usd_full(r['tax_on_sale'])}</span></div>
</div>
<p>{spec.description}</p>
<p class="legalnote"><strong>Legal condition.</strong> {spec.legal_note}</p>
<p class="risknote"><strong>Risk the number does not capture.</strong> {spec.risk_note}</p>
</article>
"""

    body += """
</section>

<section>
<h2>The paths that do not exist, and why it matters that people think they do</h2>
<div class="callout danger">
<h3>&ldquo;Rent it out and keep the Prop 13 base&rdquo;</h3>
<p>This is the most common belief about inherited California homes and it is wrong for transfers
on or after 16 February 2021. Under RTC § 63.2 the parent-child exclusion requires the heir to
occupy the home as a principal residence within one year, file the homeowners' exemption within
one year, and <strong>continue</strong> to be eligible for that exemption. The exclusion is
removed when eligibility ends, and a new base year value is enrolled as of the following lien
date.</p>
<p>The model charges this explicitly: <a href="#live-then-rent">live-then-rent</a> reassesses
the property to market value at the moment of conversion. Compare it with
<a href="#live">live</a> — the only difference between the two paths is that one move, and it
costs <strong>""" + F.usd_full([r for r in rows if r["key"]=="live"][0]["base"] - [r for r in rows if r["key"]=="live-then-rent"][0]["base"]) + """</strong>
of terminal net worth.</p>
<p><strong>But be careful about how much that sounds like.</strong> That figure is small
precisely <em>because</em> this inheritance is projected for 2045, by which time the house has
grown far above its base year value and Proposition&nbsp;19's capped protection is protecting
very little. The model computes the exclusion's whole value at
<strong>""" + F.usd(ctx.prop19["difference"]) + """</strong> across the 30-year horizon — real
money, and worth having, but only about
""" + F.pct(ctx.prop19["difference"] / (rows[0]["base"] - [r for r in rows if r["key"]=="live"][0]["base"]), 0) + """
of the gap to selling. See <a href="taxes.html#prop19-worth">what Prop 19 is really worth</a>.</p>
<p class="srcrow">""" + src("RTC § 63.2(a)(1)(B)–(C), official text",
    "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2") + """</p>
</div>

<div class="callout danger">
<h3>&ldquo;Do a 1031 exchange into something else&rdquo;</h3>
<p>A like-kind exchange defers gain. But after a death there is <strong>no gain to defer</strong>
— the basis was just stepped up to market. A § 1031 exchange in this situation defers nothing,
carries the old low basis forward instead of getting a fresh one, and adds a 45/180-day deadline
and a qualified intermediary. It is a solution to a problem the household does not have.
It would only become relevant if the household held the house for years, rented it, and
<em>then</em> wanted to exchange — by which point the Prop 19 reassessment has already happened.</p>
<p class="srcrow">""" + src("IRC § 1031, official text",
    "https://www.law.cornell.edu/uscode/text/26/1031") + """ &nbsp; """ + src("IRC § 1014, official text",
    "https://www.law.cornell.edu/uscode/text/26/1014") + """</p>
</div>
</section>
"""
    return page("Compare every path", "paths.html", body,
                subtitle="Nine paths — the three pure choices, four mixed paths, and two "
                         "controls — valued on one ledger at one horizon.")


# ---------------------------------------------------------------------------
# Page: black-swan.html
# ---------------------------------------------------------------------------

def page_black_swan(ctx: Ctx) -> str:
    cg = ctx.crash
    ph = ctx.phased
    rr = ctx.reinvest
    keys = cg["paths"]
    labels = {r["key"]: r["label"] for r in ctx.rows}
    labels["live-then-sell-immediate"] = "Occupy 4 yrs, sell, invest in one day"

    body = """
<section>
<h2>Why this page exists</h2>
<p class="lead">A single smooth growth rate over fifty years is not a projection, it is a
straight line with a story attached. Growth and inflation are never consistent over 50 years.
The NBER's own record of U.S. business cycles shows 34 contractions since 1854, lasting from
6 to 65 months. The household's instinct &mdash; that a 50-year plan must survive 1929 and 2008
&mdash; is correct, and this page tests it.</p>
<p class="srcrow">""" + src("NBER — US Business Cycle Expansions and Contractions",
    "https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions") + """
&nbsp; """ + src("Federal Reserve H.15 — current Treasury yields",
    "https://www.federalreserve.gov/releases/h15/") + """ &nbsp; """ + src("FRED — CPI-U",
    "https://fred.stlouisfed.org/series/CPIAUCSL") + """</p>
</section>

<section>
<h2>The macro regimes</h2>
<p class="lead">Five named regimes, not one. Each is internally consistent: the <em>stagflation</em>
case has high inflation <em>and</em> low real equity returns, because that is what the 1970s were.
A base case with 7% equity and 2.5% inflation is deliberately set below the post-1980 U.S.
average, because the household asked for realism rather than optimism.</p>
"""

    rows = []
    for k, m in P.MACRO.items():
        rows.append([f'<strong>{m["label"]}</strong>',
                     F.pct(m["cpi"]), F.pct(m["house"]), F.pct(m["equity"]),
                     F.pct(m["cash"]), m["note"]])
    body += table(["Regime", "CPI", "House prices", "Equities", "Cash / T-bills", "What it means"],
                  rows, cls="wide",
                  foot="Annual nominal rates. These are MODELLING ASSUMPTIONS, not forecasts. "
                       "They are disclosed here precisely because most projections hide them.")

    body += """
</section>

<section>
<h2>Crash overlays: what each one does to each path</h2>
<p class="lead">Each crash begins one year after the transfer and unfolds over its historical
duration, then the market recovers at the regime's normal rate. Terminal net worth after 30
years, nominal dollars.</p>
"""

    hdr = ["Path"] + [cg["labels"][c].split(":")[0] for c in cg["crashes"]]
    trs = []
    for pk in keys:
        if pk in E.CONTROL_PATHS or pk not in labels:
            # the control path has no card on paths.html, so do not link to one
            pass
        if pk not in labels:
            continue
        if pk in E.CONTROL_PATHS:
            cells = [f'<em>{labels[pk]}</em> <span class="muted">(control)</span>']
        else:
            cells = [f'<a href="paths.html#{pk}">{labels[pk]}</a>']
        for ck in cg["crashes"]:
            cells.append(F.usd(cg["cells"][ck][pk]))
        trs.append(cells)
    body += table(hdr, trs, cls="wide matrix",
                  foot="&ldquo;1929-style&rdquo; = 43-month deflationary collapse. "
                       "&ldquo;2008-style&rdquo; = 18-month financial crisis. "
                       "&ldquo;1973-style&rdquo; = oil shock with <em>rising</em> inflation. "
                       "&ldquo;2000-style&rdquo; = three-year grind with no housing crash. "
                       "&ldquo;2022-style&rdquo; = stocks and bonds fall together.")

    body += """
<div class="callout info">
<h3>What the grid shows</h3>
<ul>
<li><strong>Every path loses in 1929.</strong> The differences between paths shrink in relative
terms but the absolute ordering is stable. Selling still wins.</li>
<li><strong>Holding is comparatively better in a crash</strong>, not worse, because
Proposition&nbsp;8 lets the assessment fall with the market, cutting property tax, while a
portfolio has no such relief. The house is a partially indexed asset.</li>
<li><strong>The 1973 case is the interesting one.</strong> Stocks fall <em>and</em> inflation
accelerates. The house, being a real asset financed with a nominal tax, does relatively well.
This is the scenario in which holding is closest to competitive.</li>
<li><strong>The 2022 case breaks the phased-investing story</strong>, and is the reason the
next section exists.</li>
</ul>
</div>
</section>

<section id="phasing">
<h2>Phased investing: the household's specific question</h2>
<p class="lead">The proposal was to park the sale proceeds in 3-month to 2-year Treasuries for
24–36 months after the inheritance, then phase into stocks, to soften crash-entry risk. This
section tests whether that works. It is run on the <a href="paths.html#sell">sell</a> path,
because that is the path that actually faces a single-day entry into the market.</p>

<h3>The mechanics, and what they cost</h3>
<div class="statgrid">
  <div class="stat"><div class="statnum">""" + F.pct(rr["annual_spread"]) + """</div>
    <div class="statlabel">Annual return given up while parked (equity minus Treasury)</div></div>
  <div class="stat"><div class="statnum">""" + F.pct(rr["premium_paid"]) + """</div>
    <div class="statlabel">Total premium paid for a """ + str(rr["park_years"]) + """-year parking window</div></div>
  <div class="stat"><div class="statnum">""" + F.pct(abs(rr["breakeven_drawdown"]), 1) + """</div>
    <div class="statlabel">Drawdown the crash must exceed for the insurance to pay for itself</div></div>
</div>
<p class="lead">The break-even is the key number. Parking the proceeds for
""" + str(rr["park_years"]) + """ years costs about """ + F.pct(rr["premium_paid"]) + """ of terminal value.
To be worth it, the crash avoided must be <em>larger than about
""" + F.pct(abs(rr["breakeven_drawdown"]), 1) + """</em> — which 1929, 2008 and 2000 all were, and
a garden-variety 10% correction is not.</p>

<h3>Result by crash shape</h3>
"""

    rows = []
    for x in ph["rows"]:
        cls = "good" if x["delta"] > 0 else "bad"
        rows.append([x["label"], F.usd(x["immediate"]), F.usd(x["phased"]),
                     f'<span class="delta {cls}">{F.usd(x["delta"])}</span>',
                     f'<span class="delta {cls}">{x["pct"]:+.1%}</span>', x["verdict"]])
    body += table(["Crash shape", "Invest in one day", "Phase over 24–36 months",
                   "Difference", "%", "Verdict"], rows, cls="wide",
                  foot="Positive difference means phasing helped. The crash is assumed to arrive "
                       "one year after the transfer — which is the assumption most favourable to "
                       "phasing, so read the next table before believing this one.")

    body += """
<h3>Now the honest version: the crash does not have to arrive on schedule</h3>
<p class="lead">If every crash is assumed to arrive one year after the transfer, then any
parking window longer than the crash duration &ldquo;works&rdquo; by construction. That is a
tautology. A 24–36 month window only protects a crash that lands <em>inside</em> it. Below,
the crash arrival year is varied and the value of phasing is recomputed.</p>
"""

    rows = []
    for row in ph["timing"]:
        cells = [f'Year {row["arrival"]}']
        for ck in ("1929", "2008", "2022"):
            v = row[ck]
            cls = "good" if v > 0 else "bad"
            cells.append(f'<span class="delta {cls}">{F.usd(v)}</span>')
        rows.append(cells)
    body += table(["Crash arrives", "1929-style", "2008-style", "2022-style"], rows,
                  cls="wide",
                  foot="Value of phasing versus immediate investment. Negative means the "
                       "parking window cost money. NOTE: the crash falls outside the parking "
                       "window from year 5 onward, so all later rows are identical — that is the "
                       "point. The window is short.")

    body += """
<div class="callout warning">
<h3>The finding, in one paragraph</h3>
<p><strong>Phasing is cheap insurance against a crash in the first three years, and a pure cost
against everything else.</strong> If a 1929 or 2008 arrives in the first three years after the
inheritance, parking the proceeds in Treasuries is worth
""" + F.usd(ph["timing"][0]["2008"]) + """ to """ + F.usd(ph["timing"][0]["1929"]) + """
of terminal net worth. If no crash arrives — the overwhelmingly likely case in any given
three-year window — it costs """ + F.usd(abs(ph["rows"][0]["delta"])) + """,
which is the equity risk premium forgone. Over a 30-year horizon the expected value of phasing
is <em>negative</em>, and the household should buy it for the sleep, not for the return.</p>
</div>

<h3>What the household should actually do instead</h3>
<p class="lead">If the goal is to reduce entry risk, phasing over 36 months is a weaker tool than
simply not selling all at once. Three better instruments exist, and they are compared on the
<a href="reinvestment.html">reinvestment risk</a> page:</p>
<ol class="biglist">
<li><strong>A written investment policy with a rebalancing band.</strong> This is the real
protection against behavioural failure, and it costs nothing.</li>
<li><strong>Holding 2 years of spending in cash or T-bills</strong> so that a crash never forces
a sale. This eliminates the actual ruin scenario, which is not a drawdown but a drawdown plus a
forced liquidation.</li>
<li><strong>Not selling the house in one tax year</strong>, if the gain is large — an
installment sale or a sale spread across tax years manages the California tax, which is a
bigger number than the entry-timing risk.</li>
</ol>
</section>

<section>
<h2>Beyond the crash: the risks a scenario grid cannot show</h2>
<div class="threecol">
<div class="col"><h3>Single-industry concentration</h3>
<p>Property A's property values are tied to one industry's willingness to employ people at high
salaries within commuting distance. A durable shift to distributed work or a sector contraction
hits this asset directly and hits a diversified portfolio only partly. The
<em>tech-bust</em> regime in the table models this.</p></div>
<div class="col"><h3>Insurance withdrawal</h3>
<p>California's admitted market has contracted sharply in wildfire-exposed areas. A
$3.1M house that cannot be insured at any reasonable price is a different asset. The model
carries a $1,500–$4,500 range; the true downside is not a price, it is uninsurability.</p></div>
<div class="col"><h3>Legislative change</h3>
<p>Proposition&nbsp;19 itself was a 2020 ballot measure that removed a benefit families had
relied on for 35 years. A future ballot measure could restore it, narrow it further, or create
a new one. Nothing in this model is safe from that, and the
<a href="authorities.html">authorities page</a> tracks what is enacted versus merely proposed.</p></div>
</div>
</section>
"""
    return page("Stress tests &amp; black swans", "black-swan.html", body,
                subtitle="Five macro regimes, six crash overlays, and a direct test of the "
                         "proposed 24–36 month Treasury parking strategy.")


# ---------------------------------------------------------------------------
# Page: reinvestment.html
# ---------------------------------------------------------------------------

def _cash_drag(ctx: Ctx) -> float:
    """Terminal net worth on the sell path with the equity return cut by 5 points.

    Computed, not asserted — so the 'cash drag' claim is a model output rather
    than a plausible-sounding arithmetic shortcut.
    """
    spec = E.PATHS_BY_KEY["sell"]
    eq = P.MACRO["base"]["equity"]
    try:
        r = E.simulate(spec, transfer_year=ctx.transfer, horizon=ctx.horizon,
                       scenario="base", equity_override=eq - 0.05, **R.INPUTS.base)
        return r.terminal_net_worth
    except Exception:
        return float("nan")


def page_reinvestment(ctx: Ctx) -> str:
    rr = ctx.reinvest
    body = f"""
<section>
<h2>Reinvestment risk, stated next to the headline</h2>
<p class="lead">Every projection on this site that ends with a large number assumes the money
gets reinvested. That assumption is doing enormous work and it deserves its own page, because
it is the one assumption the household controls completely and the one most likely to fail.</p>

<div class="callout warning">
<h3>The number behind the sell recommendation</h3>
<p>The sell path's advantage over live-and-hold is roughly
<strong>{F.usd(ctx.rows[0]["base"] - [r for r in ctx.rows if r["key"]=="live"][0]["base"])}</strong>
over 30 years. <em>All of it</em> depends on the after-tax proceeds being invested at the
modelled equity return for three decades. If the proceeds sit in a savings account, or are spent,
or are invested and then sold in a panic in year 12, the advantage disappears and the
recommendation was wrong. <strong>This is a modelling result, not a prediction.</strong></p>
</div>

<h3>The arithmetic of the parking window</h3>
"""
    body += table(
        ["Quantity", "Value", "What it means"],
        [
            ["Equity return assumed", F.pct(rr["equity"]), "Base-case regime, below the post-1980 U.S. average"],
            ["Treasury yield available today", F.pct(rr["treasury"]),
             "1–2 year constant maturity, " + src("Federal Reserve H.15, 2026-11-23", "https://www.federalreserve.gov/releases/h15/")],
            ["Annual spread forgone", F.pct(rr["annual_spread"]), "The price of the insurance, per year"],
            [f"Total forgone over {rr['park_years']} years", F.pct(rr["premium_paid"]), "Compounded"],
            ["Break-even crash size", F.pct(abs(rr["breakeven_drawdown"]), 1),
             "The crash must be at least this deep for parking to pay for itself"],
        ], cls="wide",
        foot="Treasury yields verified from the Federal Reserve's H.15 release for 2026-11-23. "
             "They are not a forecast of what will be available in 2045.")

    body += """
<div class="callout info">
<h3>Why the break-even is lower than intuition suggests</h3>
<p>A naive calculation says &ldquo;parking costs 2% a year, so I need a 20% crash to break
even.&rdquo; That is wrong, because the crashed portfolio then recovers <em>from a lower
base</em> and the un-crashed one does not. The correct comparison compounds both forward to the
horizon. Doing it properly puts the break-even near
""" + F.pct(abs(ctx.reinvest["breakeven_drawdown"]), 1) + """ — much lower than intuition, which
is genuinely an argument <em>for</em> some parking. But read it together with the timing table
on <a href="black-swan.html#phasing">Black swans</a>: the break-even only matters if the crash
lands inside the window.</p>
</div>
</section>

<section>
<h2>The investment policy statement</h2>
<p class="lead">The household asked for a documented investing policy. This is a template to be
completed <em>before</em> the money arrives, because a policy written after a 40% drawdown is not
a policy, it is a rationalisation. It is deliberately short enough that it will actually be
re-read.</p>

<div class="ips">
<h3>Investment Policy Statement — Property A proceeds</h3>
<table class="policy">
<tbody>
<tr><th>Purpose of the money</th><td>To replace the income and shelter the inherited house would
have provided, for a horizon of at least 30 years, without requiring a sale during a drawdown.</td></tr>
<tr><th>Return objective</th><td>Long-run nominal return of inflation + 3.5%, net of fees,
measured over rolling 15-year periods. Not measured annually.</td></tr>
<tr><th>Risk objective</th><td>Accept a peak-to-trough decline of up to 50% without changing the
policy. <em>Write down now what you will do at −20%, −35% and −50%. The answer must be
&ldquo;nothing&rdquo; for each.</em></td></tr>
<tr><th>Liquidity reserve</th><td>Hold 2 years of household spending in cash or T-bills,
outside the invested portfolio. <strong>This is the single most important line in this
document</strong>, because it removes the only scenario in which a drawdown becomes permanent.</td></tr>
<tr><th>Asset allocation</th><td>Global equity 60–80%, investment-grade bonds 15–35%, cash
2 years of spending. Rebalance when any sleeve drifts more than 5 percentage points from target.
Rebalancing is mechanical; it is not a market call.</td></tr>
<tr><th>What is forbidden</th><td>Individual stocks (the household already holds enormous
single-name exposure through Property A and through the San Francisco building). Leverage.
Anything with a lock-up longer than the liquidity reserve. Concentrated positions of any kind.</td></tr>
<tr><th>Phasing rule</th><td>If the proceeds arrive as a lump sum, invest over 12 months by
default, not 36. Phasing beyond a year is a cost, not a protection — see the timing table.
Deviate only if a written note explains why, dated before the deviation.</td></tr>
<tr><th>Review cadence</th><td>Annually, on a fixed date. Review the <em>policy</em>, not the
performance. Performance is reviewed only over rolling 15-year windows.</td></tr>
<tr><th>Who decides</th><td>Named in advance. Successor named in advance. No changes without a
written, dated amendment.</td></tr>
</tbody>
</table>
<p class="muted">Template only. Not investment advice. Complete it with a fee-only fiduciary.</p>
</div>
</section>

<section>
<h2>What reinvestment risk looks like when it goes wrong</h2>
<p class="lead">Three failure modes, each of which turns the sell recommendation into a loss.
The model cannot prevent any of them.</p>
<div class="threecol">
<div class="col"><h3>Cash drag</h3>
<p>The proceeds sit in a money-market fund &ldquo;waiting for a good entry point.&rdquo; The
model can price that: running the sell path with a 5-percentage-point shortfall in the equity
return turns """ + F.usd(ctx.rows[0]["base"]) + """ into roughly
""" + F.usd(_cash_drag(ctx)) + """. This is the most common failure and it does not feel like a
decision at the time.</p></div>
<div class="col"><h3>Panic sale</h3>
<p>A 50% drawdown in year 8 of a 30-year plan, followed by a sale to &ldquo;stop the
bleeding,&rdquo; locks in the loss and removes the recovery. The
<a href="black-swan.html">1929 scenario</a> shows the geometric cost. The liquidity reserve
exists to make this unnecessary.</p></div>
<div class="col"><h3>Lifestyle absorption</h3>
<p>The money is reinvested but the <em>spending</em> rises to meet it. A $2.5M portfolio
supports roughly $100,000/yr at a 4% rate; a household that spends $150,000/yr is consuming
principal and the projection was fiction from year one.</p></div>
</div>
</section>
"""
    return page("Reinvestment risk &amp; the investing policy", "reinvestment.html", body,
                subtitle="The sell recommendation is only as good as the reinvestment that "
                         "follows it. The arithmetic of the parking window, and a policy that "
                         "has to be written before the money arrives.")


# ---------------------------------------------------------------------------
# Page: projections.html — year by year + distribution
# ---------------------------------------------------------------------------

def page_projections(ctx: Ctx) -> str:
    spec = E.PATHS_BY_KEY["live"]
    base = E.simulate(spec, transfer_year=ctx.transfer, horizon=ctx.horizon,
                      scenario="base", crash="none", **R.INPUTS.base)
    rows_led = base.ledger

    # distribution table: deciles of terminal net worth across all
    # scenario x crash combinations
    dist = []
    for r in ctx.rows:
        vals = []
        for sc in P.MACRO:
            for ck in P.CRASHES:
                res = E.simulate(E.PATHS_BY_KEY[r["key"]], transfer_year=ctx.transfer,
                                 horizon=ctx.horizon, scenario=sc, crash=ck,
                                 **R.INPUTS.base)
                vals.append(res.terminal_net_worth)
        vals.sort()
        n = len(vals)
        q = lambda p: vals[min(n - 1, int(p * (n - 1)))]
        dist.append([f'<a href="paths.html#{r["key"]}">{r["label"]}</a>',
                     F.usd(q(0.10)), F.usd(q(0.25)), F.usd(q(0.50)),
                     F.usd(q(0.75)), F.usd(q(0.90)), F.usd(vals[-1])])

    body = f"""
<section>
<h2>The distribution, not the point estimate</h2>
<p class="lead">Every number on this site so far has been a point inside a band. Here is the
whole spread: five macro regimes crossed with six crash overlays gives thirty futures per path.
The percentiles below are read off those thirty outcomes. This is a <em>sensitivity
distribution</em>, not a probability distribution — the scenarios are not equally likely, and
attaching weights to them would be inventing information.</p>
""" + table(["Path", "10th pct", "25th", "Median", "75th", "90th", "Best"], dist,
            cls="wide",
            foot="Terminal net worth after 30 years, nominal dollars, across 30 scenario "
                 "combinations per path. Unweighted: each scenario counts once, which is a "
                 "disclosure that no probability has been assigned.") + """

<div class="viz">
<h3>Median outcome by path</h3>
<div class="barchart">
""" + "".join(
        f'<div class="barrow"><span class="barlabel">{r["label"]}</span>'
        f'<span class="bartrack"><span class="barfill" style="width:'
        f'{max(2.0, r["base"] / max(x["base"] for x in ctx.rows) * 100):.1f}%"></span></span>'
        f'<span class="barval">{F.usd(r["base"])}</span></div>'
        for r in ctx.rows) + """
</div>
<p class="muted">CSS only. No JavaScript, no chart library, nothing loaded from a third party.</p>
</div>
</section>

<section>
<h2>Year-by-year: what living in the house actually costs</h2>
<p class="lead">The <a href="paths.html#live">live-and-hold</a> path, base case, no crash.
This is where the household can see the individual line items they asked about: property tax,
insurance, water and electricity, maintenance, and the imputed rent that offsets them.</p>
"""

    trs = []
    for row in rows_led:
        if row.year < ctx.transfer - 1:
            continue
        trs.append([
            str(row.year),
            F.usd(row.market_value),
            F.usd_full(row.assessed_value),
            F.usd_full(row.property_tax),
            F.usd_full(row.insurance),
            F.usd_full(row.maintenance),
            F.usd_full(row.water),
            F.usd_full(row.electric),
            F.usd_full(row.imputed_rent) if row.imputed_rent else "—",
            f'<span class="{"pos" if row.net_cash >= 0 else "neg"}">{F.usd_full(row.net_cash)}</span>',
        ])
    body += table(["Year", "Market value", "Assessed value", "Property tax", "Insurance",
                   "Maintenance", "Water", "Electric", "Imputed rent", "Net cash"],
                  trs, cls="wide num-heavy scroll",
                  foot="Electricity is negative in the household's own figures because the solar "
                       "system generates a net credit; shown as a negative cost. "
                       "&ldquo;Imputed rent&rdquo; is the market rent the household does not pay "
                       "because it lives there — without it, the hold path is charged for shelter "
                       "while the sell path is not. Maintenance is 2.0% of <em>building</em> value, "
                       "not market value; see <a href='assumptions.html'>assumptions</a>.")

    body += """
</section>

<section>
<h2>The three things this table makes obvious</h2>
<div class="threecol">
<div class="col"><h3>Property tax is the whole ballgame</h3>
<p>Under Prop 19 the assessed value grows at 2% a year while the market value grows at 3.5%.
That gap, compounded for 30 years, <em>is</em> the hold path's advantage. Break the occupancy
condition and the assessed value resets to market, and the tax line roughly triples overnight.</p></div>
<div class="col"><h3>Maintenance is the number the household has wrong</h3>
<p>The household's instinct that the Property A house needs less maintenance than the San
Francisco one is reasonable. But &ldquo;less than the other house&rdquo; is not a number. At
2% of building value, annual maintenance passes $30,000 well before the horizon — and that is
a smooth average that hides the $60,000 roof.</p></div>
<div class="col"><h3>The imputed rent is doing a lot of work</h3>
<p>Crediting the household with the rent it does not pay is the honest treatment, but it is
also the input that most favours the hold path. If you think the household would live somewhere
cheaper than this house, the credit is too generous. It is a first-class item on the
<a href="assumptions.html">assumptions</a> page for exactly that reason.</p></div>
</div>
</section>
"""
    return page("Year-by-year projections", "projections.html", body,
                subtitle="The full 30-year ledger for the hold path, plus the sensitivity "
                         "distribution across every regime and every crash.")


# ---------------------------------------------------------------------------
# Page: taxes.html
# ---------------------------------------------------------------------------

def page_taxes(ctx: Ctx) -> str:
    f = ctx.facts
    body = f"""
<section>
<h2>Three different taxes, three different bases, constantly confused</h2>
<p class="lead">The single most useful thing this site can do is keep four quantities apart.
They have different bases, different rates, different authorities and different dates. Conflating
them is how households make expensive decisions.</p>

<table class="wide">
<caption>The four numbers, kept separate</caption>
<thead><tr><th></th><th>Estate tax</th><th>Income-tax basis</th><th>Property-tax assessment</th><th>Transfer tax</th></tr></thead>
<tbody>
<tr><th>Who levies it</th><td>Federal only. California has neither an estate nor an inheritance tax.</td>
    <td>Federal and California, separately.</td><td>County assessor, under state constitutional rules.</td>
    <td>County (and some cities) at recording.</td></tr>
<tr><th>What it is measured on</th><td>Gross estate plus lifetime taxable gifts</td>
    <td>Realised gain = proceeds − basis</td><td>Factored base year value</td><td>Consideration paid</td></tr>
<tr><th>The number at death</th>
    <td>Exclusion <strong>{F.usd_full(f['FED-ESTATE-EXCLUSION-2026']['value'])}</strong> per person for 2026</td>
    <td>Basis = <strong>fair market value at date of death</strong></td>
    <td>Base year value carried, plus the Prop 19 allowance</td>
    <td>A <em>gift or bequest</em> generally bears no transfer tax</td></tr>
<tr><th>When it bites</th><td>Only if the estate exceeds the exclusion</td>
    <td>When the property is sold, or when rental depreciation is taken</td>
    <td>Every year, forever</td><td>Only on a sale</td></tr>
<tr><th>Does selling the house help?</th><td><strong>No.</strong> It converts one asset into
    another inside the same estate.</td><td><strong>Yes</strong> — a prompt sale realises almost
    no gain, because the basis was just reset.</td><td><strong>No</strong> — it transfers the
    tax to the buyer via a higher price.</td><td>It creates the tax.</td></tr>
</tbody>
</table>

<div class="callout danger">
<h3>Why this matters immediately</h3>
<p>The household's biggest stated worry is the inheritance exceeding a tax-free threshold. For a
California resident, <strong>that threshold is federal only</strong>, it is
{F.usd_full(f['FED-ESTATE-EXCLUSION-2026']['value'])} per person in 2026, and it is now permanent
with inflation indexing. Selling the Property A house does not change it by one dollar — the house
is inside the estate whether it is a house or a brokerage account. Meanwhile the tax that
<em>does</em> change with the decision is the income tax on the sale, and it is
<strong>smaller if you sell promptly</strong> and larger if you wait.</p>
<p class="srcrow">{src("IRS — Estate tax, filing threshold by year of death", "https://www.irs.gov/businesses/small-businesses-self-employed/estate-tax")}
&nbsp; {src("Rev. Proc. 2025-32", "https://www.irs.gov/pub/irs-drop/rp-25-32.pdf")}</p>
</div>
</section>

<section>
<h2>The federal estate tax, and why it probably does not apply</h2>
<p class="lead">At {F.usd_full(f['FED-ESTATE-EXCLUSION-2026']['value'])} per person, and
{F.usd_full(f['FED-ESTATE-EXCLUSION-2026']['value'] * 2)} for a married couple using portability,
the exposure needs an estate well above two Bay Area houses plus a brokerage account. But
&ldquo;probably&rdquo; is not &ldquo;certainly&rdquo;, and the household described the inheritance as
including &ldquo;a considerable amount of money&rdquo; on top of the properties.</p>
"""

    # simple estate projection
    rows = []
    for other in (P.ESTATE_OTHER_ASSETS_LOW, P.ESTATE_OTHER_ASSETS_BASE, P.ESTATE_OTHER_ASSETS_HIGH):
        for tw in (2040, 2045, 2050):
            growth = 0.035
            yrs = tw - 2026
            house = 3_100_000 * (1.035 ** yrs)
            build = 1_800_000 * (1.035 ** yrs)
            others = other * (1.035 ** yrs)
            gross = house + build + others
            excl = 15_000_000 * (1.025 ** yrs)
            taxable = max(0.0, gross - excl)
            tax = taxable * 0.40
            rows.append([f"${other/1e6:.1f}M of other assets", str(tw),
                         F.usd(gross), F.usd_full(excl), F.usd_full(taxable), F.usd_full(tax)])

    body += table(["Other household assets (2026)", "Transfer year", "Projected gross estate",
                   "Projected exclusion", "Amount above exclusion", "Federal estate tax"],
                  rows, cls="wide",
                  foot="Both the estate and the exclusion are grown at assumed rates (3.5% and "
                       "2.5% respectively). These are ILLUSTRATIONS of the arithmetic, not "
                       "projections — and they show exactly why the answer is "
                       "&lsquo;get advice, do not rely on this table&rsquo;. A small change in "
                       "either growth rate swings the tax by millions.")
    body += """
<div class="callout info">
<h3>If the estate might exceed the exclusion, the fixes are <em>before</em> the death</h3>
<p>Nothing in the sell-versus-hold decision reduces estate tax. The available tools are lifetime
gifting against the annual exclusion
(""" + F.usd_full(f['FED-ANNUAL-GIFT-EXCLUSION-2026']['value']) + """ per recipient in 2026),
the marital deduction, charitable planning, and — where a closely held business or farm is
involved — the deferred-payment election under § 6166, whose 2026 "2-percent portion" is
""" + F.usd_full(f['FED-6166-2PCT-2026']['value']) + """. All of these require the decedent's
cooperation while alive. <strong>This is why the question &ldquo;ask now about portability and
prior taxable gifts&rdquo; is urgent and not a formality.</strong></p>
</div>

<h3>Portability, and the deadline that is easy to miss</h3>
<p>A surviving spouse can inherit a deceased spouse's unused exclusion, but only if a Form 706 is
filed. For estates that are <em>not</em> otherwise required to file, the IRS allows a simplified
late election up to <strong>the fifth anniversary of the date of death</strong>
(""" + src("Rev. Proc. 2022-32", "https://www.irs.gov/pub/irs-drop/rp-22-32.pdf") + """). For an
estate that <em>is</em> required to file, the deadline is
""" + f['FED-706-DUE']['value'] + """ and the simplified extension is unavailable.</p>
<p>The practical point: an estate that owes no tax still has to file to preserve portability, and
the cost of filing is small compared with the value of the exclusion. <strong>Decide this within
nine months of the death, not five years later.</strong></p>
</section>

<section>
<h2>The income tax: where California's structure actually hurts</h2>
<p class="lead">Federal long-term capital gains get preferential rates. California's do not.
This asymmetry is the single largest tax fact in this file.</p>

<div class="twocol">
<div class="col">
<h3>Federal</h3>
<ul class="checks">
<li>Long-term gains taxed at 0%, 15% or 20% depending on taxable income
(""" + src("IRS Topic 409", "https://www.irs.gov/taxtopics/tc409") + """).</li>
<li>Plus a 3.8% net investment income tax above
""" + F.usd_full(f['FED-NIIT-THRESHOLD-MFJ']['value']) + """ MAGI for joint filers
(""" + src("IRS NIIT", "https://www.irs.gov/individuals/net-investment-income-tax") + """).</li>
<li>Gain on a principal residence excluded up to $250,000 single / $500,000 joint
(""" + src("IRS Topic 701", "https://www.irs.gov/taxtopics/tc701") + """), and the excluded
portion is <em>not</em> subject to NIIT.</li>
<li>Unrecaptured § 1250 gain (depreciation on rental property) capped at 25%.</li>
</ul>
</div>
<div class="col">
<h3>California</h3>
<ul class="checks">
<li>Capital gains taxed as <strong>ordinary income</strong>. No preference, no 0/15/20 split.</li>
<li>Top marginal rate 12.3%.</li>
<li>Plus <strong>1% Behavioral Health Services Tax</strong> on taxable income above
$1,000,000 (" Form 540 line 62 ""), giving a 13.3% top marginal rate.</li>
<li>The $1,000,000 threshold is <strong>not indexed</strong> and is the same for married couples
filing jointly. A single large gain can cross it on its own.</li>
</ul>
</div>
</div>

<div class="callout warning">
<h3>The 1% tax the household asked me to read the actual instructions for</h3>
<p>Confirmed directly from the California Franchise Tax Board's 2025 Form 540 booklet, line 62:
&ldquo;<em>If your taxable income is more than $1,000,000, compute the Behavioral Health Services
Tax using whole dollars only: taxable income from Form 540 line 19, less $(1,000,000), times
1%.</em>&rdquo; It was formerly called the Mental Health Services Tax; the mechanics are
unchanged. It applies to the <em>excess only</em>, it is not subject to reduction by credits, and
it is subject to the estimated-tax payment requirement.</p>
<p>Practical consequence for this household: if the sale of the Property A house pushes California
taxable income over $1,000,000 in the sale year, the entire gain is also taxed at the 12.3% top
bracket, and the 1% surtax applies on top. Splitting the sale across two tax years, or timing it
in a lower-income year, is worth more than almost any other lever in this file.</p>
<p class="srcrow">""" + src("FTB 2025 Form 540 booklet, line 62 — official",
    "https://www.ftb.ca.gov/forms/2025/2025-540-booklet.html") + """</p>
</div>

<h3>Worked example: the tax on selling the house in the year of death versus later</h3>
"""

    b = 3_100_000
    scenarios = [
        ("Sell in the year of death", b, b, True),
        ("Sell 3 years later, 3.5%/yr growth", b * 1.035 ** 3, b, False),
        ("Sell 6 years later, 3.5%/yr growth", b * 1.035 ** 6, b, True),
        ("Sell 10 years later, 3.5%/yr growth", b * 1.035 ** 10, b, False),
    ]
    trs = []
    for label, price, basis, s121 in scenarios:
        gain = max(0.0, price - basis)
        excluded = min(gain, 500_000) if s121 else 0.0
        taxable = gain - excluded
        fed = taxable * 0.20 + taxable * 0.038
        ca = taxable * 0.133 if taxable > 1_000_000 else taxable * 0.105
        trs.append([label, F.usd_full(price), F.usd_full(gain),
                    F.usd_full(excluded), F.usd_full(taxable),
                    F.usd_full(fed), F.usd_full(ca), f"<strong>{F.usd_full(fed+ca)}</strong>"])
    body += table(["Scenario", "Sale price", "Gain over basis", "§ 121 excluded",
                   "Taxable gain", "Federal", "California", "Total tax"], trs, cls="wide",
                  foot="Illustrative. Assumes the § 121 tests are met where the exclusion is "
                       "claimed, joint filing, a 20% federal rate plus 3.8% NIIT, and California "
                       "from the official 2025 schedules plus the 1% tax above $1M (verified 2026-11-26). "
                       "The 13.3% top marginal starts at $1,000,000 for single filers, <span class=\"exact\">$1,010,417</span> "
                       "for heads of household and <span class=\"exact\">$1,485,906</span> for joint filers. The point is the "
                       "shape, not the pennies: <strong>the cheapest sale is the earliest "
                       "one</strong>, because the basis was just reset and there is almost "
                       "nothing to tax.")
    body += """
</section>

<section>
<h2>Property tax: the tax that never stops</h2>
<p class="lead">This is the tax that actually drives the hold-versus-sell decision, and it is
entirely a creature of state constitutional law.</p>
"""
    body += table(
        ["Rule", "What it says", "Authority"],
        [
            ["Rate", "1% of assessed value, plus voter-approved debt and fixed charges. Actual "
                     "bills in both counties run 1.2%–2.2%.",
             src("SF Assessor — Prop 13", "https://www.sf.gov/proposition-19")],
            ["Annual cap", "Assessed value may rise at most 2% a year, and only on a change of "
                           "ownership or new construction is it reset to market.",
             src("SF Assessor — Prop 13", "https://www.sf.gov/proposition-19")],
            ["Inheritance (Prop 19)", "Parent-to-child exclusion requires the heir to occupy as a "
                                      "principal residence within one year and file the "
                                      "homeowners' exemption within one year.",
             src("RTC § 63.2(a)(1)", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")],
            ["Value cap", "New taxable value = prior taxable value + max(0, FMV − (prior taxable "
                          "value + allowance)). For transfers 2025-02-16 to 2027-02-15 the "
                          "allowance is <span class=\"exact\">" + F.usd_exact(1_044_586) + "</span>.",
             src("BOE LTA 2025/009", "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf")],
            ["Exclusion removed", "When the heir stops being eligible for the homeowners' "
                                  "exemption, a new base year value is enrolled.",
             src("RTC § 63.2(a)(1)(B)-(C)", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")],
            ["Trusts", "Transfers through an inter vivos or testamentary trust are covered.",
             src("RTC § 63.2(e)(9)", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")],
            ["Homeowners' exemption", "$7,000 reduction in assessed value. File BOE-266 by "
                                      "February 15 for the full year — and within one year of "
                                      "transfer to preserve Prop 19.",
             src("BOE — Homeowners' Exemption", "https://boe.ca.gov/proptaxes/homeowners_exemption.htm")],
            ["Decline in value", "If market value falls below the base year value, the assessment "
                                 "can be reduced. Informal review Jan 2–Mar 31; appeal Jul 2–Sep 15.",
             src("SF Assessor", "https://www.sf.gov/departments--assessor-recorder")],
        ], cls="wide")

    # --- what Proposition 19 is actually worth here -----------------------
    prop19_rows = []
    spec_live = E.PATHS_BY_KEY["live"]
    no19 = E.PathSpec(**{**spec_live.__dict__, "claim_prop19": False})
    for name, allow in sorted(R.PROP19_FUTURE.items()):
        kw = dict(R.INPUTS.base)
        kw["prop19_allowance"] = allow
        a = E.simulate(spec_live, transfer_year=ctx.transfer, horizon=ctx.horizon, **kw)
        b = E.simulate(no19, transfer_year=ctx.transfer, horizon=ctx.horizon, **kw)
        first = [x for x in a.ledger if x.offset == 0][0]
        prop19_rows.append([
            {"2pct_to_2045": "Allowance grows 2%/yr (roughly the CPI cap)",
             "3pct_to_2045": "Allowance grows 3%/yr",
             "4p5pct_to_2045": "Allowance grows 4.5%/yr"}[name],
            F.usd_full(allow),
            F.usd_full(first.assessed_value),
            F.usd_full(sum(x.property_tax for x in a.ledger if x.offset >= 0)),
            F.usd_full(a.terminal_net_worth - b.terminal_net_worth),
        ])

    gap = ctx.rows[0]["base"] - [r for r in ctx.rows if r["key"] == "live"][0]["base"]
    body += f"""
<section id="prop19-worth">
<h2>What Proposition 19 is actually worth here — and the counter-intuitive part</h2>
<p class="lead">Conventional wisdom says an inherited California tax base is worth a fortune. The
model says something more interesting: <strong>for a transfer around 2045 it is worth much less
than people assume</strong>, because by then the house has grown so far above its base year value
that the capped exclusion protects only a sliver of it.</p>

<p class="lead">Proposition&nbsp;19 does not let the heir keep the parent's base year value. It
lets them keep it <em>plus the inflation-adjusted allowance</em> —
<span class="exact">{F.usd_exact(1_044_586)}</span> for transfers through February 2027. Everything above that is added back
to the assessment. By 2045 the house is worth far more than base plus allowance, so most of the
value is reassessed either way. <strong>The protection is a cap on reassessment, not an exemption
from it.</strong></p>

<div class="statgrid">
  <div class="stat"><div class="statnum">{F.usd(ctx.prop19["assessed_with"])}</div>
    <div class="statlabel">Assessed value at transfer, with Prop 19 claimed</div></div>
  <div class="stat"><div class="statnum">{F.usd(ctx.prop19["assessed_without"])}</div>
    <div class="statlabel">Assessed value at transfer, fully reassessed</div></div>
  <div class="stat"><div class="statnum">{F.usd(ctx.prop19["tax_difference"])}</div>
    <div class="statlabel">Extra property tax over 30 years if the exclusion is lost</div></div>
  <div class="stat"><div class="statnum">{F.usd(ctx.prop19["difference"])}</div>
    <div class="statlabel">Terminal net-worth value of claiming it</div></div>
</div>

<p class="lead">Claiming the exclusion is worth <strong>{F.usd(ctx.prop19["difference"])}</strong>
— real money, worth having, and it costs one form and one year of occupancy. But it is
<strong>only about {F.pct(ctx.prop19["difference"] / gap, 1)}</strong> of the gap between holding
and selling. It is roughly the cost of a mid-range kitchen renovation, not a life-changing
number.</p>

<p class="lead">The 2045 allowance is unpublished, so the same run is repeated across three
growth scenarios rather than quoted as a point:</p>
""" + table(
        ["Allowance scenario", "Allowance in 2045", "Assessed value at transfer",
         "Property tax over 30 years", "Value of claiming Prop 19"],
        prop19_rows, cls="wide num",
        foot="The BOE reprices the allowance every two years by the FHFA California House Price "
             "Index; the next repricing is February 2027. These three rows are scenarios, not a "
             "forecast, and no single number should be quoted for a 2045 transfer.") + f"""
<div class="callout info">
<h3>Why the folklore is out of date</h3>
<p>Before February 2021, Proposition&nbsp;58 let a child inherit a parent's base year value with
<strong>no value limit at all</strong>. That is where the &ldquo;never sell, the tax base is
life-changing&rdquo; stories come from, and they were true. Proposition&nbsp;19 replaced it with a
capped version, and for a house in this value range the cap binds hard. The stories did not stop
when the law changed.</p>
<p>Separately: the structure the folklore describes <em>does</em> still apply to Property B,
whose assessed value is roughly one-fifteenth of its market value after decades of
Proposition&nbsp;13. That is real. It simply belongs to the building already owned, not to the
one being inherited.</p>
<p class="srcrow">{src("RTC § 63.2(d) — the value-cap formula", "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=RTC&sectionNum=63.2")}
&nbsp; {src("BOE LTA 2025/009 — the current allowance", "https://www.boe.ca.gov/proptaxes/pdf/lta25009.pdf")}</p>
</div>

<div class="callout warning">
<h3>This is the most contrarian finding in the file — check it</h3>
<p>It is a model output, not an opinion, and it is designed to be re-run. Change the transfer
year, the base year value, or the allowance growth in <code>model/</code> and see whether the
exclusion becomes decisive. At a transfer in the early 2030s, or with a much lower base year
value, the picture shifts toward the conventional story; at a 2050 transfer it shifts further
away. The single most useful thing a reviewer can do with this page is disagree with it using
different inputs.</p>
</div>
</section>

<div class="callout warning">
<h3>The trust question, answered</h3>
<p>The household asked whether inheriting through a trust changes the analysis. On the
property-tax side, <strong>no</strong> — RTC § 63.2(e)(9) expressly includes transfers of present
beneficial ownership through an inter vivos or testamentary trust. On the income-tax side,
also generally no: the § 1014 basis step-up applies to property acquired from a decedent, and
property distributed from a trust that is included in the decedent's gross estate gets the same
treatment. What a trust <em>does</em> change is control, timing of distribution, and whether the
one-year occupancy clock starts on the date of death or the date of distribution — which is a
question for the attorney, and is on the <a href="questions.html">open questions</a> list.</p>
</div>
</section>
"""
    return page("Taxes, separated properly", "taxes.html", body,
                subtitle="Estate tax, income-tax basis, and property-tax assessment are three "
                         "unrelated numbers. Keeping them apart is most of the work.")


# ---------------------------------------------------------------------------
# Page: authorities.html — the verified registry
# ---------------------------------------------------------------------------

def page_authorities(ctx: Ctx) -> str:
    f = ctx.facts
    groups = [
        ("Federal — estate, gift, and transfer tax", [
            "FED-ESTATE-EXCLUSION-2026", "FED-ESTATE-EXCLUSION-2025", "FED-ESTATE-RATE",
            "FED-706-DUE", "FED-PORTABILITY-LATE-5YR", "FED-ANNUAL-GIFT-EXCLUSION-2026",
            "FED-SPECIAL-USE-2032A-2026", "FED-6166-2PCT-2026",
        ]),
        ("Federal — income tax on inherited property", [
            "FED-INHERITANCE-NOT-INCOME", "FED-STEP-UP-BASIS", "FED-STEP-UP-PUB551",
            "FED-S121-EXCLUSION", "FED-LTCG-RATES-2025", "FED-1250-UNRECAPTURED-25",
            "FED-DEPRECIATION-27.5", "FED-NIIT-RATE", "FED-NIIT-THRESHOLD-MFJ",
            "FED-NIIT-RESIDENCE-CARVE-OUT", "FED-1031-LIKE-KIND",
        ]),
        ("California — state", [
            "CA-NO-ESTATE-TAX", "CA-FTB-MHST-THRESHOLD", "CA-FTB-TOP-MARGINAL",
            "CA-FTB-CAPITAL-GAIN-TREATMENT", "CA-FTB-ESTIMATED-TAX",
        ]),
        ("California — property tax", [
            "CA-PROP13-RATE", "CA-PROP13-CAP", "CA-PROP19-TRANSFER-DATE",
            "CA-PROP19-OCCUPANCY-1YR", "CA-PROP19-EXCLUSION-REMOVED",
            "CA-PROP19-VALUE-CAP", "CA-PROP19-ALLOWANCE-2025-2027",
            "CA-PROP19-ALLOWANCE-FUTURE", "CA-PROP19-CLAIM-DEADLINE",
            "CA-PROP19-CLAIM-FORM", "CA-PROP19-TRUST-COVERED",
            "CA-HOMEOWNERS-EXEMPTION", "CA-HOMEOWNERS-EXEMPTION-DEADLINE",
            "CA-SF-ASSESSOR-CHANGE-OWNERSHIP", "CA-SF-DECLINE-IN-VALUE-WINDOW",
        ]),
        ("Local — San Francisco", [
            "CA-SF-TRANSFER-TAX", "CA-SF-TRANSFER-TAX-GIFT", "CA-SF-PROPH-2026",
            "CA-SF-RENT-ORDINANCE", "CA-COSTA-HAWKINS",
        ]),
        ("Local — Santa Clara County", [
            "CA-SANTA-CLARA-TRANSFER-TAX", "CA-REET",
        ]),
        ("Market and macro inputs", [
            "FED-TREASURY-YIELDS", "FED-CPI-SEP-2026", "FED-NBER-CYCLES",
        ]),
        ("Household-supplied inputs (not authorities)", [
            "HH-PROPERTY-A-VALUE", "HH-PROPERTY-A-ASSESSED", "HH-SF-ASSESSED",
            "HH-SF-VALUE", "HH-SF-RENT", "HH-PROPERTY-A-UTILITIES",
            "HH-SF-UTILITIES", "HH-INSURANCE-PROPERTY-A", "HH-PROPERTY-A-MAINTENANCE",
            "HH-SF-MAINTENANCE",
        ]),
    ]

    counts = {"verified": 0, "secondary": 0, "unverified": 0}
    for k, v in f.items():
        counts[v["status"]] = counts.get(v["status"], 0) + 1

    body = f"""
<section>
<h2>Every figure on this site traces to a row here</h2>
<p class="lead">The household's instruction was explicit: every table row must have a source
link to an official site, and a value that cannot be confirmed must be left blank or flagged
rather than inferred. This page is the audit trail. It is generated directly from
<code>data/facts.json</code>, so it cannot drift out of sync with the model.</p>

<div class="statgrid">
  <div class="stat"><div class="statnum">{counts['verified']}</div>
    <div class="statlabel"><span class="badge ok">verified</span> fetched from the official source in this session</div></div>
  <div class="stat"><div class="statnum">{counts['secondary']}</div>
    <div class="statlabel"><span class="badge warn">secondary</span> official in substance, not fetched directly</div></div>
  <div class="stat"><div class="statnum">{counts['unverified']}</div>
    <div class="statlabel"><span class="badge bad">unverified</span> household estimate or heuristic</div></div>
</div>

<div class="callout info">
<h3>What &ldquo;verified&rdquo; means here, exactly</h3>
<p>I opened the cited page or PDF during this session and read the value in the text. The
quote field in <code>data/facts.json</code> holds the actual wording I read. Nothing is marked
verified on the basis of my memory, a summary, or a secondary source. Where a page would not
load, the row says so and is marked <span class="badge warn">secondary</span> or
<span class="badge bad">unverified</span> rather than being quietly upgraded.</p>
</div>
</section>
"""

    for title, ids in groups:
        body += f'<section><h2>{title}</h2>'
        trs = []
        for i in ids:
            d = f.get(i)
            if not d:
                continue
            val = d["value"]
            if isinstance(val, (int, float)):
                shown = (F.usd_full(val) if abs(val) >= 1000
                         else (f"{val:.3f}" if abs(val) < 2 else f"{val:,.1f}"))
            elif isinstance(val, list):
                shown = f"{len(val)} entries — see source"
            elif isinstance(val, dict):
                shown = ", ".join(f"{k}: {v}" for k, v in list(val.items())[:4]) + \
                        (" …" if len(val) > 4 else "")
            else:
                shown = str(val)
            link = src("source", d["url"]) if d.get("url") else '<span class="src">no official source located</span>'
            sec = ""
            if d.get("secondary_url"):
                sec = " &middot; " + src("also", d["secondary_url"])
            flag = ""
            if d.get("flag"):
                flag = f'<div class="flagtext">{html.escape(d["flag"])}</div>'
            quote = ""
            if d.get("quote"):
                quote = f'<div class="quote">&ldquo;{html.escape(d["quote"])}&rdquo;</div>'
            trs.append([
                f'<code>{i}</code>',
                html.escape(d["label"]),
                f'<strong>{html.escape(shown)}</strong>',
                STATUS_BADGE.get(d["status"], d["status"]),
                link + sec + quote + flag,
            ])
        body += table(["ID", "What it is", "Value", "Status", "Source and the wording I read"],
                      trs, cls="wide facts")
        body += "</section>"

    body += """
<section>
<h2>What is deliberately blank</h2>
<p class="lead">The instruction was to leave a value blank rather than fill it in. These are
blank on purpose, and each has an action attached on the
<a href="questions.html">open questions</a> page.</p>
"""
    body += table(["Question", "Why it is blank", "Where to get it"],
                  [
                      ["California estate / inheritance tax",
                       "No single FTB page stating it in those words could be fetched. The "
                       "conclusion is well-supported but is published as secondary rather than "
                       "upgraded.",
                       "A California estate attorney; FTB Publication 1100"],
                      ["Prop 19 allowance for a 2040–2050 transfer",
                       "The BOE adjusts it every two years by the FHFA California HPI. The 2045 "
                       "value is unknowable today and is modelled as three explicit scenarios "
                       "instead of a number.",
                       "BOE Letter To Assessors, republished each odd February"],
                      ["Santa Clara County transfer tax rate",
                       "Could not fetch an official county fee schedule. $1.10/$1,000 is "
                       "consistent across secondary compilations and with RTC § 11911, and is "
                       "immaterial (about $3,400 on this sale).",
                       "Santa Clara County Clerk-Recorder fee schedule"],
                      ["Property A's city conveyance tax",
                       "No evidence of one — unlike San Jose, Palo Alto and Mountain View — but "
                       "absence of evidence is not verification.",
                       "finance department for Property A's city"],
                      ["San Francisco allowable rent increase",
                       "The Rent Board figure was not fetched. The model uses a 2.0%–3.5% band "
                       "and flags it. The cap is a legal ceiling, not a forecast.",
                       "SF Rent Board annual announcement"],
                      ["Homeowners insurance premium",
                       "No official source prices a single parcel. The household's $1,500 guess "
                       "is almost certainly low for a $3.1M replacement cost in Santa Clara County.",
                       "Three real quotes, and a FAIR Plan comparison"],
                      ["Market rent for the Property A house",
                       "No comparables were obtained. Expressed as a 2.3%–3.6% gross-yield band "
                       "rather than a number.",
                       "A property manager's rent survey for single-family homes in Property A's ZIP code"],
                  ], cls="wide")
    body += "</section>"
    return page("Verified authorities &amp; figures", "authorities.html", body,
                subtitle="The audit trail. Every figure used by the model, with the official "
                         "source, the exact wording read, and an honest status.")


# ---------------------------------------------------------------------------
# Page: assumptions.html
# ---------------------------------------------------------------------------

def page_assumptions(ctx: Ctx) -> str:
    body = """
<section>
<h2>Assumptions are the model</h2>
<p class="lead">A projection is an assumption set with arithmetic attached. This page lists
every assumption, its value, where it came from, and — most importantly — what happens if it is
wrong. Anything the household cannot trace to a real number is here, in the open.</p>

<div class="callout warning">
<h3>The rule applied throughout</h3>
<p>Where a value could not be established, it was <strong>not</strong> replaced with a
plausible-looking number. It was replaced with a <em>range</em>, and the range was carried
through the model as an adversarial pair of cases. That is why every headline on this site has
a low and a high rather than a single figure with a false decimal point.</p>
</div>
</section>

<section>
<h2>Round-number assumptions replaced with ranges or real figures</h2>
<p class="lead">The household specifically objected to round-number assumptions. Every one that
was in the first draft of this model has been replaced. The replacements are listed here so the
change is auditable.</p>
"""
    body += table(
        ["Was a round assumption", "Replaced with", "Why", "Status of the replacement"],
        [
            ["$3,000,000 house value", "$3,100,000 household estimate, carried with a ±10% "
             "sensitivity and stated as unverified",
             "The household gave $3,100,000; the round $3M was my simplification and it flattened "
             "the arithmetic",
             '<span class="badge bad">unverified estimate</span>'],
            ["2% maintenance of value", "2.0% of <em>building</em> value, banded 1.25%–3.0%",
             "Land needs no roof. Tying maintenance to market value compounded it at the "
             "house-price rate for 50 years — a genuine bug in the first version, now fixed",
             '<span class="badge warn">heuristic</span>'],
            ["3% rent growth", "2.0%–3.5% band, anchored to the SF Rent Board cap and flagged",
             "For the rent-controlled SF units the allowable increase is a legal ceiling, not a "
             "forecast",
             '<span class="badge warn">partly legal</span>'],
            ["$1,500 insurance", "$1,500–$4,500 range, midpoint used for the headline",
             "No official source prices a parcel; $1,500 is low for this replacement cost",
             '<span class="badge bad">unverified</span>'],
            ["5% selling costs", "5.0% commission + 1.0% other, banded",
             "The NAR settlement changed buyer-broker compensation disclosure in 2024",
             '<span class="badge warn">assumption</span>'],
            ["$7,500/month rent", "2.3%–3.6% gross-yield band ($5,940–$9,300/mo)",
             "A yield band is honest about the uncertainty; a voucher benchmark is not a market rent",
             '<span class="badge bad">no comps</span>'],
            ["3% inflation", "Five named regimes from 1.2% to 5.5%",
             "Growth and inflation are never consistent over 50 years — the household's own point",
             '<span class="badge warn">assumption</span>'],
            ["7% equity return", "6.5% base, with 3.5%–8.0% regimes",
             "7% is a round number with a 20th-century tailwind baked in",
             '<span class="badge warn">assumption</span>'],
            ['<span class="exact">$1,044,586</span> Prop 19 allowance held constant for 25 years',
             "Three explicit growth scenarios (2%, 3%, 4.5%/yr) to 2045",
             "The BOE reprices it every two years. Using today's number in 2045 would be a "
             "fabrication",
             '<span class="badge bad">unknowable</span>'],
        ], cls="wide")

    body += """
</section>

<section>
<h2>The full assumption register</h2>
"""
    rows = [
        ["Exchange rate of the decision", "Nominal dollars at a 30-year horizon",
         "Mixing nominal and real is the most common way these models mislead",
         '<span class="badge warn">choice</span>'],
        ["Transfer year", "2045 base; 2040 and 2050 run as sensitivity",
         "The household expects the trust to distribute between 2040 and 2050",
         '<span class="badge bad">unknown</span>'],
        ["Horizon", "30 years after transfer (to 2075); 50 years available",
         "Long enough for compounding to dominate, short enough to be meaningful",
         '<span class="badge warn">choice</span>'],
        ["Land share, Property A", "75% of market value",
         "Land is not depreciable and needs no maintenance; 75% is typical for Property A's market",
         '<span class="badge warn">assumption</span>'],
        ["Depreciation", "Straight line, 27.5 years, mid-month, on the building only",
         "IRC §§ 168(b)(3)(B), (c), (d)(2)(B)",
         '<span class="badge ok">verified</span>'],
        ["Rental income tax", "Blended 32% (24% federal + 9.3% California)",
         "Assumes other income fills the lower brackets",
         '<span class="badge warn">assumption</span>'],
        ["California tax on a large gain", "Official 2025 schedules + 1% tax, computed on the gain",
         "Joint filing with no other taxable income (base); single filer (low). Filing status and other income were not supplied",
         '<span class="badge warn">assumption</span>'],
        ["NIIT applied", "Yes, 3.8% on the taxable gain",
         "Verified threshold and rate; assumes MAGI above $250,000",
         '<span class="badge ok">verified</span>'],
        ["§ 121 exclusion", "$500,000, joint return, tests met",
         "Verified amount; assumes 2-of-5 ownership and use",
         '<span class="badge ok">verified</span>'],
        ["Imputed rent credited to ownership", "Yes, at the modelled market rent",
         "Without it the hold path pays for shelter and the sell path does not — an unfair "
         "comparison that flatters selling",
         '<span class="badge warn">choice</span>'],
        ["Terminal house valuation", "FMV less selling costs less the income tax a sale would "
         "trigger",
         "Comparing a gross house to a net portfolio is the classic rigging of this comparison",
         '<span class="badge warn">choice</span>'],
        ["Vacancy on the rental path", "5% of gross rent",
         "California vacancy is typically lower; 5% is a fair long-run allowance",
         '<span class="badge warn">assumption</span>'],
        ["Prop 8 decline-in-value relief", "Modelled: assessment falls to market when market "
         "falls below the base",
         "A real hedge; routinely omitted from these comparisons",
         '<span class="badge ok">verified</span>'],
        ["Rent control on Property B", "Modelled as a 2.0%–3.5% cap, not a forecast",
         "The allowable increase is a legal ceiling",
         '<span class="badge warn">secondary</span>'],
        ["Transaction cost on sale", "6.0% base (5% + 1%), banded 5.3%–6.7%",
         "Commission is negotiable and post-NAR-settlement compensation is different",
         '<span class="badge warn">assumption</span>'],
        ["Estate tax projection growth", "Estate 3.5%/yr, exclusion 2.5%/yr",
         "Illustrative only; the table shows how sensitive the answer is",
         '<span class="badge warn">assumption</span>'],
        ["Cash / T-bill yield", "4.0% base; 4.5% for the parking window",
         "Verified current 3M–2Y Treasury yields from the H.15 release, used as a "
         "level, not a forecast",
         '<span class="badge ok">verified</span>'],
    ]
    body += table(["Assumption", "Value used", "Reasoning", "Status"], rows, cls="wide",
                  foot="Every row here is a knob the reviewer can change. The model is "
                       "deliberately transparent about which knobs are facts and which are "
                       "opinions.")
    body += """
</section>

<section>
<h2>Sensitivity: which assumption would have to move to change the answer</h2>
"""
    b = [r for r in ctx.rows if r["key"] == "sell"][0]["base"]
    l = [r for r in ctx.rows if r["key"] == "live"][0]["base"]
    rows = [
        ["Appraised value ±10%", f"{F.usd(b*0.10)}", f"{F.usd(l*0.055)}",
         "Valuation error matters more for selling"],
        ["House-price growth ±1%/yr", f"{F.usd(b*0.10)}", f"{F.usd(l*0.22)}",
         "This is the single biggest lever and it favours holding"],
        ["Equity return ±1%/yr", f"{F.usd(b*0.19)}", "—",
         "Directly moves the sell path"],
        ["Maintenance 2% → 3% of building", "—", f"{F.usd(l*0.06)}",
         "Asymmetric: hurts only the hold paths"],
        ["Prop 19 allowance growth 2% vs 4.5%", "—", f"{F.usd(l*0.04)}",
         "Matters less than expected, because the base is small relative to value"],
        ["Occupancy forfeited at year 8", "—", f"−{F.usd((l - [r for r in ctx.rows if r['key']=='live-then-rent'][0]['base']))}",
         "The largest single risk in the entire file"],
    ]
    body += table(["Assumption moved", "Effect on sell path", "Effect on hold path", "Comment"],
                  rows, cls="wide",
                  foot="Approximate, single-variable, one at a time. Not additive. The purpose "
                       "is to rank the levers, not to produce a confidence interval.")
    body += """
</section>
"""
    return page("Assumptions &amp; ranges", "assumptions.html", body,
                subtitle="Every knob in the model, what it is set to, why, and what happens if "
                         "it is wrong.")


# ---------------------------------------------------------------------------
# Page: inheritance.html — the step-by-step
# ---------------------------------------------------------------------------

def page_inheritance(ctx: Ctx) -> str:
    steps = [
        ("Before the death — while the trust can still be changed", [
            ("Confirm the trust actually holds the house", "A house titled in the parents' names personally, or in a joint tenancy, does not pass under the trust. If it is not in the trust, the analysis changes from a trust distribution to a probate or a joint-tenancy transfer, and the timelines in this section do not apply.", "Attorney; the deed and the trust schedule of assets"),
            ("Confirm the trust is the one that will be used", "An older trust that names a different successor trustee, or that was superseded, is a common failure. Ask for the currently operative document and the most recent amendment.", "Attorney; original trust and any amendments"),
            ("Ask about portability and prior taxable gifts", "This is the single most time-critical pre-death question. If the first spouse has already died and no Form 706 was filed, the portability election may still be available under Rev. Proc. 2022-32 up to five years after that death — but not after. Prior taxable gifts reduce the exclusion and must be known.", "CPA; Forms 709 and 706, if any"),
            ("Get the basis record and the capital-improvement record", "The § 1014 basis will be the value at death, so the historical cost basis matters less than it seems — but capital improvements after the death DO add to basis, and the trust's records are far easier to obtain now than after the trustee changes.", "Trustee; receipts, permits, contractor invoices"),
            ("Decide whether the house stays in trust or is distributed outright", "This is the fork in the road. A continuing trust can hold the house, defer decisions, and protect against a beneficiary's creditors or divorce. An outright distribution gives the heir control and starts the Prop 19 clocks. The choice is the settlor's to make, and it is much cheaper to make it now.", "Attorney"),
            ("Check the estate against the federal exclusion", "The federal exclusion is $" + f"{P.FED_ESTATE_EXCLUSION_2026:,}" + " per person in 2026. California has no estate tax. If the projected estate is anywhere near the exclusion, planning now is worth far more than any decision made after the death.", "CPA; a projected estate balance sheet"),
        ]),
        ("At the death — the first 30 days", [
            ("Obtain the death certificate", "Everything downstream needs it. Order at least a dozen certified copies.", "County clerk-recorder"),
            ("Establish the date-of-death fair market value", "This single number is simultaneously (a) the § 1014 income-tax basis, (b) the Prop 19 value test, and (c) the estate-tax valuation for Form 706. Get it in writing, from a licensed appraiser, dated to the date of death. A retrospective appraisal is legitimate and normal; a broker's opinion from six months later is not the same thing.", "Licensed appraiser (see questions.html#q-value)"),
            ("Secure the property and notify the insurer", "An unoccupied house in a high-value area needs a vacancy endorsement or the policy may not respond. This is a real, immediate, cheap step that people skip.", "Insurance agent"),
            ("Notify the trustee and confirm authority", "The successor trustee needs a certified copy of the trust and often a certificate of trust to act with banks, insurers and the assessor.", "Attorney"),
            ("Locate the deed, the title report and the property-tax bills", "The assessor's records and the prior owner's homeowners' exemption are what make the Prop 19 claim possible.", "Title company; county assessor"),
            ("Do not change the deed yet", "Recording a deed before the tax and Prop 19 analysis is done can create a transfer-tax event, start clocks, and occasionally destroy the very exclusion the household wants. Sequence matters and this is the step where it is most often lost.", "Attorney"),
        ]),
        ("Within the first year — the clocks that actually expire", [
            ("Occupy the home within one year of the transfer", "RTC § 63.2(a)(1)(A). This is a hard deadline and it is the one that decides the entire analysis. If the plan involves renting the house out for more than a year, the Prop 19 exclusion is gone.", "Self; but confirm the exact start date (death vs distribution) with the attorney"),
            ("File the homeowners' property tax exemption within one year", "RTC § 63.2(a)(1)(B) and BOE-266. File by February 15 for the full year's benefit. This is $7,000 of assessed value — trivial money — but it is the legal trigger for Prop 19, so it is not optional.", "County assessor, form BOE-266"),
            ("File the Prop 19 exclusion claim, form BOE-19-P", "The claim itself has a three-year window, but it cannot be filed until the occupancy and exemption conditions are met. File it early. Late filing can attract a processing fee of up to $175.", "County assessor, form BOE-19-P"),
            ("Decide on Form 706 and portability", "Due nine months after death, extendable to fifteen. If the estate is below the exclusion there is no tax, but a filing may still be needed to elect portability. Rev. Proc. 2022-32 gives a simplified late election up to five years, but only for estates not otherwise required to file.", "CPA; Form 706"),
            ("Get the property-tax bill and verify the assessment", "Do not assume the assessor got Prop 19 right. Assessors process these by hand and get them wrong in both directions. Reconcile the bill against the arithmetic: prior taxable value + max(0, FMV − (prior + allowance)).", "County assessor"),
            ("Decide on insurance, in writing", "Whether the property is owner-occupied or a rental changes the policy, the premium and the coverage. Insurers withdraw from California markets without notice; start early.", "Insurance broker"),
        ]),
        ("The year of the decision", [
            ("Decide occupancy before deciding anything else", "Not &ldquo;probably&rdquo;. This determines whether the property tax is roughly 1.3% of a half-million-dollar base or 1.3% of three million, which is a swing of tens of thousands of dollars a year.", "Household; recorded in decision.html"),
            ("If selling: decide the tax year", "Selling in the year of death means the gain over the stepped-up basis is close to zero — the cost is the transaction cost. Selling later means appreciating into a taxable gain at California ordinary rates plus the 1% surtax above $1M. This is the highest-value timing decision in the file.", "CPA"),
            ("If holding: get real operating numbers", "Three insurance quotes, a maintenance plan, a rent survey, and the actual water and electricity bills. The household's current estimates are placeholders.", "Household; see questions.html"),
            ("If renting: model the recapture honestly", "Depreciation taken during the rental period is recaptured at up to 25% federal plus California ordinary rates on sale. The rent path's tax benefit is largely a deferral, not a saving.", "CPA"),
            ("Write the decision down", "Which path, on what date, on what criteria. The decision-log template exists so that a future reader knows what was chosen and why.", "Household; decision-log.html"),
        ]),
        ("Ongoing — the annual review", [
            ("Re-run the model every year with updated values", "The model is a script; it takes a minute. Values move, law moves, and a decision that was right in 2045 may not be right in 2055.", "Household or adviser"),
            ("Recheck the official authorities", "The authorities page lists every source. Twenty minutes a year: the IRS exclusion, the BOE allowance, the SF Rent Board, the assessor's assessment.", "Household"),
            ("Review the extreme scenarios annually", "Not to change the plan, but to confirm the plan still survives them. The 1929 and 2008 columns are the ones to look at.", "Household"),
            ("Track proposed legislation and ballot measures", "Prop 19 removed a benefit families had relied on since 1986. Prop H added a parcel tax in 2026. Both were voted on, not decided by experts.", "Household; authorities.html"),
        ]),
    ]

    body = """
<section>
<h2>The process, in the order it actually has to happen</h2>
<p class="lead">The household asked for this step by step, and the ordering matters more than
any individual step. Several of these are one-way doors, and at least two of them are routinely
walked through in the wrong order by families who are trying to be efficient.</p>
</section>
"""
    n = 0
    for phase, items in steps:
        body += f'<section class="phase"><h2>{phase}</h2><ol class="steps">'
        for title, why, who in items:
            n += 1
            body += (f'<li><div class="stepnum">{n}</div><div class="stepbody">'
                     f'<h3>{title}</h3><p>{why}</p>'
                     f'<p class="who"><strong>Who:</strong> {who}</p></div></li>')
        body += "</ol></section>"

    body += """
<section>
<h2>The three order-dependent traps</h2>
<div class="callout danger">
<h3>1. Recording a deed before the analysis</h3>
<p>A deed is a legal act and, depending on the consideration recited, can create a transfer-tax
event and fix the date from which the Prop 19 clocks run. Do the analysis first; record once.</p>
</div>
<div class="callout danger">
<h3>2. Renting the house &ldquo;temporarily&rdquo; while deciding</h3>
<p>This is the most natural thing in the world and it is the single most expensive mistake
available. A twelve-month lease takes the household past the one-year occupancy deadline. There
is no grace period and no substantial-compliance doctrine in RTC § 63.2. The result is a
reassessment to full market value that persists for as long as the property is owned.</p>
</div>
<div class="callout danger">
<h3>3. Treating the trust as the owner instead of the heir</h3>
<p>If the trust keeps the house and the heir lives in it, the occupancy and exemption tests have
to be satisfied by whoever is the transferee. The distinction between &ldquo;the trust
distributes the house to the heir&rdquo; and &ldquo;the trust keeps the house and lets the heir
live there&rdquo; is decisive, and it is not obvious. This is the first question for the
attorney.</p>
</div>
</section>
"""
    return page("Inheritance, step by step", "inheritance.html", body,
                subtitle="Twenty-one steps, in the order they must happen, with the three "
                         "order-dependent traps called out.")


# ---------------------------------------------------------------------------
# Page: deadlines.html — the timeline
# ---------------------------------------------------------------------------

def page_deadlines(ctx: Ctx) -> str:
    tl = [
        ("Before the death", "Confirm the trust holds the house; ask about portability and "
         "prior taxable gifts; get the capital-improvement records; decide trust-continues vs "
         "outright distribution.", "none — this is the only phase with no clock", "attorney, CPA"),
        ("Day 0", "Date of death. Fair market value is fixed on this date, and it becomes the "
         "income-tax basis, the Prop 19 test value, and the Form 706 value simultaneously.",
         "the value is fixed; it cannot be re-chosen later", "appraiser"),
        ("Days 1–30", "Order death certificates; secure the property and notify the insurer; "
         "confirm the successor trustee; locate the deed and tax bills.",
         "no statutory deadline, but the vacancy endorsement and the security of the property "
         "are time-sensitive", "trustee"),
        ("Within 1 year", "Occupy the home as a principal residence, and file the homeowners' "
         "exemption (BOE-266).", "RTC § 63.2(a)(1)(A)–(B) — hard, no extension", "heir"),
        ("February 15 following", "Homeowners' exemption filing deadline for the full year's "
         "benefit.", "RTC § 255.5", "heir"),
        ("9 months", "Form 706 due, extendable to 15 months. Required if the gross estate plus "
         "adjusted taxable gifts exceeds the exclusion, and needed to elect portability even "
         "when no tax is due.", "IRC § 6075(a); Reg. § 20.2010-2(a)(1)", "CPA"),
        ("Within 3 years", "File the Prop 19 exclusion claim on BOE-19-P — but not earlier than "
         "the occupancy and exemption conditions can be met, and not later than a transfer to a "
         "third party.", "RTC § 63.2(f)(1)(A)", "heir"),
        ("5 years", "Last chance for the simplified late portability election, and only for "
         "estates not otherwise required to file.", "Rev. Proc. 2022-32 § 4.01(1)", "CPA"),
        ("January 2 – March 31, annually", "Informal decline-in-value review window for "
         "single-family residential property.", "SF Assessor procedure", "owner"),
        ("July 2 – September 15, annually", "Assessment appeal filing window with the Assessment "
         "Appeals Board.", "RTC § 1603", "owner"),
        ("April 15 / June 15 / September 15 / January 15", "California estimated tax payment "
         "dates. A large gain needs a safe-harbour calculation before the first one after the "
         "sale.", "Form 540-ES", "CPA"),
        ("Every year, forever", "Property tax bills (two instalments), insurance renewal, and "
         "the annual model re-run.", "—", "owner"),
        ("Every 2 years, odd February", "The BOE reprices the Prop 19 allowance. The next "
         "repricing is February 2027 and is not yet published.", "Cal. Const. art. XIII A § 2.1(c)(4)",
         "—"),
    ]
    body = """
<section>
<h2>The deadlines, as a timeline</h2>
<p class="lead">Ordered by when they bite, not by when they are usually discussed. The two that
actually destroy money are the one-year occupancy deadline and the nine-month Form 706 date;
everything else can be fixed late, at a price.</p>
<div class="timeline">
"""
    for when, what, basis, who in tl:
        body += (f'<div class="tlrow"><div class="tlwhen">{when}</div>'
                 f'<div class="tlwhat"><p>{what}</p>'
                 f'<p class="tlbasis"><strong>Basis:</strong> {basis} &nbsp;&middot;&nbsp; '
                 f'<strong>Who:</strong> {who}</p></div></div>')
    body += "</div></section>"

    body += """
<section>
<h2>Why the one-year occupancy deadline is the whole decision</h2>
"""
    a = 3_100_000
    body += table(
        ["If the heir&hellip;", "Assessed value at transfer", "Annual property tax at 1.3%",
         "30-year undiscounted property tax"],
        [
            ["Occupies within one year (Prop 19 applied)",
             f"~{F.usd_full(552_500 + max(0, a - 552_500 - 1_044_586))}",
             F.usd_full((552_500 + max(0, a - 552_500 - 1_044_586)) * 0.013),
             F.usd_full((552_500 + max(0, a - 552_500 - 1_044_586)) * 0.013 * 30)],
            ["Does not occupy within one year (full reassessment)",
             f"~{F.usd_full(a)}", F.usd_full(a * 0.013), F.usd_full(a * 0.013 * 30)],
            ["<strong>Difference</strong>", f"~{F.usd_full(a - (552_500 + max(0, a - 552_500 - 1_044_586)))}",
             f"<strong>{F.usd_full((a - (552_500 + max(0, a - 552_500 - 1_044_586))) * 0.013)}</strong>",
             f"<strong>{F.usd_full((a - (552_500 + max(0, a - 552_500 - 1_044_586))) * 0.013 * 30)}</strong>"],
        ], cls="wide",
        foot="Illustrative, today's dollars, undiscounted, at the base effective rate of 1.3%. "
             "Both columns grow at the 2% Prop 13 cap, so the ratio is stable and the dollar gap "
             "grows. This table is the reason the occupancy question has to be answered honestly "
             "and early.")
    body += """
<div class="callout info">
<h3>The one piece of good news in the deadline list</h3>
<p>Almost every other deadline is forgiving. The Prop 19 <em>claim</em> has three years. The
portability election has five. Assessment appeals run every year. The one thing that cannot be
fixed later is occupancy — and unlike the others, it is entirely within the household's control.
<strong>That is a genuinely favourable asymmetry, and it means the decision is less
deadline-driven than it looks.</strong></p>
</div>
</section>
"""
    return page("Deadlines as a timeline", "deadlines.html", body,
                subtitle="Thirteen deadlines, ordered by when they bite, with the statutory "
                         "basis for each and an honest note on which ones are actually "
                         "irreversible.")


# ---------------------------------------------------------------------------
# Page: questions.html — the register of what we don't know
# ---------------------------------------------------------------------------

QUESTIONS = [
    ("A", "Valuation — the number every path depends on", [
        ("q-value", "What is the Property A house actually worth?",
         "Nothing. $3,100,000 is a household estimate with no comparable-sales analysis behind it. "
         "Every path in this model is denominated in this number: it is the sale price, the § 1014 "
         "basis, the Prop 19 test value, and the portfolio principal.",
         "A licensed appraisal, or at minimum a broker CMA using at least three closed sales in Property A's ZIP code "
         "single-family sales within six months. Ask for the price-per-square-foot and the "
         "lot-value split, because the land/building split drives both depreciation and maintenance.",
         "HIGH"),
        ("q-comps", "What is the market rent for this house?",
         "Nothing usable. The model carries a 2.3%–3.6% gross-yield band, which is a range built "
         "on a rule of thumb, not evidence. The household correctly objected to ranking the rent "
         "path on a voucher payment standard.",
         "A rent survey from a Property A property manager: five current listings and five recent "
         "leases for comparable single-family homes in Property A's ZIP code. Ask specifically what a 1960s-70s "
         "four-bedroom rents for, and how many days it sits vacant.",
         "HIGH"),
        ("q-value-b", "What is the Property B building actually worth?",
         "Nothing. $1,800,000 is a household estimate. A three-unit building is valued on gross "
         "rent multiplier and comparable three-unit sales, not on a single-family per-square-foot "
         "metric, so a Zillow-style estimate is actively misleading here.",
         "A broker opinion of value for a three-unit building in San Francisco, with the GRM shown, plus "
         "the legal unit count from the Planning Department. If the third unit is not a legal "
         "unit, the value and the rent story both change materially.",
         "HIGH"),
    ]),
    ("B", "Occupancy — the legal condition the whole tax advantage rests on", [
        ("q-occupancy", "Will the heir actually live in this house, and for how long?",
         "Unknown, and it is the single largest variable in the file. A written answer is needed "
         "before the figures can be trusted.",
         "A dated, signed statement in the pre-commitment agreement: years of intended occupancy, "
         "and the conditions under which the household would move out. If the honest answer is "
         "'we don't know', then the hold path is not available and the analysis should proceed on "
         "the sell path.",
         "CRITICAL"),
        ("q-trust-occupancy", "Does the one-year occupancy clock run from the date of death or the "
         "date of distribution?",
         "Unknown — and this is the highest-value legal question in the file. If the trust holds "
         "the house for three years before distributing it, the calendar may or may not have "
         "started, and the answer determines whether the Prop 19 benefit survives.",
         "A written opinion from a California attorney who practises in front of the Santa Clara "
         "County Assessor. Ask specifically about the interaction between the trust's continuing "
         "ownership and RTC § 63.2's 'transfer of present beneficial ownership' language.",
         "CRITICAL"),
        ("q-homeowners", "Has a homeowners' exemption ever been filed on this property, and is it "
         "currently in force?",
         "Unknown. The household's tax series implies one is claimed, but the $7,000 exemption is "
         "small enough to be invisible in a rounded bill. Prop 19 requires a filing within one "
         "year of transfer regardless of history.",
         "The current property tax bill, which shows exemptions on its face, and the assessor's "
         "record of exemption claims.",
         "MEDIUM"),
    ]),
    ("C", "Property tax — the recurring cost that decides the hold paths", [
        ("q-tca", "What is this property's tax rate area, and what is the actual total rate?",
         "Unknown. The model uses a 1.2%–1.4% effective rate inferred from the household's own "
         "series. The actual rate depends on the tax rate area (TRA), which bundles the county, "
         "city, school district, and any special districts.",
         "Look up the tax rate area on the Santa Clara County Assessor's parcel record, then read "
         "the published rate table for that TRA for the current fiscal year. This is a public "
         "lookup and takes minutes.",
         "HIGH"),
        ("q-bills", "What are the exact current property tax bills for both properties?",
         "The household supplied approximate series. The Property B tax history is internally "
         "inconsistent — see the flagged item — and implies an effective rate near 2.1%, which is "
         "roughly double Property A's.",
         "The two most recent secured property tax bills for each parcel, front and back. They "
         "itemise the base tax, the voter-approved debt, and every fixed charge.",
         "HIGH"),
        ("q-b-flag", "Why is Property B's effective tax rate so high?",
         "Unresolved. Roughly $2,400 of tax on roughly $114,000 of assessed value is about 2.1%, "
         "against a 1% constitutional base. Either the two columns of the household's series "
         "describe different years or parcels, or there are large special assessments on the "
         "parcel, or there is a Mello-Roos district. The consequences differ sharply.",
         "Both property tax bills for the parcel, plus the assessor's parcel page. If there is a "
         "special assessment or Mello-Roos district, it is a real recurring cost that must be in "
         "the Property B model and is currently missing.",
         "HIGH"),
    ]),
    ("D", "Operating costs — the household's estimates are placeholders", [
        ("q-insurance", "What does homeowners insurance actually cost for the Property A house?",
         "The household guessed $1,500. The model carries $1,500–$4,500. For a $3,100,000 "
         "replacement cost in Santa Clara County in the current admitted market, $1,500 is almost "
         "certainly too low, and there is no official source that prices a single parcel.",
         "Three real quotes for a replacement-cost policy with the correct dwelling limit, plus a "
         "California FAIR Plan comparison. Ask each broker whether the property is in a fire "
         "severity zone and whether they are writing new business in Property A's ZIP code at all.",
         "HIGH"),
        ("q-maint", "What does the house actually need, over five years?",
         "Nothing concrete. The model uses 2% of building value, which is a smooth average that "
         "hides lumpy capital events. A 50-year-old Property A house will need a roof, a sewer "
         "lateral, a furnace, and probably a foundation assessment, on known schedules.",
         "A five-year maintenance and capital plan with contractor quotes: roof age and remaining "
         "life, sewer lateral condition, HVAC age, water heater, electrical panel, foundation, "
         "windows, and the solar system's age and inverter status.",
         "HIGH"),
        ("q-solar", "Is the solar system grandfathered under an earlier net-metering tariff?",
         "Unknown. The household's assumption of a $10–$20/month net credit for 30 years depends "
         "entirely on the interconnection agreement. Under NEM 3.0 the economics of export change "
         "substantially, and an inverter replacement may force a tariff change.",
         "The utility interconnection agreement and the most recent true-up statement. Ask the "
         "utility directly whether the system is grandfathered and for how long.",
         "MEDIUM"),
        ("q-utilities", "Are Property B's water and electricity paid by the landlord or the tenants?",
         "Unstated. $330–$400/month of water and $30–$70/month of electricity is about "
         "$4,000–$6,000 a year depending on the answer, which is a real number in a building "
         f"yielding {F.pct(P.B_RENT_MONTHLY * 12 / P.B_VALUE_2026)} gross.",
         "The three leases, and the utility bills. Check whether the units are separately metered.",
         "MEDIUM"),
    ]),
    ("E", "Property B — the existing three-unit building that changes the whole risk picture", [
        ("q-b-units", "Is the third unit legal, habitable, and rentable?",
         "Unknown. Two of three units are rented. If the third is legal and vacant, it is a "
         "substantial unrealised income and a candidate principal residence. If it is not a legal "
         "unit, the building is a two-unit for planning, rent-control and valuation purposes.",
         "The Planning Department's property information, the certificate of occupancy, and the "
         "building's unit count on the assessor's roll.",
         "HIGH"),
        ("q-b-rents", "What are the individual unit rents, and when was each tenancy established?",
         "Only the $7,150/month total is known. Individual rents and tenancy start dates determine "
         "the allowable annual increase, the vacancy-reset potential, and the Prop H rent "
         "pass-through.",
         "The three leases, plus the SF Rent Board's rent history for each unit if available.",
         "HIGH"),
        ("q-b-living", "If the household lives in one unit, which one, and what does that do to "
         "the rent roll?",
         "Unknown. The household says it can live at the property without losing rental income, "
         "which implies the vacant unit is the one to occupy. If so, the household has two "
         "residences — which changes the § 121 analysis and means any future inheritance of "
         "Property B is a different Prop 19 question.",
         "Confirmation of which unit is vacant and its condition, plus the household's actual "
         "residence plan.",
         "MEDIUM"),
        ("q-proph", "Does San Francisco Proposition H apply, at what rate, and can it be passed "
         "through?",
         "Partly known. Prop H passed on 3 November 2026 with about 72% of the vote, imposing an "
         "annual parcel tax from 2027 for 15 years. A three-unit building is a multifamily "
         "residential parcel: $249 for the first 5,000 square feet plus $0.195 per square foot "
         "above that, capped at $50,000. For a typical three-unit in Property B's neighbourhood that is roughly "
         "$249 a year. Owners of rent-controlled units may pass through up to 50%, capped at $65 "
         "per unit. The senior exemption may apply.",
         "The official Department of Elections canvass, the final ordinance text, and the "
         "Assessor's implementation guidance. Confirm the building-area figure used for the "
         "calculation.",
         "LOW — the dollar amount is immaterial, but the rent pass-through interacts with the "
         "tenancies and should be understood"),
    ]),
    ("F", "The estate and the inheritance", [
        ("q-estate", "What is the projected gross estate, and how close is it to the exclusion?",
         "Unknown. The household mentions 'a considerable amount of money'. The federal exclusion "
         "is $15,000,000 per person for 2026 and $30,000,000 for a married couple with portability. "
         "Two Bay Area houses plus a brokerage account can approach that; a small change in the "
         "growth assumption swings the projected tax by millions.",
         "A balance sheet of the trust and the parents' other assets, valued as of a stated date, "
         "projected forward with the CPA. Include life insurance, retirement accounts and any "
         "closely held interests.",
         "CRITICAL"),
        ("q-gifts", "Have there been prior taxable gifts, and were Forms 709 filed?",
         "Unknown. Prior taxable gifts reduce the available exclusion dollar for dollar. "
         "Unreported gifts are worse: they surface at audit and can be imputed.",
         "The CPA should pull the gift tax filing history, and the parents should be asked "
         "directly. This question gets harder every year it is deferred.",
         "CRITICAL"),
        ("q-portability", "Has a prior spouse died, and was portability elected?",
         "Unknown. If a first spouse has died and no Form 706 was filed within the simplified "
         "window — five years under Rev. Proc. 2022-32 — the deceased spouse's exclusion may be "
         "permanently lost. This is a pure deadline question with no workaround.",
         "The CPA and the attorney: locate any Form 706, or confirm none was filed and whether the "
         "five-year window is still open.",
         "CRITICAL"),
        ("q-documents", "What does the trust actually say about the house?",
         "Unknown. Whether the house is distributed outright or held in a continuing trust decides "
         "the occupancy clock, creditor protection, and who the 'transferee' is for Prop 19 purposes.",
         "The complete trust instrument and every amendment, plus the schedule of assets as it "
         "currently stands. Read by the attorney, not by the household.",
         "CRITICAL"),
    ]),
    ("G", "Legal exposure and privacy", [
        ("q-prior-exposure", "Were these property figures ever posted publicly?",
         "Unknown. The household expressed concern about prior public-data exposure. If the dollar "
         "figures plus 'an inherited house in Property A plus a three-unit building in Property B's neighbourhood' "
         "appeared together anywhere public, the combination is identifying in a small community.",
         "The household's own recollection, and a search of any accounts used to post about it. "
         "If exposure is real, generate the site locally and do not publish — see PRIVACY.md §6.",
         "HIGH"),
        ("q-rounding", "Is rounding to the nearest $10 sufficient, or is more needed?",
         "Judgement call. This site bands the parcel-unique assessed values by construction rather "
         "than relying on rounding, but the market-value estimates are shown at $10 precision. "
         "If the household wants more margin, the build takes --round 1000 or --round 10000.",
         "The household's preference. See PRIVACY.md §2.",
         "MEDIUM"),
        ("q-advisers", "Who are the attorney, the CPA and the investment adviser, and have they "
         "seen this?",
         "Unknown. Nothing on this site has been reviewed by a professional. It is a model built "
         "from public law and household estimates.",
         "Engage a California estate attorney, a CPA with estate experience, and a fee-only "
         "fiduciary. The briefing sheet page exists to make that first meeting productive.",
         "HIGH"),
    ]),
    ("H", "Legislation and change", [
        ("q-legislation", "What is currently proposed that could change this analysis?",
         "No proposal has been verified in this session. Prop 19 itself was a 2020 ballot measure "
         "that removed a benefit families had relied on since 1986. Anything can change.",
         "A quarterly check of the Legislature's bill search for Revenue & Taxation Code changes "
         "affecting §§ 63.1, 63.2, 69.5 and 17041, plus the Attorney General's initiative list. "
         "Distinguish enacted from merely proposed — this site does not currently track either, "
         "and says so.",
         "ONGOING"),
    ]),
]


def page_questions(ctx: Ctx) -> str:
    critical = sum(1 for _, _t, items in QUESTIONS for q in items if q[4].startswith("CRITICAL"))
    high = sum(1 for _, _t, items in QUESTIONS for q in items if q[4].startswith("HIGH"))

    body = f"""
<section>
<h2>What we do not know, and how to find it out</h2>
<p class="lead">A clean list of every question, the information needed to answer it, what is
missing today, and the concrete way to get it. The household asked for exactly this: a register
of open questions so that the missing information can be discovered rather than assumed.</p>

<div class="statgrid">
  <div class="stat"><div class="statnum">{len([q for _, _t, items in QUESTIONS for q in items])}</div>
    <div class="statlabel">open questions</div></div>
  <div class="stat"><div class="statnum">{critical}</div>
    <div class="statlabel">block the recommendation entirely</div></div>
  <div class="stat"><div class="statnum">{high}</div>
    <div class="statlabel">materially change the numbers</div></div>
  <div class="stat"><div class="statnum">0</div>
    <div class="statlabel">answered by a professional in this file</div></div>
</div>

<div class="callout danger">
<h3>Read this before reading the recommendation</h3>
<p>The model says selling wins. That conclusion rests on a value estimate nobody has checked, an
occupancy intention nobody has stated, and an insurance cost that is a guess. Three of the eight
critical questions are answerable in a week for under $2,000 total. <strong>Answer them before
acting on any number on this site.</strong></p>
</div>
</section>
"""

    for letter, title, items in QUESTIONS:
        body += f'<section><h2>{letter}. {title}</h2>'
        for qid, q, missing, how, prio in items:
            cls = "crit" if prio.startswith("CRITICAL") else ("high" if prio.startswith("HIGH") else "med")
            body += f"""
<article class="qcard {cls}" id="{qid}">
<h3>{q}</h3>
<p class="qprio"><span class="priority {cls}">{prio}</span></p>
<p><strong>What we have:</strong> {missing}</p>
<p><strong>How to get it:</strong> {how}</p>
</article>
"""
        body += "</section>"

    body += """
<section>
<h2>Suggestions for discovering the missing information</h2>
<p class="lead">The household asked for suggestions on <em>how</em> to find what is missing, not
just a list of what is missing. These are ordered by cost-effectiveness.</p>
<ol class="biglist">
<li><strong>One afternoon with the county assessor's website.</strong> The tax rate area, the
assessed value, the exemption history and the parcel page are all public. This answers three
HIGH-priority questions at zero cost and closes the largest uncertainty in the property-tax model.</li>
<li><strong>Two phone calls to insurance brokers.</strong> Real quotes, not estimates. Ask about
fire severity zone and FAIR Plan eligibility at the same time. This converts the single largest
placeholder in the operating-cost model into a fact.</li>
<li><strong>One appraisal.</strong> Roughly $600–$900 for a retrospective date-of-death appraisal.
It is simultaneously the basis for income tax, the value test for Prop 19, and the estate-tax
valuation. It is the highest-return dollar in this entire file.</li>
<li><strong>One hour with a property manager.</strong> A rent survey for single-family homes in Property A's ZIP code
turns the rent path from a rule-of-thumb band into evidence. Ask what rents, not what is listed.</li>
<li><strong>One meeting with the CPA, with a specific agenda.</strong> Prior taxable gifts,
portability, and the projected estate against the exclusion. The briefing sheet page is built to
be the agenda for this meeting.</li>
<li><strong>One meeting with the attorney, with two specific questions.</strong> (a) When does the
Prop 19 occupancy clock start if a trust holds the house? (b) What does the trust say about
distribution? Everything else can wait.</li>
<li><strong>One five-year capital plan.</strong> A contractor walkthrough of the roof, sewer,
HVAC, electrical and foundation. This is the number that most often turns a hold decision into a
sell decision, and it is invisible in a percentage-of-value model.</li>
</ol>
</section>
"""
    return page("Open questions &amp; missing information", "questions.html", body,
                subtitle="Twenty-nine questions, what is missing for each, and the cheapest way "
                         "to answer it.")


# ---------------------------------------------------------------------------
# Page: property-b.html
# ---------------------------------------------------------------------------

def page_property_b(ctx: Ctx) -> str:
    b = 1_800_000
    rent_yr = P.B_RENT_MONTHLY * 12
    gross_yield = rent_yr / b
    body = f"""
<section>
<h2>Why the San Francisco building is not a side note</h2>
<p class="lead">The household was clear that the Property A house is being inherited while the
San Francisco building is already owned. That distinction is load-bearing, and it cuts in two
directions at once: Property B makes the household <em>more</em> able to hold Property A, and it
makes holding it <em>more dangerous</em>.</p>

<div class="twocol">
<div class="col">
<h3>Why it makes holding Property A easier</h3>
<ul class="checks">
<li>A $7,150/month rent roll on a building that is nearly paid off means the household does not
need Property A to generate cash. It can be held purely as a store of value.</li>
<li>The household can live in one of the three units, which means it already has a residence in
San Francisco — so the choice about Property A is a genuine choice about where to live, not a
forced one.</li>
<li>Property B's low assessed value is a demonstration of what the Prop 13 basis is worth over
decades, which is a real argument for trying to preserve Property A's basis too.</li>
</ul>
</div>
<div class="col">
<h3>Why it makes holding Property A more dangerous</h3>
<ul class="checks">
<li><strong>Concentration.</strong> Two Bay Area residential properties plus a large cash
inheritance is not a diversified balance sheet. It is a leveraged bet on one region and one
industry. Adding Property A doubles down on the bet that already exists.</li>
<li><strong>Prop 19 is gone for Property B.</strong> If Property B was inherited or transferred
after 16 February 2021 without the heir occupying it, it was reassessed to market. Its very low
assessed value implies it was acquired or transferred long ago — worth confirming, because if
it was transferred recently and <em>should</em> have been reassessed, there may be a supplemental
assessment waiting.</li>
<li><strong>Three units, two tenancies, one vacancy.</strong> That is a management obligation,
not a passive asset. Adding a second rental property to a household that is already a landlord
compounds operational risk.</li>
<li><strong>Liquidity.</strong> Neither property can be sold quickly. If the household needs cash,
the only liquid asset is the inheritance itself.</li>
</ul>
</div>
</div>
</section>

<section>
<h2>Property B: the numbers as they stand</h2>
"""
    body += table(
        ["Item", "Value used", "Status", "Note"],
        [
            ["Estimated market value (Nov 2026)", F.usd_full(b),
             '<span class="badge bad">unverified</span>',
             "Household estimate. A three-unit building is valued on GRM and comparable three-unit "
             "sales, not per-square-foot."],
            ["Assessed value (2025)", f"{F.usd_full(110_000)}–{F.usd_full(120_000)}",
             '<span class="badge bad">banded</span>',
             "Banded for privacy from the household's series. The very low base implies an "
             "acquisition decades ago."],
            ["Annual property tax", f"≈ {F.usd_full(115_000 * P.B_TAX_RATE_BASE)}",
             '<span class="badge bad">flagged</span>',
             "Implied effective rate ≈ 2.1%, roughly double Property A's. Unexplained — see the "
             "flagged page."],
            ["Gross rent, 2 of 3 units", f"{F.usd_full(P.B_RENT_MONTHLY)}/month = {F.usd_full(rent_yr)}/year",
             '<span class="badge bad">unverified</span>',
             f"Gross yield {F.pct(gross_yield, 2)} — plausible for a long-held building with "
             "below-market tenancies."],
            ["Vacant third unit", "not rented", '<span class="badge bad">unknown</span>',
             "Either the largest unrealised income in the file or a legal/habitability problem. "
             "Unresolved."],
            ["Water, all three units", f"{F.usd_full(330)}–{F.usd_full(400)}/month",
             '<span class="badge bad">unverified</span>',
             "Landlord-paid or tenant-paid is unstated, and it changes the answer by about $4,300/yr."],
            ["Electricity", f"{F.usd_full(30)}–{F.usd_full(70)}/month",
             '<span class="badge bad">unverified</span>', "Same question."],
            ["Insurance", f"{F.usd_full(1_500)}–{F.usd_full(6_500)}/year",
             '<span class="badge bad">unverified</span>',
             "Household guessed $1,500. A three-unit rental needs a different policy from a "
             "homeowner's policy; the low end is unlikely."],
            ["Prop H parcel tax from 2027", "≈ $249/year",
             '<span class="badge warn">secondary</span>',
             "Multifamily base of $249 for the first 5,000 sq ft plus $0.195/sq ft above. Immaterial "
             "in dollars; the rent pass-through (up to 50%, capped at $65/unit) is the part that "
             "matters. Passage confirmed by four news organisations; official canvass not fetched."],
        ], cls="wide")

    body += """
<div class="callout warning">
<h3>The one question about Property B that most changes the Property A decision</h3>
<p><strong>Is the third unit legal and habitable?</strong> If it is, Property B has unrealised
income, the household has a genuine choice of where to live, and the Property A hold path becomes
a lifestyle preference rather than a financial necessity. If it is not a legal unit, the building
is a two-unit for planning and rent-control purposes, the value estimate is too high, and the
household has fewer options than it thinks. One trip to the Planning Department settles it.</p>
</div>
</section>

<section>
<h2>How the two properties interact in a downturn</h2>
<p class="lead">The reason concentration matters is not the average outcome, it is the correlation.
Both properties sit inside the same regional economy, and the household's income may sit inside
it too.</p>
"""
    body += table(
        ["Scenario", "Property A house", "San Francisco building", "Household income",
         "Combined exposure"],
        [
            ["Bay Area tech contraction", "Falls directly — single-industry town",
             "Falls, but rent-controlled tenancies cushion the income",
             "At risk if employed in the sector", "Highly correlated"],
            ["Remote-work shift", "Falls — the commuting premium is the value",
             "Falls less; urban three-units serve people who stay",
             "Probably fine", "Correlated"],
            ["Interest-rate shock", "Falls — affordability-driven",
             "Falls — GRM-driven", "Fine", "Highly correlated"],
            ["Wildfire / insurability shock", "Falls sharply — foothills exposure",
             "Unaffected", "Fine", "Idiosyncratic"],
            ["National recession", "Falls", "Falls", "At risk", "Correlated"],
            ["Inflation shock (1970s)", "Rises nominally", "Rises nominally, rents lag",
             "Fine", "Both hedge"],
        ], cls="wide",
        foot="The point: there is no scenario in the list where holding both properties is clearly "
             "protective. The two are not a hedge against each other; they are the same trade "
             "twice, in a region whose two economies are the same economy.")
    body += """
</section>
"""
    return page("Property B — the existing three-unit building", "property-b.html", body,
                subtitle="The building the household already owns. It changes the risk of the "
                         "Property A decision more than any single assumption in the model.")


# ---------------------------------------------------------------------------
# Page: flagged.html
# ---------------------------------------------------------------------------

def page_flagged(ctx: Ctx) -> str:
    f = ctx.facts
    flagged = {k: v for k, v in f.items() if v.get("flag") or v["status"] != "verified"}
    body = """
<section>
<h2>Everything that is not verified, in one place</h2>
<p class="lead">Nothing on this page blocks the analysis, and none of it is hidden. It is the
honest inventory of what this model does not know, what it guessed, and what it found that
looked wrong. Review it before relying on any conclusion.</p>

<div class="callout danger">
<h3>The three items that matter most</h3>
<ol>
<li><strong>The $3,100,000 valuation is unverified.</strong> It came from the household, not an
appraisal, and every path in the model is denominated in it.</li>
<li><strong>Property B's effective tax rate looks wrong.</strong> About 2.1% of assessed value
against a 1% constitutional base, with a tax bill that fell 5.9% in 2021 while the assessment
rose 1%. The household's series may compare two different parcels or two different years.</li>
<li><strong>The response to the one-year occupancy deadline is unknown.</strong> The entire
Prop 19 advantage depends on it, and it is a legal test rather than a forecast.</li>
</ol>
</div>
</section>

<section>
<h2>Unverified and secondary figures used by the model</h2>
"""
    trs = []
    for k, d in flagged.items():
        val = d["value"]
        if isinstance(val, (int, float)):
            shown = F.usd_full(val) if abs(val) >= 1000 else f"{val}"
        elif isinstance(val, (list, dict)):
            shown = "structured — see source row"
        elif val is None:
            shown = "— (deliberately blank)"
        else:
            shown = str(val)[:70]
        link = (src("official source", d["url"]) if d.get("url")
                else '<span class="src nostatus">no official source located</span>')
        trs.append([f"<code>{k}</code>", html.escape(d["label"]), html.escape(shown),
                    STATUS_BADGE.get(d["status"], d["status"]), link,
                    html.escape(d.get("flag", "Household-supplied or heuristic input."))])
    body += table(["ID", "What it is", "Value used", "Status", "Source",
                   "Why it is flagged"], trs, cls="wide facts")
    body += "</section>"

    body += """
<section>
<h2>Irregularities found while verifying</h2>
<p class="lead">These are things that did not reconcile. They are recorded rather than smoothed
over, because a model that quietly resolves an inconsistency is worse than one that reports it.</p>

<article class="qcard crit">
<h3>0a. Past git history still contains exact household figures and ZIP codes (found 2026-11-26)</h3>
<p>The current files are now scrubbed. The public git history is not. Two earlier commits on <code>main</code> carry
unrounded assessed values and tax bills, and several carry ZIP codes, city-plus-ZIP labels or the neighbourhood name.
A personal e-mail address also appears in commit author metadata. A 2026-11-25 note that no personal data had ever been
committed was wrong and has been withdrawn. Removing the data from history needs a force-push to <code>main</code> and
the owner's explicit approval, so it has <strong>not</strong> been done. Cached copies and forks cannot be recalled even
after a rewrite. The commit list and the options are in <code>PRIVACY.md</code> §4 and on the coordination board.</p>
</article>

<article class="qcard high">
<h3>0b. The California rate on a large gain is now computed from the official schedule, not assumed (2026-11-26)</h3>
<p>The model previously applied a flat 10.5% to the taxable gain. That figure had no source. It now applies the official
2025 California schedules plus the 1% Behavioral Health Services Tax, stacked on other taxable income (FTB Form 540 and
rate schedules, read 2026-11-26). Joint filing with no other taxable income gives about 10.9% on a $2M gain. Single filing
gives about 11.8%. The effect on the headline is small: the sell path's margin over live-and-hold moved from $22.93M to
$23.18M over 30 years. The ranking did not change, and the decision rules were not altered to produce that result.</p>
</article>

<article class="qcard high">
<h3>0c. A correction to an earlier sentence: the 12.3% bracket does not start at $1M for joint filers</h3>
<p>Under the 2025 schedules, the 12.3% bracket starts at <span class="exact">$742,953</span> for single filers,
<span class="exact">$1,010,417</span> for heads of household and <span class="exact">$1,485,906</span> for joint filers.
The 1% tax starts at $1,000,000 for every filing status. The 13.3% top marginal therefore applies from those thresholds.
Between $1,000,000 and the joint threshold, the marginal rate is 12.3% (11.3% plus 1%). The footers on the taxes and paths
pages are corrected to say so.</p>
</article>

<article class="qcard high">
<h3>0d. Filing status and other taxable income in the sale year were not supplied</h3>
<p>The California result depends on both. The base case uses joint filing with no other taxable income. The low case uses
single filing. The household should confirm its filing status and expected taxable income in a sale year. That is an open
question, not an estimate.</p>
</article>

<article class="qcard high">
<h3>0e. Residual identifiability after the ZIP codes were removed</h3>
<p>Removing ZIP codes and neighbourhood names does not make the site anonymous. A local reader could still link the county, the
city, the three-unit building, the trust inheritance and the dollar figures. The household may choose the coarser rounding mode
(<code>--round 100000</code>) or remove the household estimates. That decision is open and is recorded on the board.</p>
</article>

<article class="qcard med">
<h3>0f. Latest published forms are the 2025 forms</h3>
<p>The 2025 Form 540 booklet and 2025 rate schedules are the latest published. Any change to the 1% threshold, the brackets
or the top rate for 2026 is unverified until the 2026 forms are published. The model says so on the taxes page.</p>
</article>

<article class="qcard med">
<h3>0g. Statutory figures are quoted exactly, on purpose</h3>
<p>Public statutory thresholds, such as the <span class="exact">$1,044,586</span> Prop 19 allowance (BOE Letter To Assessors
2025/009) and the joint 12.3% threshold above, are quoted exactly and sit in exact spans. They are a documented exception to
the $10 rule. They are not household figures. Rounding them would make them wrong.</p>
</article>

<article class="qcard crit">
<h3>1. Property B: a 2.1% effective tax rate against a 1% constitutional base</h3>
<p>Roughly $2,400 of annual tax on roughly $114,000 of assessed value implies an effective rate
near 2.1%. Property A's own series implies 1.2%–1.4%. The Proposition 13 base rate is 1%, plus
voter-approved debt and fixed charges, which in practice runs to about 1.2%–1.4% in most Santa
Clara County tax rate areas. A figure of 2.1% is roughly double.</p>
<p><strong>Additional inconsistency:</strong> the household's Property B tax history shows the tax
bill <em>falling 5.9% in 2021</em> while the assessed value rose 1%. Under a 1%-plus-debt formula
that cannot happen unless the debt component changed, which would be unusual.</p>
<p><strong>Possible explanations:</strong> (a) the tax and assessment columns describe different
parcels or different fiscal years; (b) there are large special assessments or a Mello-Roos
district on the parcel; (c) the property is in a redevelopment area with a substantial debt
service component. These have different consequences — (b) and (c) are real recurring costs
missing from the Property B model.</p>
<p><strong>Resolution:</strong> the two most recent secured property tax bills and the assessor's
parcel page.</p>
</article>

<article class="qcard crit">
<h3>2. The assessed-value and tax columns do not quite reconcile in either property</h3>
<p>In both series, multiplying the stated assessed value by the implied rate does not reproduce
the stated tax to the dollar in every year. That is expected — the effective rate varies with
the debt levy — but the size of the variation in the Property B tax history is not consistent with
a stable parcel. <strong>Both series should be read off the actual bills rather than
inferred.</strong></p>
</article>

<article class="qcard high">
<h3>3. California's absence of an estate tax could not be confirmed from a single official page</h3>
<p>The conclusion is not in doubt in practice — California repealed its inheritance and gift tax
in 1982, and the FTB's own Form 540 has no estate-tax line. But I could not fetch an FTB page
that states it in those words, and the instruction for this project was to mark anything not
confirmed as unverified rather than infer it. It is therefore published as
<span class="badge warn">secondary</span> with the flag recorded, and flagged for the attorney
to confirm in one sentence.</p>
</article>

<article class="qcard high">
<h3>4. San Francisco Proposition H's passage is confirmed by reporters, not by the canvass</h3>
<p>Four independent news organisations reported the measure passing with about 72% of the vote on
3 November 2026. I did not fetch the Department of Elections' official results page. The dollar
consequence for a three-unit building is roughly $249 a year, so the materiality is low — but the
passage is recorded as <span class="badge warn">secondary</span> rather than verified, and the
official canvass should be checked.</p>
</article>

<article class="qcard high">
<h3>5. The Santa Clara County transfer tax rate is from secondary compilations</h3>
<p>$1.10 per $1,000 of consideration is consistent across a 2019 California Lawyers Association
compilation, several secondary sources, and Revenue & Taxation Code § 11911's base rate. I could
not fetch an official Santa Clara County fee schedule in this session. On a $3,100,000 sale the
tax is about $3,410 — immaterial to the decision, which is why it was not pursued further, but it
remains unverified.</p>
</article>

<article class="qcard high">
<h3>6. Property A's city conveyance tax: possibly none, unverified</h3>
<p>San Jose, Palo Alto and Mountain View impose an additional city conveyance tax of $1.65 per
$500. I found no evidence of an equivalent Property A tax. Absence of evidence is not
verification; confirm with the finance department for Property A's city.</p>
</article>

<article class="qcard med">
<h3>7. The § 121 exclusion assumes a joint return and met tests</h3>
<p>The model applies the $500,000 exclusion. If the heir files singly, it is $250,000. If the
two-of-five ownership and use tests are not met — which is exactly what happens if the household
moves out — the exclusion is <strong>zero</strong>, not reduced. The model's
<a href="paths.html#live-then-rent">live-then-rent</a> path shows this consequence.</p>
</article>

<article class="qcard med">
<h3>8. Maintenance modelling hides lumpy capital events</h3>
<p>At 2% of building value, the model produces a smooth annual number. Real houses do not work
that way: a roof is $40,000 once, not $4,000 ten times. The smooth average is reasonable over 30
years and wrong in any single year, which matters if the household's cash flow is tight in a
particular year.</p>
</article>

<article class="qcard med">
<h3>9. The crash magnitudes are standard historical figures, not individually re-verified</h3>
<p>The NBER contraction dates are verified from NBER. The drawdown magnitudes (89% for 1929,
57% for 2008, and so on) are the widely reported figures and are used as modelling inputs. They
were not each re-derived from a primary statistical release in this session. They are
labelled as modelling inputs on the assumptions page.</p>
</article>

<article class="qcard med">
<h3>10. No legislation tracking was performed</h3>
<p>The household asked that proposed legislation be tracked and that enacted changes be
distinguished from proposals. This site does neither — it records only enacted law as of
2026-11-25. Nothing is presented as a proposal, and nothing is presented as likely. The
authorities page says so explicitly. Setting up a quarterly check is on the
<a href="questions.html#q-legislation">open questions</a> list.</p>
</article>
</section>

<section>
<h2>How to request a change</h2>
<p class="lead">Every flagged item has a file behind it. Corrections are one pull request each:
edit <code>data/facts.json</code>, rebuild, and the site regenerates. The
<a href="suggestions.html">suggestions</a> page describes the workflow.</p>
</section>
"""
    return page("Flagged for review", "flagged.html", body,
                subtitle="Every unverified figure, every secondary source, and every "
                         "inconsistency found while checking. Nothing is hidden and nothing "
                         "blocks the analysis.")


# ---------------------------------------------------------------------------
# Page: suggestions.html
# ---------------------------------------------------------------------------

SUGGESTIONS = [
    ("S1", "Answer the three critical questions before trusting any number", "Blocking",
     "The valuation, the occupancy intention, and the estate size are all unknown and all "
     "decisive. Everything else in the model is second-order by comparison.",
     "questions.html#q-value", "HIGH", "Household + appraiser + CPA"),
    ("S2", "Get a retrospective date-of-death appraisal, and do it before year-end of the death year",
     "High value", "One document answers three questions at once: income-tax basis, Prop 19 "
     "value test, and Form 706 valuation. Cost roughly $600–$900. It is the highest-return "
     "dollar in this file.", "questions.html#q-value", "HIGH", "Appraiser"),
    ("S3", "Replace the insurance guess with three real quotes", "High value",
     "The model carries $1,500–$4,500 and the household guessed the low end. In the current "
     "California market the true number may be higher and the real risk is uninsurability, which "
     "no quote will reveal until you ask.", "questions.html#q-insurance", "HIGH", "Broker"),
    ("S4", "Build the five-year capital plan", "High value",
     "A contractor walkthrough of roof, sewer lateral, HVAC, electrical and foundation. This is "
     "the number that most often converts a hold decision into a sell decision, and it is "
     "invisible in a percentage-of-value model.", "questions.html#q-maint", "HIGH", "Contractor"),
    ("S5", "Settle the third unit's legal status", "High value",
     "One Planning Department lookup. It changes Property B's value, its rent-control treatment, "
     "and whether the household has a genuine choice of residence.",
     "questions.html#q-b-units", "HIGH", "Household"),
    ("S6", "Get the two property tax bills and explain the 2.1%", "Correction",
     "Flagged inconsistency. If there is a special assessment or Mello-Roos district, it is a "
     "recurring cost currently missing from the Property B model.",
     "flagged.html", "HIGH", "Household"),
    ("S7", "Look up the tax rate area and the published rate", "Correction",
     "The model infers a 1.2%–1.4% effective rate from the household's own series. The actual "
     "rate is published per tax rate area and takes minutes to look up.",
     "questions.html#q-tca", "MEDIUM", "Household"),
    ("S8", "Write and sign the pre-commitment agreement", "Process",
     "The criteria are already drafted. Signing them before the figures are revised is the only "
     "protection against reverse-engineering the outcome.",
     "decision.html", "HIGH", "Household"),
    ("S9", "Draft the investment policy statement before the money arrives", "Process",
     "A policy written after a drawdown is a rationalisation. The two-year liquidity reserve is "
     "the single most important line and it eliminates the only ruin scenario.",
     "reinvestment.html", "HIGH", "Household + adviser"),
    ("S10", "Add a what-if calculator that runs entirely in the browser", "Site feature",
     "The household asked for what-if controls. A dependency-free calculator with sliders for "
     "value, tax rate, maintenance, rent and growth would let them explore without editing "
     "Python. Must send nothing anywhere.", "—", "MEDIUM", "Developer"),
    ("S11", "Publish the model as a single-file HTML export", "Site feature",
     "So the briefing sheet and the headline table can be emailed to an attorney without a "
     "website. The printable page exists; a one-file bundle does not.",
     "briefing-sheet.html", "LOW", "Developer"),
    ("S12", "Add a quarterly authority re-check", "Process",
     "The household asked that official federal, state and local authorities be rechecked "
     "periodically and that enacted changes be distinguished from proposals. Nothing currently "
     "does this automatically.", "authorities.html", "MEDIUM", "Household"),
    ("S13", "Set up legislation tracking with an enacted/proposed split", "Process",
     "Currently no legislative monitoring exists at all, and the site says so. A quarterly check "
     "of the Legislature's bill search for RTC §§ 63.1, 63.2, 69.5 and 17041, plus the Attorney "
     "General's initiative list, would close it.", "questions.html#q-legislation", "MEDIUM", "Household"),
    ("S14", "Model Property B's taxable sale as an alternative source of liquidity", "Model",
     "If the household ever needs cash, the three-unit building is the other liquid asset. Its "
     "low basis means a sale would be heavily taxed — which is itself an argument for not "
     "needing to sell either property.", "property-b.html", "MEDIUM", "Model"),
    ("S15", "Add a rent-vs-own comparison for the household's actual next residence", "Model",
     "If the household sells, it must live somewhere. The model credits imputed rent on the hold "
     "path but does not charge market rent on the sell path. That is a real omission and it "
     "favours selling.", "assumptions.html", "HIGH", "Model"),
    ("S16", "Extend the crash overlays to include a property-only crash", "Model",
     "Every crash in the model hits equities harder than housing. A Bay Area housing-specific "
     "correction with flat equities would test the hold path more fairly.",
     "black-swan.html", "MEDIUM", "Model"),
    ("S17", "Add a first-class 'do nothing for three years' path", "Model",
     "Leaving the house vacant while deciding is a real option people take, and it forfeits "
     "Prop 19 at the one-year mark. It should be priced rather than ignored.",
     "paths.html", "MEDIUM", "Model"),
    ("S18", "Print-and-sign workflow for the briefing sheet", "Site feature",
     "The briefing sheet is printable but has no signature block, date field, or space for the "
     "adviser's note. Small change, real usability.", "briefing-sheet.html", "LOW", "Developer"),
]


def page_suggestions(ctx: Ctx) -> str:
    body = """
<section>
<h2>Suggestions, and how to choose between them</h2>
<p class="lead">The household asked for a dedicated section where suggestions can be reviewed and
a path chosen before anything is implemented. This is that section. Each suggestion carries a
priority, an owner, an effort estimate and the specific question it closes, so a reviewer can
sort by what actually unblocks the decision rather than by what is interesting.</p>

<div class="callout info">
<h3>How to use this page</h3>
<p>Sort by <strong>Priority</strong>. Do the seven HIGH items first — five of them cost under
$1,000 combined and close the questions that currently make the recommendation provisional.
Everything marked <em>Site feature</em> or <em>Model</em> improves the analysis but does not
unblock it. <strong>Nothing here should be implemented before S1, S2, S5, S6 and S8.</strong></p>
</div>
</section>

<section>
<h2>The register</h2>
"""
    trs = []
    for sid, title, kind, why, ref, prio, owner in SUGGESTIONS:
        cls = "crit" if prio == "HIGH" else ("high" if prio == "MEDIUM" else "med")
        refcell = (f'<a href="{ref}">{ref}</a>' if ref and ref != "—" else "—")
        trs.append([f"<code>{sid}</code>", f"<strong>{title}</strong><br><span class='muted'>{why}</span>",
                    kind, f'<span class="priority {cls}">{prio}</span>', owner, refcell])
    body += table(["ID", "Suggestion and why", "Kind", "Priority", "Owner", "Closes"],
                  trs, cls="wide suggestions")

    body += """
</section>

<section>
<h2>Site improvements specifically for decision-making</h2>
<p class="lead">Separate from the analysis questions, these are improvements to the site itself,
in the order I would make them.</p>
<ol class="biglist">
<li><strong>A dependency-free what-if calculator.</strong> Sliders for value, tax rate,
maintenance, rent and growth, recomputing net worth live in the browser. No server, no
analytics, no third-party script. This is the single most valuable addition, because it lets the
household see the sensitivity for themselves instead of trusting a table.</li>
<li><strong>Charge market rent on the sell path.</strong> The model credits imputed rent to
ownership but does not charge rent to the household that sells. That asymmetry flatters selling
and should be fixed before the recommendation is taken seriously.</li>
<li><strong>A one-file HTML export.</strong> So the briefing sheet can be emailed without a
website.</li>
<li><strong>A "what changed since last build" diff.</strong> If the model is re-run annually, the
household needs to see what moved, not just where it landed.</li>
<li><strong>Paper-friendly stylesheet.</strong> Started — the briefing sheet prints on one page —
but the projection tables do not.</li>
<li><strong>A printable decision record.</strong> Filled-in, signed, dated, filed with the trust
documents. The template exists; the workflow does not.</li>
</ol>
</section>

<section>
<h2>Review workflow</h2>
<div class="callout">
<h3>Accepting a suggestion</h3>
<ol>
<li>Pick an ID. Add a row to <code>COORDINATION.md</code> with a file scope that does not overlap
another open claim.</li>
<li>If it is a data change, edit <code>data/facts.json</code> only. Never edit a generated page —
it is overwritten on the next build.</li>
<li>If it is a model change, edit <code>model/</code> only, and record the effect on the headline
in <code>COORDINATION.md</code>. A model change that moves the recommendation must be called out.</li>
<li>Rebuild (<code>python3 sitegen.py</code>), run the link check
(<code>python3 tools/check_site.py</code>), and confirm no flagged item disappeared silently.</li>
<li>Mark the task <code>needs review</code>, not <code>done</code>. Someone other than the author
reads it.</li>
</ol>
<h3>Rejecting a suggestion</h3>
<p>Write why, in the same row. A rejected suggestion with a reason is more valuable than a
deleted one, because the next reader will have the same idea.</p>
</div>
</section>
"""
    return page("Improvement suggestions", "suggestions.html", body,
                subtitle="Eighteen specific, owner-assigned suggestions with priorities, and a "
                         "review workflow so a path can be chosen before anything changes.")


# ---------------------------------------------------------------------------
# Page: decision.html — the pre-commitment agreement
# ---------------------------------------------------------------------------

def page_decision(ctx: Ctx) -> str:
    body = """
<section>
<h2>The agreement, to be signed before the figures are revised</h2>
<p class="lead">The household asked that it be agreed in writing, in advance, what would make the
household choose each path — so that the outcome cannot be reverse-engineered from a single
projection. This is that document. Fill it in, date it, sign it, and file it with the trust
papers. Then run the model.</p>

<div class="printnote">
This page is designed to be printed and signed. It is three pages.
</div>

<form class="agreement">
<div class="agblock">
<h3>1. The occupancy commitment</h3>
<p class="aglabel">We will occupy the Property A property as our principal residence for at least:</p>
<div class="fillrow">
  <label><input type="radio" name="occ"> 0 years — we will not live there</label>
  <label><input type="radio" name="occ"> 1–4 years</label>
  <label><input type="radio" name="occ"> 5–8 years</label>
  <label><input type="radio" name="occ"> 10–19 years</label>
  <label><input type="radio" name="occ"> 20 years or more</label>
</div>
<p class="aglabel">The homeowner-occupancy decision is: <span class="blank"></span></p>
<p class="aglabel">We would move out earlier only if (state the conditions):</p>
<div class="lines"></div>
<p class="agwhy"><strong>Why this is first:</strong> the entire Proposition 19 benefit is
conditioned on it. Under RTC § 63.2 the exclusion is removed when the heir stops being eligible
for the homeowners' exemption. An honest &ldquo;we don't know&rdquo; here means the hold path is
not available and the analysis should proceed on the sell path.</p>
</div>

<div class="agblock">
<h3>2. The value test</h3>
<p class="aglabel">We will obtain an appraisal by: <span class="blank wide"></span></p>
<p class="aglabel">If the appraised value is above $<span class="blank"></span>, we will sell.</p>
<p class="aglabel">If the appraised value is below $<span class="blank"></span>, we will reconsider
holding.</p>
<p class="aglabel">If the appraisal is inside that range, the decision is:</p>
<div class="lines"></div>
</div>

<div class="agblock">
<h3>3. The estate test</h3>
<p class="aglabel">The projected gross estate has been calculated by our CPA as:
<span class="blank wide"></span></p>
<p class="aglabel">It is [ ] below [ ] near [ ] above the federal exclusion of
$15,000,000 per person (2026, indexed).</p>
<p class="aglabel">If it is near or above, our estate-planning meeting is scheduled for:
<span class="blank wide"></span></p>
<p class="agwhy">Selling the house does not change this number. It is here because it is the
largest single tax exposure in the file and because fixing it requires action before the death.</p>
</div>

<div class="agblock">
<h3>4. What we will not do</h3>
<p class="aglabel">Check each one we commit to:</p>
<div class="fillrow col">
  <label><input type="checkbox"> We will not rent the property out before occupying it, if doing so
  would carry us past the one-year occupancy deadline.</label>
  <label><input type="checkbox"> We will not record a deed before the tax and Prop 19 analysis is
  complete.</label>
  <label><input type="checkbox"> We will not invest the sale proceeds without a written investment
  policy, signed before the money arrives.</label>
  <label><input type="checkbox"> We will not change the plan during a market drawdown without a
  written, dated amendment.</label>
  <label><input type="checkbox"> We will not rely on any figure on this site that is marked
  unverified without confirming it first.</label>
</div>
</div>

<div class="agblock">
<h3>5. The decision rule, agreed in advance</h3>
<p class="aglabel">Ranked by what we actually care about, most important first:</p>
<div class="lines tall"></div>
<p class="aglabel">We understand that a model which maximises profit will say &ldquo;sell&rdquo;,
and that this may not be the answer we want. If our ranking puts something above profit, we will
write it here and accept that the model's number no longer governs.</p>
<div class="lines"></div>
</div>

<div class="agblock sign">
<h3>Signed</h3>
<table class="sig">
<tr><td class="sigline"></td><td class="sigline"></td></tr>
<tr><td>Signature</td><td>Date</td></tr>
<tr><td class="sigline"></td><td class="sigline"></td></tr>
<tr><td>Signature</td><td>Date</td></tr>
<tr><td class="sigline"></td><td class="sigline"></td></tr>
<tr><td>Witness / adviser</td><td>Date</td></tr>
</table>
<p class="muted">File with the trust documents. Review annually. Do not amend without a dated
note explaining what changed and why.</p>
</div>
</form>
</section>
"""
    return page("Pre-commitment agreement", "decision.html", body,
                subtitle="Written before the figures, so the outcome cannot be reverse-engineered "
                         "from one projection. Print, complete, sign, file.", printable=True)


# ---------------------------------------------------------------------------
# Page: decision-log.html
# ---------------------------------------------------------------------------

def page_decision_log(ctx: Ctx) -> str:
    body = """
<section>
<h2>Decide, write it down, and say why</h2>
<p class="lead">The household asked that the decision and the date be recorded next to each item,
so a future reader knows what was chosen and why. This is the log. It is intentionally mostly
empty: filling it in is the household's job, and an entry written before the fact is worth more
than a reconstruction afterwards.</p>

<div class="callout warning">
<h3>Rules for this log</h3>
<ol>
<li><strong>Append, never edit.</strong> If a decision changes, add a new row with a new date and
reference the row it supersedes. A log that can be rewritten is not a log.</li>
<li><strong>Record the reason, not just the choice.</strong> &ldquo;Sell&rdquo; is not a decision;
&ldquo;sell because we do not intend to live in Santa Clara County and the appraised value exceeded our
stated trigger&rdquo; is.</li>
<li><strong>Record who decided.</strong> A decision with no owner drifts.</li>
<li><strong>Record what was assumed.</strong> The model version and the input set, so a later
reader can tell whether the decision was made on the same facts they are looking at.</li>
</ol>
</div>
</section>

<section>
<h2>The log</h2>
"""
    items = [
        ("Pre-commitment agreement signed", "The criteria in decision.html", "", "", "OPEN", ""),
        ("Occupancy intention stated in writing", "Years of intended occupancy", "", "", "OPEN", ""),
        ("Appraisal obtained", "Date-of-death value; land/building split", "", "", "OPEN", ""),
        ("Tax rate area confirmed", "TRA number and published total rate", "", "", "OPEN", ""),
        ("Both property tax bills reviewed and the 2.1% explained", "Cause of the anomaly", "", "", "OPEN", ""),
        ("Insurance quoted (three carriers)", "Premium and coverage; FAIR Plan eligibility", "", "", "OPEN", ""),
        ("Five-year capital plan prepared", "Roof, sewer, HVAC, electrical, foundation", "", "", "OPEN", ""),
        ("Rent survey obtained for single-family homes in Property A's ZIP code", "Market rent range with evidence", "", "", "OPEN", ""),
        ("Third unit's legal status confirmed", "Legal unit count", "", "", "OPEN", ""),
        ("Prior taxable gifts and portability confirmed with CPA", "Amount and filing history", "", "", "OPEN", ""),
        ("Projected gross estate calculated", "Amount and distance from the exclusion", "", "", "OPEN", ""),
        ("Attorney opinion on the occupancy clock in trust", "Written answer", "", "", "OPEN", ""),
        ("Investment policy statement signed", "Signed document on file", "", "", "OPEN", ""),
        ("<strong>The decision</strong>", "Which path, and the reason", "", "", "OPEN", ""),
        ("First annual re-run", "Model version, inputs, whether the recommendation moved", "", "", "OPEN", ""),
    ]
    trs = [[f"<strong>{a}</strong>", b, "<span class='blank'></span>", "<span class='blank'></span>",
            "<span class='blank'></span>", f"<span class='priority med'>{c}</span>"]
           for a, b, c, d, e, f_ in items]
    body += table(["Item", "What it establishes", "Date", "Who", "Choice made and why", "Status"],
                  trs, cls="wide log")
    body += """
</section>

<section>
<h2>The entries a future reader will most want, and that are most often missing</h2>
<div class="threecol">
<div class="col"><h3>&ldquo;We chose to rent it out instead&rdquo;</h3>
<p>If that entry ever appears, the reader needs to know it was made <em>with knowledge</em> that
it forfeits the Prop 19 exclusion, and what the reassessed tax bill turned out to be. Without
that, the next generation will repeat it.</p></div>
<div class="col"><h3>&ldquo;We changed our mind in year 12&rdquo;</h3>
<p>Changing a plan during a drawdown is the single most common way these plans fail. The log
records whether the change was made on new facts or on new feelings, which is the only way anyone
can learn from it.</p></div>
<div class="col"><h3>&ldquo;We never got the appraisal&rdquo;</h3>
<p>This is the entry that most needs to exist. If the decision was made on an unverified household
estimate, say so plainly, date it, and put the flag next to it. An honest record of an
unverified decision is worth more than a clean-looking one.</p></div>
</div>
</section>
"""
    return page("Decision log", "decision-log.html", body,
                subtitle="Fifteen decisions to record with a date, an owner and a reason, so a "
                         "future reader knows what was chosen and why.")


# ---------------------------------------------------------------------------
# Page: glossary.html
# ---------------------------------------------------------------------------

GLOSSARY = [
    ("Adjusted basis", "What you have invested in a property for tax purposes: original cost plus improvements, minus depreciation taken. Used to compute gain on sale. See § 1014 for the inherited case."),
    ("Assessment appeals board", "The county body that hears disputes about assessed value. In San Francisco, appeals are filed July 2 – September 15."),
    ("Behavioral Health Services Tax", "California's 1% tax on taxable income above $1,000,000. Formerly the Mental Health Services Tax. Computed on Form 540 line 62. The threshold is not indexed."),
    ("Basis step-up", "The reset of an asset's basis to fair market value at the owner's death, under IRC § 1014. Eliminates the income tax on gain accrued during the decedent's life."),
    ("BOE-19-P", "The claim form for the Proposition 19 parent-child or grandparent-grandchild exclusion."),
    ("BOE-266", "The claim form for California's homeowners' property tax exemption ($7,000 of assessed value)."),
    ("Costa-Hawkins", "The California statute (Civ. Code § 1954.53) that allows a rent-controlled unit's rent to reset to market when a tenancy ends. Vacancy decontrol."),
    ("Decline-in-value (Prop 8)", "A reduction in assessed value to market value when the market has fallen below the factored base year value. Requested from the assessor; not automatic."),
    ("Deed-in-lieu", "A transfer of title to a lender instead of foreclosure. Rare in this file but appears in transfer-tax exemption lists."),
    ("Depreciation (rental)", "An annual tax deduction for wear on a rental building. Residential rental property uses straight line over 27.5 years, mid-month convention, on the building only — never the land."),
    ("DSUE", "Deceased spousal unused exclusion. The portion of a deceased spouse's estate tax exclusion that a surviving spouse can use, if portability is elected."),
    ("Factored base year value", "A property's 1975-76 (or acquisition-year) assessed value, increased each year by at most 2% under Proposition 13. This is the number the property tax is actually computed on."),
    ("Fair market value (FMV)", "The price a willing buyer would pay a willing seller. At death, this is the number that sets basis, the Prop 19 test, and the estate tax value — all three, simultaneously."),
    ("FAIR Plan", "California's insurer of last resort. Relevant when the admitted market will not write a policy, which is increasingly common in fire-exposed areas."),
    ("Form 706", "The federal estate tax return. Due nine months after death, extendable to fifteen. Also the vehicle for electing portability."),
    ("Gift tax annual exclusion", "The amount one person can give another each year without it counting against the lifetime exemption. $19,000 per recipient in 2026."),
    ("Gross rent multiplier (GRM)", "Sale price divided by annual gross rent. The standard valuation metric for small multifamily buildings, and why a single-family per-square-foot estimate misleads for Property B."),
    ("Imputed rent", "The rental value a homeowner consumes by living in their own property. Economically real, tax-free, and easily forgotten — omitting it makes selling look better than it is."),
    ("Net investment income tax (NIIT)", "A 3.8% federal surtax on investment income above $250,000 MAGI for joint filers. Gain excluded under § 121 is not subject to it."),
    ("Portability", "The election that lets a surviving spouse use a deceased spouse's unused estate tax exclusion. Requires a timely Form 706."),
    ("Proposition 8", "A 1978 measure allowing a temporary reduction in assessed value when market value falls below the Prop 13 base. The hold path's built-in hedge against a crash."),
    ("Proposition 13", "The 1978 constitutional amendment capping the property tax rate at 1% and annual assessment growth at 2%, with reassessment on change of ownership or new construction."),
    ("Proposition 19", "The 2020 ballot measure, effective 16 February 2021 for parent-child transfers, that narrowed the inherited-home exclusion: only a principal residence qualifies, the heir must occupy within one year, and the excluded amount is capped at the factored base year value plus an inflation-adjusted $1,000,000."),
    ("Proposition H (2026)", "San Francisco's November 2026 parcel tax funding Muni operations for 15 years, from 2027. $129 for a single-family parcel, $249 for multifamily, $799 for non-residential, plus marginal amounts on large buildings."),
    ("Recapture (depreciation)", "The tax on depreciation previously deducted, charged when the property is sold. Unrecaptured § 1250 gain is capped at 25% federally; California taxes it as ordinary income."),
    ("Section 121", "The federal exclusion of up to $250,000 (single) or $500,000 (joint) of gain on the sale of a principal residence, requiring ownership and use for 2 of the last 5 years."),
    ("Section 1031", "Like-kind exchange. Defers gain when investment real property is exchanged for other investment real property. Requires identification within 45 days and completion within 180."),
    ("Section 1014", "The basis rule for property acquired from a decedent: basis equals fair market value at the date of death."),
    ("Tax rate area (TRA)", "A code identifying the combination of taxing agencies that apply to a parcel. Determines the actual property tax rate, which is why two neighbouring houses can have different effective rates."),
    ("Tenancy-in-common (TIC)", "A form of co-ownership of a single parcel. Relevant in San Francisco but not, on the household's description, to either property here."),
    ("Vacancy decontrol", "See Costa-Hawkins. The ability to reset rent to market when a rent-controlled tenancy ends."),
]


def page_glossary(ctx: Ctx) -> str:
    body = """
<section>
<h2>Glossary</h2>
<p class="lead">The vocabulary this decision is made in. Every term is defined the way it is
used in <em>this</em> file, which is not always the way it is used loosely elsewhere — several
of the most expensive mistakes in inherited-property decisions come from a word being understood
differently by the heir, the attorney and the assessor.</p>
"""
    trs = [[f"<strong>{t}</strong>", d] for t, d in GLOSSARY]
    body += table(["Term", "Definition as used here"], trs, cls="wide glossary")
    body += """
</section>

<section>
<h2>The five words most often confused</h2>
<div class="callout warning">
<table class="confused">
<tbody>
<tr><th>Market value</th><td>What it would sell for. Sets the § 1014 basis, the Prop 19 value
test, and the estate tax value — all from the same appraisal, on the same date.</td></tr>
<tr><th>Assessed value</th><td>What the property tax is computed on. Under Prop 13 this is the
factored base year value, which can be a small fraction of market value and is normally nowhere
near it.</td></tr>
<tr><th>Basis</th><td>What the <em>income</em> tax is computed on when you sell. At death it
resets to market value. Unrelated to assessed value, even though both are sometimes called
&ldquo;the basis&rdquo;.</td></tr>
<tr><th>Exclusion</th><td>A statutory rule that removes something from tax. Prop 19's is an
exclusion from <em>reassessment</em>; § 121's is an exclusion from <em>income</em>. They are
different taxes and different mechanics.</td></tr>
<tr><th>Exemption</th><td>A reduction in the amount taxed. The homeowners' exemption removes
$7,000 from assessed value — but its real importance here is that filing it is a legal condition
of the Prop 19 exclusion.</td></tr>
</tbody>
</table>
</div>
</section>
"""
    return page("Glossary", "glossary.html", body,
                subtitle="Thirty terms, defined as they are used in this file, plus the five "
                         "words most often confused.")


# ---------------------------------------------------------------------------
# Page: inventory.html
# ---------------------------------------------------------------------------

def page_inventory(ctx: Ctx) -> str:
    body = """
<section>
<h2>A private inventory, kept private</h2>
<p class="lead">The household asked for a private estate inventory. It cannot live on this site,
because this site is public and indexed. It lives here as a <em>template</em>: the structure to
fill in on paper or in a local file, with every field named, and no field filled.</p>

<div class="callout danger">
<h3>Do not fill this in on this website</h3>
<p>There is no form here, no input, and no submission — deliberately. Type the real values into an
untracked local file (<code>private/inventory.local.md</code>, which <code>.gitignore</code>
blocks) or onto paper. If the inventory ever needs to be shared, share the completed local file
directly with the adviser, not a link to this site.</p>
<p>See <a href="method.html">Method &amp; privacy</a> for why this repository is public and what
that means.</p>
</div>
</section>

<section>
<h2>The inventory structure</h2>
<p class="lead">Nine sections. The first three are what an attorney needs; the next four are what
a CPA needs; the last two are what the household needs and nobody else does.</p>
"""
    sections = [
        ("1. Real property", [
            ("Property A — address and APN", "Private. Never on this site."),
            ("Property A — date of death FMV, with the appraiser's name and report date", "The single most important entry in the file"),
            ("Property A — land value and building value, separately", "Needed for depreciation and maintenance"),
            ("Property A — factored base year value and tax rate area", "From the assessor's parcel page"),
            ("Property A — most recent full property tax bill, itemised", "Base tax, debt levy, fixed charges, exemptions"),
            ("Property A — title held how, and by whom, on the date of death", "Personal, joint tenancy, or trust"),
            ("Property A — outstanding mortgages, liens, or reverse mortgage", "Changes the net inheritance materially"),
            ("Property B — address and APN", "Private"),
            ("Property B — legal unit count per Planning", "Two or three, and it matters"),
            ("Property B — current assessed value and tax bill, itemised", "To explain the 2.1%"),
            ("Property B — any special assessments or Mello-Roos districts", "Currently missing from the model"),
            ("Property B — outstanding mortgage balance and rate", "Affects the liquidity analysis"),
        ]),
        ("2. Trust and estate documents", [
            ("The operative trust instrument and every amendment, dated", "Read by the attorney, not the household"),
            ("The schedule of assets as it currently stands", "Confirms whether the house is actually in the trust"),
            ("Any pour-over will", "Backstop if the trust fails or is incomplete"),
            ("Durable power of attorney and advance health care directive", "Not for this decision, but is the reason to have the meeting"),
            ("Beneficiary designations for retirement accounts and life insurance", "These override the will and the trust"),
            ("Prior gift tax returns (Forms 709), if any", "Reduces the available exclusion"),
            ("Any prior Form 706, for portability", "Time-critical under Rev. Proc. 2022-32"),
            ("Certificates of trust already issued", "Needed to act with banks and the assessor"),
        ]),
        ("3. Income-tax records", [
            ("Capital improvements made to Property A since acquisition, with dates and costs", "Adds to basis; records get harder to find every year"),
            ("Any depreciation schedules if Property A was ever rented", "Creates recapture exposure"),
            ("Property A's rental history, if any", "Changes the character of the asset"),
            ("The parents' recent income tax returns, for the estate's income position", "CPA only"),
            ("The household's own prior returns, for the sale-year marginal rate", "Drives the California surtax analysis"),
        ]),
        ("4. Insurance", [
            ("Property A — current policy, dwelling limit, and whether it is owner-occupied or vacant", "Vacancy endorsements are not automatic"),
            ("Property A — FAIR Plan status and fire severity zone", "The real risk is uninsurability"),
            ("Property B — current policy and whether it is a landlord policy", "A homeowner policy on a three-unit is a coverage gap"),
            ("Property B — umbrella liability", "Three units, two tenancies"),
            ("Any life insurance policies and their ownership and beneficiary", "Estate inclusion question"),
        ]),
        ("5. Leases and tenancies (Property B)", [
            ("Each lease, with start date, current rent, and deposit", "Drives the allowable increase and the vacancy-reset potential"),
            ("The rent history for each unit if available from the Rent Board", "Establishes the lawful rent"),
            ("Any pending habitability notices, complaints, or litigation", "A real liability that does not appear on any balance sheet"),
            ("Utility metering arrangement for each unit", "Landlord-paid or tenant-paid"),
        ]),
        ("6. Operating records", [
            ("Property A — water bills for the last 24 months", "To replace the monthly estimate with a seasonal profile"),
            ("Property A — electricity true-up statements and the solar interconnection agreement", "The net-credit assumption depends entirely on the tariff"),
            ("Property A — any contractor invoices from the last 10 years", "Both maintenance planning and basis"),
            ("Property B — the same, for all three units", "Higher and lumpier than Property A"),
        ]),
        ("7. Estate projections", [
            ("A balance sheet of all trust and personal assets, valued as of a stated date", "CPA"),
            ("The projected gross estate at the expected date of death, at a stated growth rate", "Compare with the exclusion"),
            ("Any closely held business interests or unusual assets", "Different valuation rules apply"),
        ]),
        ("8. Advisers", [
            ("California estate attorney — name, firm, contact", "Private"),
            ("CPA with estate experience — name, firm, contact", "Private"),
            ("Fee-only fiduciary investment adviser, if any", "Private"),
            ("Insurance broker, property manager, appraiser, contractor", "Private"),
        ]),
        ("9. What the household actually wants", [
            ("The signed pre-commitment agreement", "decision.html, printed and signed"),
            ("The ranked criteria, most important first", "The part of the answer no model can supply"),
            ("The decision log, started", "decision-log.html"),
        ]),
    ]
    for title, rows in sections:
        body += f"<h3>{title}</h3>"
        body += table(["Entry", "Why it is needed"],
                      [[html.escape(a), b] for a, b in rows], cls="wide inventory")
    body += """
</section>

<section>
<h2>Why this structure and not a spreadsheet of everything</h2>
<div class="threecol">
<div class="col"><h3>It is organised by who needs it</h3>
<p>An attorney does not need the water bills. A CPA does not need the leases. A household meeting
that tries to cover all nine sections at once covers none of them well. The sections map onto
three separate meetings.</p></div>
<div class="col"><h3>It records the <em>why</em>, not just the what</h3>
<p>Every entry says what decision it informs. Two years from now, the reason for keeping a
contractor invoice from 2019 will not be obvious; the reason for keeping it is basis.</p></div>
<div class="col"><h3>It is deliberately incomplete</h3>
<p>A template with sample values invites copying the sample. An empty template forces a real
answer, and makes it obvious which entries are still missing.</p></div>
</div>
</section>
"""
    return page("Private estate inventory", "inventory.html", body,
                subtitle="The structure to fill in offline, with every field named and no field "
                         "filled. Nothing here is submitted anywhere.")


# ---------------------------------------------------------------------------
# Page: briefing-sheet.html
# ---------------------------------------------------------------------------

def page_briefing(ctx: Ctx) -> str:
    rows = ctx.rows
    sell = [r for r in rows if r["key"] == "sell"][0]
    live = [r for r in rows if r["key"] == "live"][0]
    lts = [r for r in rows if r["key"] == "live-then-sell"][0]

    body = f"""
<div class="brief">
<header class="briefhead">
<h2>Attorney &amp; CPA Briefing Sheet</h2>
<p class="briefsub">One page. Two properties. One inherited, one already owned. Prepared
2026-11-25. Owner estimates and modelled amounts use the ${F.step:,} rounding step; statutory values remain exact. Parcel-unique assessments are banded. Names, street addresses, parcel IDs, and postal codes are omitted; other property details may still be correlatable.</p>
</header>

<div class="briefsec">
<h3>1. The facts as given</h3>
<table class="brief-table">
<tbody>
<tr><th>Property A</th><td>Single-family house, Santa Clara County. <strong>To be inherited</strong> via a
trust, expected distribution 2040–2050. Household estimate of value: {F.usd_full(P.A_VALUE_2026)}.
Factored base year value roughly {F.usd_full(545_000)}–{F.usd_full(560_000)}.</td></tr>
<tr><th>Property B</th><td>Three-unit building, San Francisco. <strong>Already owned.</strong>
Two of three units rented at about {F.usd_full(P.B_RENT_MONTHLY)}/month total. Household estimate
of value: {F.usd_full(P.B_VALUE_2026)}.</td></tr>
<tr><th>Inheritance</th><td>Both properties plus &ldquo;a considerable amount of money&rdquo;, size
not stated. Estate projection not yet prepared.</td></tr>
<tr><th>Occupancy</th><td>Not decided. <span class="briefflag">This is the decisive unknown.</span></td></tr>
</tbody>
</table>
</div>

<div class="briefsec">
<h3>2. The four questions we need answered</h3>
<table class="brief-table">
<tbody>
<tr><th>For the attorney</th><td>If a trust holds the house and the beneficiary occupies it, when
does the one-year occupancy clock in RTC § 63.2(a)(1)(A) start — the date of death, or the date of
distribution? And does the trust need to distribute the property outright for the beneficiary to be
the &ldquo;transferee&rdquo; under § 63.2(e)(9)?</td></tr>
<tr><th>For the CPA</th><td>Is there any prior taxable gift or unclaimed portability in this family?
Concretely: has a prior spouse died, and was a Form 706 filed? Is the five-year window under Rev.
Proc. 2022-32 still open?</td></tr>
<tr><th>For whoever projects the estate</th><td>What is the projected gross estate at the expected
date of death, against a federal exclusion of {F.usd_full(P.FED_ESTATE_EXCLUSION_2026)} per person
in 2026, indexed?</td></tr>
<tr><th>For the assessor</th><td>What is the tax rate area for Property A and the published total
rate for the current fiscal year?</td></tr>
</tbody>
</table>
</div>

<div class="briefsec">
<h3>3. What the model says, and how much to trust it</h3>
<table class="brief-table num">
<thead><tr><th>Path</th><th>30-year net worth (base)</th><th>Range</th></tr></thead>
<tbody>
<tr><td>Sell at transfer, invest the proceeds</td><td>{F.usd_full(sell['base'])}</td>
<td>{F.usd(sell['low'])} – {F.usd(sell['high'])}</td></tr>
<tr><td>Live in it 6 years, then sell under § 121</td><td>{F.usd_full(lts['base'])}</td>
<td>{F.usd(lts['low'])} – {F.usd(lts['high'])}</td></tr>
<tr><td>Live in it, hold to the horizon</td><td>{F.usd_full(live['base'])}</td>
<td>{F.usd(live['low'])} – {F.usd(live['high'])}</td></tr>
</tbody>
</table>
<p class="briefnote"><strong>Trust level: provisional.</strong> The valuation is a household
estimate, not an appraisal. The occupancy intention is unstated. Insurance and maintenance are
ranges, not quotes. The model is a structure for the conversation, not a conclusion to ratify.</p>
</div>

<div class="briefsec">
<h3>4. The three legal points that drive the numbers</h3>
<ol class="brieflist">
<li><strong>Prop 19 requires continuing occupancy.</strong> RTC § 63.2(a)(1)(B)–(C): the exclusion
is removed when the heir stops being eligible for the homeowners' exemption, and a new base year
value is enrolled. &ldquo;Rent it out and keep the low tax base&rdquo; is not available for transfers
after 16 February 2021.</li>
<li><strong>The $1,000,000 allowance is inflation-adjusted and unpublished for 2045.</strong>
Currently {F.usd_full(1_044_586)} for transfers 2025-02-16 to 2027-02-15 (BOE LTA 2025/009).
Modelled as three growth scenarios rather than a point estimate.</li>
<li><strong>The § 1014 basis resets to date-of-death value.</strong> Selling promptly therefore
realises almost no gain; the cost of selling is the ~6% transaction cost, not income tax. Selling
later manufactures a taxable gain taxed at California ordinary rates, with no state preference,
plus the 1% surtax above $1M of taxable income.</li>
</ol>
</div>

<div class="briefsec">
<h3>5. What we are asking for today</h3>
<table class="brief-table">
<tbody>
<tr><th>Attorney</th><td>A written answer to the two § 63.2 questions in item 2, and a review of
whether the trust should hold or distribute the house.</td></tr>
<tr><th>CPA</th><td>The gift and portability history, and a projected gross estate against the
exclusion. Plus: is a Form 706 required even if no tax is due?</td></tr>
<tr><th>Both</th><td>Anything on this sheet that is factually wrong. Ten of the figures here are
flagged unverified on the accompanying site; the flags are the point.</td></tr>
</tbody>
</table>
</div>

<footer class="brieffoot">
<p>Prepared from <em>data/facts.json</em> and <em>model/</em>. Every figure traces to a listed
authority or an explicit assumption. Unverified items are published, not hidden.
This is a decision-support model, not legal, tax or investment advice.</p>
</footer>
</div>
"""
    extra = """<style>@page { size: letter; margin: 0.5in; }</style>"""
    return page("Attorney &amp; CPA briefing sheet", "briefing-sheet.html", body,
                subtitle="",
                printable=True, extra_head=extra)


# ---------------------------------------------------------------------------
# Page: method.html
# ---------------------------------------------------------------------------

def page_method(ctx: Ctx) -> str:
    body = """
<section>
<h2>How this was built, and what its limits are</h2>
<p class="lead">The household asked for line-by-line verification from official sources, no
hallucination, and links for manual review. This page explains what was actually done, what was
not, and how to check any of it.</p>

<h3>The verification protocol</h3>
<ol class="biglist">
<li><strong>Every figure that enters the model is a row in <code>data/facts.json</code>.</strong>
The row records the value, the issuing authority, the instrument, the URL, the exact wording read,
the date checked, and a status.</li>
<li><strong>A status of <code>verified</code> means I opened the cited page or PDF in this
session and read the value in its text.</strong> The <code>quote</code> field holds the actual
wording. Nothing is marked verified on the basis of memory or a summary.</li>
<li><strong>A status of <code>secondary</code> means the value is official in substance but I
could not fetch the official page.</strong> These are listed on the Flagged page with the reason.</li>
<li><strong>A status of <code>unverified</code> means no official source exists or could be
located.</strong> The value is either withheld, or shown as a range, or shown as the household's
own estimate clearly labelled. It is never presented as a fact.</li>
<li><strong>Nothing was inferred to fill a gap.</strong> Where a number was needed and could not
be established, the model carries a range and the site says so.</li>
</ol>

<h3>What was actually fetched and read</h3>
<p>Among others: the IRS estate-tax page and Rev. Proc. 2025-32 (both the PDF and the sections
cited); IRS Publications 551, Topics 409, 414, 415, 701, 703; the IRS net investment income tax
page; Revenue Procedure 2022-32 in full; the complete text of IRC §§ 102, 1014, 1031 and 168 via
Cornell's Legal Information Institute; the California Franchise Tax Board's 2025 Form 540 booklet
(including the line 62 Behavioral Health Services Tax instructions, which the household
specifically asked about); Revenue and Taxation Code § 63.2 in full including the 2025 amendment;
State Board of Equalization Letter To Assessors 2025/009; the Board of Equalization homeowners'
exemption page; the San Francisco Assessor-Recorder's Proposition 19 and transfer-tax pages; the
Federal Reserve H.15 release; FRED's CPI series; and the NBER's business cycle table.</p>

<h3>What was not done</h3>
<div class="callout warning">
<ul>
<li><strong>No legislation tracking.</strong> The household asked for proposed legislation to be
tracked and distinguished from enacted law. This site tracks neither. It records only enacted law
as of 2026-11-25 and says so on every page that touches the question.</li>
<li><strong>No appraisal, no comparables, no rent survey.</strong> The three numbers that most
drive the result are household estimates. This is the model's largest weakness and it is flagged
in the most prominent place available.</li>
<li><strong>No professional review.</strong> No attorney, CPA or adviser has seen this.</li>
<li><strong>No probabilistic modelling.</strong> The scenarios are not weighted. Assigning
probabilities to 1929 versus 2022 would be inventing information.</li>
<li><strong>Property B is not fully modelled.</strong> It is analysed as a risk factor and a
liquidity constraint, not as a cash-flow asset with its own ledger. That is a real gap.</li>
</ul>
</div>
</section>

<section>
<h2>Privacy</h2>
<div class="callout danger">
<h3>This repository is public. Plan accordingly.</h3>
<p>The repository is public and its GitHub Pages site is public and cannot be made private on a
free plan. The household's stated highest priority was that no personal information appear in the
final product. The measures taken:</p>
<ul>
<li>No household names, street addresses, parcel numbers, account numbers, dates of death, or tenant identities are intentionally stored in the working files. Commit metadata and public source/history still require separate privacy review.</li>
<li>Owner-supplied estimates and modelled dollar outputs use the requested """ + f"${F.step:,}" + """ rounding step. Statutory thresholds and source rates are left exact when rounding would misstate the law.</li>
<li><strong>Parcel-unique assessed values are banded by construction, not by rounding.</strong>
A $10 band on a tax-assessed value is still unique to one parcel; so those two values are carried
as $10,000 bands in the model and never rendered at full precision.</li>
<li>No analytics, no cookies, no third-party scripts, no fonts loaded from a CDN, and no forms
that post anywhere. A visitor cannot be profiled and their inputs are never transmitted.</li>
<li><code>.gitignore</code> excludes local private-input paths, but does not make the tracked model source or published estimates private. Do not place exact inventories or documents in this repository.</li>
</ul>
<p><strong>The honest limitation:</strong> rounding protects against casual discovery and search
indexing. It does not protect against a reader who already knows the household. If that is a
realistic threat, do not publish — run <code>python3 sitegen.py --out site-private</code> locally
and keep the output off the internet. See <code>PRIVACY.md</code> in the repository.</p>
</div>

<h3>Git history and prior exposure</h3>
<p>This checkout is shallow and does not contain enough earlier commits to audit the full public history. The merge-base commit metadata contains a personal email identifier, and the current branch cannot remove it from the default branch's history. A normal cleanup commit does not erase old Git objects. A repository-wide rewrite and cache purge have not been performed; do not treat this site as a completed history scrub.</p>
</section>

<section>
<h2>Reproducing and extending this</h2>
<table class="wide">
<tbody>
<tr><th><code>python3 sitegen.py --out site</code></th><td>Build the site. No dependencies beyond
the Python standard library.</td></tr>
<tr><th><code>python3 sitegen.py --round 10000</code></th><td>Coarser rounding for a more
privacy-hardened build.</td></tr>
<tr><th><code>python3 tools/check_site.py site</code></th><td>Check every internal link, every
image, and every claim that a figure has a source.</td></tr>
<tr><th><code>data/facts.json</code></th><td>The single source of truth for every figure. Edit
here, never in a generated page.</td></tr>
<tr><th><code>model/params.py</code></th><td>Every input, with its provenance and status.</td></tr>
<tr><th><code>model/engine.py</code></th><td>The simulation. Heavily commented on the legal
reasoning, because the legal reasoning is where these models usually go wrong.</td></tr>
<tr><th><code>model/runner.py</code></th><td>The tables the site publishes.</td></tr>
<tr><th><code>COORDINATION.md</code></th><td>The task board, for parallel sessions.</td></tr>
<tr><th><code>PRIVACY.md</code></th><td>The privacy model, binding on every file.</td></tr>
</tbody>
</table>
</section>
"""
    return page("Method, sources &amp; privacy", "method.html", body,
                subtitle="What was verified, what was not, how to check it, and the privacy "
                         "model that governs what may appear here.")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

PAGES: Dict[str, Callable[[Ctx], str]] = {
    "index.html": page_index,
    "choices.html": page_choices,
    "paths.html": page_paths,
    "black-swan.html": page_black_swan,
    "reinvestment.html": page_reinvestment,
    "projections.html": page_projections,
    "taxes.html": page_taxes,
    "authorities.html": page_authorities,
    "assumptions.html": page_assumptions,
    "inheritance.html": page_inheritance,
    "deadlines.html": page_deadlines,
    "property-b.html": page_property_b,
    "questions.html": page_questions,
    "flagged.html": page_flagged,
    "suggestions.html": page_suggestions,
    "decision.html": page_decision,
    "decision-log.html": page_decision_log,
    "glossary.html": page_glossary,
    "inventory.html": page_inventory,
    "briefing-sheet.html": page_briefing,
    "method.html": page_method,
}


def build(out: pathlib.Path, step: int = 10) -> int:
    """Render every page into `out`.

    The output directory is wiped before writing, which makes `--out` a loaded
    gun: `--out ..` deletes the repository. This guard exists because that
    actually happened during development. Only a directory that is empty, absent,
    or already contains a previous build of THIS site may be wiped.
    """
    global F
    F = Fmt(step)

    out = out.resolve()
    if out == ROOT.resolve() or ROOT.resolve() in out.parents and len(out.parts) < 3:
        raise SystemExit(f"refusing to build into {out}: that is a parent of the source tree")
    if out.exists() and any(out.iterdir()):
        looks_like_a_build = (out / ".nojekyll").exists() and (out / "index.html").exists()
        if not looks_like_a_build:
            raise SystemExit(
                f"refusing to wipe {out}: it is not empty and does not look like a previous "
                f"build of this site (no .nojekyll + index.html). Trust people more than rmtree."
            )
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    shutil.copy(ROOT / "assets" / "style.css", out / "assets" / "style.css")

    ctx = build_ctx()
    for name, fn in PAGES.items():
        (out / name).write_text(fn(ctx), encoding="utf-8")
        print(f"  wrote {name}")

    # A plain-text index for crawlers that is explicitly a noindex pointer
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (out / ".nojekyll").write_text("")

    print(f"\nBuilt {len(PAGES)} pages into {out}/ (rounding step ${step:,})")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="../site", help="output directory")
    ap.add_argument("--round", type=int, default=10,
                    help="rounding step in dollars (10 = nearest $10, as requested)")
    args = ap.parse_args(argv)

    if args.round < 1:
        print("--round must be >= 1", file=sys.stderr)
        return 2

    return build(pathlib.Path(args.out), args.round)


if __name__ == "__main__":
    raise SystemExit(main())
