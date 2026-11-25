(() => {
  const form = document.getElementById('scenario-form');
  if (!form) return;
  const resultMessage = document.getElementById('result-message');
  const resultList = document.getElementById('result-list');
  const resultTitle = document.querySelector('.results-head h3');
  const resultMark = document.querySelector('.result-mark');
  const chart = document.getElementById('outcome-chart');
  const required = ['homeValue','horizon','otherCash','homeGrowth','homeGrowthLow','homeGrowthHigh','expenseInflation','expenseInflationLow','expenseInflationHigh','cpi','cpiLow','cpiHigh','rentGrowth','rentGrowthLow','rentGrowthHigh','saleCost','saleTax','debt','rentSaleTax','liveSaleTax','rentFlow','imputedRent','aTax','aInsurance','aUtilities','aCapital','bStayFlow','bAFlow','treasuryReturn','treasuryLow','treasuryHigh','stockReturn','stockLow','stockHigh','stageYears','shock','shockLow','shockHigh','cashReturn','cashStockShare'];
  const read = name => {
    const el = form.elements[name];
    if (!el || el.value === '') return null;
    const value = Number(el.value);
    return Number.isFinite(value) ? value : null;
  };
  const money = n => new Intl.NumberFormat('en-US', {style:'currency',currency:'USD',maximumFractionDigits:0}).format(Math.round(n / 10) * 10);
  const clamp = (x,lo,hi) => Math.max(lo,Math.min(hi,x));
  const cashSeries = (amount,H,cashReturn,flowGrowth) => {
    let total=0;
    for(let y=0;y<H;y++) total += amount*Math.pow(1+flowGrowth,y)*Math.pow(1+cashReturn,H-1-y);
    return total;
  };
  const add = (name,values,description,max) => {
    const [minimum,base,maximum]=values;
    const width=n=>max>0?clamp(n/max*100,3,100):3;
    const row=document.createElement('div');row.className='result-item';
    const top=document.createElement('div');top.className='result-item-top';
    const title=document.createElement('strong');title.textContent=name;
    const amount=document.createElement('b');amount.textContent=money(base);
    top.append(title,amount);
    const text=document.createElement('p');text.textContent=`Range ${money(minimum)}–${money(maximum)} · base ${money(base)}. ${description}`;
    const bar=document.createElement('div');bar.className='range-bar';
    const band=document.createElement('i');
    const start=clamp(width(minimum),0,100), end=clamp(width(maximum),start,100), marker=clamp(width(base),start,end);
    band.style.left=`${start}%`;band.style.width=`${Math.max(1,end-start)}%`;bar.append(band);
    const pin=document.createElement('b');pin.style.left=`${marker}%`;bar.append(pin);
    row.append(top,text,bar);resultList.append(row);
  };
  const resetView=()=>{
    resultTitle.textContent='Waiting for complete inputs';resultMark.textContent='—';
    resultMessage.textContent='No projection is shown until all required fields are supplied. This avoids silently filling missing facts with assumptions.';
    resultList.hidden=true;resultList.replaceChildren();
    chart.querySelector('.chart-top span:last-child').textContent='Not computed';
    chart.querySelector('.chart-empty').innerHTML='Enter low / base / high assumptions to plot a sensitivity band.<br><span>A range is not a probability distribution.</span>';
  };
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const absent=required.filter(name=>read(name)===null);
    if(absent.length){
      resultTitle.textContent='Waiting for complete inputs';resultMark.textContent='—';
      resultMessage.textContent=`Missing ${absent.length} required input${absent.length===1?'':'s'}. No values are defaulted or guessed.`;
      resultList.hidden=true;resultList.replaceChildren();
      chart.querySelector('.chart-top span:last-child').textContent='Not computed';
      chart.querySelector('.chart-empty').innerHTML='Enter low / base / high assumptions to plot a sensitivity band.<br><span>A range is not a probability distribution.</span>';
      return;
    }
    const d=Object.fromEntries(required.map(name=>[name,read(name)]));
    const H=Math.floor(d.horizon),phase=Math.floor(d.stageYears);
    const rangePairs=[['homeGrowthLow','homeGrowth','homeGrowthHigh'],['expenseInflationLow','expenseInflation','expenseInflationHigh'],['cpiLow','cpi','cpiHigh'],['rentGrowthLow','rentGrowth','rentGrowthHigh'],['treasuryLow','treasuryReturn','treasuryHigh'],['stockLow','stockReturn','stockHigh'],['shockLow','shock','shockHigh']];
    const badRange=rangePairs.some(([lo,base,hi])=>d[lo]>d[base]||d[base]>d[hi]);
    if(H<1||H>50||d.saleCost<0||d.saleCost>100||d.cashStockShare<0||d.cashStockShare>100||phase<1||phase>=H||badRange){
      resultTitle.textContent='Review input ranges';resultMark.textContent='!';
      resultMessage.textContent='Horizon must be 1–50; sale friction / stock allocation must be 0–100%; staging must be shorter than the horizon; and each low / base / high range must be in ascending order. No result was computed.';
      resultList.hidden=true;resultList.replaceChildren();return;
    }
    const scenario=(homePct,expenseInflationPct,cpiPct,rentGrowthPct,treasuryPct,stockPct,shockPct)=>{
      const house=1+homePct/100,stock=1+stockPct/100,cash=1+d.cashReturn/100,treasury=1+treasuryPct/100,shock=1+shockPct/100;
      const inflation=1+cpiPct/100,rentGrowth=1+rentGrowthPct/100;
      if([house,stock,cash,treasury,shock,inflation,rentGrowth].some(x=>x<0))return null;
      const saleFactor=1-d.saleCost/100;
      const netNow=Math.max(0,d.homeValue*saleFactor-d.saleTax-d.debt);
      const homeAtHorizon=d.homeValue*Math.pow(house,H)*saleFactor;
      const rentExit=Math.max(0,homeAtHorizon-d.rentSaleTax-d.debt);
      const liveExit=Math.max(0,homeAtHorizon-d.liveSaleTax-d.debt);
      const liquidNow=d.otherCash*shock*Math.pow(stock,H-1);
      const taxA=d.aTax, insA=d.aInsurance, utilitiesA=d.aUtilities, capitalA=d.aCapital;
      const ownerCosts=cashSeries(taxA+insA+utilitiesA+capitalA,H,cash,expenseInflationPct/100);
      const sold=(netNow+d.otherCash)*shock*Math.pow(stock,H-1)+cashSeries(d.bStayFlow,H,cash,rentGrowthPct/100);
      const bStay=cashSeries(d.bStayFlow,H,cash,rentGrowthPct/100);
      const stagedDuringShock=netNow*Math.pow(treasury,phase)*Math.pow(stock,H-phase)+liquidNow+bStay;
      const stagedAtEntry=netNow*Math.pow(treasury,phase)*shock*Math.pow(stock,H-phase-1)+liquidNow+bStay;
      const rental=rentExit+cashSeries(d.rentFlow,H,cash,rentGrowthPct/100)+bStay+liquidNow;
      const live=liveExit+cashSeries(d.imputedRent,H,cash,rentGrowthPct/100)-ownerCosts+cashSeries(d.bAFlow,H,cash,rentGrowthPct/100)+liquidNow;
      const stockShare=d.cashStockShare/100;
      const stagedCashAtEntry=d.otherCash*(1-stockShare)*Math.pow(treasury,phase)*shock*Math.pow(stock,H-phase-1);
      const nowCash=d.otherCash*stockShare*shock*Math.pow(stock,H-1);
      const mixed=rentExit+cashSeries(d.rentFlow,H,cash,rentGrowthPct/100)+bStay+stagedCashAtEntry+nowCash;
      const realDeflator=Math.pow(inflation,H);
      return [sold,stagedDuringShock,stagedAtEntry,rental,live,mixed].map(value=>value/realDeflator);
    };
    const low=scenario(d.homeGrowthLow,d.expenseInflationHigh,d.cpiHigh,d.rentGrowthLow,d.treasuryLow,d.stockLow,d.shockLow);
    const base=scenario(d.homeGrowth,d.expenseInflation,d.cpi,d.rentGrowth,d.treasuryReturn,d.stockReturn,d.shock);
    const high=scenario(d.homeGrowthHigh,d.expenseInflationLow,d.cpiLow,d.rentGrowthHigh,d.treasuryHigh,d.stockHigh,d.shockHigh);
    if(!low||!base||!high){
      resultTitle.textContent='Review return inputs';resultMark.textContent='!';resultMessage.textContent='Every annual growth, return, inflation rate and entry shock must be at least -100%. No result was computed.';resultList.hidden=true;resultList.replaceChildren();return;
    }
    const names=[
      ['Sell A in transfer year → invest now (crash at transfer)','Immediate stock entry takes the entered drawdown at transfer; B cash flow assumes household stays at B.'],
      [`Stage A proceeds ${phase} years → enter after transfer-year crash`,`A proceeds stay in Treasuries through the one-time shock and then enter stocks; assumes post-entry return, not a historical recovery sequence.`],
      [`Stage A proceeds ${phase} years → crash at staged stock entry`,`Shows delayed-entry risk: a drawdown arriving as Treasuries mature hits the staged amount. Separate inherited cash is invested now.`],
      ['Rent A; stay at B; sell A at horizon','A rent and B net cash flows are escalated at the rent-growth assumption; future sale tax entered separately.'],
      ['Live in A; model B occupancy change; sell at horizon','Imputed rent grows with rent assumption; A property tax, insurance, utilities and capital reserve grow with expense inflation.'],
      [`Mixed: rent A + ${Math.round(d.cashStockShare)}% of liquid cash in stocks now`,'Retains A as a rental; separate net inherited cash is divided between stocks now and a Treasury phase; staged cash is exposed to the entry-shock case.']
    ]; 
    const max=Math.max(1,...low,...base,...high);
    resultList.replaceChildren();
    names.forEach(([name,description],i)=>{
      const minimum=Math.min(low[i],base[i],high[i]);
      const maximum=Math.max(low[i],base[i],high[i]);
      add(name,[minimum,base[i],maximum],description,max);
    });
    resultList.hidden=false;resultTitle.textContent=`${H}-year real outcomes (transfer-year dollars)`;resultMark.textContent='✓';
    resultMessage.textContent=`Each range combines user-entered home growth, expense inflation, rent growth, Treasury yield, stock return and drawdown. The transfer-year-crash staging row assumes A sale proceeds remain in Treasuries through the shock; the staged-entry-crash row assumes the drawdown occurs as the Treasury phase ends. The low case uses higher expense / general inflation and lower rent-growth assumptions; the high case reverses them. Values are real purchasing-power estimates in transfer-year dollars, rounded to $10. These are not historical 1929 / 2008 sequences, probability percentiles, tax calculations, forecasts or recommendations.`;
    chart.querySelector('.chart-top span:last-child').textContent='Real sensitivity ranges';
    chart.querySelector('.chart-empty').innerHTML='Band = minimum / maximum of the combined low/base/high cases; marker = base case.<br><span>Not a probability distribution. Annual tax estimates / cash flows remain user inputs.</span>';
  });
  form.addEventListener('reset',()=>setTimeout(resetView,0));
  document.querySelectorAll('.nav-link').forEach(link=>link.addEventListener('click',()=>{
    document.querySelectorAll('.nav-link').forEach(item=>item.classList.remove('active'));link.classList.add('active');
  }));
})();
