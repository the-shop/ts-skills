import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { root } from './validate.mjs';

const [harness, caseName, model] = process.argv.slice(2);
const scenarios = JSON.parse(readFileSync(path.join(root, 'test/scenarios.json'), 'utf8'));
assert.ok(['claude', 'codex', 'grok'].includes(harness) && scenarios[caseName],
  'Usage: node scripts/smoke.mjs <claude|codex|grok> <diagnosis|implementation|plan|review|handoff> [model]');
const scenario = scenarios[caseName];
const directory = mkdtempSync(path.join(tmpdir(), `ts-skills-${harness}-${caseName}-`));
const work = path.join(directory, 'work');
cpSync(path.join(root, 'fixtures', ['diagnosis', 'implementation'].includes(caseName) ? 'checkout' : caseName), work, { recursive: true });
for (const name of scenario.skills) cpSync(path.join(root, 'skills', name), path.join(work, 'skills', name), { recursive: true });
// SKILL.md, reference.toon, then any other skill files by name, so two-file skills keep their earlier hashes.
const skillFiles = name => ['SKILL.md', 'reference.toon', ...readdirSync(path.join(work, 'skills', name), { withFileTypes: true })
  .filter(e => e.isFile() && !['SKILL.md', 'reference.toon'].includes(e.name)).map(e => e.name).sort()];
const skillHash = name => skillFiles(name).reduce((h, f) => h.update(readFileSync(path.join(work, 'skills', name, f))),
  createHash('sha256')).digest('hex');
const skillHashes = Object.fromEntries(scenario.skills.map(name => [name, skillHash(name)]));
const snapshots = Object.fromEntries(readdirSync(work, { withFileTypes: true }).filter(e => e.isFile())
  .map(e => [e.name, readFileSync(path.join(work, e.name), 'utf8')]));
const prompt = `Use the skill entrypoints listed below from this checkout, not similarly named global skills. Read each entrypoint and follow its reference. These are ordinary readable instruction files; use the tools available in this harness.\n\n${scenario.skills.map(n => `skills/${n}/SKILL.md`).join('\n')}\n\nTask:\n${scenario.task}`;
writeFileSync(path.join(directory, 'prompt.txt'), prompt);
let args;
if (harness === 'claude') args = ['-p', prompt, '--setting-sources', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
  '--no-session-persistence', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Bash,Edit,Write', '--output-format', 'stream-json', '--verbose'];
if (harness === 'codex') args = ['exec', '--ignore-user-config', '--ignore-rules', '--skip-git-repo-check', '--ephemeral',
  '--sandbox', 'workspace-write', '-c', 'model_reasoning_effort="medium"', '--json', '--output-last-message', path.join(directory, 'final.txt'), prompt];
if (harness === 'grok') args = ['--prompt-file', path.join(directory, 'prompt.txt'), '--output-format', 'streaming-json',
  '--disable-web-search', '--no-subagents', '--max-turns', '30', '--permission-mode', 'acceptEdits'];
if (model) args.push('--model', model);
const started = Date.now();
const child = spawn(harness, args, { cwd: work, env: { ...process.env, AGENT_BUS: 'off', FLEET_SKILL_GATE: 'off',
  FLEET_EDIT_GUARD: 'off', FLEET_READ_GUARD: 'off', FLEET_SKILL_ROUTER: 'off' }, stdio: ['ignore', 'pipe', 'pipe'] });
let stdout = '', stderr = '', timedOut = false;
child.stdout.on('data', d => { stdout += d; });
child.stderr.on('data', d => { stderr += d; });
const timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); }, 300000);
const exit = await new Promise((resolve, reject) => { child.on('error', reject); child.on('close', resolve); });
clearTimeout(timer);
writeFileSync(path.join(directory, 'stdout.log'), stdout);
writeFileSync(path.join(directory, 'stderr.log'), stderr);
let final = '', reportedModel = model || 'harness-default';
if (harness === 'claude') {
  try {
    const events = stdout.split('\n').filter(Boolean).map(line => JSON.parse(line));
    const r = events.findLast(event => event.type === 'result');
    final = r?.result || '';
    reportedModel = Object.keys(r?.modelUsage || {}).join(',') || reportedModel;
  }
  catch { final = ''; }
} else if (harness === 'codex') {
  try { final = readFileSync(path.join(directory, 'final.txt'), 'utf8'); } catch {}
} else {
  const segments = []; let current = '';
  for (const line of stdout.split('\n')) {
    let event; try { event = JSON.parse(line); } catch { continue; }
    if (event.type === 'end') reportedModel = Object.keys(event.modelUsage || {}).join(',') || reportedModel;
    if (event.type === 'text') current += typeof event.data === 'string' ? event.data : '';
    else if (!['thought', 'end'].includes(event.type) && current.trim()) { segments.push(current); current = ''; }
  }
  if (current.trim()) segments.push(current);
  final = segments.at(-1) || '';
}
writeFileSync(path.join(directory, 'final.txt'), final);
const changed = Object.keys(snapshots).filter(name => {
  try { return readFileSync(path.join(work, name), 'utf8') !== snapshots[name]; } catch { return true; }
});
const extraFiles = readdirSync(work, { withFileTypes: true }).filter(e => e.isFile() && !(e.name in snapshots)).map(e => e.name);
let fixtureCheck = null;
if (['implementation', 'handoff'].includes(caseName)) fixtureCheck = spawnSync(process.execPath, ['check.mjs'], { cwd: work, encoding: 'utf8' });
const behavior = caseName === 'implementation'
  ? fixtureCheck.status === 0 && changed.length === 1 && changed[0] === 'pricing.mjs' && extraFiles.length === 0
  : caseName === 'handoff'
    ? fixtureCheck.status === 0 && changed.length === 0 && extraFiles.includes('handoff2.md')
      && extraFiles.every(name => name === 'handoff2.md' || /draft/i.test(name))
    : changed.length === 0 && extraFiles.length === 0;
const skillsUnchanged = scenario.skills.every(name => {
  try { return skillHash(name) === skillHashes[name]; } catch { return false; }
});
const result = { harness, case: caseName, reportedModel, exit, timedOut, elapsedSeconds: Math.round((Date.now() - started) / 1000),
  changed, extraFiles, fixtureCheck: fixtureCheck && { exit: fixtureCheck.status, stdout: fixtureCheck.stdout, stderr: fixtureCheck.stderr },
  finalWords: final.trim().split(/\s+/).filter(Boolean).length, mechanicalPass: exit === 0 && !timedOut && behavior && skillsUnchanged && final.trim().length > 0,
  humanReviewRequired: true, skillsUnchanged, skillHashes, directory };
writeFileSync(path.join(directory, 'result.json'), JSON.stringify(result, null, 2) + '\n');
const artifacts = path.join(root, '.artifacts'); mkdirSync(artifacts, { recursive: true });
writeFileSync(path.join(artifacts, `${harness}-${caseName}.json`), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
process.exitCode = result.mechanicalPass ? 0 : 1;
