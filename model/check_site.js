#!/usr/bin/env node
/* Headless smoke-test for site/js/site.js: loads real JSON, runs every renderer,
   fails on exceptions or obviously empty output. Usage: node model/check_site.js [page] */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "site");
const els = {};
function el(id) {
  if (!els[id]) els[id] = {
    innerHTML: "", value: "", dataset: {},
    addEventListener() {}, dispatchEvent() {},
    set textContent(v) { this._t = v; }, get textContent() { return this._t || ""; },
  };
  return els[id];
}
global.document = {
  body: { dataset: { page: process.argv[2] || "index" } },
  getElementById: el,
  addEventListener() {},
};
global.window = { print() {} };
global.Event = class { constructor(t) { this.type = t; } };
global.fetch = async (url) => {
  const p = path.join(ROOT, url);
  const txt = fs.readFileSync(p, "utf8");
  return { json: async () => JSON.parse(txt) };
};

const siteSrc = fs.readFileSync(path.join(ROOT, "js", "site.js"), "utf8");
const testSrc = `
(async () => {
  await Site.load();
  const renders = ["renderIndex","renderDashboard","renderBlackswan","renderData","renderTimeline",
    "renderQuestions","renderSuggestions","renderGlossary","renderFlagged","renderSources","renderBriefing"];
  const pages = { renderIndex:"exec", renderDashboard:"cmp-table", renderBlackswan:"bs-entries",
    renderData:"hist-a", renderTimeline:"tl", renderQuestions:"ql", renderSuggestions:"sg",
    renderGlossary:"gl", renderFlagged:"fl", renderSources:"sr", renderBriefing:"brief" };
  const FNS = { renderIndex, renderDashboard, renderBlackswan, renderData, renderTimeline,
    renderQuestions, renderSuggestions, renderGlossary, renderFlagged, renderSources, renderBriefing };
  let fails = 0;
  for (const fn of renders) {
    try {
      FNS[fn]();
      const html = document.getElementById(pages[fn]).innerHTML;
      if (!html || html.length < 50) { console.error("EMPTY output: " + fn); fails++; }
      else console.log("ok  " + fn + "  (" + html.length + " chars)");
    } catch (e) { console.error("FAIL " + fn + ": " + e.message); fails++; }
  }
  try {
    const out = document.getElementById("wi-out").innerHTML;
    if (!out || out.length < 50) { console.error("EMPTY what-if output"); fails++; }
    else console.log("ok  whatif initial (" + out.length + " chars)");
  } catch (e) { console.error("FAIL whatif: " + e.message); fails++; }
  try {
    const html = document.getElementById("sr").innerHTML;
    const bad = [...html.matchAll(/href="([^"]*)"/g)].map(m => m[1]).filter(u => !u.startsWith("http"));
    if (bad.length) { console.error("bad source hrefs: " + bad.join(",")); fails++; }
    else console.log("ok  sources hrefs all absolute");
    if ((html.match(/<tr>/g) || []).length < 20) { console.error("too few source rows"); fails++; }
    else console.log("ok  source rows >= 20");
  } catch (e) { console.error("FAIL sources: " + e.message); fails++; }
  console.log(fails ? ("FAILED: " + fails) : "ALL CHECKS PASSED");
  process.exit(fails ? 1 : 0);
})();
`;
eval(siteSrc + "\n" + testSrc);
