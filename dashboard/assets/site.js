(function(){
  var el=document.getElementById('whatif-data'); if(!el) return;
  var D=JSON.parse(el.textContent);
  var ry=document.getElementById('ry'), hp=document.getElementById('hp'), out=document.getElementById('whatif-out');
  if(!ry||!hp||!out) return;
  var names={LIVE:'Live in A',RENT:'Rent A',SELL_LUMP:'Sell, lump sum',SELL_P24:'Sell, park 24 months, phase in over 12',SELL_P36:'Sell, park 36 months, phase in over 12',LIVE3_SELL:'Mixed: live 3 years, then sell',RENT3_SELL:'Mixed: rent 3 years, then sell',LIVE3_RENT:'Mixed: live 3 years, then rent'};
  var order=['LIVE','RENT','SELL_LUMP','SELL_P24','SELL_P36','LIVE3_SELL','RENT3_SELL','LIVE3_RENT'];
  D.rent_yields.forEach(function(v,i){var o=document.createElement('option');o.value=i;o.textContent=(v*100).toFixed(2)+'%';if(i===1)o.selected=true;ry.appendChild(o);});
  D.hpa.forEach(function(v,i){var o=document.createElement('option');o.value=i;o.textContent=(v*100).toFixed(1)+'% a year';if(i===1)o.selected=true;hp.appendChild(o);});
  function money(v){return (v<0?'-$':'$')+Math.abs(v).toLocaleString('en-US');}
  function render(){
    var r=parseInt(ry.value,10), h=parseInt(hp.value,10);
    var cell=D.cells.filter(function(c){return c.rent_yield===D.rent_yields[r]&&c.hpa===D.hpa[h];})[0];
    if(!cell){out.textContent='No result for this combination.';return;}
    var best=order.reduce(function(a,b){return cell.paths[b]>cell.paths[a]?b:a;});
    var rows=order.map(function(p){return '<tr'+(p===best?' style="background:#eef8f2"':'')+'><td>'+names[p]+'</td><td>'+money(cell.paths[p])+'</td></tr>';}).join('');
    out.innerHTML='<table><thead><tr><th>Path</th><th>Real financial position, 2050 transfer + 20 years (rounded to $10)</th></tr></thead><tbody>'+rows+'</tbody></table><p class="small">Highest in this combination: '+names[best]+'. The rules still apply (see Rules and pick).</p>';
  }
  ry.addEventListener('change',render); hp.addEventListener('change',render); render();
})();
