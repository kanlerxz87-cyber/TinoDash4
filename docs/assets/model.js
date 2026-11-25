/*
 * Decision model for the inherited-property comparison.
 * Shared by tools/build.js (Node, build time) and the browser (what-if controls).
 *
 * Tags on every constant:
 *   [V]  verified against an official source (see docs/sources.html)
 *   [U]  user-supplied, not yet verified
 *   [A]  modelling assumption, illustrative, not a forecast
 *   [F]  flagged: needed by the model but not verified; listed on docs/flagged.html
 *   BLANK  unknown; the model uses the conservative fallback stated beside it
 *
 * Money is in US dollars. Published figures are rounded to the nearest $10.
 * The model tests the rules in DECISION_RULES.md. It does not change them.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TinoModel = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const C = {
    // [V] Rev. Proc. 2025-32 §2.14: 2026 basic exclusion amount (estate and gift)
    fedBasicExclusion2026: 15000000,
    // [V] Rev. Proc. 2025-32 §4.03: 15% long-term gain bracket top, married filing jointly 2026
    cg15TopMFJ: 613700,
    // [V] BOE LTA 2025/009: indexed amount $1,044,586 for transfers 2/16/2025 to 2/15/2027
    prop19Indexed: 1044586,
    // [V] BOE LTA 2026/002: 2026-27 inflation factor 1.02 (Prop 13 cap on base-year growth)
    prop13Factor: 0.02,
    // [V] RTC §11911: county documentary transfer tax $0.55 per $500 = 0.0011
    countyTransferRate: 0.0011,
    // [V] FTB Form 540 2025 booklet: top rate 12.30%
    caTopRate: 0.123,
    // [V] RTC §17043: 1% surcharge on CA taxable income above $1,000,000
    caMhsRate: 0.01,
    // [V] SSA 2026 Trustees Report, Alt I / II / III long-range CPI-W
    cpiAltI: 0.030, cpiAltII: 0.024, cpiAltIII: 0.018,
    // [V] Fed History (1929 essay): Dow fell ~89% peak to trough 1929-1932; nominal peak regained Nov 1954
    dow1929Drawdown: 0.89,
    // [V] Fed History: S&P 500 fell 57% Oct 2007 to Mar 2009
    sp2008Drawdown: 0.57,
    // [F] Fed History essay (404 on fetch); home price fall ~30% taken from search snippet only
    homeDrawdown: 0.30,
  };

  // Default inputs. Unknown values use the stated conservative fallback.
  const DEFAULTS = {
    fmv2026: 3100000,      // [U] Property A market estimate, Nov 2026 (user-supplied, unverified)
    fbyv2026: null,        // BLANK: base-year assessed value not supplied. Fallback: full reassessment at FMV.
    effRate: 0.0119,       // [F] secondary: Santa Clara combined rate ~1.19%; County Controller not yet checked
    insA: 2340,            // [F] secondary: CDI 2025 data-call average $2,339.99 (all homeowners forms); ZIP-specific quote pending
    waterA: 1500,          // [U] $100-$150/month midpoint $125 x 12 (user-supplied, unverified)
    solarCredit: 180,      // [U] $10-$20/month midpoint $15 x 12 (user-supplied, unverified)
    maintPct: 0.0075,      // [A] maintenance and capital reserve, share of value per year
    marketYield: 0.025,    // [F] gross rent / value; BLANK: no verified rental comparables
    mgmtPct: 0.08,         // [A] vacancy, management and landlord overhead, share of gross rent
    rentalInsMult: 1.4,    // [A] landlord-policy premium multiplier over owner policy
    sellPct: 0.05,         // [F] total selling costs, agent + closing; not verified
    cityTransferRate: 0.0, // BLANK: any city transfer tax on Property A not verified; set to zero and flagged
    mixShare: 0.5,         // [A] occupied share of Property A in path E
    liveYears: 3,          // [A] years lived before sale in path F
    exclusion: 250000,     // [F] §121 single-filer exclusion; statute not yet fetched
    fedGainRate: 0.20,     // [F] top LTCG rate above the 15% bracket; §1(h) not yet fetched
    caGainRate: C.caTopRate + C.caMhsRate, // [V] CA top rate plus MHS surcharge, applied to large gains
    niitRate: 0.038,       // [F] §1411 net investment income tax; not yet fetched
    cashRate: 0.045,       // [F] short-term Treasury yield used for parked cash; Treasury source not yet fetched
    equityDrag: 0.005,     // [A] annual cost drag on index funds
    phaseMonths: 12,       // [A] months over which parked cash is phased into equities
    crashOnsetMonth: 12,   // [A] crash begins 12 months after transfer
    pCrash: 0.10,          // [A] probability in Monte Carlo that a crash occurs in the horizon
    commitLive: false,     // Rule 3: written commitment to occupy A within 12 months
    comparables: 0,        // Rule 4: number of verified rental comparables
  };

  // Six fixed economic scenarios. Each has its own CPI, used to deflate that scenario's outcome.
  const SCENARIOS = [
    { id: 'base', label: 'Base (SSA Alt II inflation)', cpi: C.cpiAltII, hpa: 0.029, eq: 0.065, crash: 'none' },
    { id: 'low', label: 'Low inflation, low growth (SSA Alt III)', cpi: C.cpiAltIII, hpa: 0.015, eq: 0.045, crash: 'none' },
    { id: 'highinf', label: 'High inflation (SSA Alt I)', cpi: C.cpiAltI, hpa: 0.035, eq: 0.075, crash: 'none' },
    { id: 'stag', label: 'Stagflation (illustrative 5% CPI, 0.5% home growth)', cpi: 0.05, hpa: 0.005, eq: 0.03, crash: 'none' },
    { id: 'c2008', label: '2008-type crash, 12 months after transfer', cpi: C.cpiAltII, hpa: 0.029, eq: 0.065, crash: '2008' },
    { id: 'c1929', label: '1929-type crash, 12 months after transfer', cpi: C.cpiAltII, hpa: 0.029, eq: 0.065, crash: '1929' },
  ];

  const PATHS = [
    { code: 'A', name: 'Live in A', share: 1, live: true },
    { code: 'B', name: 'Rent A', share: 0 },
    { code: 'C', name: 'Sell, invest lump sum', share: 0, sell: true, park: 0 },
    { code: 'D24', name: 'Sell, park 24 mo, phase 12 mo', share: 0, sell: true, park: 24 },
    { code: 'D36', name: 'Sell, park 36 mo, phase 12 mo', share: 0, sell: true, park: 36 },
    { code: 'E', name: 'Mixed: occupy 50%, rent 50%', share: 'mix', live: true },
    { code: 'F', name: 'Live 3 years, then sell', share: 1, live: true, liveThenSell: true },
  ];

  const CASES = [
    { T: 2040, H: 10 }, { T: 2040, H: 20 }, { T: 2050, H: 10 }, { T: 2050, H: 20 },
  ];

  const r10 = (x) => Math.round(x / 10) * 10;

  // Equity and home multipliers relative to trend, by month since transfer (crash onset = peak).
  // The shock is peak-relative: after the trough the index climbs back to the pre-crash PEAK, then grows at
  // trend. The gap to trend therefore persists after recovery (lost compounding). Timing is [A] except where noted.
  function shockPath(kind, months, onset, g, hpa) {
    const eq = new Float64Array(months + 1).fill(1);
    const home = new Float64Array(months + 1).fill(1);
    if (kind === 'none') return { eq, home };
    // [V] drop sizes from Fed History; [A] timing: 2008 trough 17 months after peak; 1929 trough 34 months after peak
    const dropEq = kind === '2008' ? C.sp2008Drawdown : C.dow1929Drawdown;
    const troughM = kind === '2008' ? 17 : 34;
    // [A] months from trough back to the pre-crash peak: 2008 = 48; 1929 = 268 (trough 1932 to nominal peak Nov 1954)
    const backM = kind === '2008' ? 48 : 268;
    const recoverM = troughM + backM;
    const trough = 1 - dropEq;
    const hTrough = 1 - C.homeDrawdown; // [F] home drop, see flagged page
    const hBottomM = 12, hBackM = 60;   // [A] home bottom 12 months after peak, back to peak 60 months later
    for (let m = 1; m <= months; m++) {
      const tt = m - onset;
      if (tt <= 0) continue;
      let q;
      if (tt <= troughM) q = Math.pow(trough, tt / troughM);
      else if (tt <= recoverM) q = Math.exp(Math.log(trough) * (1 - (tt - troughM) / backM));
      else q = Math.pow(1 + g, (tt - recoverM) / 12);
      eq[m] = q / Math.pow(1 + g, tt / 12);
      let hq;
      if (tt <= hBottomM) hq = Math.pow(hTrough, tt / hBottomM);
      else if (tt <= hBottomM + hBackM) hq = Math.exp(Math.log(hTrough) * (1 - (tt - hBottomM) / hBackM));
      else hq = Math.pow(1 + hpa, (tt - hBottomM - hBackM) / 12);
      home[m] = hq / Math.pow(1 + hpa, tt / 12);
    }
    return { eq, home };
  }

  // Simulate one path, one case, one scenario (or one Monte Carlo draw). Returns nominal and real results.
  function simulate(p, path, sc, T, H) {
    const months = H * 12;
    const cpi = sc.cpi, hpa = sc.hpa;
    const trendEq = sc.eq - p.equityDrag;
    const shock = shockPath(sc.crash, months, p.crashOnsetMonth, trendEq, hpa);
    const cashM = p.cashRate / 12;
    const share = path.share === 'mix' ? p.mixShare : path.share;

    const fmvT = p.fmv2026 * Math.pow(1 + hpa, T - 2026);
    // Prop 19 taxable value for an occupied share: the lesser of FMV and factored base year plus indexed amount.
    // Fallback when base-year value is blank: full FMV (conservative). [A] proportional split for path E.
    const capT = C.prop19Indexed * Math.pow(1 + hpa, T - 2026);
    const fbyvT = p.fbyv2026 === null ? null : p.fbyv2026 * Math.pow(1 + C.prop13Factor, T - 2026);
    const ntvOcc = fbyvT === null ? fmvT : Math.min(fmvT, fbyvT + capT);
    const taxable0 = share * ntvOcc + (1 - share) * fmvT;
    const taxGrowth = Math.min(C.prop13Factor, cpi);

    const gainRate = p.fedGainRate + p.caGainRate + p.niitRate;
    const sellNet = 1 - p.sellPct - C.countyTransferRate - p.cityTransferRate;

    let cash = 0, units = 0, held = true, liquidAtT = 0, impCum = 0, finCum = 0;
    let yr1Tax = 0, yr1Cost = 0, yr1Rent = 0, yr1Imp = 0;
    const valueAt = (m) => fmvT * Math.pow(1 + hpa, m / 12) * shock.home[m];
    const idxAt = (m) => Math.pow(1 + trendEq, m / 12) * shock.eq[m];
    const parkAmt = { v: 0 };
    const sellTaxed = (price) => {
      const gain = Math.max(0, price - fmvT - p.exclusion * share);
      return gain * gainRate;
    };

    if (path.sell) {
      held = false;
      const price = valueAt(0) * sellNet;
      cash = price - sellTaxed(price);
      liquidAtT = cash;
      parkAmt.v = cash;
    }

    const park = path.park || 0;
    const phaseEnd = park + p.phaseMonths;

    for (let m = 0; m < months; m++) {
      if (path.code === 'C' && m === 0) { units += cash / idxAt(0); cash = 0; }
      if (path.sell && path.park > 0 && m >= park && m < phaseEnd) {
        const tr = Math.min(cash, parkAmt.v / p.phaseMonths);
        cash -= tr; units += tr / idxAt(m);
      }
      if (path.liveThenSell && held && m === p.liveYears * 12) {
        const price = valueAt(m) * sellNet;
        const tax = sellTaxed(price);
        cash += price - tax; held = false; liquidAtT = price - tax;
        units += cash / idxAt(m); cash = 0;
      }
      if (held) {
        const V = valueAt(m);
        const infl = Math.pow(1 + cpi, m / 12);
        const taxable = taxable0 * Math.pow(1 + taxGrowth, m / 12);
        const propTax = (taxable * p.effRate) / 12;
        const ins = (((1 - share) * p.rentalInsMult + share) * p.insA * infl) / 12;
        const water = (p.waterA * infl) / 12;
        const maint = (p.maintPct * V) / 12;
        const solar = (p.solarCredit * infl) / 12;
        const grossRent = ((1 - share) * p.marketYield * V) / 12;
        const rent = grossRent * (1 - p.mgmtPct);
        const imputed = (share * p.marketYield * V) / 12; // [A] imputed rent for the occupied share
        const cf = rent + solar - propTax - ins - water - maint;
        finCum += cf; impCum += imputed;
        if (m < 12) { yr1Tax += propTax; yr1Cost += ins + water + maint; yr1Rent += rent; yr1Imp += imputed; }
        cash += cf;
      }
      cash *= 1 + cashM;
      // Equity units also run; cash in units changes only via idx (already embedded)
    }

    let terminal = 0;
    if (held) {
      const price = valueAt(months) * sellNet;
      terminal = price - sellTaxed(price);
    }
    const equity = units * idxAt(months);
    const nominalFinancial = cash + equity + terminal;
    // Path with occupancy also counts imputed rent as value received (rule 3 economic value of living).
    const nominalWithImputed = nominalFinancial + impCum;
    const realFin = nominalFinancial / Math.pow(1 + cpi, H);
    const realWith = nominalWithImputed / Math.pow(1 + cpi, H);
    return {
      nominal: nominalWithImputed, real: realWith,
      realFinancial: realFin, nominalFinancial,
      impCum, finCum, liquidAtT,
      yr1Tax, yr1Cost, yr1Rent, yr1Imp,
      fmvT, ntvOcc, taxable0, gainRate, cpi,
      terminalValue: terminal,
    };
  }

  function median(arr) {
    const a = arr.slice().sort((x, y) => x - y);
    const n = a.length;
    return n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2;
  }
  function quantile(arr, q) {
    const a = arr.slice().sort((x, y) => x - y);
    const pos = (a.length - 1) * q;
    const lo = Math.floor(pos), hi = Math.ceil(pos);
    return a[lo] + (a[hi] - a[lo]) * (pos - lo);
  }

  function prng(seed) {
    let s = seed >>> 0;
    return function () {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Monte Carlo ranges [A], drawn uniformly. These are not forecasts.
  const RANGES = {
    cpi: [C.cpiAltIII, C.cpiAltI],
    hpa: [0.0, 0.04],
    eq: [0.035, 0.08],
    effRate: [0.0115, 0.0135],
    marketYield: [0.02, 0.03],
    maintPct: [0.005, 0.01],
    sellPct: [0.04, 0.06],
    fmv2026: [2800000, 3400000],
  };

  function monteCarlo(params, T, H, n, seed) {
    const rnd = prng(seed || 20261125);
    const base = Object.assign({}, DEFAULTS, params || {});
    const out = {}; const outFin = {};
    PATHS.forEach((path) => { out[path.code] = []; outFin[path.code] = []; });
    for (let i = 0; i < n; i++) {
      const d = {};
      Object.keys(RANGES).forEach((k) => { const [lo, hi] = RANGES[k]; d[k] = lo + (hi - lo) * rnd(); });
      const u = rnd();
      const crash = u < base.pCrash / 2 ? '2008' : u < base.pCrash ? '1929' : 'none';
      const sc = { id: 'mc', cpi: d.cpi, hpa: d.hpa, eq: d.eq, crash };
      const pp = Object.assign({}, base, { effRate: d.effRate, marketYield: d.marketYield, maintPct: d.maintPct, sellPct: d.sellPct, fmv2026: d.fmv2026 });
      PATHS.forEach((path) => {
        const r = simulate(pp, path, sc, T, H);
        out[path.code].push(r.real); outFin[path.code].push(r.realFinancial);
      });
    }
    const summary = {};
    PATHS.forEach((path) => {
      const arr = out[path.code];
      summary[path.code] = {
        p10: quantile(arr, 0.1), p50: quantile(arr, 0.5), p90: quantile(arr, 0.9),
        p10Fin: quantile(outFin[path.code], 0.1), p50Fin: quantile(outFin[path.code], 0.5),
      };
    });
    return { n, seed: seed || 20261125, pCrash: base.pCrash, summary, draws: out };
  }

  // Full case evaluation: scenarios, MC, black-swan results, and the rule-based choice.
  function evaluate(params, T, H, opts) {
    const p = Object.assign({}, DEFAULTS, params || {});
    const n = (opts && opts.n) || 1000;
    const mc = monteCarlo(p, T, H, n, 20261125);
    const rows = {};
    PATHS.forEach((path) => {
      const sc = {};
      SCENARIOS.forEach((s) => { sc[s.id] = simulate(p, path, s, T, H); });
      const scReal = SCENARIOS.map((s) => sc[s.id].real);
      const pooled = scReal.concat(mc.draws[path.code]);
      rows[path.code] = {
        code: path.code, name: path.name,
        scenarios: sc,
        primaryMedian: median(pooled),
        p10: mc.summary[path.code].p10,
        p50: mc.summary[path.code].p50,
        p90: mc.summary[path.code].p90,
        medianFin: median(SCENARIOS.map((s) => sc[s.id].realFinancial)),
        worstBlackSwan: Math.min(sc.c2008.real, sc.c1929.real),
        base: sc.base,
      };
    });
    const choice = choose(rows, p);
    return { T, H, rows, choice, mc: mc.summary, params: p };
  }

  // Rule-based choice. Implements DECISION_RULES.md §2 as written.
  function choose(rows, p) {
    const eligible = ['C', 'D24', 'D36'];
    if (p.commitLive) { eligible.push('A', 'F', 'E'); }
    const pool = eligible.slice();
    const notes = [];
    if (!p.commitLive) notes.push('Rule 3: A, E and F removed (no written occupancy commitment).');
    if (p.comparables < 3) notes.push('Rule 4: B is reported as a floor, not a choice (fewer than three verified comparables).');
    // Primary metric: best median among eligible paths
    let best = pool.reduce((a, b) => (rows[b].primaryMedian > rows[a].primaryMedian ? b : a));
    // Rule 8 tie: within 2% of best, prefer higher liquidity at transfer
    const near = pool.filter((c) => rows[best].primaryMedian - rows[c].primaryMedian <= 0.02 * Math.abs(rows[best].primaryMedian));
    if (near.length > 1) {
      const liq = (c) => (rows[c].base.liquidAtT || 0);
      const regRank = { C: 0, D24: 1, D36: 2, E: 3, A: 4, F: 4 }; // [interpretation] sale paths carry less Prop 19 / rule-change exposure; shorter parking first
      best = near.reduce((a, b) => {
        const la = liq(a), lb = liq(b);
        if (lb !== la) return lb > la ? b : a;
        return regRank[b] < regRank[a] ? b : a;
      });
      notes.push('Rule 8: paths within 2% on the primary metric; higher liquidity at transfer, then lower regulatory exposure (interpretation: sale paths and shorter parking first).');
    }
    // Rule 5: D beats C only if black-swan worst and base median pass
    if (best === 'D24' || best === 'D36') {
      const d = rows[best], c = rows.C;
      const worstOk = d.worstBlackSwan >= c.worstBlackSwan;
      const baseOk = Math.abs(d.primaryMedian - c.primaryMedian) <= 0.05 * Math.abs(c.primaryMedian) || d.primaryMedian >= c.primaryMedian * 0.95;
      if (!(worstOk && baseOk)) { best = 'C'; notes.push('Rule 5: phased path failed black-swan or base test; lump sum (C) used.'); }
    }
    // Rule 2 downside guard against C's 10th percentile
    const guard = (c) => rows[c].p10 >= 0.9 * rows.C.p10 || rows.C.p10 <= 0;
    if (best !== 'C' && !guard(best)) { best = 'C'; notes.push('Rule 2: downside guard failed; Path C chosen.'); }
    // Rule 6: mixed only if it beats best pure path on primary and guard
    if (best === 'E') {
      const pure = pool.filter((x) => x !== 'E').reduce((a, b) => (rows[b].primaryMedian > rows[a].primaryMedian ? b : a));
      if (!(rows.E.primaryMedian > rows[pure].primaryMedian && guard('E'))) { best = pure; notes.push('Rule 6: mixed path did not beat the best pure path.'); }
    }
    return { pick: best, eligible: pool, notes };
  }

  // Break-even gross rent yield where Path B equals Path C on the base financial measure.
  function breakEvenRentYield(params, T, H) {
    const p = Object.assign({}, DEFAULTS, params || {});
    const sc = SCENARIOS[0];
    const B = PATHS.find((x) => x.code === 'B'), Cp = PATHS.find((x) => x.code === 'C');
    const target = simulate(p, Cp, sc, T, H).realFinancial;
    let lo = 0, hi = 0.15;
    for (let i = 0; i < 60; i++) {
      const mid = (lo + hi) / 2;
      const v = simulate(Object.assign({}, p, { marketYield: mid }), B, sc, T, H).realFinancial;
      if (v < target) lo = mid; else hi = mid;
    }
    return (lo + hi) / 2;
  }

  // Generic break-even: find the value of `key` at which path `pathCode` equals `vsCode` on primary-style base metric.
  // Uses the financial measure for rent and the financial+imputed measure for occupancy paths (as in the rules).
  function breakEven(params, T, H, key, pathCode, vsCode, lo, hi) {
    const p = Object.assign({}, DEFAULTS, params || {});
    const sc = SCENARIOS[0];
    const P = PATHS.find((x) => x.code === pathCode), Q = PATHS.find((x) => x.code === vsCode);
    const target = simulate(p, Q, sc, T, H).real;
    const f = (v) => simulate(Object.assign({}, p, { [key]: v }), P, sc, T, H).real - target;
    let a = lo, b = hi, fa = f(a), fb = f(b);
    if (fa * fb > 0) return null; // no sign change in range
    for (let i = 0; i < 80; i++) {
      const m = (a + b) / 2, fm = f(m);
      if (fa * fm <= 0) { b = m; fb = fm; } else { a = m; fa = fm; }
    }
    return (a + b) / 2;
  }

  // Estate tax exposure. Property A alone is tested against the basic exclusion. Other assets are unknown.
  function estateExposure(fmvT, otherAssets) {
    const ex = C.fedBasicExclusion2026;
    const known = fmvT + (otherAssets || 0);
    return {
      propertyA: fmvT,
      exclusion: ex,
      headroomPropertyAOnly: ex - fmvT,
      otherAssets: otherAssets === undefined ? null : otherAssets,
      taxIfKnownOnly: Math.max(0, known - ex) * 0.4,  // [F] 40% top rate; §2001 not yet fetched
      note: otherAssets === undefined ? 'Other assets unknown: no estate-tax liability assumed (Rule 7).' : '',
    };
  }

  return {
    C, DEFAULTS, SCENARIOS, PATHS, CASES, RANGES,
    simulate, evaluate, monteCarlo, choose, breakEvenRentYield, breakEven, estateExposure,
    median, quantile, r10, shockPath,
  };
});
