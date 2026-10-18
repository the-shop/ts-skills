import assert from 'node:assert/strict';
import { test } from 'node:test';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { root } from '../scripts/validate.mjs';

const python = ['python3', 'python', 'py'].find(cmd => {
  const r = spawnSync(cmd, ['-c', 'import sys; assert sys.version_info >= (3, 8)'], { encoding: 'utf8' });
  return r.status === 0;
});

test('ts-handoff merge_facts.py passes its Python suite', () => {
  assert.ok(python, 'Python 3.8+ is required to test merge_facts.py');
  const r = spawnSync(python, ['-I', '-B', '-m', 'unittest', 'discover', '-s', path.join(root, 'test', 'python'), '-v'],
    { encoding: 'utf8', env: { ...process.env, PYTHON_COLORS: '0', NO_COLOR: '1' } });
  assert.equal(r.status, 0, r.stderr + r.stdout);
  assert.match(r.stderr, /^Ran 21 tests in /m);
  assert.match(r.stderr, /^OK$/m);
});
