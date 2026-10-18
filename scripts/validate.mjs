import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDocument } from 'yaml';
import { decode } from '@toon-format/toon';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const names = ['ts-context', 'ts-elon', 'ts-handoff', 'ts-plan', 'ts-review', 'ts-rootcause', 'ts-think', 'ts-verify'];
const allowed = new Set(['name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools']);

export function validateSkill(directory) {
  const entry = readFileSync(path.join(directory, 'SKILL.md'), 'utf8');
  const match = entry.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  assert.ok(match, 'SKILL.md needs YAML frontmatter');
  const document = parseDocument(match[1], { uniqueKeys: true });
  assert.equal(document.errors.length, 0, 'invalid YAML');
  const meta = document.toJS();
  assert.ok(meta && typeof meta === 'object' && !Array.isArray(meta), 'metadata must be an object');
  for (const key of Object.keys(meta)) assert.ok(allowed.has(key), `unsupported metadata key: ${key}`);
  assert.match(meta.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/);
  assert.ok(meta.name.length <= 64);
  assert.equal(meta.name, path.basename(directory));
  assert.ok(typeof meta.description === 'string' && meta.description.length > 0 && meta.description.length <= 1024);
  assert.equal(meta.license, 'MIT');
  assert.ok(meta.metadata && typeof meta.metadata === 'object' && !Array.isArray(meta.metadata));
  for (const value of Object.values(meta.metadata)) assert.equal(typeof value, 'string');
  const blocks = [...match[2].matchAll(/```toon\r?\n([\s\S]*?)\r?\n```/g)];
  assert.equal(blocks.length, 1, 'entrypoint needs exactly one TOON routing block');
  const routing = decode(blocks[0][1], { strict: true });
  assert.equal(routing.read, 'reference.toon', 'reference must remain inside the installed skill');
  assert.ok(match[2].includes('[reference.toon](reference.toon)'));
  assert.ok(entry.split(/\s+/).length <= 180, 'entrypoint exceeds 180-word discovery budget');
  const reference = readFileSync(path.join(directory, routing.read), 'utf8');
  const data = decode(reference, { strict: true });
  assert.equal(data.skill, meta.name);
  assert.equal(data.version, meta.metadata.version);
  assert.ok(typeof data.purpose === 'string' && data.purpose.length);
  for (const key of ['scope', 'evidence', 'composition', 'unavailable']) {
    assert.ok(typeof data.contract?.[key] === 'string' && data.contract[key].length, `missing contract: ${key}`);
  }
  assert.ok(Array.isArray(data.steps) && data.steps.length);
  for (const step of data.steps) for (const key of ['step', 'action', 'evidence']) {
    assert.ok(typeof step[key] === 'string' && step[key].length, `missing step field: ${key}`);
  }
  assert.ok(data.completion && Object.values(data.completion).every(v => typeof v === 'string' && v.length));
  const bundled = readdirSync(directory, { withFileTypes: true }).filter(e => e.isFile())
    .map(e => readFileSync(path.join(directory, e.name), 'utf8')).join('\n');
  assert.doesNotMatch(bundled, /\/Users\/|\/home\/[A-Za-z]|[A-Z]:\\Users\\|gbrain|ai-fleet|FLEET_/,
    'skill contains a private path or internal integration dependency');
  return { name: meta.name, entryWords: entry.split(/\s+/).length, referenceBytes: Buffer.byteLength(reference) };
}

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(item => {
    if (['node_modules', '.git', '.artifacts'].includes(item.name)) return [];
    const full = path.join(directory, item.name);
    return item.isDirectory() ? walk(full) : [full];
  });
}

export function validateLinks(directory) {
  for (const file of walk(directory).filter(p => p.endsWith('.md'))) {
    for (const [, target] of readFileSync(file, 'utf8').matchAll(/\]\(([^)]+)\)/g)) {
      if (/^(?:https?:|mailto:|#)/.test(target)) continue;
      const relative = decodeURIComponent(target.split('#')[0]);
      assert.ok(relative, `empty link in ${file}`);
      readFileSync(path.resolve(path.dirname(file), relative));
    }
  }
}

export function validateAll(directory = root) {
  const found = readdirSync(path.join(directory, 'skills')).sort();
  assert.deepEqual(found, names);
  const results = found.map(name => validateSkill(path.join(directory, 'skills', name)));
  validateLinks(directory);
  return results;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  for (const result of validateAll()) console.log(`${result.name}: valid; entry ${result.entryWords} words; TOON ${result.referenceBytes} bytes`);
  console.log('8 skills valid; local documentation links resolve');
}
