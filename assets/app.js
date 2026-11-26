// Dependency-free what-if: reads the precomputed grid only (no re-simulation in the browser).
(function(){
  var el = document.getElementById('grid-data');
  if(!el) return;
  var grid = JSON.parse(el.textContent);
  var labels = {S:'Sell in transfer year, invest lump sum',SP24:'Sell, park 24 months, then phase in',SP36:'Sell, park 36 months, then phase in',
    L2S:'Mixed: live 2 years, then sell',R10S:'Mixed: rent 10 years, then sell',R:'Rent long-term, sell at horizon',
    L5S:'Mixed: live 5 years, then sell',L5R_B:'Mixed: live 5 years, then rent (Prop 19 base reset on move-out)',
    L:'Live long-term, sell at horizon'};
  var order = ['S','SP24','SP36','L2S','R10S','R','L5S','L5R_B','L'];
  function v(id){ return document.getElementById(id).value; }
  function money(x){ return '$' + (Math.round(x/10)*10).toLocaleString('en-US'); }
  function render(){
    var T = parseInt(v('w-T'),10), H = parseInt(v('w-H'),10), ap = v('w-ap'), eq = v('w-eq'), c = parseFloat(v('w-c'));
    var row = grid.find(function(r){ return r.T===T && r.H===H && r.appreciation===ap && r.equity===eq && Math.abs(r.credit-c)<1e-9; });
    var out = document.getElementById('w-out');
    if(!row){ out.textContent = 'No grid row for these settings.'; return; }
    var max = Math.max.apply(null, order.map(function(p){ return row.results[p]; }));
    var best = order.reduce(function(a,p){ return row.results[p] > row.results[a] ? p : a; }, order[0]);
    var html = '<p><strong>Highest result for these settings:</strong> ' + labels[best] + ' (' + money(row.results[best]) + ', real 2026 dollars).</p>';
    order.forEach(function(p){
      var w = Math.max(2, Math.round(100 * row.results[p] / max));
      html += '<div class="wbar"><span>' + labels[p] + '</span><span><span class="bar" style="width:' + w + '%"></span></span><strong>' + money(row.results[p]) + '</strong></div>';
    });
    html += '<p class="note">Settings: transfer ' + T + ', horizon ' + H + ' years, appreciation ' + ap + ', stock returns ' + eq + ', imputed rent credit ' + Math.round(c*100) + '%. Liquidated after tax; rounded to $10.</p>';
    out.innerHTML = html;
  }
  ['w-T','w-H','w-ap','w-eq','w-c'].forEach(function(id){ var n=document.getElementById(id); if(n) n.addEventListener('change', render); });
  render();
})();
