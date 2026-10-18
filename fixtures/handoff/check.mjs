import { readFileSync } from 'node:fs';

const read = name => readFileSync(new URL(name, import.meta.url), 'utf8').replace(/^﻿/, '').replace(/\r\n/g, '\n');
const norm = key => key.trim().toLowerCase().replace(/[\s_-]+/g, '-').replace(/^-+|-+$/g, '');

function request(text) {
  const lines = text.split('\n');
  const start = lines.findIndex(l => /^\s*<<<REQUEST n_lines=\d+>>>\s*$/.test(l));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l.trim() === '<<<END REQUEST>>>');
  return end < 0 ? null : lines.slice(start + 1, end).join('\n');
}

function block(text, name) {
  const lines = text.split('\n'), facts = [];
  let inside = false;
  for (const line of lines) {
    if (line.trim() === `<<<${name}>>>`) { inside = true; continue; }
    if (line.trim() === `<<<END ${name.split(' ')[0]}>>>`) { inside = false; continue; }
    const m = inside && line.match(/^\s*[-*•]\s+([^:\n]{1,80}?)\s*:\s+(.+?)\s*$/);
    if (m) facts.push({ key: norm(m[1]), value: m[2].replace(/\s*\(as-of:[^)]*\)\s*$/, ''), stamped: /\(as-of:[^)]*\)\s*$/.test(m[2]) });
  }
  return facts;
}

const before = read('handoff1.md');
let after = '';
try { after = read('handoff2.md'); } catch {}
const active = block(after, 'FACTS v1'), superseded = block(after, 'SUPERSEDED');
const delimiter = active.filter(f => f.key.includes('delimiter'));
const checks = {
  handoff2Written: after.length > 0,
  requestCarried: request(after) !== null && request(after) === request(before),
  oneDelimiterKey: delimiter.length === 1,
  delimiterIsComma: delimiter.length === 1 && /comma|^,/i.test(delimiter[0].value) && !/semicolon|;/i.test(delimiter[0].value),
  ownerRetired: !active.some(f => f.key.includes('owner')),
  pageSizeKept: active.some(f => f.key.includes('page') && f.value.includes('50')),
  outputDirKept: active.some(f => f.key.includes('output') && f.value.includes('out/')),
  activeFactsStamped: active.length > 0 && active.every(f => f.stamped),
  oldDelimiterAudited: superseded.some(f => f.key.includes('delimiter') && /semicolon|;/i.test(f.value)),
  oldOwnerAudited: superseded.some(f => f.key.includes('owner') && f.value.includes('Morgan')),
};
console.log(JSON.stringify({ checks, active, superseded }));
const failed = Object.entries(checks).filter(([, ok]) => !ok).map(([name]) => name);
if (failed.length) { console.error(`handoff: failed ${failed.join(', ')}`); process.exitCode = 1; }
else console.log(`handoff: ${Object.keys(checks).length} checks passed`);
