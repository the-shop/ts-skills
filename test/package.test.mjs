import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cpSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { decode, encode } from '@toon-format/toon';
import { root, names, validateSkill, validateAll } from '../scripts/validate.mjs';

function temporarySkill(t, name = 'ts-rootcause') {
  const temp = mkdtempSync(path.join(tmpdir(), 'ts skills test '));
  t.after(() => rmSync(temp, { recursive: true, force: true }));
  const directory = path.join(temp, name);
  cpSync(path.join(root, 'skills', name), directory, { recursive: true });
  return directory;
}

test('the complete distribution validates without private dependencies', () => assert.equal(validateAll().length, 8));
for (const name of names) {
  test(`${name} installs independently in a relocated path with spaces`, t => {
    const directory = temporarySkill(t, name);
    assert.equal(validateSkill(directory).name, name);
    const text = readFileSync(path.join(directory, 'reference.toon'), 'utf8');
    assert.deepEqual(decode(encode(decode(text))), decode(text));
  });
}
test('unsupported trigger metadata is rejected', t => {
  const directory = temporarySkill(t);
  const file = path.join(directory, 'SKILL.md');
  writeFileSync(file, readFileSync(file, 'utf8').replace('license: MIT', 'license: MIT\ntriggers: [debug]'));
  assert.throws(() => validateSkill(directory), /unsupported metadata key/);
});
test('missing reference fails instead of silently treating the entrypoint as complete', t => {
  const directory = temporarySkill(t);
  rmSync(path.join(directory, 'reference.toon'));
  assert.throws(() => validateSkill(directory), /ENOENT/);
});
test('references cannot escape the individually installed skill', t => {
  const directory = temporarySkill(t);
  const file = path.join(directory, 'SKILL.md');
  writeFileSync(file, readFileSync(file, 'utf8').replace('read: "reference.toon"', 'read: "../reference.toon"'));
  assert.throws(() => validateSkill(directory), /inside the installed skill/);
});
test('truncated TOON tables fail strict decoding', t => {
  const directory = temporarySkill(t);
  const file = path.join(directory, 'reference.toon');
  writeFileSync(file, readFileSync(file, 'utf8').replace('steps[7]', 'steps[8]'));
  assert.throws(() => validateSkill(directory));
});
test('Windows line endings are accepted without changing decoded instructions', t => {
  const directory = temporarySkill(t);
  for (const name of ['SKILL.md', 'reference.toon']) {
    const file = path.join(directory, name);
    writeFileSync(file, readFileSync(file, 'utf8').replaceAll('\n', '\r\n'));
  }
  assert.equal(validateSkill(directory).name, 'ts-rootcause');
});
test('mismatched skill identity is rejected', t => {
  const directory = temporarySkill(t);
  const file = path.join(directory, 'reference.toon');
  writeFileSync(file, readFileSync(file, 'utf8').replace('skill: "ts-rootcause"', 'skill: "ts-verify"'));
  assert.throws(() => validateSkill(directory));
});
