#!/usr/bin/env node
/* Build the static site under estate-model/ from tools/model.js and tools/content.js. Run: node tools/build.js */
'use strict';
const fs = require('fs');
const path = require('path');
const M = require('./model.js');
const { SOURCES, FLAGGED, TIMELINE, GLOSSARY, SUGGESTIONS } = require('./content.js');

const ROOT = path.join(__dirname, '..');
const DOCS = path.join(ROOT, 'estate-model');
const N = 1000; // Monte Carlo draws per case
const money = (v) => { const x = M.r10(v); return (x < 0 ? '\u2212$' : '$') + Math.abs(x).toLocaleString('en-US'); };
const pct = (v, d = 2) => (v * 100).toFixed(d) + '%';
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const src = (k) => { const s = SOURCES[k]; return `<a href="${esc(s.url)}" rel="noopener">${esc(s.title.split(':')[0].split('(')[0].trim())}</a>`; };
const flagTag = (id) => ` <span class="flag" title="See flagged item">[${id}]</span>`;

const CASES = M.CASES;
const results = {};
CASES.forEach((c) => { results[`${c.T}-${c.H}`] = M.evaluate({}, c.T, c.H, { n: N }); });
const committed = {};
CASES.forEach((c) => { committed[`${c.T}-${c.H}`] = M.evaluate({ commitLive: true, comparables: 3 }, c.T, c.H, { n: 400 }); });

// Break-evens (base scenario, financial measure)
const be = {};
CASES.forEach((c) => {
  const k = `${c.T}-${c.H}`;
  be[k] = {
    rentVsSell: M.breakEven({}, c.T, c.H, 'marketYield', 'B', 'C', 0, 0.15),
    liveVsSell: M.breakEven({}, c.T, c.H, 'marketYield', 'A', 'C', 0, 0.15),
  };
});

// Sensitivity: does any single input change the pick? (default eligibility and committed eligibility)
const SENS = [
  { key: 'fmv2026', lo: 2800000, hi: 3400000, label: 'Property A value (\u00b110%)' },
  { key: 'effRate', lo: 0.0115, hi: 0.0135, label: 'Property-tax rate (1.15% to 1.35%)' },
  { key: 'marketYield', lo: 0.02, hi: 0.03, label: 'Gross rent yield (2.0% to 3.0%)' },
  { key: 'maintPct', lo: 0.005, hi: 0.01, label: 'Maintenance reserve (0.5% to 1.0%)' },
  { key: 'insA', lo: 1200, hi: 2340, label: 'Owner insurance ($1,200 to $2,340)' },
  { key: 'sellPct', lo: 0.04, hi: 0.06, label: 'Selling costs (4% to 6%)' },
  { key: 'exclusion', lo: 0, hi: 500000, label: '§121 exclusion ($0 to $500,000)' },
  { key: 'pCrash', lo: 0, hi: 0.3, label: 'Crash probability in Monte Carlo (0% to 30%)' },
];
const sensitivity = {};
{
  const c = CASES[1]; // 2040, 20 years, the case the household asked about first
  const pickOf = (p) => M.evaluate(p, c.T, c.H, { n: 200 }).choice.pick;
  const base = pickOf({});
  const baseC = pickOf({ commitLive: true, comparables: 3 });
  sensitivity.base = base; sensitivity.baseC = baseC;
  sensitivity.rows = SENS.map((s) => {
    const lo = pickOf({ [s.key]: s.lo }); const hi = pickOf({ [s.key]: s.hi });
    const loC = pickOf({ [s.key]: s.lo, commitLive: true, comparables: 3 });
    const hiC = pickOf({ [s.key]: s.hi, commitLive: true, comparables: 3 });
    return { label: s.label, lo, hi, loC, hiC, flips: lo !== base || hi !== base || loC !== baseC || hiC !== baseC };
  });
}

// ---- Shared page chrome --------------------------------------------------
const NAV = [
  { group: 'Decide', items: [['index.html', 'Start here'], ['results.html', 'Results by case'], ['whatif.html', 'What-if controls'], ['rules.html', 'Decision criteria']] },
  { group: 'Evidence', items: [['estate.html', 'Estate, income and property tax'], ['phased.html', 'Phased investing'], ['blackswan.html', 'Black swan tests'], ['timeline.html', 'Timeline of deadlines']] },
  { group: 'Reference', items: [['glossary.html', 'Glossary'], ['sources.html', 'Source register'], ['brief.html', 'Attorney/CPA brief (print)']] },
  { group: 'Review', items: [['flagged.html', 'Flagged for review'], ['suggestions.html', 'Suggestions']] },
];
function page(title, active, body, opts = {}) {
  const nav = NAV.map((g) => `<div class="navg"><div class="navt">${g.group}</div>${g.items.map(([h, l]) => `<a href="${h}"${h === active ? ' class="on"' : ''}>${esc(l)}</a>`).join('')}</div>`).join('');
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · Inherited-property decision</title><link rel="stylesheet" href="assets/style.css"></head>
<body class="${opts.cls || ''}"><header class="top"><strong>Inherited-property decision (Property A, Santa Clara County; Property B, San Francisco)</strong>
<span class="sub">Privacy-first. No personal identifiers. Figures rounded to the nearest $10. Model results are illustrative, not advice.</span></header>
<div class="wrap"><nav class="menu">${nav}</nav><main>${body}</main></div>
<footer>Last built ${new Date().toISOString().slice(0, 10)}. Source register: <a href="sources.html">sources.html</a>. Unverified items: <a href="flagged.html">flagged.html</a>.</footer></body></html>`;
}

// ---- Derived numbers for copy --------------------------------------------
const r2040_20 = results['2040-20'];
const r2050_20 = results['2050-20'];
const pickName = (code) => (M.PATHS.find((p) => p.code === code) || { name: code }).name;
const pathLabel = (code) => `${code} · ${pickName(code)}`;
const pick2040_20 = r2040_20.choice.pick;
const pickC2040_20 = committed['2040-20'].choice.pick;
const pickAll = CASES.map((c) => `${c.T}/${c.H}: ${results[`${c.T}-${c.H}`].choice.pick}`);

function estate() {
  const e = M.estateExposure(r2040_20.rows.A.base.fmvT);
  return e;
}

// ---- Pages -----------------------------------------------------------------
const pages = {};

pages['index.html'] = page('Start here', 'index.html', `
<section class="card key">
<h1>What would change the answer</h1>
<p class="lead">Under the current rules, the choice set has no occupancy path unless the household commits in writing to occupy Property A within 12 months (Rule 3). Rent is a floor until three verified comparables exist (Rule 4).</p>
<ul class="chg">
<li><b>Written occupancy commitment.</b> Without it, paths A, E and F are removed. With it, the pick for the 2040 transfer, 20-year case is <b>${esc(pathLabel(pickC2040_20))}</b>${pickC2040_20 === pick2040_20 ? ', the same as without it. Living does not overtake sale in the base case' : ' (was ' + esc(pathLabel(pick2040_20)) + ')'}.</li>
<li><b>Black-swan probability.</b> The phased pick depends on the crash probability in the Monte Carlo draws: at 0% the lump sum (C) leads; at the 10% default, a phased path (D) leads (see <a href="whatif.html">what-if controls</a>).</li>
<li><b>Rent yield.</b> The gross rent yield needed for renting to match a sale (base case, 2040 transfer, 20 years) is about <b>${pct(be['2040-20'].rentVsSell, 1)}</b>, against an assumed 2.5% with no verified comparables${flagTag('F11')}.</li>
<li><b>Living value.</b> Living in A matches a sale only at a gross yield of about <b>${pct(be['2040-20'].liveVsSell, 1)}</b> (2040, 20 years, base case). Imputed rent is counted for occupancy paths only.</li>
<li><b>Base-year value.</b> The Prop 19 base-year value is not yet verified${flagTag('F08')}. Until it is entered, the model reassesses Property A at full value, which is the conservative fallback.</li>
<li><b>Single-input tests.</b> ${sensitivity.rows.filter((r) => r.flips).length} of ${sensitivity.rows.length} tested inputs change the pick at least once (see <a href="whatif.html">what-if controls</a>).</li>
</ul>
<p class="small">Default pick across all four cases (no commitment): ${esc(pickAll.join(' · '))}.</p>
</section>

<section class="card"><h2>Executive summary</h2>
<ul>
<li><b>Question.</b> Live in, rent, sell, or mix Property A (inherited Santa Clara County home) and Property B (San Francisco home already owned), at transfers in 2040 and 2050 and horizons of 10 and 20 years.</li>
<li><b>Result under the rules.</b> Without an occupancy commitment, the choice is among sale paths: lump sum (C) or phased (D). Phasing wins only if it passes Rule 5 (black-swan and base-case tests). Paths A, E, F are shown for reference.</li>
<li><b>Estate tax.</b> Property A alone is well below the $15,000,000 federal basic exclusion for 2026 (Rev. Proc. 2025-32). No estate-tax liability is assumed because other estate assets are unknown (Rule 7).${flagTag('F01')}</li>
<li><b>Prop 19.</b> Living in A preserves the lower base-year value only if the child occupies it as a principal residence within one year and files the claim within three years (BOE).${flagTag('F07')}</li>
<li><b>Black swans.</b> Phased paths help in 1929-type and 2008-type crash timing but depend heavily on crash timing, which is an assumption.${flagTag('F20')}</li>
<li><b>Status.</b> Model results depend on flagged inputs: rent, insurance, selling costs, capital-gain rates, and cash yield. See <a href="flagged.html">flagged for review</a>.</li>
</ul>
<p class="small">Decision and date next to each item: 2026-11-25 (initial rules, written before model output). No choice has been committed.</p>
</section>

<section class="card"><h2>Menu</h2>
<div class="grid">${NAV.map((g) => `<div><h3>${g.group}</h3><ul>${g.items.map(([h, l]) => `<li><a href="${h}">${esc(l)}</a></li>`).join('')}</ul></div>`).join('')}</div>
</section>`);

// Results page
function caseTable(c) {
  const r = results[`${c.T}-${c.H}`];
  const rows = M.PATHS.map((p) => {
    const x = r.rows[p.code];
    const elig = r.choice.eligible.includes(p.code) ? '' : ' <span class="muted">(not in choice set)</span>';
    const flagB = p.code === 'B' ? ' <span class="muted">floor only</span>' : '';
    return `<tr><td><b>${esc(p.code)}</b> ${esc(p.name)}${elig}${flagB}</td>
<td class="num">${money(x.primaryMedian)}</td>
<td class="num">${money(x.p10)} to ${money(x.p90)}</td>
<td class="num">${money(x.worstBlackSwan)}</td>
<td class="num">${money(x.base.liquidAtT)}</td>
<td class="num">${money(x.base.yr1Tax + x.base.yr1Cost)}</td>
<td class="small">${basisLinks(p.code)}</td></tr>`;
  }).join('');
  return `<h3>Transfer ${c.T} · horizon ${c.H} years (pick: <b>${esc(pathLabel(r.choice.pick))}</b>)</h3>
<div class="scroll"><table><thead><tr><th>Path</th><th>Primary: median real net</th><th>10th to 90th percentile</th><th>Worst black swan</th><th>Liquid at transfer</th><th>Year-1 carrying cost</th><th>Official basis</th></tr></thead><tbody>${rows}</tbody></table></div>
<p class="small">Notes: ${esc(r.choice.notes.join(' '))}</p>`;
}
function basisLinks(code) {
  const map = {
    A: [['boeProp19', 'Prop 19'], ['lta25009', 'indexed amount'], ['lta26026', 'occupancy rules']],
    B: [['boeProp19', 'reassessment'], ['sfRent', ''] ],
    C: [['rtc11911', 'transfer tax'], ['pub551', 'basis'], ['rtc17043', 'CA surcharge']],
    D24: [['treasury', 'Treasury'], ['rtc11911', 'transfer tax']],
    D36: [['treasury', 'Treasury'], ['rtc11911', 'transfer tax']],
    E: [['boeProp19', 'Prop 19'], ['lta26026', 'occupancy']],
    F: [['boeProp19', 'Prop 19'], ['pub551', 'basis']],
  };
  return (map[code] || []).map(([k, l]) => `${src(k)}${l ? ' (' + l + ')' : ''}`).join('; ') + flagTag(code === 'B' ? 'F11' : 'F12');
}
pages['results.html'] = page('Results by case', 'results.html', `
<section class="card"><h1>Results by case</h1>
<p class="small">Primary metric (DECISION_RULES.md §2): median real net position across six fixed scenarios and ${N} Monte Carlo draws. Paths A, E and F include imputed rent for the occupied share (Rule 3). Financial-only results are in <code>data/model.json</code>.</p>
${CASES.map(caseTable).join('')}
<h3>Break-even gross rent yield (base case)</h3>
<table><thead><tr><th>Case</th><th>Yield at which renting (B) matches sale (C)</th><th>Yield at which living (A) matches sale (C)</th></tr></thead><tbody>
${CASES.map((c) => { const k = `${c.T}-${c.H}`; return `<tr><td>${c.T}, ${c.H} years</td><td class="num">${pct(be[k].rentVsSell, 1)}</td><td class="num">${pct(be[k].liveVsSell, 1)}</td></tr>`; }).join('')}
</tbody></table>
<p class="small">Assumed gross yield: 2.5% (no verified comparables)${flagTag('F11')}. Source for the model's constants: <a href="sources.html">source register</a>.</p>
</section>`);

// Black swan page
const sc = M.SCENARIOS;
pages['blackswan.html'] = page('Black swan tests', 'blackswan.html', `
<section class="card"><h1>Black swan tests</h1>
<p>Two stylised crashes start 12 months after transfer. The drop sizes come from the Federal Reserve History essay on the 1929 crash and the 2008 Great Recession; the timing and recovery lengths are illustrative assumptions${flagTag('F20')}.</p>
<ul>
<li><b>1929-type:</b> equities fall about 89% from peak to trough over 34 months, then return to the pre-crash peak about 268 months later (nominal peak regained November 1954, per the Fed History essay). Home prices fall ${pct(M.C.homeDrawdown, 0)} over 12 months${flagTag('F21')}.</li>
<li><b>2008-type:</b> equities fall about 57% over 17 months (October 2007 to March 2009, per the Fed History essay), back to peak in 48 months after trough (assumed).</li>
</ul>
<p class="small">Sources: <a href="https://www.federalreservehistory.org/essays/stock-market-crash-of-1929">Federal Reserve History: 1929</a>. Peak-relative recovery means the lost compounding does not come back.</p>
</section>
<section class="card"><h2>Real outcome by scenario (2040 transfer, 20-year horizon)</h2>
<div class="scroll"><table><thead><tr><th>Scenario</th>${M.PATHS.map((p) => `<th>${esc(p.code)}</th>`).join('')}</tr></thead><tbody>
${sc.map((s) => `<tr><td>${esc(s.label)}</td>${M.PATHS.map((p) => `<td class="num">${money(results['2040-20'].rows[p.code].scenarios[s.id].real)}</td>`).join('')}</tr>`).join('')}
</tbody></table></div>
<p class="small">Each scenario uses its own CPI to deflate outcomes. Stagflation is illustrative (5% CPI). CPI bases: <a href="${esc(SOURCES.ssa2026.url)}">SSA 2026 Trustees Report</a> (Alt I 3.0%, Alt II 2.4%, Alt III 1.8%). Latest official CPI index: <a href="${esc(SOURCES.blsCpi.url)}">BLS</a>; the 12-month rate for October 2026 was not published.</p>
</section>
<section class="card"><h2>Worst black-swan outcome, all cases</h2>
<table><thead><tr><th>Case</th>${M.PATHS.map((p) => `<th>${esc(p.code)}</th>`).join('')}</tr></thead><tbody>
${CASES.map((c) => `<tr><td>${c.T}, ${c.H} yrs</td>${M.PATHS.map((p) => `<td class="num">${money(results[`${c.T}-${c.H}`].rows[p.code].worstBlackSwan)}</td>`).join('')}</tr>`).join('')}
</tbody></table>
<p class="small">Rule 5 uses the worse of the two black-swan outcomes. Stagflation is shown on the scenario table, not in this table.</p>
</section>`);

// Phased investing page
const phasedRows = CASES.map((c) => {
  const r = results[`${c.T}-${c.H}`];
  const C_ = r.rows.C, D = r.rows.D36, D24 = r.rows.D24;
  const d24 = r.rows.D24, d36 = r.rows.D36;
  const r5 = (d) => (d.worstBlackSwan >= C_.worstBlackSwan && Math.abs(d.primaryMedian - C_.primaryMedian) <= 0.05 * Math.abs(C_.primaryMedian)) ? 'passes' : 'fails';
  return `<tr><td>${c.T}, ${c.H} yrs</td><td class="num">${money(C_.primaryMedian)}</td><td class="num">${money(d24.primaryMedian)}</td><td class="num">${money(d36.primaryMedian)}</td><td class="num">${money(C_.worstBlackSwan)}</td><td class="num">${money(d24.worstBlackSwan)}</td><td class="num">${money(d36.worstBlackSwan)}</td><td>${r5(d24)} / ${r5(d36)}</td></tr>`;
}).join('');
pages['phased.html'] = page('Phased investing', 'phased.html', `
<section class="card"><h1>Phased investing (Treasury bills, then equities)</h1>
<p>Sale proceeds are parked in short Treasury bills (3-month to 2-year) for 24 or 36 months, then moved into a broad equity index in equal monthly tranches over 12 months. Parked cash earns the modelled cash rate${flagTag('F15')}.</p>
<p class="small">Sources: <a href="${esc(SOURCES.treasury.url)}">US Treasury yield curve</a> (not fetched, rate flagged). Holding period: DECISION_RULES.md §1 (24 to 36 months).</p>
</section>
<section class="card"><h2>Rule 5 check (phased vs lump sum)</h2>
<p>Phased (D) beats lump sum (C) only if its worse black-swan outcome is at least C's, and its base median is within 5% of C's.</p>
<div class="scroll"><table><thead><tr><th>Case</th><th>C median</th><th>D24 median</th><th>D36 median</th><th>C worst black swan</th><th>D24 worst</th><th>D36 worst</th><th>Rule 5 (D24 / D36)</th></tr></thead><tbody>${phasedRows}</tbody></table></div>
</section>
<section class="card"><h2>Draft investing policy (for attorney and CPA review)</h2>
<p class="small">Draft. Not investment advice. No amounts are decided here. Source for the policy text: DECISION_RULES.md §5.</p>
<ol>
<li><b>Purpose.</b> Hold sale proceeds for the household's stated goals; protect against forced sales in a downturn.</li>
<li><b>Liquidity reserve.</b> Hold an amount equal to <i>[placeholder: months of household spending, to be set by the household]</i> in cash or Treasury bills.</li>
<li><b>Staging.</b> If phasing is chosen, move proceeds into equities in equal monthly tranches over 24 to 36 months. <i>[placeholder: period to be chosen before funds arrive]</i>.</li>
<li><b>Diversification and rebalancing.</b> Broad index exposure; rebalance once a year to targets set in advance.</li>
<li><b>Drawdown rule.</b> Do not sell equities to fund emergencies while the reserve is intact.</li>
<li><b>Review.</b> Annual review, aligned with the annual model re-run.</li>
<li><b>Tax coordination.</b> The CPA confirms the holding structure, and any trust or entity wrapper, before funds are invested.</li>
</ol>
</section>`);

// Estate page: separate items
const ex = estate();
pages['estate.html'] = page('Estate, income and property tax', 'estate.html', `
<section class="card"><h1>Estate tax, income-tax basis and property tax: three separate items</h1>
<p class="small">Each item below has its own rule and its own source. They are not combined into one number.</p>
<h2>1. Federal estate tax (against the exclusion)</h2>
<table><tbody>
<tr><th>Federal basic exclusion, 2026</th><td class="num">${money(M.C.fedBasicExclusion2026)}</td><td class="small">${src('revproc')} (§2.14)</td></tr>
<tr><th>Property A alone, at the 2040 transfer value (model)</th><td class="num">${money(ex.propertyA)}</td><td class="small">Model estimate${flagTag('F12')}</td></tr>
<tr><th>Headroom with Property A alone</th><td class="num">${money(ex.headroomPropertyAOnly)}</td><td class="small">Computed</td></tr>
<tr><th>Other estate assets</th><td>Unknown</td><td class="small">Rule 7: no liability assumed until the total is verified.</td></tr>
</tbody></table>
<p class="small">Estate-tax top rate and filing deadline are flagged${flagTag('F26')}${flagTag('F01')}. The 2026 filing threshold of $15,000,000 is on the <a href="${esc(SOURCES.irsEstate.url)}">IRS estate-tax page</a>. Prior taxable gifts, portability and the unified credit are flagged${flagTag('F03')}${flagTag('F04')}.</p>
<h2>2. Income-tax basis</h2>
<ul>
<li>Inherited property generally takes basis at fair market value on the date of death. Pub. 551 gives examples; the statute text (IRC §1014) is not yet read${flagTag('F06')}. Source: ${src('pub551')}.</li>
<li>Written valuation at the date of death is needed before any sale. Sale gain is measured from that basis.</li>
<li>Converting personal use to rental changes the depreciation basis (lesser of FMV or adjusted basis at the change). Source: ${src('pub551')}. CPA to confirm recapture.</li>
<li>Like-kind exchange (§1031): the CPA should advise before any sale; the statute text is not yet read${flagTag('F06')}.</li>
<li>Capital-gain rates applied in the model: 20% federal top (flagged${flagTag('F13')}), 3.8% NIIT (flagged${flagTag('F13')}), and CA 12.30% plus 1% surcharge over $1,000,000 (${src('ftb540')}; ${src('rtc17043')}).</li>
</ul>
<h2>3. Property tax and Prop 19</h2>
<ul>
<li>Parent-child exclusion (RTC §69.6, effective 4/1/2021) applies only to the principal residence. Source: ${src('boeProp19')}.</li>
<li>Taxable value for an occupied home: the lesser of fair market value and factored base-year value plus the indexed amount ($1,044,586 for 2/16/2025 to 2/15/2027). Source: ${src('lta25009')}. Next adjustment due 2/16/2027.</li>
<li>Child occupies the home within 1 year and claims the homeowners' exemption; claim within 3 years or before a third-party transfer. Source: ${src('lta26026')} (chunks 0 to 2).${flagTag('F07')}</li>
<li>Property not occupied (path B, or the rented share of E) is reassessed at full value. The model uses full value as the fallback when the base-year value is blank${flagTag('F08')}.</li>
<li>The Prop 13 inflation factor for 2026-27 is 1.02; growth in taxable value is capped at the lesser of 2% or CPI. Source: ${src('lta26002')}.</li>
</ul>
<h2>Liquidity plan if the estate exceeds the exclusion</h2>
<p>Not applicable under the current inputs (no liability assumed). If the verified total exceeds the basic exclusion, the plan must cover the 40% top-rate liability before distribution. The model cannot give this figure until other assets are known.${flagTag('F26')}</p>
</section>`);

pages['timeline.html'] = page('Timeline of deadlines', 'timeline.html', `
<section class="card"><h1>Timeline of deadlines</h1>
<table><thead><tr><th>When</th><th>What</th><th>Source</th><th>Status</th></tr></thead><tbody>
${TIMELINE.map((t) => `<tr><td>${esc(t.when)}</td><td>${esc(t.what)}</td><td class="small">${src(t.src)}</td><td class="small">${esc(t.status)}</td></tr>`).join('')}
</tbody></table></section>`);

pages['glossary.html'] = page('Glossary', 'glossary.html', `
<section class="card"><h1>Glossary</h1>
<table><thead><tr><th>Term</th><th>Plain meaning</th><th>Source</th></tr></thead><tbody>
${GLOSSARY.map(([t, d, s]) => `<tr><td><b>${esc(t)}</b></td><td>${esc(d)}</td><td class="small">${src(s)}</td></tr>`).join('')}
</tbody></table></section>`);

pages['rules.html'] = page('Decision criteria', 'rules.html', `
<section class="card"><h1>Decision criteria (fixed before model output)</h1>
<p class="small">Written 2026-11-25. Source: DECISION_RULES.md in the repository. Changes after model output must be dated and logged in COORDINATION.md.</p>
<ol>
<li><b>Primary metric:</b> median real net position at the horizon, across the six scenarios and Monte Carlo draws.</li>
<li><b>Downside guard:</b> a path must keep its 10th-percentile real outcome within 10% of Path C's.</li>
<li><b>Live (A, F):</b> eligible only with a written commitment to occupy A as principal residence within 12 months. The same condition is applied to mixed path E (interpretation, flagged${flagTag('F24')}).</li>
<li><b>Rent (B):</b> eligible only with at least three verified comparables; until then it is a floor.</li>
<li><b>Phased (D) beats lump sum (C):</b> only if its worse black-swan outcome is at least C's and its base median is within 5% of C's.</li>
<li><b>Mixed (E):</b> chosen only if it beats the best pure path on the primary metric and the downside guard.</li>
<li><b>Estate tax:</b> no liability assumed unless the total taxable estate is verified above the basic exclusion.</li>
<li><b>Ties:</b> within 2%, prefer more liquidity at transfer, then lower regulatory exposure (interpretation${flagTag('F25')}).</li>
</ol>
<h2>What would make the household choose each path</h2>
<ul>
<li><b>A (live):</b> written occupancy commitment; living value (including imputed rent) at least the sale median; 1-year Prop 19 filing achievable.</li>
<li><b>B (rent):</b> verified comparables with a gross yield at or above the model break-even; a landlord policy quote; acceptance of full reassessment.</li>
<li><b>C (sell, lump sum):</b> sale path leads on the primary metric and the downside guard is met without phasing.</li>
<li><b>D (sell, phased):</b> passes Rule 5; household accepts 24 to 36 months of Treasury-level returns while waiting.</li>
<li><b>E or F (mixed):</b> Rule 6 is met, or the household prefers a stated occupancy schedule.</li>
</ul>
<h2>Triggers that re-open the decision</h2>
<ul>
<li>Change to the Prop 19 indexed amount (next due 2/16/2027; <a href="${esc(SOURCES.lta25009.url)}">BOE LTA 2025/009</a>).</li>
<li>Change to the federal basic exclusion or to step-up in basis.</li>
<li>Verified change in Property A's assessed value or tax rate area.</li>
<li>Verified market rent for Property A.</li>
<li>Change in the household's occupancy plan.</li>
</ul>
</section>`);

// What-if page (client-side model)
pages['whatif.html'] = page('What-if controls', 'whatif.html', `
<section class="card"><h1>What-if controls</h1>
<p class="small">Runs the same model in your browser. Nothing is sent anywhere. Changing a control recalculates the table below. Values marked as flagged are not verified.</p>
<form id="wf" class="ctl">
<label>Transfer year <select name="T"><option>2040</option><option>2050</option></select></label>
<label>Horizon (years) <select name="H"><option>10</option><option selected>20</option></select></label>
<label>Property A value at transfer base, $ (2026) <input name="fmv2026" type="number" step="10000" value="3100000"></label>
<label>Gross rent yield (%) <input name="marketYield" type="number" step="0.1" value="2.5"> <span class="flag">[F11]</span></label>
<label>Property-tax rate (%) <input name="effRate" type="number" step="0.01" value="1.19"> <span class="flag">[F09]</span></label>
<label>Owner insurance, $ per year <input name="insA" type="number" step="10" value="2340"> <span class="flag">[F10]</span></label>
<label>Maintenance reserve (% of value) <input name="maintPct" type="number" step="0.05" value="0.75"></label>
<label>Selling costs (%) <input name="sellPct" type="number" step="0.1" value="5"> <span class="flag">[F12]</span></label>
<label>Equity trend return (%) <input name="eq" type="number" step="0.1" value="6.5"></label>
<label>Monte Carlo crash probability (%) <input name="pCrash" type="number" step="1" value="10"> <span class="flag">[F22]</span></label>
<label><input name="commitLive" type="checkbox"> Written commitment to occupy within 12 months (Rule 3)</label>
<label>Verified rental comparables (count) <input name="comparables" type="number" step="1" value="0"> <span class="flag">[F11]</span></label>
<button type="button" id="run">Recalculate</button>
</form>
<div id="out" class="small">Loading model…</div>
</section>
<script src="assets/model.js"></script>
<script src="assets/whatif.js"></script>`);

// Flagged page
pages['flagged.html'] = page('Flagged for review', 'flagged.html', `
<section class="card"><h1>Flagged for review</h1>
<p>These items do not block merge. They are unverified, partly verified, or interpreted. Each one is used in the model or copy and is marked on the page where it appears. Entries are removed only after an official source is recorded.</p>
<table><thead><tr><th>ID</th><th>Item</th><th>Why flagged</th><th>What is needed</th><th>Source to check</th></tr></thead><tbody>
${FLAGGED.map((f) => `<tr><td>${f.id}</td><td>${esc(f.item)}</td><td class="small">${esc(f.why)}</td><td class="small">${esc(f.need)}</td><td class="small">${src(f.src)}</td></tr>`).join('')}
</tbody></table></section>`);

pages['suggestions.html'] = page('Suggestions', 'suggestions.html', `
<section class="card"><h1>Suggestions</h1><ol>${SUGGESTIONS.map((s) => `<li>${esc(s)}</li>`).join('')}</ol></section>`);

pages['sources.html'] = page('Source register', 'sources.html', `
<section class="card"><h1>Source register</h1>
<p class="small">Each link is to an official or primary source. "NOT FETCHED" entries are linked for reference only and are flagged.</p>
<table><thead><tr><th>Source</th><th>Link</th><th>Status</th></tr></thead><tbody>
${Object.entries(SOURCES).map(([k, s]) => `<tr><td>${esc(s.title)}</td><td class="small"><a href="${esc(s.url)}">${esc(s.url)}</a></td><td class="small">${esc(s.status)}</td></tr>`).join('')}
</tbody></table></section>`);

pages['brief.html'] = page('Attorney and CPA brief', 'brief.html', `
<section class="card brief"><h1>Attorney and CPA briefing (one page)</h1>
<p class="small">Prepared 2026-11-25 for review. Anonymised: Property A (Santa Clara County, inherited via trust, expected about 2040 to 2050); Property B (San Francisco, owned by the heir). Not advice.</p>
<h2>Questions</h2>
<ol>
<li>Confirm the Prop 19 claim path: one-year occupancy, three-year claim, and the step-transaction rule (BOE LTA 2026/026).${flagTag('F07')}</li>
<li>Confirm the base-year value for Property A and the factored-base computation.${flagTag('F08')}</li>
<li>Confirm estate-tax position at the date of death: Property A is far below $15,000,000 alone; other assets unknown. Confirm the Form 706 deadline and portability.${flagTag('F01')}${flagTag('F03')}</li>
<li>Written valuation at the date of death; basis at FMV (Pub. 551).</li>
<li>Like-kind exchange (§1031) advice before any sale; depreciation and recapture if any part is rented.${flagTag('F06')}</li>
<li>Principal-residence exclusion ($250,000 single, pending verification); capital-gain rates applied.${flagTag('F13')}${flagTag('F14')}</li>
<li>Holding structure for sale proceeds (investing policy, DECISION_RULES.md §5).</li>
</ol>
<h2>Key figures (rounded to $10)</h2>
<table><tbody>
<tr><th>Federal basic exclusion, 2026</th><td class="num">${money(M.C.fedBasicExclusion2026)}</td><td class="small">${src('revproc')}</td></tr>
<tr><th>Prop 19 indexed amount (2/16/2025 to 2/15/2027)</th><td class="num">${money(M.C.prop19Indexed)}</td><td class="small">${src('lta25009')}</td></tr>
<tr><th>County documentary transfer tax</th><td>$0.55 per $500</td><td class="small">${src('rtc11911')}</td></tr>
<tr><th>CA top rate; 1% surcharge above $1,000,000</th><td>12.30%; 1%</td><td class="small">${src('ftb540')}; ${src('rtc17043')}</td></tr>
<tr><th>Small-estate affidavit threshold (CA)</th><td class="num">${money(166250)}</td><td class="small">${src('prob13100')}</td></tr>
<tr><th>Default pick (no commitment), 2040/20</th><td>${esc(pathLabel(pick2040_20))}</td><td class="small">Model</td></tr>
<tr><th>Default pick (with commitment and comparables), 2040/20</th><td>${esc(pathLabel(pickC2040_20))}</td><td class="small">Model</td></tr>
</tbody></table>
<h2>Decision and date</h2>
<p>Criteria fixed 2026-11-25 (DECISION_RULES.md). No choice committed. Re-run yearly and on any trigger in §4.</p>
</section>`, { cls: 'print' });

// ---- Write -----------------------------------------------------------------
fs.mkdirSync(path.join(DOCS, 'assets'), { recursive: true });
fs.mkdirSync(path.join(DOCS, 'data'), { recursive: true });
for (const [name, html] of Object.entries(pages)) fs.writeFileSync(path.join(DOCS, name), html);
fs.copyFileSync(path.join(__dirname, 'model.js'), path.join(DOCS, 'assets', 'model.js'));
fs.writeFileSync(path.join(DOCS, '.nojekyll'), '');

const out = { built: new Date().toISOString().slice(0, 10), defaults: M.DEFAULTS, cases: {}, sensitivity, scenarios: M.SCENARIOS };
for (const c of CASES) {
  const k = `${c.T}-${c.H}`;
  const r = results[k];
  out.cases[k] = {
    T: c.T, H: c.H, pick: r.choice.pick, eligible: r.choice.eligible, notes: r.choice.notes,
    pickCommitted: committed[k].choice.pick,
    breakEven: be[k],
    rows: M.PATHS.map((p) => ({ code: p.code, name: p.name, primaryMedian: M.r10(r.rows[p.code].primaryMedian), p10: M.r10(r.rows[p.code].p10), p90: M.r10(r.rows[p.code].p90), worstBlackSwan: M.r10(r.rows[p.code].worstBlackSwan), liquidAtT: M.r10(r.rows[p.code].base.liquidAtT), medianFinancial: M.r10(r.rows[p.code].medianFin) })),
  };
}
fs.writeFileSync(path.join(DOCS, 'data', 'model.json'), JSON.stringify(out, null, 1));
console.log('built', Object.keys(pages).length, 'pages; picks:', pickAll.join(' | '));
