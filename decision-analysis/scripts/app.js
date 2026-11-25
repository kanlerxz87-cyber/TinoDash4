/* What-if controls: runs the same model as the build, in the browser. No external calls. */
(function () {
  'use strict';
  var PATHS = ['LIVE', 'RENT', 'SELL', 'M1', 'M2', 'M3', 'M4'];
  var NAMES = { LIVE: 'Live', RENT: 'Rent', SELL: 'Sell', M1: 'Live→Sell', M2: 'Rent→Sell', M3: 'Sell→Stage', M4: 'Live→Rent' };
  var TY = [2040, 2045, 2050], HZ = [5, 10, 20];

  function num(id) {
    var el = document.getElementById(id);
    if (!el || el.value === '' || el.value === null) return null;
    var x = Number(el.value);
    return isFinite(x) ? x : null;
  }
  function usd(x) {
    if (x === null || x === undefined || !isFinite(x)) return '—';
    var v = Math.round(x / 10) * 10;
    return (v < 0 ? '−$' : '$') + Math.abs(v).toLocaleString('en-US');
  }
  function readParams() {
    var p = {};
    var req = { V0: num('c_V0'), eq: num('c_eq'), g_prop: num('c_g_prop'), infl: num('c_infl'),
      cash_yield: num('c_cash_yield'), park_months: num('c_park_months'), rent_mult: num('c_rent_mult'), fed_ord: num('c_fed_ord') };
    if (req.V0 !== null) p.V0 = req.V0;
    if (req.eq !== null) p.eq = req.eq / 100;
    if (req.g_prop !== null) p.g_prop = req.g_prop / 100;
    if (req.infl !== null) p.infl = req.infl / 100;
    if (req.cash_yield !== null) p.cash_yield = req.cash_yield / 100;
    if (req.park_months !== null) p.park_months = req.park_months;
    if (req.rent_mult !== null) p.rent_mult = req.rent_mult;
    if (req.fed_ord !== null) p.fed_ord = req.fed_ord / 100;
    // Blank = unknown: stays null (the model never infers a missing value)
    p.parentBase = num('c_parentBase');
    p.ins_own = num('c_ins_own');
    return p;
  }

  function run() {
    var M = window.TinoModel;
    var out = document.getElementById('whatif-out');
    if (!M || !out) return;
    var p = readParams();
    var T = Number(document.getElementById('c_T').value);
    var H = Number(document.getElementById('c_H').value);
    var mac = M.constMacro(Object.assign({}, M.DEFAULTS, p));
    var rows = PATHS.map(function (id) {
      var r = M.run(id, T, H, mac, p);
      return { id: id, real: r.realRounded, nominal: r.nominalRounded };
    });
    var sorted = rows.slice().sort(function (a, b) { return b.real - a.real; });
    var rank = M.rankDeterministic(p);
    fetch('results.json').then(function (x) { return x.json(); }).then(function (base) {
      var moved = [];
      TY.forEach(function (t) { HZ.forEach(function (h) {
        var k = t + '|' + h;
        var topNow = rank[k][0].id, topBase = base.base[k][0].path;
        if (topNow !== topBase) moved.push(t + '/' + h + 'y: ' + NAMES[topBase] + ' → ' + NAMES[topNow]);
      }); });
      var html = '<h3>Result for transfer ' + T + ', horizon ' + H + ' years (real $, 2026)</h3>';
      html += '<div class="scroll"><table><thead><tr><th>Path</th><th>Real wealth</th><th>Nominal</th></tr></thead><tbody>';
      rows.forEach(function (r) {
        var cls = r.id === sorted[0].id ? ' class="best"' : '';
        html += '<tr><td' + cls + '>' + NAMES[r.id] + '</td><td' + cls + '>' + usd(r.real) + '</td><td>' + usd(r.nominal) + '</td></tr>';
      });
      html += '</tbody></table></div>';
      html += '<p><strong>Top path here:</strong> ' + NAMES[sorted[0].id] + '.</p>';
      html += '<p><strong>Recommendation moved?</strong> ' + (moved.length ? 'Yes, in ' + moved.length + ' combination(s): ' + moved.join('; ') : 'No, same top path in all nine transfer-year and horizon combinations as the base case.') + '</p>';
      html += '<p class="small">Blank inputs are treated as unknown (not zero). Flagged inputs keep the recommendation conditional. Not advice.</p>';
      out.innerHTML = html;
    }).catch(function () {
      out.innerHTML = '<p class="flag">Could not load the base-case file (results.json). The table above still updates.</p>';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var ids = ['c_V0', 'c_eq', 'c_g_prop', 'c_infl', 'c_cash_yield', 'c_park_months', 'c_parentBase', 'c_ins_own', 'c_rent_mult', 'c_fed_ord', 'c_T', 'c_H'];
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) { el.addEventListener('input', run); el.addEventListener('change', run); }
    });
    run();
  });
})();
