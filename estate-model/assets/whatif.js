(function(){
  'use strict';
  var M = window.TinoModel;
  var money = function(v){ var x = Math.round(v/10)*10; return (x<0?'\u2212$':'$') + Math.abs(x).toLocaleString('en-US'); };
  function read(form){
    var f = new FormData(form), p = {};
    p.fmv2026 = +f.get('fmv2026');
    p.marketYield = +f.get('marketYield')/100;
    p.effRate = +f.get('effRate')/100;
    p.insA = +f.get('insA');
    p.maintPct = +f.get('maintPct')/100;
    p.sellPct = +f.get('sellPct')/100;
    p.eq = null;
    p.commitLive = !!f.get('commitLive');
    p.comparables = +f.get('comparables') || 0;
    p.pCrash = +f.get('pCrash')/100;
    return { p: p, T: +f.get('T'), H: +f.get('H'), eq: +f.get('eq')/100 };
  }
  function run(){
    var form = document.getElementById('wf');
    var input = read(form);
    var p = input.p;
    // Equity trend return is a scenario input: override base scenario only.
    var saved = M.SCENARIOS[0].eq;
    M.SCENARIOS[0].eq = input.eq;
    var r = M.evaluate(p, input.T, input.H, { n: 400 });
    M.SCENARIOS[0].eq = saved;
    var rows = M.PATHS.map(function(path){
      var x = r.rows[path.code];
      var inSet = r.choice.eligible.indexOf(path.code) >= 0 ? '' : ' <span class="muted">(not in choice set)</span>';
      return '<tr><td><b>'+path.code+'</b> '+path.name+inSet+'</td><td class="num">'+money(x.primaryMedian)+'</td><td class="num">'+money(x.p10)+' to '+money(x.p90)+'</td><td class="num">'+money(x.worstBlackSwan)+'</td><td class="num">'+money(x.base.liquidAtT)+'</td></tr>';
    }).join('');
    document.getElementById('out').innerHTML =
      '<p><b>Pick under these settings:</b> '+r.choice.pick+' · '+r.choice.notes.join(' ')+'</p>'+
      '<div class="scroll"><table><thead><tr><th>Path</th><th>Primary: median real net</th><th>10th to 90th percentile</th><th>Worst black swan</th><th>Liquid at transfer</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+
      '<p class="muted">Monte Carlo draws: 400. Illustrative; flagged inputs are on the flagged page.</p>';
  }
  document.getElementById('run').addEventListener('click', run);
  document.getElementById('wf').addEventListener('change', run);
  run();
})();
