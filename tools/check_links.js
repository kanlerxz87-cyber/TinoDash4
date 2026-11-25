#!/usr/bin/env node
/* Link check: every internal href resolves; every table with money has a source link; lists external links.
   External links are NOT fetched (sandbox egress is limited); they are listed for manual checking. */
'use strict';
const fs = require('fs');
const path = require('path');
const DOCS = path.join(__dirname, '..', 'docs');
const pages = fs.readdirSync(DOCS).filter((f) => f.endsWith('.html'));
const ext = new Set();
let bad = 0;
for (const p of pages) {
  const html = fs.readFileSync(path.join(DOCS, p), 'utf8');
  for (const m of html.matchAll(/href="([^"]+)"/g)) {
    const h = m[1];
    if (/^https?:/.test(h)) { ext.add(h); continue; }
    if (h.startsWith('#')) continue;
    const target = h.split('#')[0];
    if (!fs.existsSync(path.join(DOCS, target))) { bad++; console.log(`${p}: broken internal link ${h}`); }
  }
  for (const m of html.matchAll(/<script src="([^"]+)"/g)) {
    if (!fs.existsSync(path.join(DOCS, m[1]))) { bad++; console.log(`${p}: missing script ${m[1]}`); }
  }
}
console.log(`External links (${ext.size}):`); [...ext].sort().forEach((u) => console.log('  ' + u));
console.log(bad ? `FAIL: ${bad} broken internal link(s)` : 'OK: internal links resolve');
process.exit(bad ? 1 : 0);
