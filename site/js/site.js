/* TinoDash4 — shared site engine: data loading, nav, tables, charts, what-if lab.
   Maps exactly to model/build_model.py output shapes. */
"use strict";

const NAV = [
  { group: "Start", items: [
    ["index", "Executive summary", "index.html"],
    ["dashboard", "Dashboard & What-if lab", "dashboard.html"],
  ]},
  { group: "Analysis", items: [
    ["blackswan", "Black swans & entry path", "blackswan.html"],
  ]},
  { group: "Data & law", items: [
    ["data", "Data tables", "data.html"],
    ["timeline", "Inheritance timeline", "timeline.html"],
    ["flagged", "Flagged for review", "flagged.html"],
    ["sources", "Source registry", "sources.html"],
  ]},
  { group: "Reference", items: [
    ["questions", "Questions & info needed", "questions.html"],
    ["suggestions", "Suggestions for review", "suggestions.html"],
    ["glossary", "Glossary", "glossary.html"],
    ["briefing", "Attorney & CPA briefing", "briefing.html"],
  ]},
];

const COLORS = ["#5b9dff", "#39d0a3", "#ffb454", "#ff6b7a", "#b48cff", "#65c7ff"];

const Site = { d: {} };
Site.load = async function () {
  const files = ["sources", "tables", "projection", "sensitivity", "blackswan",
                 "mc", "model_constants", "same_year_sale", "timeline", "questions",
                 "glossary", "suggestions", "flags"];
  const out = {};
  await Promise.all(files.map(async f => {
    try { out[f] = await (await fetch(`data/${f}.json`)).json(); }
    catch (e) { out[f] = null; console.error("load fail", f, e); }
  }));
  this.d = out;
  return out;
};

/* ---------- helpers ---------- */
const money = v => (v == null || isNaN(v)) ? "—" : "$" + Math.round(v).toLocaleString("en-US");
const moneyC = v => {
  if (v == null || isNaN(v)) return "—";
  const a = Math.abs(v);
  if (a >= 1e9) return (v < 0 ? "-$" : "$") + (a / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return (v < 0 ? "-$" : "$") + (a / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return (v < 0 ? "-$" : "$") + (a / 1e3).toFixed(0) + "k";
  return money(v);
};
const pct = (v, d = 1) => (v == null || isNaN(v)) ? "—" : (v * 100).toFixed(d) + "%";
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function src(id) {
  const s = Site.d.sources && Site.d.sources[id];
  if (!s) return id ? `<span class="pill">${esc(id)}</span>` : "";
  return `<a href="${esc(s.u)}" target="_blank" rel="noopener" title="${esc(s.o)} — ${esc(s.t)}">[${esc(id)}]</a>`;
}
function srcCell(ids) {
  if (!ids) return "";
  const arr = Array.isArray(ids) ? ids : [ids];
  return `<span class="src">${arr.map(src).join(" ")}</span>`;
}
const sevPill = sev => `<span class="pill ${String(sev).toLowerCase() === "high" ? "high" : String(sev).toLowerCase() === "medium" ? "med" : "low"}">${esc(sev)}</span>`;

/* ---------- nav ---------- */
function buildNav() {
  const page = document.body.dataset.page || "";
  const el = document.getElementById("nav");
  if (!el) return;
  let h = `<div class="brand">TinoDash4</div>
    <div class="sub">Household decision model · estate &amp; property · as of 2026-11-25<br>Public data only · no personal data</div>`;
  for (const g of NAV) {
    h += `<div class="grp">${esc(g.group)}</div>`;
    for (const [key, label, href] of g.items)
      h += `<a href="${href}" class="${key === page ? "active" : ""}">${esc(label)}</a>`;
  }
  el.innerHTML = h;
}

/* ---------- charts (pure SVG) ---------- */
function lineChart(container, series, opts = {}) {
  const W = opts.width || 860, H = opts.height || 340;
  const ml = 64, mr = 16, mt = 14, mb = 34;
  const all = series.flatMap(s => s.data).filter(v => v != null && !isNaN(v));
  if (!all.length || !container) { if (container) container.innerHTML = "<p class='lede'>No data.</p>"; return; }
  let ymin = Math.min(...all), ymax = Math.max(...all);
  if (opts.zeroBase) ymin = Math.min(0, ymin);
  const pad = (ymax - ymin) * 0.06 || 1;
  ymin -= pad; ymax += pad;
  const n = Math.max(...series.map(s => s.data.length));
  const X = i => ml + (W - ml - mr) * (n <= 1 ? 0 : i / (n - 1));
  const Y = v => mt + (H - mt - mb) * (1 - (v - ymin) / (ymax - ymin));
  let g = "";
  for (let k = 0; k <= 4; k++) {
    const v = ymin + (ymax - ymin) * k / 4;
    g += `<line x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="#2a3550" stroke-width="1"/>
          <text x="${ml - 6}" y="${Y(v) + 4}" fill="#9aa7bd" font-size="11" text-anchor="end">${moneyC(v)}</text>`;
  }
  const xTicks = opts.xTicks || [0, Math.floor(n / 3), Math.floor(2 * n / 3), n - 1];
  for (const i of xTicks) {
    if (i < 0 || i >= n) continue;
    g += `<text x="${X(i)}" y="${H - 10}" fill="#9aa7bd" font-size="11" text-anchor="middle">${esc((opts.xLabels && opts.xLabels[i]) || ("t" + i))}</text>`;
  }
  series.forEach((s, si) => {
    const pts = s.data.map((v, i) => v == null ? null : `${X(i).toFixed(1)},${Y(v).toFixed(1)}`).filter(Boolean).join(" ");
    if (pts) g += `<polyline points="${pts}" fill="none" stroke="${s.color || COLORS[si % COLORS.length]}" stroke-width="${s.width || 2.2}" stroke-linejoin="round"/>`;
  });
  const legend = series.map((s, i) => `<span><i style="background:${s.color || COLORS[i % COLORS.length]}"></i>${esc(s.label)}</span>`).join("");
  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px;display:block">${g}</svg>
    <div class="legend">${legend}</div>`;
}

function barChart(container, groups, opts = {}) {
  const W = opts.width || 860, H = opts.height || 300;
  const ml = 64, mr = 16, mt = 14, mb = 48;
  const all = groups.flatMap(gr => gr.values.map(v => v.value)).filter(v => v != null);
  if (!all.length || !container) { if (container) container.innerHTML = "<p class='lede'>No data.</p>"; return; }
  let ymin = Math.min(0, ...all), ymax = Math.max(...all);
  const pad = (ymax - ymin) * 0.08 || 1; ymax += pad; if (ymin < 0) ymin -= pad;
  const Y = v => mt + (H - mt - mb) * (1 - (v - ymin) / (ymax - ymin));
  const gw = (W - ml - mr) / groups.length;
  let g = "";
  for (let k = 0; k <= 4; k++) {
    const v = ymin + (ymax - ymin) * k / 4;
    g += `<line x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="#2a3550"/>
          <text x="${ml - 6}" y="${Y(v) + 4}" fill="#9aa7bd" font-size="11" text-anchor="end">${moneyC(v)}</text>`;
  }
  g += `<line x1="${ml}" x2="${W - mr}" y1="${Y(0)}" y2="${Y(0)}" stroke="#57648a"/>`;
  groups.forEach((gr, gi) => {
    const bw = Math.min(46, (gw - 18) / Math.max(gr.values.length, 1));
    const x0 = ml + gi * gw + (gw - bw * gr.values.length) / 2;
    gr.values.forEach((v, vi) => {
      if (v.value == null) return;
      const y = Y(Math.max(v.value, 0)), h = Math.abs(Y(v.value) - Y(0));
      g += `<rect x="${x0 + vi * bw}" y="${y}" width="${bw - 3}" height="${Math.max(h, 1)}" fill="${v.color || COLORS[vi % COLORS.length]}" rx="2"/>`;
    });
    String(gr.label).split("|").forEach((ln, li) => {
      g += `<text x="${ml + gi * gw + gw / 2}" y="${H - 30 + li * 13}" fill="#9aa7bd" font-size="11" text-anchor="middle">${esc(ln)}</text>`;
    });
  });
  const legendKeys = {};
  groups.forEach(gr => gr.values.forEach(v => { if (!(v.label in legendKeys)) legendKeys[v.label] = v.color || COLORS[Object.keys(legendKeys).length % COLORS.length]; }));
  const legend = Object.entries(legendKeys).map(([k, c]) => `<span><i style="background:${c}"></i>${esc(k)}</span>`).join("");
  container.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px;display:block">${g}</svg>
    <div class="legend">${legend}</div>`;
}

function renderTable(cols, rows, withSrc) {
  let h = "<table><thead><tr>";
  for (const c of cols) h += `<th class="${c.num ? "num" : ""}">${esc(c.label)}</th>`;
  if (withSrc) h += `<th>Sources</th>`;
  h += "</tr></thead><tbody>";
  for (const r of rows) {
    h += "<tr>";
    for (const c of cols) {
      const v = c.render ? c.render(r) : r[c.k];
      h += `<td class="${c.num ? "num" : ""}">${v == null ? "—" : v}</td>`;
    }
    if (withSrc) h += `<td>${srcCell(r.src || r.srcIds || [])}</td>`;
    h += "</tr>";
  }
  return h + "</tbody></table>";
}

/* ---------- client-side what-if model (port of build_model, deterministic) ---------- */
function DEF() {
  const m = Site.d.model_constants || {};
  return {
    av: m.A_VALUE_2026 ?? 3.1e6, bv: m.B_VALUE_2026 ?? 1.8e6,
    rateA: m.A_RATE_IMPL ?? 0.013353, sfRate: m.SF_RATE ?? 0.0118162182,
    traA: 1490, traB: 4000,
    cap: m.PROP19_CAP_2026 ?? 1044590, sc: m.XFER_SC ?? 0.0011,
    cost: m.SELL_COST_PCT ?? 0.055, rec: m.RECORD_FEE ?? 110,
    aRent: m.A_RENT_FLOOR_MO ?? 3600, bRent: m.B_RENT_MO ?? 7150,
    aIns: m.A_INS ?? 1500, aWater: m.A_WATER_MO ?? 120, aElec: m.A_ELEC_MO ?? -20,
    aSewer: m.A_SEWER_YR ?? 800, bIns: m.B_INS ?? 1500, bWater: m.B_WATER_MO ?? 360, bElec: m.B_ELEC_MO ?? 50,
    aMaint: m.A_MAINT_PCT ?? 0.0075, bMaint: m.B_MAINT_PCT ?? 0.01,
    sec121: m.SEC_121 ?? 500000, cgFed: m.FED_TOP_CG ?? 0.238, caTop: m.CA_TOP_ALLIN ?? 0.133,
    bea: m.BEA ?? 15e6, beaRate: m.ESTATE_RATE ?? 0.40,
    propH: m.PROP_H_MF ?? 250, mgmt: m.MGMT_PCT ?? 0.08,
  };
}

function portfolioPath2(net0, sg, bg, parkM, phaseM, n) {
  const parkY = parkM / 12, phaseY = phaseM / 12, nTr = Math.max(Math.round(phaseY * 2), 1);
  let bs = 0, bb = net0;
  const sched = [];
  if (parkM > 0) for (let i = 0; i < nTr; i++) sched.push({ w: parkY + i * phaseY / nTr, f: 1 / nTr });
  else { bs = net0; bb = 0; }
  const out = [];
  for (let t = 0; t < n; t++) {
    for (const s of sched) if (Math.abs(s.w - t) < 1e-9) { const mv = net0 * s.f; if (bb >= mv - 1e-6) { bb -= mv; bs += mv; } }
    let mid = 0;
    for (const s of sched) if (Math.abs(s.w - (t + 0.5)) < 1e-9) { const mv = net0 * s.f; if (bb >= mv - 1e-6) { bb -= mv; bs += mv; mid += mv; } }
    bs *= (1 + sg); bb *= (1 + bg); bs += mid * sg * 0.5;
    out.push(bs + bb);
  }
  return out;
}

function runWhatIf(c) {
  const m = DEF();
  const N = 31, Y = c.Y || 2045;
  const grow = Math.pow(1 + c.hg, Y - 2026);
  const vA = [m.av * grow], vB = [m.bv * grow];
  for (let t = 1; t < N; t++) { vA.push(vA[t - 1] * (1 + c.hg)); vB.push(vB[t - 1] * (1 + c.hg)); }
  const inf = t => Math.pow(1 + c.infl, t);
  const propH = yr => (yr >= 2027 ? m.propH : 0);
  const taxOcc = [], taxFull = [], aOps = [], bTax = [], bOps = [], rentA = [], rentB = [];
  for (let t = 0; t < N; t++) {
    const yr = Y + t;
    const fbyv = Math.max(m.av, vA[0]);            // Prop 19 FBYV ≈ FMV at death (conservative max)
    const prop19taxable = (c.policy === "none") ? vA[t] : Math.max(fbyv, vA[t] - m.cap);
    taxOcc.push(prop19taxable * m.rateA + m.traA * Math.pow(1.02, t) + propH(yr));
    taxFull.push(vA[t] * m.rateA + m.traA * Math.pow(1.02, t) + propH(yr));
    aOps.push((m.aIns + m.aWater * 12 + m.aElec * 12 + m.aSewer) * inf(t) + vA[t] * m.aMaint);
    bTax.push(vB[0] * m.sfRate * Math.pow(1.02, t) + m.traB * 0 + propH(yr));  // B: official SF rate + parcels ≈ flag
    bOps.push((m.bIns + m.bWater * 12 + m.bElec * 12) * inf(t) + vB[t] * m.bMaint);
    rentA.push(m.aRent * 12 * inf(t));
    rentB.push(m.bRent * 12 * inf(t));
  }
  const bNet = rentB.map((r, t) => r - bTax[t] - bOps[t]);
  const imputed = rentA.map(r => r * (c.imputed / m.aRent));

  const liveCF = bNet.map((b, t) => b - taxOcc[t] - aOps[t] - imputed[t]);
  const rentCF = bNet.map((b, t) => b + rentA[t] - taxFull[t] - aOps[t] - m.mgmt * rentA[t]);
  const sellCF = bNet.slice();

  const xfer = (c.policy === "none") ? Math.max(0, (vA[0] - m.bea) * m.beaRate)
            : (c.policy === "expanded" ? Math.max(0, (vA[0] - m.bea) * m.beaRate) : 0);
  const net0 = vA[0] * (1 - m.sc - m.cost) - m.rec - xfer;
  const port = portfolioPath2(net0, c.sg, c.bg, c.park, 24, N);
  const cum = arr => { const o = []; let s = 0; for (const x of arr) { s += x; o.push(s); } return o; };
  const sellCum = cum(sellCF), liveCum = cum(liveCF), rentCum = cum(rentCF);

  const sellNW = port.map((p, t) => p + vB[t] + sellCum[t]);
  const liveNW = vA.map((v, t) => v * (1 - m.cost) + vB[t] + liveCum[t]);
  const rentNW = vA.map((v, t) => v * (1 - m.cost) + vB[t] + rentCum[t]);

  const H = Math.max(0, Math.min(10, c.holdY | 0));
  const mixCF = liveCF.map((x, t) => t <= H ? x : sellCF[t]);
  const mixCum = cum(mixCF);
  const holdNW = [];
  for (let t = 0; t < N; t++) {
    if (t <= H) holdNW.push(vA[t] * (1 - m.cost) + vB[t] + mixCum[t]);
    else {
      const gain = Math.max(vA[H] - vA[0], 0);
      const cap121 = c.s121 === "single" ? 250000 : m.sec121;
      const tax = (gain - Math.min(gain, cap121)) * (m.cgFed + m.caTop);
      const proceeds = vA[H] * (1 - m.sc - m.cost) - m.rec - xfer - tax;
      const p = portfolioPath2(proceeds, c.sg, c.bg, c.park, 24, t - H + 1);
      holdNW.push(p[p.length - 1] + vB[t] + mixCum[t]);
    }
  }
  const paths = [
    { path: "LIVE in A (Prop 19)", nw: liveNW, cf: liveCF, color: COLORS[1] },
    { path: "RENT A out (full reassessment)", nw: rentNW, cf: rentCF, color: COLORS[2] },
    { path: "SELL at inheritance → park then stocks", nw: sellNW, cf: sellCF, color: COLORS[0] },
    { path: `LIVE ${H}y → sell (§121)`, nw: holdNW, cf: mixCF, color: COLORS[4] },
  ];
  const winner = paths.reduce((a, b) => (b.nw[30] > a.nw[30] ? b : a));
  const r10 = v => Math.round(v / 10) * 10;
  return { paths, winner, r10,
           taxOccY1: r10(taxOcc[0]), taxFullY1: r10(taxFull[0]),
           vA0: vA[0], net0: r10(net0), xfer: r10(xfer) };
}

/* ---------- page: index ---------- */
function renderIndex() {
  const p = Site.d.projection, t = Site.d.tables, b = Site.d.blackswan, mc = Site.d.model_constants;
  const P = p && p["2045"];
  const host = document.getElementById("exec");
  if (!host) return;
  const find = pre => P && P.paths.find(x => x.path.startsWith(pre));
  const ls = find("SELL Property A → lump"), live = find("LIVE"), rent = find("RENT"),
        phase = P && P.paths.find(x => x.path.includes("24-mo"));
  const ev19 = b && b.entries.find(e => e.start_year === 1929);
  const ev08 = b && b.entries.find(e => e.start_year === 2008);
  const ddOf = (ev, i) => ev ? ev.strategies[i].max_drawdown_pct : null;
  const flags = Site.d.flags || [];
  const front = (Site.d.questions && Site.d.questions.front) || [];

  host.innerHTML = `
  <div class="cards">
    <div class="card"><div class="k">Baseline winner · 30-year horizon</div>
      <div class="v" style="color:${COLORS[0]}">SELL ${moneyC(ls && ls.net_worth["30"])}</div>
      <div class="n">vs LIVE ${moneyC(live && live.net_worth["30"])} · RENT ${moneyC(rent && rent.net_worth["30"])} · phased ${moneyC(phase && phase.net_worth["30"])} (inherit 2045, stocks 8.5% / homes 3.5% / bills 2.5%)</div></div>
    <div class="card"><div class="k">Federal estate tax</div>
      <div class="v">$0 <span class="badge ok">exclusion $15M</span></div>
      <div class="n">2026 basic exclusion ${money(mc && mc.BEA)} ${src("irs-rp2532")}; California estate tax $0 by statute (R&amp;T §13302) ${src("leginfo-13302")}</div></div>
    <div class="card"><div class="k">Prop 19 tax gap · first year</div>
      <div class="v">${money(live && live.property_tax_first_year)} <span style="font-size:14px;color:var(--muted)">vs</span> ${money(rent && rent.property_tax_first_year)}</div>
      <div class="n">occupy (capped base) vs full reassessment ≈ ${money((rent && rent.property_tax_first_year || 0) - (live && live.property_tax_first_year || 0))}/yr at transfer ${src("boe-prop19")}</div></div>
    <div class="card"><div class="k">1929 entry · drawdown</div>
      <div class="v" style="color:${COLORS[3]}">${ddOf(ev19, 0)}%</div>
      <div class="n">lump-sum vs ${ddOf(ev19, 1)}% (24-mo park) — year-10 value ${moneyC(ev19 && ev19.strategies[0].value_y10)} vs ${moneyC(ev19 && ev19.strategies[1].value_y10)} ${src("damodaran")}</div></div>
    <div class="card"><div class="k">2008 entry · drawdown</div>
      <div class="v" style="color:${COLORS[3]}">${ddOf(ev08, 0)}%</div>
      <div class="n">lump-sum vs ${ddOf(ev08, 1)}% for the Treasury-park path; year 10 ${moneyC(ev08 && ev08.strategies[0].value_y10)} vs ${moneyC(ev08 && ev08.strategies[1].value_y10)}</div></div>
    <div class="card"><div class="k">Flagged for review</div>
      <div class="v" style="color:${COLORS[2]}">${flags.length}</div>
      <div class="n">unverified items (SCC rate book, parcel components, insurance, NEM 3.0, §121 text…) — see <a href="flagged.html">Flagged for review</a></div></div>
  </div>

  <div class="hl">
    <h3 style="margin-top:0">Decision at a glance <span class="pill">values rounded to $10 · model run 2026-11-25</span></h3>
    <ul class="tight">
      <li><b>Selling the inherited house (Property A) and reinvesting leads on projected net worth at every horizon in the baseline</b> (30y: ${moneyC(ls && ls.net_worth["30"])} vs ${moneyC(live && live.net_worth["30"])} holding) — property tax (≈1.335% implied) + 0.75%/yr maintenance + 5.5% exit cost drag a ${moneyC(mc && mc.A_VALUE_2026)} house vs a diversified portfolio at 8.5%.</li>
      <li><b>Living in it (Prop 19 claim) beats renting it out</b>: first-year property tax ${money(live && live.property_tax_first_year)} vs ${money(rent && rent.property_tax_first_year)}, plus 8% management and vacancy on the rental path. You must live somewhere; both homes are owned outright in every path.</li>
      <li><b>Phased Treasury entry (24–36 months in 3M–2Y bills, then 24-month phase into stocks) beat day-one lump-sum in 4 of 5 historical entries over 10 years</b> and cut the worst drawdowns from −65% → −34% (1929) and −37% → −4% (2008). It lags in V-shaped rebounds (2020). Recommended default for the proceeds <span class="pill">decision · 2026-11-25</span></li>
      <li><b>No estate-tax problem today</b>: federal exclusion ${money(mc && mc.BEA)} (2026) ${src("irs-rp2532")}; CA collects $0 ${src("leginfo-13302")}. The 2026 repeal initiative failed to qualify (watch 2028) ${src("ag-init250035")}.</li>
    </ul>
  </div>

  <div class="hl risk">
    <h3 style="margin-top:0">What would change the answer</h3>
    <ul class="tight">
      ${front.map(f => `<li><b>${esc(f.lever)}</b> — <span class="badge">${esc(f.current)}</span> ${esc(f.changes)}</li>`).join("")}
      <li><b>Sensitivity matrix (stocks × homes, inherit 2045)</b>: SELL leads at 30y in all 9 tested combinations (stocks 6–12% × homes 1–5.5%) — the lead narrows to ~${moneyC(21e6)} at 6% stocks/5.5% homes and widens past ${moneyC(180e6)} at 8.5%/3.5%. The realistic flip risks are therefore <i>sequence/entry crashes</i> (handled by phasing), <i>cost assumptions</i> (5.5% sell cost, maintenance — flagged F9), and <i>future law</i>, not baseline growth rates. Full grid: <a href="data.html#sens">Data tables</a>.</li>
      <li><b>Same-year sale after inheritance</b>: basis = FMV at death → taxable gain ≈ $0 (income tax ≈ $0), but 5.5% selling cost + 0.11% transfer + $110 recording still leave ≈ ${moneyC(((Site.d.same_year_sale || [{}])[0].transfer_tax_sc_county || 0) + ((Site.d.same_year_sale || [{}])[0].recording_fees || 0) + ((Site.d.same_year_sale || [{}])[0].selling_costs || 0))} of friction — see <a href="data.html#same-year">same-year table</a>.</li>
    </ul>
  </div>`;
}

/* ---------- page: dashboard ---------- */
function renderDashboard() {
  const P = Site.d.projection && Site.d.projection["2045"];
  const el = document.getElementById("cmp-table");
  if (el && P) {
    const rows = P.paths.map(pt => ({
      path: pt.path,
      n10: money(pt.net_worth["10"]), n20: money(pt.net_worth["20"]), n30: money(pt.net_worth["30"]),
      cf30: money(pt.cum_net_cash_flow["30"]),
      tax1: pt.property_tax_first_year != null ? money(pt.property_tax_first_year) : "—",
      risk: pt.path.startsWith("SELL Property A → lump") ? "market timing — worst dd −65% (1929)"
          : pt.path.includes("24-mo") ? "entry risk cut (park + phase)"
          : pt.path.startsWith("LIVE") ? "illiquid · Prop 19 tax · maintenance on A"
          : pt.path.startsWith("RENT") ? "full reassessment · mgmt 8% · vacancy"
          : "mixed",
      liq: pt.liquidity || "",
      riskNote: pt.reinvestment_risk || "",
    }));
    el.innerHTML = renderTable([
      { k: "path", label: "Path (inherit 2045)" },
      { k: "n10", label: "Net worth 10y", num: true }, { k: "n20", label: "20y", num: true }, { k: "n30", label: "30y", num: true },
      { k: "cf30", label: "Cum. cash flow 30y", num: true }, { k: "tax1", label: "A tax yr-1", num: true },
      { k: "risk", label: "Key risk" },
    ], rows);
    // expandable details
    const det = document.getElementById("cmp-details");
    if (det) det.innerHTML = P.paths.map(pt => `<details><summary>${esc(pt.path)}</summary>
      <p class="page-note"><b>Reinvestment risk:</b> ${esc(pt.reinvestment_risk || "—")}<br>
      <b>Liquidity:</b> ${esc(pt.liquidity || "—")}<br>
      <b>Taxes modeled:</b> ${esc(pt.taxes_modeled || "—")}</p></details>`).join("");

    const c1 = document.getElementById("chart-nw");
    if (c1) {
      const yrs = P.paths[0].series_nw.length;
      const xTicks = Array.from({ length: yrs }, (_, i) => i).filter(i => (2045 + i) % 5 === 0 || i === 0);
      lineChart(c1, P.paths.map((pt, i) => ({
        label: pt.path.replace("Property A ", "A ").replace("SELL Property A", "Sell A"),
        data: pt.series_nw, color: COLORS[i % COLORS.length],
      })), { xTicks, xLabels: Array.from({ length: yrs }, (_, i) => String(2045 + i)) });
    }
  }

  // sensitivity matrix
  const se = document.getElementById("sens-table");
  const sens = Site.d.sensitivity;
  if (se && sens && sens.matrix) {
    se.innerHTML = renderTable([
      { k: "stocks", label: "Stocks", render: r => pct(r.stocks, 1) },
      { k: "home", label: "Homes", render: r => pct(r.home, 1) },
      { k: "s10", label: "SELL−LIVE @10y", num: true, render: r => money(r.at10) },
      { k: "s20", label: "@20y", num: true, render: r => money(r.at20) },
      { k: "s30", label: "@30y", num: true, render: r => money(r.at30) },
      { k: "lead", label: "30y leader", render: r => `<span class="badge ${r.lead30 === "SELL" ? "acc" : "warn"}">${r.lead30}</span>` },
    ], sens.matrix);
    const st = document.getElementById("stock-stats");
    if (st && sens.stock_stats) st.innerHTML = `<span class="badge ok">history</span> stocks arithmetic mean ${sens.stock_stats.mean_arith_pct}%/yr (σ ${sens.stock_stats.sd_pct}%), T-bills ${sens.stock_stats.bill_mean_pct}%/yr over ${sens.stock_stats.n} years ${src("damodaran")} — forward baseline uses 8.5% (deliberately below the historical mean).`;
  }

  // reinvestment-risk box
  const bs = Site.d.blackswan;
  const rr = document.getElementById("reinvest-box");
  if (rr && bs) {
    rr.innerHTML = `<h3>Reinvestment risk — same entry dates on both paths</h3>
      <p class="lede">Day-one lump sum vs 24- or 36-month Treasury park, then 24-month phase into stocks; actual annual returns ${src("damodaran")}. ${esc(bs.phasing_note || "")}</p>
      <div class="chart" id="chart-bs"></div>
      <p class="lede"><b>Max drawdown by entry</b> (bars below zero are losses from peak):</p>
      <div class="chart" id="chart-dd"></div>`;
    const strats = ["Lump sum", "Park 24m", "Park 36m"];
    const cols = [COLORS[3], COLORS[0], COLORS[1]];
    barChart(document.getElementById("chart-bs"), bs.entries.map(e => ({
      label: e.label.replace(" entry", ""),
      values: e.strategies.map((st2, i) => ({ label: strats[i] || st2.strategy, value: st2.value_y5, color: cols[i] })),
    })));
    barChart(document.getElementById("chart-dd"), bs.entries.map(e => ({
      label: e.label.replace(" entry", ""),
      values: e.strategies.map((st2, i) => ({ label: strats[i], value: st2.max_drawdown_pct, color: cols[i] })),
    })), { height: 260 });
    const note = document.getElementById("bs-note");
    if (note) note.innerHTML = `<div class="note">Read: parking in 3M–2Y Treasuries for 24–36 months, then phasing over 24 months, cut the worst drawdowns from −65% → −34% (1929) and −37% → −4% (2008) and ended year 10 ahead in <b>every entry that has 10 years of data</b> — except 2020, where the V-shaped rebound punished phasing (lump sum ${moneyC(bs.entries[4].strategies[0].value_y5)} vs park ${moneyC(bs.entries[4].strategies[1].value_y5)} at year 5; year-10 values unavailable, series ends 2025).</div>`;
  }

  // Monte-Carlo
  const mcEl = document.getElementById("mc-table");
  const mc = Site.d.mc;
  if (mcEl && mc) {
    mcEl.innerHTML = renderTable([
      { k: "name", label: `Bundle (${mc.horizon}y, ${mc.sims.toLocaleString()} sims, seed ${mc.seed})` },
      { k: "p10", label: "End P10", num: true, render: r => money(r.end_p10) },
      { k: "p50", label: "End median", num: true, render: r => money(r.end_p50) },
      { k: "p90", label: "End P90", num: true, render: r => money(r.end_p90) },
    ], mc.bundles);
    const c = document.getElementById("chart-mc");
    if (c) lineChart(c, mc.bundles.map((b, i) => ({
      label: b.name + " (median)", data: b.p50, color: COLORS[i % COLORS.length],
    })), { xTicks: [0, 10, 20, 29], xLabels: { 0: "yr0", 10: "yr10", 20: "yr20", 29: "yr30" } });
  }

  initWhatIf();
}

/* ---------- what-if lab ---------- */
function initWhatIf() {
  const root = document.getElementById("whatif");
  if (!root) return;
  const c = { Y: 2045, sg: 8.5, bg: 2.5, hg: 3.5, infl: 2.5, park: 24, imputed: 3600, holdY: 5, s121: "mfj", policy: "baseline" };
  root.innerHTML = `
  <div class="controls no-print">
    <div><label>Inheritance year</label>
      <select id="wi-Y"><option>2040</option><option selected>2045</option><option>2050</option></select></div>
    <div><label>Stocks /yr <span class="val" id="wi-sg-v"></span></label>
      <input type="range" id="wi-sg" min="0" max="15" step="0.5" value="8.5"></div>
    <div><label>T-bills /yr <span class="val" id="wi-bg-v"></span></label>
      <input type="range" id="wi-bg" min="0" max="6" step="0.25" value="2.5"></div>
    <div><label>Home growth /yr <span class="val" id="wi-hg-v"></span></label>
      <input type="range" id="wi-hg" min="-3" max="9" step="0.5" value="3.5"></div>
    <div><label>Inflation /yr <span class="val" id="wi-infl-v"></span></label>
      <input type="range" id="wi-infl" min="0" max="8" step="0.25" value="2.5"></div>
    <div><label>Treasury park before stocks (months) <span class="val" id="wi-park-v"></span></label>
      <input type="range" id="wi-park" min="0" max="36" step="6" value="24"></div>
    <div><label>Imputed rent of living in A ($/mo) <span class="val" id="wi-imp-v"></span></label>
      <input type="range" id="wi-imp" min="0" max="7200" step="100" value="3600"></div>
    <div><label>Live in A for N years, then sell <span class="val" id="wi-hold-v"></span></label>
      <input type="range" id="wi-hold" min="0" max="10" step="1" value="5"></div>
    <div><label>§121 exclusion</label>
      <select id="wi-s121"><option value="mfj" selected>$500k MFJ</option><option value="single">$250k single</option></select></div>
    <div><label>Policy scenario (hypotheticals flagged)</label>
      <select id="wi-policy"><option value="baseline" selected>Baseline: current law</option>
      <option value="expanded">2028 initiative ($706.5k fed exemption)</option>
      <option value="none">Hypothetical: no state death-tax credit</option></select></div>
    <div style="align-self:end"><button id="wi-reset" style="background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:8px 14px;cursor:pointer">Reset</button></div>
  </div>
  <div id="wi-out"></div>`;

  const $ = id => document.getElementById(id);
  const bind = (id, key, fmt) => {
    const inp = $(id), lab = $(id + "-v");
    const upd = () => {
      c[key] = parseFloat(inp.value);
      if (lab) lab.textContent = fmt(c[key]);
      draw();
    };
    inp.addEventListener("input", upd); upd();
  };
  $("wi-Y").addEventListener("change", () => { c.Y = parseInt($("wi-Y").value, 10); draw(); });
  bind("wi-sg", "sg", v => v.toFixed(1) + "%");
  bind("wi-bg", "bg", v => v.toFixed(2) + "%");
  bind("wi-hg", "hg", v => v.toFixed(1) + "%");
  bind("wi-infl", "infl", v => v.toFixed(2) + "%");
  bind("wi-park", "park", v => v + " mo");
  bind("wi-imp", "imputed", v => "$" + v.toLocaleString());
  bind("wi-hold", "holdY", v => v + " y");
  $("wi-s121").addEventListener("change", () => { c.s121 = $("wi-s121").value; draw(); });
  $("wi-policy").addEventListener("change", () => { c.policy = $("wi-policy").value; draw(); });
  $("wi-reset").addEventListener("click", () => {
    $("wi-Y").value = 2045; $("wi-sg").value = 8.5; $("wi-bg").value = 2.5; $("wi-hg").value = 3.5;
    $("wi-infl").value = 2.5; $("wi-park").value = 24; $("wi-imp").value = 3600; $("wi-hold").value = 5;
    $("wi-s121").value = "mfj"; $("wi-policy").value = "baseline";
    for (const id of ["wi-Y", "wi-sg", "wi-bg", "wi-hg", "wi-infl", "wi-park", "wi-imp", "wi-hold", "wi-s121", "wi-policy"])
      $(id).dispatchEvent(new Event(id === "wi-Y" || id === "wi-s121" || id === "wi-policy" ? "change" : "input"));
  });

  function draw() {
    const cc = { ...c, sg: c.sg / 100, bg: c.bg / 100, hg: c.hg / 100, infl: c.infl / 100 };
    const r = runWhatIf(cc);
    const rows = r.paths.map(p => ({
      path: p.path,
      n10: r.money10 ? r.money10(p.nw[10]) : money(r.r10(p.nw[10])),
      n30: money(r.r10(p.nw[30])),
      win: p === r.winner ? '<span class="badge ok">leads</span>' : "",
    }));
    $("wi-out").innerHTML = `
      <div class="cards">
        <div class="card"><div class="k">Winner at 30y</div>
          <div class="v" style="font-size:18px">${esc(r.winner.path)}</div>
          <div class="n">${money(r.r10(r.winner.nw[30]))} · proceeds after cost/tax ≈ ${money(r.net0)}${r.xfer ? " (incl. transfer tax " + money(r.xfer) + ")" : ""}</div></div>
        <div class="card"><div class="k">A property tax · first year</div>
          <div class="v" style="font-size:18px">${money(r.taxOccY1)} <span style="font-size:13px;color:var(--muted)">LIVE</span> · ${money(r.taxFullY1)} <span style="font-size:13px;color:var(--muted)">RENT</span></div>
          <div class="n">Prop 19 gap ${money(r.taxFullY1 - r.taxOccY1)}/yr ${src("boe-prop19")}</div></div>
        <div class="card"><div class="k">Sale friction at exit</div>
          <div class="v" style="font-size:18px">${money(r.r10(r.vA0 * 0.0011 + 110))} <span style="font-size:13px;color:var(--muted)">transfer+record</span></div>
          <div class="n">plus 5.5% selling cost (assumption F9) ≈ ${money(r.r10(r.vA0 * 0.055))} ${src("scc-recorder")}</div></div>
      </div>
      <div class="chart" id="wi-chart"></div>
      ${renderTable([
        { k: "path", label: "Path" }, { k: "n10", label: "10y", num: true },
        { k: "n30", label: "30y", num: true }, { k: "win", label: "" },
      ], rows)}`;
    const yrs = 31;
    lineChart(document.getElementById("wi-chart"), r.paths.map(p => ({ label: p.path, data: p.nw, color: p.color })),
      { xTicks: Array.from({ length: yrs }, (_, i) => i).filter(i => (c.Y + i) % 5 === 0 || i === 0),
        xLabels: Array.from({ length: yrs }, (_, i) => String(c.Y + i)) });
  }
}

/* ---------- page: blackswan ---------- */
function renderBlackswan() {
  const bs = Site.d.blackswan;
  const host = document.getElementById("bs-entries");
  if (host && bs) {
    let h = "";
    for (const e of bs.entries) {
      h += `<h3>${esc(e.label)} <span class="pill">start ${e.start_year}</span></h3>`;
      h += renderTable([
        { k: "strategy", label: "Entry strategy" },
        { k: "v5", label: "Value yr 5", num: true, render: s => money(s.value_y5) },
        { k: "v10", label: "Value yr 10", num: true, render: s => s.value_y10 == null ? "<span class='pill'>series ends 2025</span>" : money(s.value_y10) },
        { k: "dd", label: "Max drawdown", num: true, render: s => `<span class="badge ${s.max_drawdown_pct <= -30 ? "bad" : s.max_drawdown_pct <= -10 ? "warn" : "ok"}">${s.max_drawdown_pct}%</span>` },
        { k: "fy", label: "Last year used", num: true },
        { k: "note", label: "Path" },
      ], e.strategies);
      h += `<div class="chart" id="bs-path-${e.start_year}"></div>`;
      if (e.context && e.context.length) {
        h += `<details><summary>Actual returns in the entry window</summary>` +
          renderTable([
            { k: "year", label: "Year" },
            { k: "stock_pct", label: "Stocks", num: true, render: r => r.stock_pct + "%" },
            { k: "bill_pct", label: "T-bills", num: true, render: r => r.bill_pct + "%" },
          ], e.context) + `</details>`;
      }
    }
    h += `<h3>Regime context</h3>` + renderTable([
      { k: "regime", label: "Regime" }, { k: "window", label: "Window" },
      { k: "stocks_cum_pct", label: "Stocks cum.", num: true, render: r => r.stocks_cum_pct + "%" },
      { k: "bills_cum_pct", label: "Bills cum.", num: true, render: r => r.bills_cum_pct + "%" },
      { k: "note", label: "Note" },
      { k: "source", label: "Src", render: r => src(r.source) },
    ], bs.regimes);
    host.innerHTML = h;
    for (const e of bs.entries) {
      const el = document.getElementById(`bs-path-${e.start_year}`);
      const n = Math.max(...e.strategies.map(s => (s.series || []).length));
      if (el) lineChart(el, e.strategies.map((s, i) => ({
        label: ["Lump sum", "Park 24m + phase", "Park 36m + phase"][i] || s.strategy,
        data: s.series || [], color: [COLORS[3], COLORS[0], COLORS[1]][i],
      })), { xTicks: [0, 2, 5, 10].filter(i => i < n), xLabels: { 0: "yr0", 2: "yr2", 5: "yr5", 10: "yr10" } });
    }
  }
  // baseline long-run projections
  const p = Site.d.projection;
  const host2 = document.getElementById("bs-baseline");
  if (host2 && p) {
    let h = `<p class="lede">Nominal net worth by path, $10-rounded. Inflation 2.5%; homes 1 / 3.5 / 5.5%; stocks 6 / 8.5 / 12% — full grid in <a href="dashboard.html">Dashboard</a> and <a href="data.html#sens">Data tables</a>.</p>`;
    for (const [yr, P] of Object.entries(p)) {
      h += `<h3>Inherit ${yr}</h3>` + renderTable([
        { k: "path", label: "Path" },
        { k: "n10", label: "10y", num: true, render: r => money(r.net_worth["10"]) },
        { k: "n20", label: "20y", num: true, render: r => money(r.net_worth["20"]) },
        { k: "n30", label: "30y", num: true, render: r => money(r.net_worth["30"]) },
        { k: "cf", label: "Cum CF 30y", num: true, render: r => money(r.cum_net_cash_flow["30"]) },
        { k: "tax", label: "A tax yr-1 (LIVE)", num: true, render: r => money(r.property_tax_first_year) },
      ], P.paths);
    }
    host2.innerHTML = h;
  }
}

/* ---------- page: data tables ---------- */
function renderData() {
  const t = Site.d.tables;
  const put = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
  if (!t) return;

  const statusBadge = st => {
    const s = String(st || "");
    if (/^verified/i.test(s)) return `<span class="badge ok">verified</span>`;
    if (/unverified|flagged|assumption/i.test(s)) return `<span class="badge warn">flagged</span>`;
    return `<span class="pill">${esc(s.slice(0, 60))}</span>`;
  };

  put("hist-a", renderTable([
    { k: "year", label: "Year" },
    { k: "taxes", label: "Property tax", num: true, render: r => money(r.taxes) },
    { k: "assessment", label: "Assessed value", num: true, render: r => money(r.assessment) },
    { k: "chg", label: "Δ tax", num: true, render: r => r.chg == null ? "—" : (r.chg > 0 ? "+" : "") + r.chg + "%" },
    { k: "status", label: "Status", render: () => '<span class="badge warn">household report</span>' },
  ], t.property_a_hist || t.property_a_tax_history, true));

  put("hist-b", renderTable([
    { k: "year", label: "Year" },
    { k: "taxes", label: "Property tax", num: true, render: r => money(r.taxes) },
    { k: "assessment", label: "Assessed value", num: true, render: r => money(r.assessment) },
    { k: "chg", label: "Δ tax", num: true, render: r => r.chg == null ? "—" : (r.chg > 0 ? "+" : "") + r.chg + "%" },
    { k: "status", label: "Status", render: () => '<span class="badge warn">household report</span>' },
  ], t.property_b_hist || t.property_b_tax_history, true));

  put("law-table", renderTable([
    { k: "item", label: "Topic" }, { k: "value", label: "Rule / rate" },
    { k: "status", label: "Status", render: r => statusBadge(r.status) },
  ], t.law_rules, true));

  put("rates-table", renderTable([
    { k: "item", label: "Rate" }, { k: "value", label: "Value", num: true },
    { k: "status", label: "Status", render: r => statusBadge(r.status) },
  ], t.rates, true));

  put("costs-table", renderTable([
    { k: "item", label: "Cost item" },
    { k: "value", label: "Value", num: true, render: r => r.value == null ? "—" : money(r.value) },
    { k: "unit", label: "Unit" },
    { k: "status", label: "Status", render: r => statusBadge(r.status) },
  ], t.operating_costs, true));

  put("f540-table", renderTable([
    { k: "gain", label: "Gain recognized", num: true, render: r => money(r.gain) },
    { k: "ca_bhst_1pct", label: "CA BHST 1%", num: true, render: r => money(r.ca_bhst_1pct) },
    { k: "ca_ordinary_top_simplified", label: "CA ordinary top (simp.)", num: true, render: r => money(r.ca_ordinary_top_simplified) },
    { k: "fed_ltcg_niit_top_simplified", label: "Fed LTCG+NIIT top (simp.)", num: true, render: r => money(r.fed_ltcg_niit_top_simplified) },
    { k: "combined_top_simplified", label: "Combined top (simp.)", num: true, render: r => money(r.combined_top_simplified) },
  ], t.form540_sensitivity));

  put("estate-table", renderTable([
    { k: "taxable_estate", label: "Taxable estate", num: true, render: r => money(r.taxable_estate) },
    { k: "bea_2026", label: "2026 exclusion", num: true, render: r => money(r.bea_2026) },
    { k: "federal_estate_tax", label: "Federal estate tax", num: true, render: r => money(r.federal_estate_tax) },
    { k: "effective_rate_on_excess", label: "Eff. rate on excess", num: true, render: r => r.effective_rate_on_excess == null ? "—" : r.effective_rate_on_excess + "%" },
  ], t.estate_tax_scenarios));

  put("prop19-table", renderTable([
    { k: "window", label: "Filing window" },
    { k: "cap", label: "Cap", num: true, render: r => r.cap == null ? "—" : money(r.cap) },
    { k: "note", label: "Note", render: r => esc(r.note || "") },
  ], t.prop19_cap_schedule, true));

  const syList = Site.d.same_year_sale;
  if (Array.isArray(syList) && syList.length) {
    const row0 = syList[0];
    const friction = row0.transfer_tax_sc_county + row0.recording_fees + row0.selling_costs;
    put("sy-note", `<p class="lede">Sell A in the same calendar year you inherit: basis = FMV at death ${src("irs-p523")} → taxable gain ≈ $0 and income tax ≈ $0 — but friction still applies: 5.5% selling cost (F9) + 0.11% Santa Clara transfer + $110 recording ≈ <b>${money(friction)}</b> on the ${moneyC(row0.fmv_at_death)} death-year value (${pct((friction / row0.fmv_at_death), 2)} of value).</p>`);
    put("sy-table", renderTable([
      { k: "year", label: "Sale year" },
      { k: "fmv_at_death", label: "FMV at death (basis)", num: true, render: r => money(r.fmv_at_death) },
      { k: "taxable_gain_after_stepup", label: "Taxable gain", num: true, render: r => money(r.taxable_gain_after_stepup) },
      { k: "federal_income_tax", label: "Federal CG", num: true, render: r => money(r.federal_income_tax) },
      { k: "california_income_tax", label: "CA CG", num: true, render: r => money(r.california_income_tax) },
      { k: "selling_costs", label: "Sell cost 5.5%", num: true, render: r => money(r.selling_costs) },
      { k: "transfer", label: "Transfer+record", num: true, render: r => money(r.transfer_tax_sc_county + r.recording_fees) },
      { k: "net_proceeds", label: "Net to invest", num: true, render: r => money(r.net_proceeds) },
    ], syList));
  }

  const sens = Site.d.sensitivity;
  if (sens && sens.matrix) {
    put("sens-table2", renderTable([
      { k: "stocks", label: "Stocks", render: r => pct(r.stocks, 1) },
      { k: "home", label: "Homes", render: r => pct(r.home, 1) },
      { k: "at10", label: "SELL−LIVE @10y", num: true, render: r => money(r.at10) },
      { k: "at20", label: "@20y", num: true, render: r => money(r.at20) },
      { k: "at30", label: "@30y", num: true, render: r => money(r.at30) },
      { k: "sell30", label: "SELL @30y", num: true, render: r => money(r.sell30) },
      { k: "live30", label: "LIVE @30y", num: true, render: r => money(r.live30) },
      { k: "lead30", label: "Leader", render: r => `<span class="badge acc">${r.lead30}</span>` },
    ], sens.matrix));
  }

  const mc = Site.d.mc;
  if (mc) put("mc-note", `<p class="lede">Monte-Carlo: ${mc.sims.toLocaleString()} sims, seed ${mc.seed}, ${mc.horizon}-year horizon. Log-normal stocks (arithmetic mean ${Site.d.sensitivity && Site.d.sensitivity.stock_stats.mean_arith_pct}%, σ ${Site.d.sensitivity && Site.d.sensitivity.stock_stats.sd_pct}%), bills ~${Site.d.sensitivity && Site.d.sensitivity.stock_stats.bill_mean_pct}%, homes 3.5%±3%, inflation N(2.5%,1%). “Sell” = 70/30 after costs; “rental” = A rented − tax − maintenance − 8% mgmt; “live” = hold A (excludes imputed rent).</p>`);
}

/* ---------- page: timeline ---------- */
function renderTimeline() {
  const el = document.getElementById("tl");
  if (!el || !Site.d.timeline) return;
  const kindPill = k => ({ deadline: '<span class="badge warn">deadline</span>', law: '<span class="badge acc">law</span>',
    decision: '<span class="badge ok">decision</span>', process: '<span class="pill">process</span>' }[k] || `<span class="pill">${esc(k)}</span>`);
  el.innerHTML = renderTable([
    { k: "when", label: "When" },
    { k: "kind", label: "Type", render: r => kindPill(r.kind) },
    { k: "what", label: "Action" },
    { k: "src", label: "Source", render: r => src(r.src) },
  ], Site.d.timeline);
}

/* ---------- page: questions ---------- */
function renderQuestions() {
  const el = document.getElementById("ql");
  if (!el || !Site.d.questions) return;
  const q = Site.d.questions;
  el.innerHTML = `
    <h2>What would change the answer (levers)</h2>
    ${renderTable([
      { k: "lever", label: "Lever" }, { k: "current", label: "Current state" }, { k: "changes", label: "How it changes the answer" },
    ], q.front)}
    <h2>Questions to answer before any decision</h2>
    ${renderTable([
      { k: "id", label: "#" }, { k: "q", label: "Question" }, { k: "why", label: "Why it matters" },
      { k: "status", label: "Status", render: r => /MISSING|OPEN|PENDING|FLAGGED|TO BE/i.test(r.status)
          ? `<span class="badge warn">${esc(r.status)}</span>` : `<span class="badge ok">${esc(r.status)}</span>` },
      { k: "how", label: "How to resolve" },
    ], q.questions)}`;
}

/* ---------- page: suggestions ---------- */
function renderSuggestions() {
  const el = document.getElementById("sg");
  if (!el || !Site.d.suggestions) return;
  el.innerHTML = Site.d.suggestions.map(s => `
    <details><summary><span class="pill ${String(s.priority).toLowerCase() === "high" ? "high" : String(s.priority).toLowerCase() === "medium" ? "med" : "low"}">${esc(s.priority)}</span>
      ${esc(s.id)} · ${esc(s.title)}</summary>
      <p>${esc(s.body)}</p>
      <p class="page-note">Owner: ${esc(s.owner || "—")} · Status: ${esc(s.status || "—")}</p></details>`).join("")
    + `<div class="note"><b>Pre-commitment policy (sign before the transfer):</b> (1) allocate by the ranges on this site, not a single point; (2) default entry = 24-month Treasury park + 24-month phase, with a written rule for a &gt;30% drawdown within 12 months of sale; (3) re-run this model every January and after any law change; (4) no path switch without a written reason logged with the date.</div>`;
}

/* ---------- page: glossary ---------- */
function renderGlossary() {
  const el = document.getElementById("gl");
  if (!el || !Site.d.glossary) return;
  el.innerHTML = renderTable([
    { k: "term", label: "Term" }, { k: "def", label: "Definition" },
  ], Site.d.glossary);
}

/* ---------- page: flagged ---------- */
function renderFlagged() {
  const el = document.getElementById("fl");
  if (!el || !Site.d.flags) return;
  el.innerHTML = `<p class="lede">Every item below is unverified or an explicit assumption. Nothing here was inferred — resolve, then re-run <code>model/build_model.py</code> and redeploy.</p>`
    + Site.d.flags.map(f => `
    <div class="flag"><b>${esc(f.id)} · ${esc(f.item)}</b> ${sevPill(f.severity)}
      <ul class="tight">
        <li>${esc(f.detail)}</li>
        <li>Source: ${f.src ? src(f.src) : '<span class="pill">no official source</span>'}</li>
      </ul></div>`).join("");
}

/* ---------- page: sources ---------- */
function renderSources() {
  const el = document.getElementById("sr");
  if (!el || !Site.d.sources) return;
  const flagIds = new Set((Site.d.flags || []).map(f => f.src).filter(Boolean));
  const rows = Object.entries(Site.d.sources).map(([id, s]) => ({
    id, org: s.o || "",
    title: s.u ? `<a href="${esc(s.u)}" target="_blank" rel="noopener">${esc(s.t)}</a>` : esc(s.t),
    status: flagIds.has(id) ? '<span class="badge warn">flagged item cites it</span>'
          : (s.u ? '<span class="badge ok">registered</span>' : '<span class="badge warn">no public URL (household)</span>'),
    date: s.v || "",
  }));
  el.innerHTML = renderTable([
    { k: "id", label: "ID" }, { k: "org", label: "Authority" },
    { k: "title", label: "Source" }, { k: "status", label: "Status" }, { k: "date", label: "Retrieved" },
  ], rows);
}

/* ---------- page: briefing (one-page printable) ---------- */
function renderBriefing() {
  const el = document.getElementById("brief");
  if (!el) return;
  const P = Site.d.projection && Site.d.projection["2045"];
  const t = Site.d.tables;
  const q = (Site.d.questions && Site.d.questions.questions) || [];
  const flags = Site.d.flags || [];
  const find = pre => P && P.paths.find(x => x.path.startsWith(pre));
  const ls = find("SELL Property A → lump"), live = find("LIVE"), rent = find("RENT");
  const openQ = q.filter(x => /MISSING|OPEN|PENDING|FLAGGED|TO BE/i.test(x.status));
  const topFlags = flags.filter(f => f.severity === "High");
  const est = (t && t.estate_tax_scenarios) || [];

  el.innerHTML = `
  <div class="print-grid">
    <div class="card"><div class="k">Decision framed</div>
      <div class="n">Inherit Property A (single-family) ~$3.1M — occupy (Prop 19) / rent out / sell; already own Property B (three-unit) ~$1.8M, 2 units rented ~$7,150/mo. Model: inherit 2045, stocks 8.5% / homes 3.5% / bills 2.5%.</div></div>
    <div class="card"><div class="k">Baseline result (30y)</div>
      <div class="v" style="font-size:17px">SELL ${moneyC(ls && ls.net_worth["30"])} · LIVE ${moneyC(live && live.net_worth["30"])} · RENT ${moneyC(rent && rent.net_worth["30"])}</div>
      <div class="n">Recommended entry: 24-mo Treasury park → 24-mo phase (beats lump-sum in 4/5 historical crash entries; −65%→−34% drawdown in 1929).</div></div>
  </div>

  <div class="print-grid">
    <div class="card"><div class="k">1 · Questions for counsel</div>
      <ul class="tight" style="font-size:11.5px">
        <li>Confirm trust terms: who takes A, occupancy requirements, and any spendthrift/timing limits on sale.</li>
        <li>Prop 19: will heir occupy A as principal residence and file the homeowners' exclusion ≤1 year of transfer? (Decides ${money(live && live.property_tax_first_year)} vs ${money(rent && rent.property_tax_first_year)} yr-1 tax.)</li>
        <li>Form 706 needed? Portability election? Prior taxable gifts (Form 709 history) that shrink the exclusion?</li>
        <li>§121 on inherited home: ownership-use tacking under §121(d)(11) — confirm statute text (flagged F6) and whether MFJ $500k applies.</li>
        <li>Any liens/debt on A? Ancillary probate for out-of-state heirs? §6166 liquidity if the estate is taxable?</li>
        <li>Date-of-death appraisal ordered? (basis + Prop 19 FBYV evidence)</li>
      </ul></div>
    <div class="card"><div class="k">2 · Questions for CPA</div>
      <ul class="tight" style="font-size:11.5px">
        <li>Gain on same-year sale = FMV basis − costs: confirm ~$0 gain and Form 8946/4797 handling if rental use occurred first.</li>
        <li>Depreciation recapture: if A was ever rented, §1250 recapture + unrecaptured 25% rate on prior depreciation — need placed-in-service dates.</li>
        <li>Rental income of B: confirm no open FTB exposure; estimated-tax payments if A sold/rented in the transfer year.</li>
        <li>BHST 1% (Form 540 line 62) + NIIT 3.8% + CA top 13.3% on any gain — top-rate illustration for $1M gain: ${money(((t && t.form540_sensitivity || []).find(r => r.gain === 1000000) || {}).combined_top_simplified)} combined (simplified, flagged).</li>
        <li>State-tax deduction treatment of CA property tax (SALT cap interaction) for the surviving household.</li>
        <li>Basis reporting: Form 8971 within 30 days of Form 706 — heirs must use reported values.</li>
      </ul></div>
  </div>

  <div class="print-grid">
    <div class="card"><div class="k">3 · Numbers to verify (with source)</div>
      <ul class="tight" style="font-size:11.5px">
        <li>2026 federal exclusion ${money(15000000)}; 40% rate; CA estate tax $0 (R&amp;T §13302) — irs.gov / leginfo.</li>
        <li>Prop 19 cap $1,044,590 (2026-02-16 → 2027-02-15); filing windows ≤1yr / ≤3yr — BOE LTA 2025/009.</li>
        <li>A implied rate 1.335% vs SCC published 1.15–1.30% — <b>F1: get the TRA</b>.</li>
        <li>B implied 2.135% vs SF base 1.18162182% + parcels — <b>F2: get bill breakdown</b>.</li>
        <li>SCC transfer 0.11% + $110 record (verified) · sell cost 5.5% &amp; maintenance 0.75%/1.00% — <b>assumptions F9</b>.</li>
        <li>Insurance ~$1,500 each — <b>F5: quotes; CDI ZIP data for both property ZIPs (internal)</b> · HUD FMR floor $3,604 — rent comps needed (F4).</li>
      </ul></div>
    <div class="card"><div class="k">4 · Documents to collect</div>
      <ul class="tight" style="font-size:11.5px">
        <li>Trust instrument + pour-over will; death certificate(s); prior-year tax bills for A and B.</li>
        <li>Title report on A (liens) · solar interconnection/PToP date (NEM 1/2 vs 3.0 — F12).</li>
        <li>All B leases + SF Rent Ordinance registration; vacancy status of unit 3.</li>
        <li>Insurance declarations pages (HO-3 for A; DP-3/landlord for B) + any claims history.</li>
        <li>Form 709 gift returns (if any) · Form 706/4768 plan · DOD appraisal engagement letter.</li>
        <li>Household pre-commitment policy signed (allocation, entry schedule, drawdown rule).</li>
      </ul></div>
  </div>

  <div class="card"><div class="k">Estate-tax quick reference (2026 rules)</div>
    ${renderTable([
      { k: "taxable_estate", label: "Taxable estate", num: true, render: r => money(r.taxable_estate) },
      { k: "bea_2026", label: "Exclusion", num: true, render: r => money(r.bea_2026) },
      { k: "federal_estate_tax", label: "Federal tax", num: true, render: r => money(r.federal_estate_tax) },
      { k: "effective_rate_on_excess", label: "Eff. rate", num: true, render: r => r.effective_rate_on_excess == null ? "—" : r.effective_rate_on_excess + "%" },
    ], est)}
  </div>

  <div class="card"><div class="k">Open items blocking a final decision (${openQ.length} questions · ${topFlags.length} high-severity flags)</div>
    <div class="page-note">${openQ.slice(0, 8).map(x => `<b>${esc(x.id)}</b> ${esc(x.q)}`).join(" · ")}</div>
    <div class="page-note" style="margin-top:4px">High flags: ${topFlags.map(f => `<b>${esc(f.id)}</b> ${esc(f.item)}`).join(" · ")}</div>
  </div>`;
}

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded", async () => {
  buildNav();
  await Site.load();
  const page = document.body.dataset.page;
  try {
    ({ index: renderIndex, dashboard: renderDashboard, blackswan: renderBlackswan,
       data: renderData, timeline: renderTimeline, questions: renderQuestions,
       suggestions: renderSuggestions, glossary: renderGlossary, flagged: renderFlagged,
       sources: renderSources, briefing: renderBriefing }[page] || (() => {}))();
  } catch (e) { console.error("render error", e); }
});
