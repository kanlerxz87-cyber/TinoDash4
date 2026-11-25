/* Inheritance decision model - shared by the build script (Node) and the browser what-if page.
 * Pure JavaScript, no dependencies. Outputs are rounded to the nearest $10 by r10().
 * Each input in DEFAULTS has a status in INPUT_STATUS (official | owner | assumption | unverified | blank).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TinoModel = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var BASE = 2026;      // valuation year (Nov 2026)
  var MAXY = 2075;      // last modelled calendar year (2050 transfer + 20-year horizon + margin)

  function r10(x) { return Math.round(x / 10) * 10; }

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function gauss(rng) {
    var u = 0; while (u === 0) u = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
  }

  /* ---- Inputs. null = not provided (blank); the model never infers a missing value. ---- */
  var DEFAULTS = {
    V0: 3100000,          // Cupertino market value, Nov 2026 (owner estimate)
    parentBase: null,     // decedent's Prop 13 base-year value (BLANK: not yet verified)
    allowance: 1044590,   // Prop 19 added-value allowance (research figure; primary BOE LTA 2025/009 not yet read)
    cap13: 0.02,          // Prop 13 inflation factor ceiling (Cal. Const. art. XIII A s.2(b))
    tax_rate: 0.01,       // Prop 13 general levy (art. XIII A s.1); voter-approved bonds excluded (BLANK)
    g_prop: 0.03,         // property value growth, nominal (assumption)
    infl: 0.025,          // CPI, long run (assumption; Fed PCE goal 2%; Sep 2026 CPI 3.7% noted)
    eq: 0.065,            // equity total return, nominal (assumption)
    cash_yield: 0.0436,   // 3-month Treasury par yield 11/24/2026 (official)
    park_yield: 0.0463,   // 2-year Treasury par yield 11/24/2026 (official) - used only in staged path
    fmr: 3272,            // HUD FY2027 2BR FMR, San Jose metro, per month (secondary-confirmed; floor, not a house rent)
    rent_mult: 1.0,       // rent multiple on FMR (BLANK: no verified comparables; 1.0 = floor)
    vacancy: 0.05,        // vacancy (assumption)
    mgmt: 0.08,           // management fee (assumption)
    water_mo: 125,        // water, per month (owner range $100-$150; midpoint)
    elec_net_mo: 15,      // net solar credit income, per month (owner range +$10 to +$20; midpoint)
    ins_own: null,        // homeowners insurance (BLANK: CDI primary not verified)
    ins_rent: null,       // landlord insurance (BLANK)
    maint: 0.01,          // maintenance & reserves, % of value/yr (assumption)
    comm: 0.025,          // agent commission at sale (assumption, 2-3% range)
    title: 0.005,         // title/escrow at sale (assumption)
    dtt: 0.0011,          // Santa Clara County documentary transfer tax, $1.10 per $1,000 (official)
    measureE: 0,          // Measure E applies to City of San Jose only (official); Cupertino treated as 0 (confirm)
    rec: 92,              // recording: $102 first page less $10 when DTT applies = $92; includes $75 SB2 fee (county fee schedule, official)
    bldg_share: 0.8,      // building share of value for depreciation (assumption)
    dep_years: 27.5,      // residential rental recovery period (IRC s.168)
    fed_ord: 0.24,        // federal ordinary marginal rate of the household (assumption)
    ca_ord: 0.093,        // CA marginal rate (assumption; 9.3% bracket)
    cg_fed: 0.15,         // federal long-term capital gain rate (assumption)
    niit: 0.038,          // NIIT (IRS topic 559; threshold depends on MAGI - assumed applicable)
    ca_cg: 0.093,         // CA tax on capital gains (ordinary rates)
    recap_max: 0.25,      // unrecaptured s.1250 gain max federal rate (IRS Pub 544; verify)
    s121: 250000,         // home-sale exclusion, single filer (IRS Pub 523); MFJ would be 500000 (BLANK: marital status)
    park_months: 30,      // staged path: months parked (24-36 range)
    phase_months: 12,     // staged path: months to phase into equity
    L_M1: 5,              // M1: years lived before sale
    L_M2: 10,             // M2: years rented before sale
    L_M4: 5               // M4: years lived before renting
  };

  // Source status of each input (used on the site; keep in sync with DEFAULTS)
  var INPUT_STATUS = {
    V0: 'owner', parentBase: 'blank', allowance: 'unverified', cap13: 'official', tax_rate: 'official',
    g_prop: 'assumption', infl: 'assumption', eq: 'assumption', cash_yield: 'official', park_yield: 'official',
    fmr: 'secondary', rent_mult: 'blank', vacancy: 'assumption', mgmt: 'assumption', water_mo: 'owner',
    elec_net_mo: 'owner', ins_own: 'blank', ins_rent: 'blank', maint: 'assumption', comm: 'assumption',
    title: 'assumption', dtt: 'official', measureE: 'official', rec: 'official', bldg_share: 'assumption',
    dep_years: 'official', fed_ord: 'assumption', ca_ord: 'assumption', cg_fed: 'assumption', niit: 'official',
    ca_cg: 'assumption', recap_max: 'official', s121: 'official', park_months: 'assumption',
    phase_months: 'assumption', L_M1: 'assumption', L_M2: 'assumption', L_M4: 'assumption'
  };

  var PATHS = [
    { id: 'LIVE', kind: 'pure', label: 'Live in the Cupertino house', short: 'Live' },
    { id: 'RENT', kind: 'pure', label: 'Rent out the Cupertino house', short: 'Rent' },
    { id: 'SELL', kind: 'pure', label: 'Sell in the inheritance year; invest in equities', short: 'Sell' },
    { id: 'M1', kind: 'mixed', label: 'Live 5 years, then sell and invest', short: 'Live→Sell' },
    { id: 'M2', kind: 'mixed', label: 'Rent 10 years, then sell and invest', short: 'Rent→Sell' },
    { id: 'M3', kind: 'mixed', label: 'Sell; park in Treasuries 30 months; phase into equities over 12 months', short: 'Sell→Stage' },
    { id: 'M4', kind: 'mixed', label: 'Live 5 years, then rent out', short: 'Live→Rent' }
  ];
  var TRANSFER_YEARS = [2040, 2045, 2050];
  var HORIZONS = [5, 10, 20];

  /* ---- Macro arrays (index by calendar year, BASE..MAXY) ---- */
  function constMacro(p) {
    var m = { infl: [], g: [], eq: [], bill: [] };
    for (var y = BASE; y <= MAXY; y++) {
      m.infl[y] = p.infl; m.g[y] = p.g_prop; m.eq[y] = p.eq; m.bill[y] = p.cash_yield;
    }
    m.park = p.park_yield;
    return m;
  }
  function cumIdx(arr) {
    var c = []; c[BASE] = 1;
    for (var y = BASE + 1; y <= MAXY; y++) c[y] = c[y - 1] * (1 + arr[y]);
    return c;
  }

  // Regime-switching macro (Monte Carlo). Regime parameters are ASSUMPTIONS, flagged on the site.
  var REGIMES = {
    N: { name: 'Normal growth', infl: [0.025, 0.008], g: [0.03, 0.03], eq: [0.07, 0.16], real: [0.01, 0.01] },
    I: { name: 'Inflation spike', infl: [0.06, 0.015], g: [0.05, 0.05], eq: [0.03, 0.18], real: [-0.01, 0.02] },
    R: { name: 'Recession', infl: [0.015, 0.01], g: [-0.02, 0.04], eq: [-0.05, 0.22], real: [0.02, 0.015] },
    D: { name: 'Deflationary depression (1929-type)', infl: [-0.02, 0.02], g: [-0.08, 0.06], eq: [-0.12, 0.28], real: [0.03, 0.02] },
    S: { name: 'Stagflation', infl: [0.07, 0.015], g: [0.01, 0.04], eq: [-0.02, 0.18], real: [-0.02, 0.015] }
  };
  var STATES = ['N', 'I', 'R', 'D', 'S'];
  var TRANS = {
    N: [0.915, 0.035, 0.040, 0.005, 0.005],
    I: [0.350, 0.550, 0.050, 0.000, 0.050],
    R: [0.450, 0.050, 0.400, 0.020, 0.080],
    D: [0.100, 0.020, 0.200, 0.600, 0.080],
    S: [0.350, 0.150, 0.050, 0.020, 0.430]
  };

  function mcMacro(rng, start) {
    var m = { infl: [], g: [], eq: [], bill: [], regime: [] };
    var s = start || 'N';
    for (var y = BASE; y <= MAXY; y++) {
      if (y > BASE) {
        var u = rng(), acc = 0, nxt = s, row = TRANS[s];
        for (var j = 0; j < 5; j++) { acc += row[j]; if (u <= acc) { nxt = STATES[j]; break; } }
        s = nxt;
      }
      var R = REGIMES[s];
      m.infl[y] = R.infl[0] + R.infl[1] * gauss(rng);
      m.g[y] = R.g[0] + R.g[1] * gauss(rng);
      m.eq[y] = R.eq[0] + R.eq[1] * gauss(rng);
      m.bill[y] = Math.max(0, m.infl[y] + R.real[0] + R.real[1] * gauss(rng));
      m.regime[y] = s;
    }
    m.park = null; // use bill[] for park yield in MC
    return m;
  }

  /* ---- Path specification ---- */
  function pathSpec(id, T, E, p) {
    var H = E - T;
    var live = function (y) { return y < E ? 'live' : null; };
    switch (id) {
      case 'LIVE': return { modeAt: live, S: E, reinvest: null };
      case 'RENT': return { modeAt: function (y) { return y < E ? 'rent' : null; }, S: E, reinvest: null };
      case 'SELL': return { modeAt: function () { return null; }, S: T, reinvest: { park: 0, phase: 1 } };
      case 'M1': { var s1 = T + Math.min(p.L_M1, H); return { modeAt: function (y) { return y < s1 ? 'live' : null; }, S: s1, reinvest: { park: 0, phase: 1 } }; }
      case 'M2': { var s2 = T + Math.min(p.L_M2, H); return { modeAt: function (y) { return y < s2 ? 'rent' : null; }, S: s2, reinvest: { park: 0, phase: 1 } }; }
      case 'M3': return { modeAt: function () { return null; }, S: T, reinvest: { park: p.park_months, phase: p.phase_months } };
      case 'M4': { var s4 = T + Math.min(p.L_M4, H); return { modeAt: function (y) { return y < s4 ? 'live' : (y < E ? 'rent' : null); }, S: E, reinvest: null }; }
      default: throw new Error('unknown path ' + id);
    }
  }

  /* ---- Simulation (monthly). Returns nominal and real end-of-horizon wealth (financial measure). ---- */
  function run(pathId, T, H, mac, pIn, opt) {
    var p = Object.assign({}, DEFAULTS, pIn || {});
    opt = opt || {};
    var E = T + H, M = H * 12;
    var cgRate = p.cg_fed + p.niit + p.ca_cg;
    var ordRate = p.fed_ord + p.ca_ord;
    var recRate = Math.min(p.recap_max, p.fed_ord) + p.niit + p.ca_ord;
    var idx = cumIdx(mac.infl);
    var gIdx = cumIdx(mac.g);
    var capIdx = []; capIdx[BASE] = 1;
    for (var k = BASE + 1; k <= MAXY; k++) capIdx[k] = capIdx[k - 1] * (1 + Math.min(p.cap13, mac.infl[k]));
    var spec = pathSpec(pathId, T, E, p);
    var Vt = p.V0 * gIdx[T] / gIdx[BASE];
    var V = function (y) { return p.V0 * gIdx[y] / gIdx[BASE]; };
    var firstMode = spec.modeAt(T);
    // Assessed base at transfer: Prop 19 family-home rule only when the heir occupies (live first)
    var base;
    if (firstMode === 'live' && p.parentBase !== null) {
      base = p.parentBase + Math.min(p.allowance, Math.max(0, Vt - p.parentBase));
    } else {
      base = Vt; // change of ownership -> reassessed at market value; BLANK parentBase -> no Prop 19 benefit (lower bound)
    }
    var S = spec.S, sMonth = (S - T) * 12;
    var cash = 0, pk = 0, eq = 0, eqBasis = 0, D = 0, depBasis = Vt * p.bldg_share;
    var sold = false, saleRec = null, liqNet = 0, minCash = 0;
    var T_ = { ptax: 0, water: 0, maint: 0, ins: 0, gross: 0, mgmt: 0, tax: 0, imputed: 0, elecInc: 0, saleCosts: 0, saleTax: 0 };
    var eqPeakReal = 0, eqMaxDD = 0, trace = opt.trace ? [] : null;
    var annual = {}; // per-year computed flows
    var cy, base_y = base, yy;

    function doSale(y, hyp) {
      var price = V(y);
      var costs = price * (p.comm + p.title + p.dtt + p.measureE) + p.rec;
      var basis = Vt - D;
      var gain = price - costs - basis;
      var rec = Math.min(D, Math.max(0, gain));
      var rest = Math.max(0, gain - rec);
      // Section 121: 2 of the 5 years before sale must be occupied as principal residence
      var liveRecent = 0;
      for (var q = Math.max(T, y - 5); q < y; q++) if (spec.modeAt(q) === 'live') liveRecent++;
      var excl = (liveRecent >= 2) ? Math.min(p.s121, rest) : 0;
      var cg = rest - excl;
      var tax = rec * recRate + cg * cgRate;
      var net = price - costs - tax;
      T_.saleCosts += costs; T_.saleTax += tax;
      saleRec = { year: y, price: price, costs: costs, gain: gain, recapture: rec, exclusion: excl, tax: tax, net: net, hypothetical: !!hyp };
      sold = true;
      if (hyp) { liqNet = net; return; }
      if (spec.reinvest) pk += net; // staged or lump-sum reinvestment starts at sale
    }

    for (var m = 0; m <= M; m++) {
      yy = T + Math.floor(m / 12);
      if (m % 12 === 0 && m < M) {
        if (yy > T) base_y = base_y * (1 + Math.min(p.cap13, mac.infl[yy]));
        cy = idx[yy] / idx[BASE];
        var mode = spec.modeAt(yy);
        var a = { mode: mode, y: yy, value: V(yy), base: base_y, cr: cy };
        if (mode === 'live') {
          a.ptax = p.tax_rate * base_y;
          a.water = p.water_mo * 12 * cy;
          a.maint = p.maint * a.value;
          a.ins = (p.ins_own === null ? 0 : p.ins_own * cy);
          a.elec = p.elec_net_mo * 12 * cy;
          a.imputed = p.fmr * 12 * cy;
          a.net = a.elec - a.ptax - a.water - a.maint - a.ins;
          T_.ptax += a.ptax; T_.water += a.water; T_.maint += a.maint; T_.ins += a.ins; T_.elecInc += a.elec; T_.imputed += a.imputed;
        } else if (mode === 'rent') {
          a.gross = p.fmr * 12 * cy * p.rent_mult * (1 - p.vacancy);
          a.mgmt = p.mgmt * a.gross;
          a.ptax = p.tax_rate * base_y;
          a.water = p.water_mo * 12 * cy;
          a.maint = p.maint * a.value;
          a.ins = (p.ins_rent === null ? 0 : p.ins_rent * cy);
          a.dep = Math.max(0, Math.min(depBasis / p.dep_years, depBasis - D));
          var taxable = a.gross - a.mgmt - a.ptax - a.ins - a.maint - a.water - a.dep;
          a.tax = Math.max(0, taxable) * ordRate;
          a.net = a.gross - a.mgmt - a.ptax - a.ins - a.maint - a.water - a.tax;
          D += a.dep;
          T_.gross += a.gross; T_.mgmt += a.mgmt; T_.ptax += a.ptax; T_.water += a.water; T_.maint += a.maint;
          T_.ins += a.ins; T_.tax += a.tax;
        } else {
          a.net = 0;
        }
        annual = a;
        if (trace && mode) trace.push({ year: yy, mode: mode, value: a.value, base: base_y, net: a.net, tax: a.tax || 0, ptax: a.ptax || 0 });
      }
      // Sale at the start of year S (before that year's flows)
      if (m === sMonth && !sold && S < E) {
        doSale(yy, false);
      }
      if (m === M) break;
      // Monthly accrual
      var rCash = mac.bill[yy] / 12 * (1 - p.fed_ord);
      var rParkBase = (mac.park !== null && mac.park !== undefined) ? mac.park : mac.bill[yy];
      var rPark = rParkBase / 12 * (1 - p.fed_ord);
      cash += cash * rCash;
      pk += pk * rPark;
      var rEq = opt.eqMonthly ? opt.eqMonthly(m) : Math.pow(1 + mac.eq[yy], 1 / 12) - 1;
      eq *= (1 + rEq);
      var monthlyNet = (annual && annual.y === yy && annual.net !== undefined) ? annual.net / 12 : 0;
      cash += monthlyNet;
      if (cash < minCash) minCash = cash;
      // Staged reinvestment (park -> equity)
      if (spec.reinvest && sold && !saleRec.hypothetical && m >= sMonth) {
        var t = m - sMonth;
        var ph = spec.reinvest.phase, pk0 = spec.reinvest.park;
        if (t >= pk0 && t < pk0 + ph && pk > 0) {
          var mv = pk / (pk0 + ph - t);
          pk -= mv; eq += mv; eqBasis += mv;
        }
      }
      // Equity drawdown tracking (real)
      var eqReal = eq / idx[yy] * idx[BASE];
      if (eqReal > eqPeakReal) eqPeakReal = eqReal;
      if (eqPeakReal > 0) { var dd = eqReal / eqPeakReal - 1; if (dd < eqMaxDD) eqMaxDD = dd; }
    }
    // Sale at horizon end if not yet sold (hypothetical liquidation)
    if (!sold) doSale(E, true);

    var eqGain = Math.max(0, eq - eqBasis);
    var eqTax = eqGain * cgRate;
    var nominal = cash + pk + eq - eqTax + liqNet;
    var infE = idx[E] / idx[BASE];
    var out = {
      pathId: pathId, T: T, H: H, E: E,
      nominal: nominal,
      real: nominal / infE,
      realRounded: r10(nominal / infE),
      nominalRounded: r10(nominal),
      cash: cash, pk: pk, eq: eq, eqTax: eqTax, liqNet: liqNet, minCash: minCash,
      eqMaxDD: eqMaxDD,
      sale: saleRec,
      totals: {
        ptax: r10(T_.ptax), water: r10(T_.water), maint: r10(T_.maint), ins: r10(T_.ins),
        gross: r10(T_.gross), mgmt: r10(T_.mgmt), tax: r10(T_.tax), imputed: r10(T_.imputed),
        elecInc: r10(T_.elecInc), saleCosts: r10(T_.saleCosts), saleTax: r10(T_.saleTax)
      },
      imputedReal: T_.imputed / infE,
      trace: trace
    };
    return out;
  }

  /* ---- Monte Carlo over regimes ---- */
  function monteCarlo(pIn, N, seed) {
    var p = Object.assign({}, DEFAULTS, pIn || {});
    var rng = mulberry32(seed || 20261125);
    var keys = [];
    TRANSFER_YEARS.forEach(function (T) { HORIZONS.forEach(function (H) { PATHS.forEach(function (pa) { keys.push([pa.id, T, H]); }); }); });
    var samples = {};
    keys.forEach(function (k) { samples[k.join('|')] = []; });
    for (var i = 0; i < N; i++) {
      var mac = mcMacro(rng, 'N');
      keys.forEach(function (k) {
        samples[k.join('|')].push(run(k[0], k[1], k[2], mac, p).real);
      });
    }
    var out = {};
    keys.forEach(function (k) {
      var key = k.join('|'), arr = samples[key];
      var sell = samples['SELL|' + k[1] + '|' + k[2]];
      var wins = 0; for (var j = 0; j < arr.length; j++) if (arr[j] > sell[j]) wins++;
      out[key] = {
        p10: r10(quantile(arr, 0.10)), p50: r10(quantile(arr, 0.50)), p90: r10(quantile(arr, 0.90)),
        probBeatsSell: wins / arr.length
      };
    });
    return { results: out, N: N, seed: seed || 20261125 };
  }

  function quantile(arr, q) {
    var s = arr.slice().sort(function (a, b) { return a - b; });
    var pos = (s.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
    return s[lo] + (s[hi] - s[lo]) * (pos - lo);
  }

  /* ---- Deterministic ranking across all transfer years and horizons ---- */
  function rankDeterministic(pIn) {
    var p = Object.assign({}, DEFAULTS, pIn || {});
    var mac = constMacro(p);
    var out = {};
    TRANSFER_YEARS.forEach(function (T) {
      HORIZONS.forEach(function (H) {
        var list = PATHS.map(function (pa) {
          var r = run(pa.id, T, H, mac, p);
          return { id: pa.id, realRounded: r.realRounded, nominalRounded: r.nominalRounded, minCash: r10(r.minCash), imputedReal: r10(r.imputedReal) };
        });
        list.sort(function (a, b) { return b.realRounded - a.realRounded; });
        out[T + '|' + H] = list;
      });
    });
    return out;
  }

  /* ---- Black-swan stylised entry shocks (applied to the equity account from entry) ---- */
  // Monthly return path: decline to a trough over `fallMonths`, then constant-rate recovery over `recoverMonths`.
  function shockPath(trough, fallMonths, recoverMonths) {
    return function (m) {
      if (m < fallMonths) return Math.pow(trough, 1 / fallMonths) - 1;
      if (m < fallMonths + recoverMonths) return Math.pow(1 / trough, 1 / recoverMonths) - 1;
      return null; // no override: use normal equity return
    };
  }
  var SHOCKS = {
    '1929': { label: 'Stylised 1929 entry: −89% over 34 months, then recovery over 25 years', trough: 0.11, fall: 34, rec: 300, source: 'Federal Reserve History essay (Dow 381.17 to 41.22; nominal peak regained 1954); path shape is a stylised assumption' },
    '2008': { label: 'Stylised 2008 entry: −49% (lower of conflicting sources) over 17 months, recovery over 4 years', trough: 0.51, fall: 17, rec: 48, source: 'Conflicting secondary sources (49%–60%); recovery length is an assumption' }
  };
  // offset: months after transfer when the crash starts (tests entry timing; staged paths are not favoured by a lucky trough)
  function shockedRun(pathId, T, H, mac, pIn, shockName, offset) {
    var sh = SHOCKS[shockName];
    var off = offset || 0;
    var fn0 = shockPath(sh.trough, sh.fall, sh.rec);
    var fn = function (m) {
      var r = m < off ? null : fn0(m - off);
      return r === null ? (Math.pow(1 + mac.eq[T + Math.floor(m / 12)], 1 / 12) - 1) : r;
    };
    return run(pathId, T, H, mac, pIn, { eqMonthly: fn });
  }

  /* ---- Breakpoints: parameter value where two paths give equal real wealth (bisection) ---- */
  function breakpoint(paramName, lo, hi, pathA, pathB, T, H, baseP) {
    function diff(x) {
      var p = Object.assign({}, DEFAULTS, baseP || {}); p[paramName] = x;
      var mac = constMacro(p);
      return run(pathA, T, H, mac, p).real - run(pathB, T, H, mac, p).real;
    }
    var dl = diff(lo), dh = diff(hi);
    if (!isFinite(dl) || !isFinite(dh) || dl * dh > 0) return null;
    var a = lo, b = hi;
    for (var i = 0; i < 60; i++) {
      var mid = (a + b) / 2, dm = diff(mid);
      if (dl * dm <= 0) { b = mid; dh = dm; } else { a = mid; dl = dm; }
    }
    return (a + b) / 2;
  }

  return {
    BASE: BASE, MAXY: MAXY, DEFAULTS: DEFAULTS, INPUT_STATUS: INPUT_STATUS, PATHS: PATHS,
    TRANSFER_YEARS: TRANSFER_YEARS, HORIZONS: HORIZONS, REGIMES: REGIMES, TRANS: TRANS, SHOCKS: SHOCKS,
    r10: r10, mulberry32: mulberry32, constMacro: constMacro, mcMacro: mcMacro, cumIdx: cumIdx,
    pathSpec: pathSpec, run: run, monteCarlo: monteCarlo, rankDeterministic: rankDeterministic,
    shockedRun: shockedRun, breakpoint: breakpoint, quantile: quantile
  };
}));
