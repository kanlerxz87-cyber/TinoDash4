/* TinoDash4 — shared helpers. No dependencies, no tracking, no network calls beyond this
   site's own files. The pages themselves are static HTML; pages.js only adds the charts,
   the what-if lookups, sorting and local-only ticks. */
(function () {
  "use strict";
  const T = (window.TINO = window.TINO || {});
  const cache = {};
  const nf = new Intl.NumberFormat("en-US");

  /* The JSON copies under data/ exist for tooling and tests; the rendered pages do not
     depend on fetch, so they work from a file:// copy as well as from GitHub Pages. */
  T.load = async function (name) {
    if (cache[name]) return cache[name];
    const r = await fetch("data/" + name + ".json", { cache: "no-store" });
    if (!r.ok) throw new Error(name + ": " + r.status);
    cache[name] = await r.json();
    return cache[name];
  };

  T.money = function (v, opt) {
    opt = opt || {};
    if (v === null || v === undefined) return '<span class="na">not verified</span>';
    const s = Math.abs(Math.round(v));
    const str = opt.compact && s >= 1e6 ? (s / 1e6).toFixed(s >= 1e7 ? 0 : 1) + "M"
              : opt.compact && s >= 1e3 ? (s / 1e3).toFixed(0) + "k"
              : nf.format(s);
    return (v < 0 ? "-" : "") + "$" + str;
  };
  T.pct = function (v, dp) {
    if (v === null || v === undefined) return '<span class="na">not verified</span>';
    return (v * 100).toFixed(dp === undefined ? 2 : dp) + "%";
  };
  T.num = function (v, dp) {
    if (v === null || v === undefined) return '<span class="na">not verified</span>';
    return dp === undefined ? nf.format(v) : Number(v).toFixed(dp);
  };
  T.esc = function (s) {
    return String(s === null || s === undefined ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  };
  T.mk = function (n, a) {
    const e = document.createElementNS("http://www.w3.org/2000/svg", n);
    for (const k in a) e.setAttribute(k, a[k]);
    return e;
  };
  T.on = function (id, ev, fn) {
    const e = typeof id === "string" ? document.getElementById(id) : id;
    if (e) e.addEventListener(ev, fn);
  };
  T.fill = function (id, html) {
    const e = typeof id === "string" ? document.getElementById(id) : id;
    if (e) e.innerHTML = html;
    return e;
  };
})();
