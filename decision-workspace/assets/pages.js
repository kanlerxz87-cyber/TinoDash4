/* TinoDash4 — page behaviour: charts, the what-if grid lookup, sorting, local-only toggles.
   Progressive enhancement only: every table is already in the HTML this script loads into. */
(function () {
  "use strict";
  const T = window.TINO, D = window.TINO_DATA || {};
  const esc = T.esc;
  const nf = new Intl.NumberFormat("en-US");
  const money = (v) => (v === null || v === undefined)
    ? '<span class="na">not verified</span>'
    : (v < 0 ? "-" : "") + "$" + nf.format(Math.abs(Math.round(v)));

  /* ------------------------------------------------------------ charts ---- */
  function svgHost(sel) {
    const hosts = document.querySelectorAll(sel);
    return hosts.length ? hosts : null;
  }
  function makeChart(host, build) {
    if (!host) return;
    const W = 960;
    try { build(host, W); } catch (err) { host.innerHTML = '<p class="small">Chart unavailable: ' + esc(err.message) + "</p>"; }
  }

  function whisker(host, W) {
    const rows = (D.rows12 || []).slice().sort((a, b) => b.score - a.score);
    const rowH = 24, H = rows.length * rowH + 42, x0 = 270;
    let lo = Infinity, hi = -Infinity;
    rows.forEach(function (r) { lo = Math.min(lo, r.p10); hi = Math.max(hi, r.p90); });
    lo = Math.max(0, lo * 0.85); hi *= 1.03;
    const sc = (v) => x0 + (v - lo) / (hi - lo) * (W - x0 - 20);
    const s = T.mk("svg", { viewBox: "0 0 " + W + " " + H });
    [0, 0.25, 0.5, 0.75, 1].forEach(function (f) {
      const v = lo + (hi - lo) * f;
      s.appendChild(T.mk("line", { x1: sc(v), x2: sc(v), y1: 6, y2: H - 24, class: "axis" }));
      const t = T.mk("text", { x: sc(v), y: H - 10, "text-anchor": "middle", class: "lbl" });
      t.textContent = money(v).replace(/\$0/g, "$0");
      s.appendChild(t);
    });
    rows.forEach(function (r, i) {
      const y = 10 + i * rowH;
      s.appendChild(T.mk("rect", { x: sc(r.p10), y: y + 4, width: Math.max(2, sc(r.p90) - sc(r.p10)),
        height: 10, class: "bar" + (r.id === rows[0].id ? " hl" : ""), opacity: 0.7 }));
      s.appendChild(T.mk("line", { x1: sc(r.p50), x2: sc(r.p50), y1: y, y2: y + 18, class: "whisker" }));
      s.appendChild(T.mk("line", { x1: sc(r.w30), x2: sc(r.w30), y1: y + 2, y2: y + 16,
        stroke: "#111", "stroke-width": 2 }));
      const t = T.mk("text", { x: 4, y: y + 13, class: "lbl", "font-size": 11, fill: "#16181d" });
      t.textContent = r.id + "  " + (D.short[r.id] || r.name).slice(0, 44);
      s.appendChild(t);
    });
    host.innerHTML = ""; host.appendChild(s);
  }

  function bars(host, W, pairs, opt) {
    opt = opt || {};
    const H = 300, pad = 46, bw = Math.max(6, Math.min(46, (W - 60) / pairs.length - 6));
    let lo = Math.min(0, ...pairs.map(p => p[1])), hi = Math.max(0, ...pairs.map(p => p[1]));
    pairs.forEach(p => { if (p[2] !== undefined) { lo = Math.min(lo, p[2]); hi = Math.max(hi, p[2]); } });
    const sc = (v) => H - pad - (v - lo) / (hi - lo || 1) * (H - pad - 20);
    const s = T.mk("svg", { viewBox: "0 0 " + W + " " + (H + (opt.labels ? 74 : 0)) });
    s.appendChild(T.mk("line", { x1: 40, x2: W - 10, y1: sc(0), y2: sc(0), class: "axis" }));
    pairs.forEach(function (p, i) {
      const x = 46 + i * ((W - 70) / pairs.length);
      const y0 = sc(Math.max(0, p[1])), y1 = sc(Math.min(0, p[1]));
      s.appendChild(T.mk("rect", { x: x, y: y0, width: bw, height: Math.max(1, y1 - y0),
        class: "bar" + (p[1] < 0 ? " neg" : "") + (p[3] ? " hl" : ""), opacity: 0.85 }));
      if (p[2] !== undefined) {
        s.appendChild(T.mk("rect", { x: x + bw / 2 - 1, y: sc(p[2]), width: 3, height: 3, fill: "#111" }));
      }
      if (opt.labels) {
        const t = T.mk("text", { x: x + bw / 2, y: H - pad + 14, class: "lbl", "text-anchor": i % 2 ? "start" : "end",
          transform: "rotate(38 " + (x + bw / 2) + " " + (H - pad + 14) + ")" });
        t.textContent = p[0];
        s.appendChild(t);
      }
    });
    host.innerHTML = ""; host.appendChild(s);
  }

  function lines(host, W) {
    const pr = D.prop19.rows, H = 320, x0 = 70, y1 = H - 40, y0 = 14;
    const series = [["tax without the exclusion", pr.map(r => r.reassess_tax), "#a1160f"],
                    ["tax with Prop 19", pr.map(r => r.prop19_tax), "#4b6bb5"],
                    ["tax if the Prop 13 base had survived", pr.map(r => r.keep13_tax), "#1d7a46"]];
    let hi = 0;
    series.forEach(s => s[1].forEach(v => { hi = Math.max(hi, v); }));
    const sx = i => x0 + i / (pr.length - 1) * (W - x0 - 16);
    const sy = v => y1 - v / hi * (y1 - y0);
    const s = T.mk("svg", { viewBox: "0 0 " + W + " " + H });
    for (let k = 0; k < 5; k++) {
      const v = hi * k / 4, y = sy(v);
      s.appendChild(T.mk("line", { x1: x0, x2: W - 16, y1: y, y2: y, class: "axis" }));
      const t = T.mk("text", { x: x0 - 6, y: y + 3, "text-anchor": "end", class: "lbl" });
      t.textContent = money(v);
      s.appendChild(t);
    }
    series.forEach(function (ser, si) {
      let d = "";
      ser[1].forEach(function (v, i) { d += (i ? " L" : "M") + sx(i).toFixed(1) + " " + sy(v).toFixed(1); });
      s.appendChild(T.mk("path", { d: d, fill: "none", stroke: ser[2], "stroke-width": 2 }));
      const t = T.mk("text", { x: x0 + 8, y: y0 + 14 + si * 15, class: "lbl", fill: ser[2], "font-size": 11 });
      t.textContent = ser[0];
      s.appendChild(t);
    });
    [0, Math.floor(pr.length / 2), pr.length - 1].forEach(function (i) {
      const t = T.mk("text", { x: sx(i), y: y1 + 16, class: "lbl", "text-anchor": i === 0 ? "start" : "end" });
      t.textContent = pr[i].year;
      s.appendChild(t);
    });
    host.innerHTML = ""; host.appendChild(s);
  }

  function rolling(host, W) {
    const ser = D.rolling.series, H = 260, pad = 34;
    let lo = Math.min(0, ...ser.map(p => p[1])), hi = Math.max(0, ...ser.map(p => p[1]));
    const sy = v => H - pad - (v - lo) / (hi - lo) * (H - pad - 16);
    const bw = (W - 60) / ser.length;
    const s = T.mk("svg", { viewBox: "0 0 " + W + " " + H });
    s.appendChild(T.mk("line", { x1: 30, x2: W - 10, y1: sy(0), y2: sy(0), class: "axis" }));
    ser.forEach(function (p, i) {
      const x = 30 + i * bw, y = p[1] >= 0 ? sy(p[1]) : sy(0), h = Math.abs(sy(p[1]) - sy(0));
      s.appendChild(T.mk("rect", { x: x, y: y, width: Math.max(1.5, bw - 0.6), height: Math.max(0.6, h),
        class: "bar" + (p[1] < 0 ? " neg" : ""), opacity: 0.8 }));
    });
    [-2, 0, 5, 10, 15, 20].forEach(function (v) {
      if (v < lo || v > hi) return;
      const t = T.mk("text", { x: 26, y: sy(v) + 3, "text-anchor": "end", class: "lbl" });
      t.textContent = v + "%";
      s.appendChild(t);
    });
    const a = T.mk("text", { x: 30, y: H - 8, class: "lbl" });
    a.textContent = "every overlapping ten-year window from " + ser[0][0] + " to " + ser[ser.length - 1][0] +
      "  (bars below zero are decades that lost money in nominal terms)";
    s.appendChild(a);
    host.innerHTML = ""; host.appendChild(s);
  }

  function hist(host, W) {
    const order = (D.rows12 || []).slice().sort((a, b) => b.score - a.score).slice(0, 5);
    const H = 250, x0 = 20, x1 = W - 20, y0 = 16, y1 = H - 40;
    let lo = Infinity, hi = -Infinity;
    order.forEach(r => r.dist.forEach(v => { lo = Math.min(lo, v); hi = Math.max(hi, v); }));
    const sx = v => x0 + (v - lo) / (hi - lo || 1) * (x1 - x0);
    const nb = 50;
    const cols = ["#1d7a46", "#4b6bb5", "#8a5300", "#a1160f", "#5b3a9c"];
    const s = T.mk("svg", { viewBox: "0 0 " + W + " " + H });
    s.appendChild(T.mk("line", { x1: x0, x2: x1, y1: y1, y2: y1, class: "axis" }));
    order.forEach(function (r, ri) {
      const bins = new Array(nb).fill(0);
      const step = (hi - lo) / nb;
      r.dist.forEach(function (v) { bins[Math.min(nb - 1, Math.floor((v - lo) / step))]++; });
      const mx = Math.max(...bins) || 1;
      let d = "M" + x0 + " " + y1;
      bins.forEach(function (v, i) {
        const xa = lo + step * i, xb = lo + step * (i + 1);
        d += " L" + sx(xa).toFixed(1) + " " + (y1 - v / mx * (y1 - y0)).toFixed(1) +
          " L" + sx(xb).toFixed(1) + " " + (y1 - v / mx * (y1 - y0)).toFixed(1);
      });
      d += " L" + x1 + " " + y1 + " Z";
      s.appendChild(T.mk("path", { d: d, fill: cols[ri], opacity: 0.22, stroke: cols[ri], "stroke-width": 1.3 }));
      const t = T.mk("text", { x: x0 + 4 + ri * 150, y: 12, class: "lbl", fill: cols[ri], "font-size": 11 });
      t.textContent = r.id + " " + (D.short[r.id] || "").slice(0, 20);
      s.appendChild(t);
    });
    [0, 0.5, 1].forEach(function (f) {
      const v = lo + (hi - lo) * f;
      const t = T.mk("text", { x: sx(v), y: y1 + 14, class: "lbl", "text-anchor": f === 0 ? "start" : "end" });
      t.textContent = money(v);
      s.appendChild(t);
    });
    host.innerHTML = ""; host.appendChild(s);
  }

  /* --------------------------------------------------------- what if ---- */
  function keyOf(c) { return [c.home, c.equity, c.rent, c.prop19 ? 1 : 0, c.horizon].join("|"); }
  function findCell(D, home, equity, rent, p19, hz) {
    return D.cells.find(c => c.home === home && c.equity === equity && c.rent === rent &&
      !!c.prop19 === !!p19 && c.horizon === +hz);
  }
  function wireWhatIf() {
    if (document.body.dataset.page !== "what-if") return;
    const dials = ["home", "equity", "rent"];
    const K = { home: D.dials.home, equity: D.dials.equity, rent: D.dials.rent };
    function read() {
      const o = {};
      dials.forEach(d => { o[d] = K[d][+document.getElementById("d-" + d).value]; });
      o.prop19 = document.getElementById("d-prop19").value === "1";
      o.horizon = +document.getElementById("d-hz").value;
      o.metric = document.getElementById("d-metric").value;
      o.delta = document.getElementById("d-showdelta").checked;
      return o;
    }
    function paint() {
      const o = read();
      dials.forEach(function (d) {
        document.getElementById("v-" + d).textContent = o[d] + " a year";
        document.getElementById("d-" + d).previousElementSibling;
      });
      const cell = findCell(D, o.home, o.equity, o.rent, o.prop19, o.horizon);
      const base = findCell(D, "mid", "mid", "mid", true, o.horizon);
      if (!cell) { document.getElementById("wi").innerHTML = "<p>That combination is not in the published grid.</p>"; return; }
      const mk = o.metric;
      const rows = D.ids.map(id => ({ id: id, v: cell.values[id][mk], base: base.values[id][mk],
                                      name: D.short[id] })).sort((a, b) => b.v - a.v);
      const top = rows[0].v;
      let h = "<table><caption>Scenario: house " + esc(o.home) + ", equity " + esc(o.equity) +
        ", rent " + esc(o.rent) + ", Prop 19 " + (o.prop19 ? "obtained" : "not obtained") +
        ", " + o.horizon + "-year horizon. Figures are real, present-valued at 3.5%, in 2026 dollars" +
        (mk === "n" ? " (this column is nominal at the horizon - not deflated, not present-valued)" : "") + ".</caption>" +
        "<thead><tr><th>Rank</th><th>Path</th><th>In one line</th><th class='num'>Result</th>" +
        "<th class='num'>vs best</th><th class='num'>vs the same path at mid-case</th></tr></thead><tbody>";
      rows.forEach(function (r, i) {
        const dv = r.v - top, db = r.v - r.base;
        h += "<tr" + (i === 0 ? ' class="best"' : "") + "><td>" + (i + 1) + "</td><td><a href='paths.html#" +
          r.id + "'>" + r.id + "</a></td><td>" + esc(r.name) + "</td><td class='num'>" + money(r.v) +
          "</td><td class='num'>" + (i === 0 ? "&mdash;" : money(dv)) + "</td><td class='num'>" +
          (db === 0 ? "&mdash;" : (db > 0 ? "+" : "") + money(db)) + "</td></tr>";
      });
      h += "</tbody></table>";
      document.getElementById("wi").innerHTML = '<div class="wrap short">' + h + "</div>";
      const pairs = rows.map(r => [r.id, r.v, r.base, r === rows[0]]);
      const host = document.querySelector('[data-chart="wiBars"]');
      if (host) bars(host, 960, pairs, { labels: true });
      const flips = rows.filter(r => (r.v > r.base) !== (rows[0].v > rows[0].base)).length;
      const note2 = document.getElementById("flipnote");
      if (note2) note2.textContent = flips
        ? "Moving these dials changes which path leads for " + flips + " of the paths shown, relative to the mid case."
        : "Moving these dials does not change the order of the top path - the conclusion is robust to this scenario.";
    }
    dials.concat(["prop19", "hz", "metric", "showdelta"]).forEach(function (id) {
      const el = document.getElementById("d-" + id) || document.getElementById(id);
      if (el) { el.addEventListener("input", paint); el.addEventListener("change", paint); }
    });
    paint();
  }

  /* ------------------------------------------------- year-by-year table ---- */
  function wireYear() {
    const sel = document.getElementById("psel"), host = document.getElementById("yr");
    if (!sel || !host || !D.yearly) return;
    const cols = [["year", "Year"], ["mode", "Property A status"], ["valueA", "Value of A"],
                  ["assessedA", "Assessed A"], ["taxA", "Property tax A"], ["upkeepA", "Upkeep A"],
                  ["rentA", "Rent A could earn"], ["cashA", "Path cash flow"], ["noiB", "Property B net"],
                  ["taxB", "Property B tax"], ["bOcc", "Living at B?"], ["portfolio", "Invested"],
                  ["wealth", "Household wealth"]];
    function draw() {
      const rows = D.yearly[sel.value] || [];
      let h = "<table><caption>" + esc(D.short[sel.value] || sel.value) +
        " - every year of the path, at the mid case, rounded to $10. A blank means the building was sold " +
        "that year, so there is nothing left to assess.</caption><thead><tr>";
      cols.forEach(function (c) {
        h += "<th" + (c[0] === "year" || c[0] === "mode" || c[0] === "bOcc" ? "" : " class='num'") +
          ">" + c[1] + "</th>";
      });
      h += "</tr></thead><tbody>";
      rows.forEach(function (r) {
        h += "<tr>";
        cols.forEach(function (c) {
          const v = r[c[0]];
          const cell = c[0] === "year" ? v : (c[0] === "mode" || c[0] === "bOcc" ? esc(v) : money(v));
          h += "<td" + (c[0] === "year" || c[0] === "mode" || c[0] === "bOcc" ? "" : " class='num'") +
            ">" + cell + "</td>";
        });
        h += "</tr>";
      });
      h += "</tbody></table>";
      host.innerHTML = '<div class="wrap">' + h + "</div>";
    }
    sel.addEventListener("change", draw);
    const want = location.hash.replace("#", "");
    if (D.yearly[want]) sel.value = want;
    draw();
  }

  /* ------------------------------------------------- local-only choices ---- */
  function wireLocal() {
    const store = "tinodash:" + document.body.dataset.page;
    let saved = {};
    try { saved = JSON.parse(localStorage.getItem(store) || "{}"); } catch (err) { saved = {}; }
    document.querySelectorAll("input.sg, input.ck").forEach(function (el) {
      const k = el.dataset.k;
      if (saved[k]) el.checked = true;
      el.addEventListener("change", function () {
        saved[k] = el.checked;
        try { localStorage.setItem(store, JSON.stringify(saved)); } catch (err) { /* private mode */ }
        const n = document.getElementById("localcount");
        if (n) n.textContent = Object.keys(saved).filter(x => saved[x]).length + " marked in this browser";
      });
    });
    const n = document.getElementById("localcount");
    if (n) n.textContent = Object.keys(saved).filter(x => saved[x]).length + " marked in this browser";
  }

  /* ------------------------------------------------------- sort tables ---- */
  function wireSort() {
    document.querySelectorAll("main table").forEach(function (t) {
      if (t.querySelectorAll("tbody tr").length < 4) return;
      t.querySelectorAll("thead th").forEach(function (th, i) {
        th.title = "Click to sort by " + th.textContent;
        th.style.cursor = "pointer";
        th.addEventListener("click", function () {
          const rows = Array.from(t.querySelectorAll("tbody tr"));
          const dir = th.dataset.dir === "d" ? -1 : 1;
          th.dataset.dir = dir === 1 ? "d" : "a";
          rows.sort(function (a, b) {
            const av = a.cells[i].textContent.trim(), bv = b.cells[i].textContent.trim();
            const an = parseFloat(av.replace(/[^0-9.\-]/g, "")), bn = parseFloat(bv.replace(/[^0-9.\-]/g, ""));
            if (!isNaN(an) && !isNaN(bn)) return dir * (an - bn);
            return dir * av.localeCompare(bv);
          });
          rows.forEach(r => t.querySelector("tbody").appendChild(r));
        });
      });
    });
  }

  /* -------------------------------------------------------------- boot ---- */
  function boot() {
    const page = document.body.dataset.page;
    const charts = {
      "paths": [["#dist", whisker]],
      "projections": [["[data-chart='taxfan']", lines], ["[data-chart='projdist']", hist]],
      "index": [["[data-chart='dist']", whisker]],
      "black-swan": [["[data-chart='rolling']", rolling]],
      "what-if": [],
    };
    Object.keys(D).length && (charts[page] || []).forEach(function (c) {
      makeChart(document.querySelector(c[0]), c[1]);
    });
    wireWhatIf(); wireYear(); wireLocal(); wireSort();
  }
  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
