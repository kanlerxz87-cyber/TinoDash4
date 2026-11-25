#!/usr/bin/env node
/* Build the static site into site/ (served from the repository's main branch under decision-analysis/site/).
 * Inputs : model/model.js, data/*.json
 * Outputs: site/*.html, site/style.css, site/app.js, site/model.js, site/results.json
 * Every dollar figure is rounded to the nearest $10 (model.r10).
 * Run: node scripts/build.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const M = require('../model/model.js');

const ROOT = path.join(__dirname, '..');
const DOCS = path.join(ROOT, 'site');
const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const SOURCES = read('data/sources.json');
const TABLES = read('data/tables.json');
const FLAGS = read('data/flags.json');
const TIMELINE = read('data/timeline.json');
const GLOSSARY = read('data/glossary.json');
const SUGGESTIONS = read('data/suggestions.json');
const INVENTORY = read('data/inventory.json');
const CRITERIA = read('data/criteria.json');

const MC_N = 1000;
const MC_SEED = 20261125;
const BUILD_DATE = '2026-11-25';

/* ---------- formatting helpers ---------- */
const esc = (s) => String(s === null || s === undefined ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const usd = (x) => (x === null || x === undefined || !isFinite(x)) ? '—' : (x < 0 ? '−$' : '$') + Math.abs(M.r10(x)).toLocaleString('en-US');
const pct = (x, d) => (x === null || x === undefined || !isFinite(x)) ? '—' : (100 * x).toFixed(d === undefined ? 1 : d) + '%';
const pathLabel = (id) => (M.PATHS.find((p) => p.id === id) || { label: id }).label;
const pathShort = (id) => (M.PATHS.find((p) => p.id === id) || { short: id }).short;
const combos = [];
M.TRANSFER_YEARS.forEach((T) => M.HORIZONS.forEach((H) => combos.push({ T, H, key: T + '|' + H })));

function srcLink(id) {
  const s = SOURCES[id];
  if (!s) return '<span class="flag">no source</span>';
  if (!s.url) return `<span class="flag">${esc(s.publisher)} (internal)</span>`;
  return `<a href="${esc(s.url)}" rel="noopener">${esc(s.publisher)}</a> <span class="tag tag-${esc(s.type)}">${esc(s.type)}</span>`;
}

/* ---------- model runs ---------- */
const base = M.rankDeterministic({});
const mc = M.monteCarlo({}, MC_N, MC_SEED).results;

// Scenario re-runs (every input change re-runs the model; the report says whether the recommendation moved)
const SCENARIOS = [
  { id: 'eq55', label: 'Equity return 5.5% (was 6.5%)', params: { eq: 0.055 }, status: 'assumption' },
  { id: 'eq75', label: 'Equity return 7.5%', params: { eq: 0.075 }, status: 'assumption' },
  { id: 'gp2', label: 'Property value growth 2%/yr (was 3%)', params: { g_prop: 0.02 }, status: 'assumption' },
  { id: 'gp4', label: 'Property value growth 4%/yr', params: { g_prop: 0.04 }, status: 'assumption' },
  { id: 'cash3', label: 'Treasury yields 3.0% (was about 4.4%)', params: { cash_yield: 0.03, park_yield: 0.03 }, status: 'official base, test value' },
  { id: 'infl4', label: 'Inflation 4%/yr (was 2.5%)', params: { infl: 0.04 }, status: 'assumption' },
  { id: 'v28', label: 'Property A value $2.8M (was $3.1M)', params: { V0: 2800000 }, status: 'test value' },
  { id: 'v34', label: 'Property A value $3.4M', params: { V0: 3400000 }, status: 'test value' },
  { id: 'rent13', label: 'Rent 30% above HUD floor', params: { rent_mult: 1.3 }, status: 'test value' },
  { id: 'ins', label: 'Insurance $2,000 owner + $2,500 landlord (test values, not estimates)', params: { ins_own: 2000, ins_rent: 2500 }, status: 'test value' },
  { id: 'pb1m', label: 'Decedent base-year value $1,000,000 (hypothetical; Prop 19 test)', params: { parentBase: 1000000 }, status: 'hypothetical' },
  { id: 'mfj', label: 'Married filing jointly exclusion $500,000', params: { s121: 500000 }, status: 'test value' },
  { id: 'fed35', label: 'Household federal bracket 35% (was 24%)', params: { fed_ord: 0.35 }, status: 'test value' }
];
const rerun = SCENARIOS.map((sc) => {
  const r = M.rankDeterministic(sc.params);
  const changed = combos.filter((c) => r[c.key][0].id !== base[c.key][0].id);
  return { sc, r, changed };
});
const movedAny = rerun.filter((x) => x.changed.length > 0);

// Breakpoints ("what would change the answer")
const bp = {
  eqSellVsLive: M.breakpoint('eq', 0.0, 0.15, 'SELL', 'LIVE', 2040, 10, {}),
  eqSellVsRent: M.breakpoint('eq', 0.0, 0.15, 'SELL', 'RENT', 2040, 10, {}),
  gpLiveVsSell: M.breakpoint('g_prop', -0.02, 0.12, 'LIVE', 'SELL', 2040, 10, {}),
  gpRentVsSell: M.breakpoint('g_prop', -0.02, 0.12, 'RENT', 'SELL', 2040, 10, {}),
  pbLiveVsSell: M.breakpoint('parentBase', 0, 3100000, 'LIVE', 'SELL', 2040, 10, {}),
  pbLiveVsSell20: M.breakpoint('parentBase', 0, 3100000, 'LIVE', 'SELL', 2040, 20, {})
};

// Black-swan stylised shocks (entry timing)
const OFFSETS = [0, 12, 24, 36, 48];
const shocks = {};
['1929', '2008'].forEach((sh) => {
  shocks[sh] = {};
  ['SELL', 'M3'].forEach((id) => {
    const vals = OFFSETS.map((off) => M.shockedRun(id, 2040, 20, M.constMacro(M.DEFAULTS), {}, sh, off).realRounded);
    shocks[sh][id] = { vals, min: Math.min(...vals), max: Math.max(...vals), median: M.quantile(vals, 0.5) };
  });
});

// Stationary regime shares of the Markov chain (black-swan context)
function stationary() {
  const S = M.REGIMES ? Object.keys(M.REGIMES) : [];
  let pi = S.map(() => 1 / S.length);
  for (let i = 0; i < 2000; i++) {
    const nxt = S.map(() => 0);
    S.forEach((a, ia) => S.forEach((b, ib) => { nxt[ib] += pi[ia] * M.TRANS[a][ib]; }));
    pi = nxt;
  }
  return S.map((s, i) => ({ code: s, name: M.REGIMES[s].name, share: pi[i] }));
}
const regimeShares = stationary();

// Projection of the federal basic exclusion (indexed at assumed inflation; assumption)
const projections = [2026, 2040, 2045, 2050].map((y) => ({ year: y, value: 15000000 * Math.pow(1 + M.DEFAULTS.infl, y - 2026) }));

// Recommendation (base, deterministic) per combo and MC p50 top
function mcTop(T, H) {
  const ids = M.PATHS.map((p) => p.id);
  return ids.slice().sort((a, b) => mc[b + '|' + T + '|' + H].p50 - mc[a + '|' + T + '|' + H].p50)[0];
}
const baseTopCount = {};
combos.forEach((c) => { const t = base[c.key][0].id; baseTopCount[t] = (baseTopCount[t] || 0) + 1; });
const mcTopCount = {};
combos.forEach((c) => { const t = mcTop(c.T, c.H); mcTopCount[t] = (mcTopCount[t] || 0) + 1; });
const topPathBase = Object.keys(baseTopCount).sort((a, b) => baseTopCount[b] - baseTopCount[a])[0];
const topPathMC = Object.keys(mcTopCount).sort((a, b) => mcTopCount[b] - mcTopCount[a])[0];

/* ---------- HTML shell ---------- */
const NAV = [
  ['index.html', 'Home'], ['dashboard.html', 'Dashboard'], ['criteria.html', 'Criteria'],
  ['tables.html', 'Tables'], ['tax.html', 'Tax'], ['property-rules.html', 'Property rules'],
  ['blackswan.html', 'Black swan'], ['timeline.html', 'Timeline'], ['glossary.html', 'Glossary'],
  ['inventory.html', 'Inventory'], ['briefing.html', 'Attorney & CPA briefing'],
  ['flagged.html', 'Flagged for review'], ['suggestions.html', 'Suggestions'], ['sources.html', 'Sources']
];
function shell(file, title, body, opts) {
  opts = opts || {};
  const nav = NAV.map(([f, l]) => `<a href="${f}"${f === file ? ' class="on"' : ''}>${esc(l)}</a>`).join('');
  const extra = opts.head || '';
  const scripts = opts.scripts || '';
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)} · Inheritance decision analysis</title>
<link rel="stylesheet" href="style.css">${extra}
</head><body class="${opts.bodyClass || ''}">
<header class="site"><div class="brand">Inheritance decision analysis</div>
<nav>${nav}</nav></header>
<main>${body}</main>
<footer class="site">Built ${BUILD_DATE} from official sources listed on each row. Values rounded to the nearest $10. Model estimates, not tax, legal or investment advice. Blank cells are unverified and listed on the Flagged for Review page. Personal information is excluded from this site.</footer>
${scripts}
</body></html>`;
}
const write = (file, html) => fs.writeFileSync(path.join(DOCS, file), html);

function table(headers, rows, cls) {
  return `<div class="scroll"><table class="${cls || ''}"><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
const cell = (v) => esc(v);

/* ---------- Page: Home ---------- */
const topPathLabel = pathLabel(topPathBase);
const movedCount = movedAny.length;
const gapsFlagged = FLAGS.filter((f) => ['blank', 'conflict', 'unverified', 'preliminary', 'irregular'].includes(f.status)).length;
function bpText(v, what) { return v === null ? `no crossover in the tested range (${what})` : `${pct(v, 1)} (${what})`; }

const econLive = M.run('LIVE', 2040, 10, M.constMacro(M.DEFAULTS), {}).imputedReal;
const whatChanges = `
<section class="card key">
<h2>What would change the answer</h2>
<p class="small">Base case as of ${BUILD_DATE}. Conditional on the flagged inputs (Flagged for Review).</p>
<ol>
  <li><strong>Equity return.</strong> SELL = RENT at an equity return of ${bp.eqSellVsRent === null ? 'no crossover in range' : pct(bp.eqSellVsRent, 2)} (2040 transfer, 10-year horizon). SELL vs. LIVE: ${bp.eqSellVsLive === null ? 'no crossover between 0% and 15%; SELL stays first' : pct(bp.eqSellVsLive, 2)}.</li>
  <li><strong>Property growth.</strong> For LIVE to match SELL (2040, 10 years), Property A would need to appreciate about ${bp.gpLiveVsSell === null ? 'more than the tested range' : pct(bp.gpLiveVsSell, 1) + ' per year'}; for RENT, about ${bp.gpRentVsSell === null ? 'more than the tested range' : pct(bp.gpRentVsSell, 1) + ' per year'}.</li>
  <li><strong>Prop 19 base (blank).</strong> ${bp.pbLiveVsSell === null ? 'Even with a zero decedent base-year value, LIVE stays below SELL on the financial measure (2040, 10 years). The Prop 19 benefit alone does not change the answer in this model.' : 'LIVE matches SELL at a decedent base of ' + usd(bp.pbLiveVsSell) + '.'}</li>
  <li><strong>Economic view.</strong> Adding imputed rent avoided by living in Property A (${usd(econLive)} real, 2040, 10 years; not cash, and only if the household would otherwise pay rent) does not change the top path in this combination (SELL stays first). The financial view is the headline.</li>
  <li><strong>Test scenarios.</strong> ${movedCount} of ${SCENARIOS.length} tested input changes move the top-ranked path in any transfer year and horizon (see Dashboard).</li>
  <li><strong>Blank inputs.</strong> ${gapsFlagged} flagged items, including insurance, rent comparables, and the decedent's base-year value.</li>
</ol>
</section>`;

const execSummary = `
<section class="card">
<h2>Executive summary (as of ${BUILD_DATE})</h2>
<p>The model compares seven paths for Property A (Cupertino area, est. ${usd(M.DEFAULTS.V0)} in Nov 2026) over transfer years 2040, 2045 and 2050 and horizons of 5, 10 and 20 years. Property B (San Francisco) is already owned and is held constant across paths.</p>
<ul>
  <li>Base case, deterministic: <strong>${esc(topPathLabel)}</strong> ranks first in ${baseTopCount[topPathBase]} of ${combos.length} transfer-year and horizon combinations.</li>
  <li>Monte Carlo (${MC_N} regime-switching draws, median): <strong>${esc(pathLabel(topPathMC))}</strong> ranks first in ${mcTopCount[topPathMC]} of ${combos.length} combinations.</li>
  <li>Inheritance is not taxed at the California state level (secondary sources; flagged). Federal estate tax applies only above the $15,000,000 basic exclusion (2026, official), and the decedent's estate size is unknown (blank).</li>
  <li>Prop 19 only helps a path where the heir occupies the house; the decedent's base-year value is blank, so the LIVE result is a lower bound.</li>
  <li>Stress tests: 1929-type and 2008-type entry shocks change the staged path (M3) by a wide margin depending on timing. Staging reduces drawdown exposure during the staging window; it is not a guaranteed outcome.</li>
  <li>Several headline facts are preliminary (Prop 3 and Prop 40 certification on Dec 11, 2026; SF Prop H and Prop I; Measure E city scope). See Flagged for Review.</li>
</ul>
<p class="small">Decision date: ${BUILD_DATE}. Re-run after any input change; the scenario report on the Dashboard states whether the recommendation moved.</p>
</section>`;

const homeBody = `
<h1>Inheritance decision analysis</h1>
<p class="lead">A privacy-first comparison of paths for an inherited Cupertino-area house, set against an existing San Francisco property. Figures use official sources where available and label everything else.</p>
${whatChanges}
${execSummary}
<section class="card">
<h2>Where to go next</h2>
<div class="grid">
${[['dashboard.html', 'Dashboard', 'Results table and what-if controls'], ['criteria.html', 'Criteria', 'Choose-if and reject-if conditions per path'], ['tables.html', 'Tables', 'Property tax, insurance, transfer tax, yields'], ['tax.html', 'Tax thresholds', 'Federal, state and local with projections'], ['property-rules.html', 'Property rules', 'Prop 13, 19, 58, H; depreciation'], ['blackswan.html', 'Black-swan economics', 'Inflation and crash scenarios'], ['timeline.html', 'Timeline', 'Deadlines and model dates'], ['briefing.html', 'Attorney & CPA briefing', 'One printable page'], ['flagged.html', 'Flagged for review', 'Blanks, conflicts, preliminary items'], ['suggestions.html', 'Suggestions', 'For owner review; not applied']].map(([f, t, d]) => `<a class="tile" href="${f}"><strong>${esc(t)}</strong><span>${esc(d)}</span></a>`).join('')}
</div></section>`;
write('index.html', shell('index.html', 'Home', homeBody));

/* ---------- Page: Dashboard ---------- */
const dashHeaders = ['Path'].concat(combos.map((c) => `${c.T} + ${c.H}y`));
const dashRows = M.PATHS.map((pa) => [`<strong>${esc(pa.short)}</strong><br><span class="small">${esc(pa.label)}</span>`].concat(combos.map((c) => {
  const r = base[c.key].find((x) => x.id === pa.id);
  const top = base[c.key][0].id === pa.id ? ' class="best"' : '';
  return `<span${top}>${usd(r.realRounded)}</span>`;
})));
const mcRows = M.PATHS.map((pa) => [`<strong>${esc(pa.short)}</strong>`].concat(combos.map((c) => {
  const s = mc[pa.id + '|' + c.T + '|' + c.H];
  return `${usd(s.p50)} <span class="small">(${usd(s.p10)}–${usd(s.p90)}; beats Sell ${pct(s.probBeatsSell, 0)})</span>`;
})));

const scenRows = rerun.map((x) => [
  esc(x.sc.label), `<span class="tag">${esc(x.sc.status)}</span>`,
  x.changed.length ? `<strong>Yes</strong> (${x.changed.length} of ${combos.length})` : 'No',
  x.changed.length ? esc(x.changed.map((c) => `${c.T}/${c.H}y → ${pathShort(x.r[c.key][0].id)}`).join('; ')) : '—'
]);

const INPUT_SOURCE = {
  V0: 'OWNER', parentBase: 'ASSESSOR_P19', allowance: 'ASSESSOR_P19', cap13: 'BALLOT_ART13A', tax_rate: 'BALLOT_ART13A',
  infl: 'BLS_CPI', cash_yield: 'TREAS_YIELD', park_yield: 'TREAS_YIELD', fmr: 'HUD_FMR', water_mo: 'OWNER', elec_net_mo: 'OWNER',
  ins_own: 'CDI_DATA', ins_rent: 'CDI_DATA', dtt: 'CLERK_FEES', measureE: 'CLERK_MEASURE_E', rec: 'CLERK_FEES',
  bldg_share: 'IRS_P544', dep_years: 'IRS_P544', ca_ord: 'FTB_BOOKLET', ca_cg: 'FTB_BOOKLET', niit: 'IRS_TC559',
  recap_max: 'IRS_P544', s121: 'IRS_P523', cg_fed: 'IRS_RP2025_32', fed_ord: 'IRS_RP2025_32'
};
const inputsRows = Object.keys(M.DEFAULTS).map((k) => {
  const v = M.DEFAULTS[k];
  const st = M.INPUT_STATUS[k] || 'assumption';
  const sid = INPUT_SOURCE[k] || null;
  const shown = v === null ? '<span class="flag">blank</span>' : (typeof v === 'number' && Math.abs(v) >= 1000 ? usd(v) : (typeof v === 'number' && v < 1 && v > -1 ? pct(v, 2) : esc(v)));
  return [esc(k), shown, `<span class="tag tag-${esc(st)}">${esc(st)}</span>`, sid ? srcLink(sid) : '<span class="flag">assumption - no public source (flagged)</span>'];
});


const whatIf = `
<section class="card">
<h2>What-if controls (runs in your browser)</h2>
<p class="small">Change an input and the table updates using the same model. The "Recommendation moved?" line compares the new top path with the base case in this build (${BUILD_DATE}). Blank inputs stay blank unless you type a value.</p>
<div class="controls" id="controls">
  <label>Property A value (USD)<input id="c_V0" type="number" value="${M.DEFAULTS.V0}" step="10000"></label>
  <label>Equity return (nominal, %)<input id="c_eq" type="number" value="${(M.DEFAULTS.eq * 100).toFixed(2)}" step="0.25"></label>
  <label>Property growth (%/yr)<input id="c_g_prop" type="number" value="${(M.DEFAULTS.g_prop * 100).toFixed(2)}" step="0.25"></label>
  <label>Inflation (%/yr)<input id="c_infl" type="number" value="${(M.DEFAULTS.infl * 100).toFixed(2)}" step="0.25"></label>
  <label>Treasury yield (%/yr)<input id="c_cash_yield" type="number" value="${(M.DEFAULTS.cash_yield * 100).toFixed(2)}" step="0.05"></label>
  <label>Staged park months<input id="c_park_months" type="number" value="${M.DEFAULTS.park_months}" step="1"></label>
  <label>Decedent base-year value (USD; blank = unknown)<input id="c_parentBase" type="number" value="" placeholder="blank"></label>
  <label>Owner insurance, Property A ($/yr; blank = unknown)<input id="c_ins_own" type="number" value="" placeholder="blank"></label>
  <label>Rent multiple on HUD floor<input id="c_rent_mult" type="number" value="${M.DEFAULTS.rent_mult}" step="0.05"></label>
  <label>Household federal rate (%)<input id="c_fed_ord" type="number" value="${(M.DEFAULTS.fed_ord * 100).toFixed(1)}" step="0.5"></label>
  <label>Transfer year<select id="c_T">${M.TRANSFER_YEARS.map((t) => `<option value="${t}"${t === 2040 ? ' selected' : ''}>${t}</option>`).join('')}</select></label>
  <label>Horizon (years)<select id="c_H">${M.HORIZONS.map((h) => `<option value="${h}"${h === 10 ? ' selected' : ''}>${h}</option>`).join('')}</select></label>
</div>
<div id="whatif-out" class="out"></div>
</section>`;

const dashBody = `
<h1>Dashboard</h1>
<p class="lead">Real (inflation-adjusted, 2026 dollars) household wealth at the end of each horizon, financial measure only (rent and sale cash, not imputed housing). Base-case values from build ${BUILD_DATE}.</p>
<section class="card">
<h2>Table 1 - Deterministic base case, real $ (best per column in bold)</h2>
<p class="small">Sources: every input is listed in the Inputs table below with its link and status. Model rows link to those inputs.</p>
${table(dashHeaders, dashRows, 'dash')}
<p class="small">Source for every row: model run in this build; inputs in the Inputs table (links per input).</p>
</section>
<section class="card">
<h2>Table 2 - Monte Carlo (${MC_N} regime draws, seed ${MC_SEED}): median (10th–90th percentile), real $</h2>
${table(['Path'].concat(combos.map((c) => `${c.T} + ${c.H}y`)), mcRows, 'dash mc')}
<p class="small">"Beats Sell" = share of draws where the path finishes with more real wealth than Sell in the same transfer year and horizon. Regime parameters are assumptions (see Black swan).</p>
</section>
<section class="card">
<h2>Economic view (adds imputed rent avoided while living in the house; not cash)</h2>
<p class="small">Only paths with occupancy get imputed rent. Shown for comparison; the headline is the financial measure above.</p>
${table(['Path', 'Financial, real (2040+10y)', 'Imputed rent avoided, real', 'Economic, real'], ['LIVE','M1','M4'].map((id) => { const r = M.run(id, 2040, 10, M.constMacro(M.DEFAULTS), {}); return [esc(pathShort(id)), usd(r.realRounded), usd(r.imputedReal), usd(r.real + r.imputedReal)]; }))}
</section>
<section class="card">
<h2>Recommendation check</h2>
<p>Base-case top path across all ${combos.length} combinations: <strong>${esc(topPathLabel)}</strong>. Monte Carlo median top path: <strong>${esc(pathLabel(topPathMC))}</strong>.</p>
<p>Recommendation moved in ${movedAny.length} of ${SCENARIOS.length} tested input changes (table below). Each scenario is re-run from the same model; "moved" means the top path changed in at least one combination.</p>
${table(['Input change (test)', 'Status', 'Top path moved?', 'Where'], scenRows)}
</section>
${whatIf}
<section class="card">
<h2>Inputs (values, status and source)</h2>
<p class="small">Blank = not provided; the model does not infer missing values. Owner-provided figures are labelled and kept internal where they could identify the household.</p>
${table(['Input', 'Value', 'Status', 'Source'], inputsRows)}
</section>`;
const dashScripts = `<script src="model.js"></script><script src="app.js" defer></script>`;
write('dashboard.html', shell('dashboard.html', 'Dashboard', dashBody, { scripts: dashScripts }));

/* ---------- Page: Criteria ---------- */
const critRows = CRITERIA.paths.map((p) => {
  const pa = M.PATHS.find((x) => x.id === p.id);
  const bestCount = combos.filter((c) => base[c.key][0].id === p.id).length;
  const decision = `Model: ranks first in ${bestCount} of ${combos.length} combinations (base, ${BUILD_DATE}). Status: conditional (flags).`;
  return [`<strong>${esc(pa.short)}</strong><br>${esc(p.label)}`, `<ul>${p.choose_if.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`, `<ul>${p.reject_if.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`, esc(decision)];
});
const critBody = `
<h1>Decision criteria</h1>
<p class="lead">Criteria were written on ${esc(CRITERIA.written_on)}. They were written after test runs of a discarded draft model, and before the final figures in this build were generated. Changes must be logged as dated entries.</p>
<section class="card">
${table(['Path', 'Choose it if', 'Reject it if', 'Decision (dated)'], critRows)}
</section>
<section class="card">
<h2>Tie-breakers</h2>
<ul>${CRITERIA.tie_breakers.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>
</section>
<section class="card">
<h2>Decision log</h2>
${table(['Date', 'Item', 'Decision'], CRITERIA.decision_log.map((d) => [esc(d.date), esc(d.item), esc(d.decision)]))}
</section>`;
write('criteria.html', shell('criteria.html', 'Criteria', critBody));

/* ---------- Page: Tables ---------- */
function tblFromData(key) {
  const t = TABLES[key];
  return `<section class="card"><h2>${esc(t.title)}</h2>${table(t.columns, t.rows.map((r) => r.map((c, i) => {
    if (i === r.length - 2 && SOURCES[c]) return srcLink(c);
    return esc(c);
  })))}</section>`;
}
const projRows = projections.map((p) => [String(p.year), usd(p.value), srcLink('IRS_RP2025_32'), p.year === 2026 ? 'verified (2026 official amount)' : 'projection (assumption)']);
TABLES.projections.rows = projRows;
const tablesBody = `
<h1>Tables</h1>
<p class="lead">Every row has an official-source link where one exists. Blank cells are not yet verified; see Flagged for Review.</p>
${tblFromData('property_tax_cupertino')}
${tblFromData('property_tax_sf')}
${tblFromData('insurance')}
${tblFromData('local_transfer')}
${tblFromData('treasury')}
${tblFromData('macro')}
`;
write('tables.html', shell('tables.html', 'Tables', tablesBody));

/* ---------- Page: Tax ---------- */
const taxBody = `
<h1>Federal, state and local tax thresholds</h1>
<p class="lead">Thresholds as of ${BUILD_DATE}. Projections index the federal exclusion at ${pct(M.DEFAULTS.infl, 1)} a year (assumption), not law.</p>
${tblFromData('federal')}
${tblFromData('california')}
${tblFromData('local_transfer')}
<section class="card"><h2>${esc(TABLES.projections.title)}</h2>${table(TABLES.projections.columns, projRows)}</section>
<section class="card">
<h2>Proposed legislation tracking</h2>
${table(['Item', 'Status (as of ' + BUILD_DATE + ')', 'Source', 'Status'], [
  ['S.4246 Ultra-Millionaire Tax Act of 2026 (Warren)', 'Introduced Mar 26, 2026; referred to Senate Finance; no further action', srcLink('CONGRESS_S4246'), 'verified metadata; rate text conflict (F11)'],
  ['H.R.8085 (Jayapal)', 'Introduced Mar 25, 2026 (per research); referred to House Ways and Means', srcLink('CONGRESS_HR8085'), 'metadata from research; exact URL not verified'],
  ['California Prop 40 (one-time 5% billionaire tax)', 'Failed Nov 3, 2026 (preliminary)', srcLink('PROP40_NEWS'), 'preliminary (F14)'],
  ['California Prop 3 (top rates made permanent)', 'Passed Nov 3, 2026 (preliminary)', srcLink('PROP3_NEWS'), 'preliminary; certified Dec 11, 2026 (F13)']
])}
</section>`;
write('tax.html', shell('tax.html', 'Tax', taxBody));

/* ---------- Page: Property rules ---------- */
const propBody = `
<h1>Property rules: Prop 13, Prop 19, Prop 58, Prop H, depreciation and recapture</h1>
${tblFromData('property_rules')}
<section class="card">
<h2>Property A: model treatment</h2>
<ul>
  <li><strong>Live path:</strong> base carried over only if the parent's base is known (blank here). Without it, the base equals the market value at transfer, so the Prop 19 benefit shows as zero (lower bound).</li>
  <li><strong>Rent or sell:</strong> reassessed to market value at transfer; basis for income tax is the date-of-death value (step-up).</li>
  <li><strong>Depreciation:</strong> 80% building share (assumption) over 27.5 years; unrecaptured §1250 gain taxed at up to 25% federal plus NIIT and CA ordinary rates.</li>
  <li><strong>Transfer costs at sale:</strong> agent commission 2.5% and title 0.5% (assumptions); county documentary transfer tax 0.11%; recording $92; Measure E 0 for Cupertino (confirm).</li>
</ul>
</section>
<section class="card">
<h2>Property B (San Francisco): reference only</h2>
<p>Held constant across all paths. The rent roll, water, electricity and insurance are internal owner figures. The Prop H parcel tax (preliminary) and SF transfer-tax tiers are flagged; no SF tax is modelled against Property B.</p>
</section>`;
write('property-rules.html', shell('property-rules.html', 'Property rules', propBody));

/* ---------- Page: Black swan ---------- */
const shockRows = ['1929', '2008'].map((sh) => [
  `<strong>${sh}-type entry</strong><br><span class="small">${esc(M.SHOCKS[sh].label)}</span>`,
  ...['SELL', 'M3'].map((id) => `${esc(pathShort(id))}: ${usd(shocks[sh][id].min)} to ${usd(shocks[sh][id].max)} (median ${usd(shocks[sh][id].median)})`),
  `<span class="small">${esc(M.SHOCKS[sh].source)}</span>`
]);
const regimeRows = regimeShares.map((r) => [esc(r.name), pct(r.share, 1), `<span class="small">${esc(JSON.stringify(M.REGIMES[r.code]))}</span>`]);
const bsPaths = M.PATHS.map((pa) => {
  const s = mc[pa.id + '|2040|20'];
  return [esc(pa.short), usd(s.p10), usd(s.p50), usd(s.p90)];
});
const blackBody = `
<h1>Black-swan economic conditions (separate from base case)</h1>
<p class="lead">Market history and the regime model show how the paths behave when inflation and growth do not stay on the base track over about 50 years. Regime parameters are assumptions; the crash episodes are stylised paths built from official endpoints.</p>
<section class="card">
<h2>Stylised entry shocks: Sell vs. staged (2040 transfer, 20-year horizon, real $)</h2>
<p class="small">Crash starts at 0, 12, 24, 36 or 48 months after transfer. Staging buys over months 30-42; the outcome depends on when the crash starts.</p>
${table(['Scenario', 'Sell (range)', 'Staged M3 (range)', 'Source'], shockRows)}
</section>
<section class="card">
<h2>Regime model: long-run shares</h2>
<p class="small">Steady-state share of years in each regime implied by the transition matrix (assumption).</p>
${table(['Regime', 'Share of years', 'Parameters (mean/sd of inflation, growth, equity, real rate)'], regimeRows)}
</section>
<section class="card">
<h2>Monte Carlo, 2040 transfer, 20-year horizon, real $ (p10 / p50 / p90)</h2>
${table(['Path', 'p10', 'p50', 'p90'], bsPaths)}
</section>
<section class="card">
<h2>Historical anchors (official)</h2>
${table(['Item', 'Value', 'Source'], [
  ['1929 crash (Dow)', '381.17 (Sep 3, 1929) to 41.22 (Jul 8, 1932): −89%; nominal peak regained Nov 23, 1954', srcLink('FED_CRASH1929')],
  ['2007-09 equity decline', 'Conflicting: 49%–60% (lower bound used; F12)', '<span class="flag">conflict</span>'],
  ['Inflation now (CPI, Sep 2026)', '3.7% 12-month; core 2.6%', srcLink('BLS_CPI')],
  ['Longer-run inflation goal', '2% (PCE)', srcLink('FED_FAQ')]
])}
</section>`;
write('blackswan.html', shell('blackswan.html', 'Black swan', blackBody));

/* ---------- Page: Timeline ---------- */
const tlBody = `
<h1>Timeline of deadlines and model dates</h1>
${table(['Date', 'Item', 'Source', 'Status'], TIMELINE.map((t) => [esc(t.date), esc(t.item), srcLink(t.source), esc(t.status)]))}`;
write('timeline.html', shell('timeline.html', 'Timeline', tlBody));

/* ---------- Page: Glossary ---------- */
const glBody = `<h1>Glossary</h1>${table(['Term', 'Meaning'], GLOSSARY.map(([a, b]) => [esc(a), esc(b)]))}`;
write('glossary.html', shell('glossary.html', 'Glossary', glBody));

/* ---------- Page: Inventory ---------- */
const invBody = `
<h1>Anonymised private inventory</h1>
<p class="lead">Placeholders replace all names, addresses, account numbers and identifiers. Only facts needed for the analysis are shown.</p>
${INVENTORY.map((it) => `<section class="card"><h2>${esc(it.name)}</h2>${table(['Item', 'Value'], it.fields.map(([a, b]) => [esc(a), esc(b)]))}</section>`).join('')}`;
write('inventory.html', shell('inventory.html', 'Inventory', invBody));

/* ---------- Page: Flagged ---------- */
const flagBody = `
<h1>Flagged for review</h1>
<p class="lead">These items do not block the merge. Each is blank, conflicting, preliminary, unverified or an assumption, and needs the action listed.</p>
${table(['ID', 'Area', 'Item', 'Status', 'Action', 'Source'], FLAGS.map((f) => [esc(f.id), esc(f.area), esc(f.item), `<span class="tag">${esc(f.status)}</span>`, esc(f.action), srcLink(f.source)]))}`;
write('flagged.html', shell('flagged.html', 'Flagged for review', flagBody));

/* ---------- Page: Suggestions ---------- */
const sugBody = `
<h1>Suggestions (for owner review; not applied)</h1>
<p class="lead">These are suggestions, not decisions. The model does not depend on them and nothing has been changed in response.</p>
${table(['ID', 'Suggestion', 'Status'], SUGGESTIONS.map((s) => [esc(s.id), esc(s.text), 'open for owner review']))}`;
write('suggestions.html', shell('suggestions.html', 'Suggestions', sugBody));

/* ---------- Page: Briefing (one printable page) ---------- */
const topRows = combos.slice(0, 0);
const briefBody = `
<div class="print-page">
<h1>Attorney &amp; CPA briefing (one page)</h1>
<p class="small">Prepared ${BUILD_DATE} from the public site. Anonymised. Values rounded to $10. Items marked [flag] are unverified.</p>
<h3>Question</h3>
<p>Which path for an inherited Cupertino-area residence (Property A, est. ${usd(M.DEFAULTS.V0)}, owner estimate [flag]) is best for a household that already owns a San Francisco property (Property B)? Transfer year 2040, 2045 or 2050; horizons 5, 10, 20 years.</p>
<h3>Base-case result (real $)</h3>
<ul>
  <li>Top path (base, all combinations): ${esc(pathLabel(topPathBase))}; Monte Carlo top: ${esc(pathLabel(topPathMC))}.</li>
  <li>Sell at 2040, 10-year horizon: ${usd(base['2040|10'].find((x) => x.id === 'SELL').realRounded)}; Live at same: ${usd(base['2040|10'].find((x) => x.id === 'LIVE').realRounded)} (no Prop 19 benefit; base blank).</li>
</ul>
<h3>Questions for counsel and CPA</h3>
<ol>
  <li>Is the decedent's estate below the $15,000,000 federal basic exclusion (2026)? Is Form 706 required? [flag F19]</li>
  <li>What is the decedent's Prop 13 base-year value, and does the heir qualify for the Prop 19 family-home rule? [flag F02, F03]</li>
  <li>Does the trust permit an heir to occupy, or must the property be sold or rented? [flag F04]</li>
  <li>Confirm the step-up basis and the §1014(f) consistency treatment for the date-of-death value. [IRS Pub 551]</li>
  <li>Confirm Cupertino is outside Measure E (San Jose only) and the transfer tax amounts. [flag F08]</li>
  <li>Confirm the recapture and NIIT treatment for any rental period. [flag F26]</li>
</ol>
<h3>Key sources</h3>
<p class="small">IRS Rev. Proc. 2025-32; IRS Pub 523, 544, 551; IRS Topic 559; IRS Form 706 instructions; Santa Clara Clerk-Recorder fee schedule and Measure E page; Santa Clara Assessor FAQ (Props 19, 58); Treasury par yields 11/24/2026. Full list: Sources page.</p>
</div>`;
write('briefing.html', shell('briefing.html', 'Attorney & CPA briefing', briefBody, { bodyClass: 'briefing' }));

/* ---------- Page: Sources ---------- */
const srcBody = `
<h1>Sources</h1>
<p class="lead">Each row shows the publisher, type (primary = official government source; secondary = news or summary, not used as the only basis for a row) and the note on what was read.</p>
${table(['ID', 'Title', 'Publisher', 'Type', 'What was read / note'], Object.keys(SOURCES).map((k) => {
  const s = SOURCES[k];
  return [esc(k), s.url ? `<a href="${esc(s.url)}" rel="noopener">${esc(s.title)}</a>` : esc(s.title), esc(s.publisher), `<span class="tag tag-${esc(s.type)}">${esc(s.type)}</span>`, esc(s.note || '')];
}))}`;
write('sources.html', shell('sources.html', 'Sources', srcBody));

/* ---------- Results file (rounded, no personal data) ---------- */
const results = {
  build: BUILD_DATE, mc: { n: MC_N, seed: MC_SEED },
  base: Object.fromEntries(Object.keys(base).map((k) => [k, base[k].map((x) => ({ path: x.id, realRounded: x.realRounded }))])),
  mc_p50: Object.fromEntries(Object.keys(mc).map((k) => [k, { p10: mc[k].p10, p50: mc[k].p50, p90: mc[k].p90, probBeatsSell: Math.round(mc[k].probBeatsSell * 100) / 100 }])),
  scenarios: rerun.map((x) => ({ id: x.sc.id, label: x.sc.label, status: x.sc.status, moved: x.changed.length > 0, changed: x.changed.map((c) => c.key) })),
  breakpoints: bp, shocks, regimeShares, topPathBase, topPathMC
};
fs.writeFileSync(path.join(DOCS, 'results.json'), JSON.stringify(results, null, 1));

/* ---------- Browser assets ---------- */
fs.copyFileSync(path.join(ROOT, 'model/model.js'), path.join(DOCS, 'model.js'));
fs.writeFileSync(path.join(DOCS, 'style.css'), fs.readFileSync(path.join(ROOT, 'scripts/style.css'), 'utf8'));
fs.copyFileSync(path.join(ROOT, 'scripts/app.js'), path.join(DOCS, 'app.js'));
fs.writeFileSync(path.join(DOCS, '.nojekyll'), '');
console.log('built', fs.readdirSync(DOCS).length, 'files; base top:', topPathBase, 'mc top:', topPathMC, 'moved:', movedAny.length);
