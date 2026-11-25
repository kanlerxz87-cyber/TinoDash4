#!/usr/bin/env node
/* Privacy scan: fails (exit 1) if personal identifiers appear in published files or tracked files. */
'use strict';
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const ROOT = path.join(__dirname, '..');
// Scope: this session's files only (other sessions' files are checked by their owners; see COORDINATION.md).
const SCOPE = /^(estate-model\/|tools\/|DECISION_RULES\.md$)/;
const files = execSync('git ls-files -co --exclude-standard', { cwd: ROOT }).toString().split('\n').filter(Boolean)
  .filter((f) => SCOPE.test(f) && /\.(html|js|css|md|json)$/.test(f));
const patterns = [
  [/\b9501[0-9]\b|\b9412[0-9]\b/, 'ZIP code'],
  [/\b\d{1,5}\s+[A-Z][a-z]+\s+(Ave|Avenue|St|Street|Rd|Road|Blvd|Way|Ln|Lane|Dr|Drive|Ct|Court|Pl|Place)\b/, 'street address'],
  [/\bAPN\b|\b\d{3}-\d{3}-\d{3}\b/, 'parcel number'],
  [/\b550,?540\b|\b7,?150\b|\b\$?330\b.*water|assessed (value|valuation)[^<]{0,20}\$\s?\d/i, 'private figure'],
  [/@[a-z0-9.-]+\.(com|org|net|gov|edu)/i, 'email address'],
  [/\b(Mr|Ms|Mrs)\.\s+[A-Z]/, 'honorific name'],
];
let bad = 0;
for (const f of files) {
  if (f === 'tools/privacy_check.js') continue;
  const text = fs.readFileSync(path.join(ROOT, f), 'utf8');
  text.split('\n').forEach((line, i) => {
    for (const [re, label] of patterns) {
      if (re.test(line)) { bad++; console.log(`${f}:${i + 1}: ${label}: ${line.trim().slice(0, 120)}`); }
    }
  });
}
console.log(bad ? `FAIL: ${bad} hit(s)` : `OK: ${files.length} files scanned, no personal identifiers found`);
process.exit(bad ? 1 : 0);
