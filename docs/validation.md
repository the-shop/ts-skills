# Release evidence

These are packaging and configured-harness smoke checks, not a claim of universal model compliance. Each release section records what ran for that release.

## v0.2.0 — 2026-10-18

v0.2.0 changes only `ts-handoff`. It adds keyed facts and the bundled `merge_facts.py`. The other seven skills are byte-identical to v0.1.0 and keep their 0.1.0 versions and hashes, so their v0.1.0 model checks below still describe the shipped files.

### Package and installation checks

- `npm run check`: all eight skills validated; all 16 tests passed locally on macOS, including the merge script's 21 Python tests.
- The Python suite also passed on Python 3.8, the oldest supported version.
- Two regression tests, for a UTF-8 byte-order mark and for whitespace around the request delimiters, failed against the earlier script (2 failures) and pass now.
- Skills CLI 1.5.23 installed `ts-handoff` for Claude Code from a local checkout. All three files arrived byte-identical, and no `__pycache__` was left behind.
- The fixture check `fixtures/handoff/check.mjs` (12 checks) passed correctly merged briefs: with a byte-order mark and CRLF line endings, and with the comma written bare, quoted, or backticked. An independent review then built 20 briefs from a correct one. All 15 that are clearly wrong fail:
  - a stale rule under a synonym key, or hidden inside another fact;
  - the owner kept under a contact key;
  - a stale fact bullet in the body;
  - a wrong line count, or a request changed by one character;
  - two FACTS blocks, an unterminated block, or a missing stamp.

  Two values that restate the old rule (`comma (previously semicolon)`, `comma, not semicolon`) also fail, by design. The correct brief and its CRLF copy pass. One wrong brief also passes: it states the stale rule only in body prose, which no check reads.
- CI ran Ubuntu, macOS, and Windows with Node.js 20 and 22; this is the first Windows execution of the script. See the [workflow history](https://github.com/the-shop/ts-skills/actions/workflows/validate.yml) for the release commit's run.

### Executed model checks

Each run used `node scripts/smoke.mjs <harness> handoff [model]` on a fresh fixture copy. [Sanitized machine results](model-checks-0.2.0.json) record the `ts-handoff` hash `c6b5f3e56c11123704898209b91b1ed12fe585acc7862d6b77d739b85b2d75d7`. Smoke hashes now cover `SKILL.md`, `reference.toon`, then any other skill files by name; two-file skills hash exactly as before.

| CLI / reported model | Mechanical pass | Read full reference; ran merge with `--prev` | Final words (limit 120) |
| --- | --- | --- | --- |
| Claude Code 2.1.291 / `claude-opus-5-5` | yes | yes | 124 |
| Claude Code 2.1.291 / `claude-sonnet-5-5` | yes | yes | 117 |
| Claude Code 2.1.291 / `claude-haiku-4-5-20251001` | yes | yes | 69 |
| Codex CLI 0.162.1 / harness default | yes | yes | 36 |

In every run `handoff2.md` passed all fixture checks:
- exactly one delimiter key, valued comma;
- no stale value and no owner or contact key active;
- no stale bullet in the body;
- the old delimiter and owner only in the `SUPERSEDED` audit block;
- page size and output directory kept;
- the request carried unchanged;
- every active fact stamped.

The runs used a 10-check version of `check.mjs`. After the review tightened it to 12 checks, the four recorded `handoff2.md` files were re-checked and passed all 12. The models were not rerun.

`handoff1.md` was unchanged, and no other top-level file remained.

### Known limitations and failures

- Opus exceeded the 120-word limit (124 words).
- Sonnet and Haiku stamped `as-of` times that were not the actual run time. The check confirms stamps exist, not that they are accurate.
- An explicit `gpt-5.5` Codex run failed before task execution: the ChatGPT-account Codex CLI no longer supports that model. The recorded Codex run used the harness default, which the CLI did not report. The failed startup is not attributed to the skill.
- Grok was not rerun for this release.
- All model checks ran on macOS with existing authenticated clients. They are one small scenario each and do not establish a compliance rate.

## v0.1.0 — 2026-09-05

### Package and installation checks

- `npm run check`: all eight skills validated; all 15 tests passed locally on macOS.
- The skill-creator packaging validator accepted all eight standard-metadata entrypoints.
- Official TOON decoder 4.1.1 parsed every routing block and reference in strict mode. Relocation, paths with spaces, CRLF, and malformed-package rejection are covered by executable tests.
- Skills CLI 1.5.23 discovered all eight skills and installed complete, byte-identical entrypoints and references for Claude Code, Codex, Grok, Hermes, Pi, and OpenCode in a temporary project. Codex and OpenCode share `.agents/skills`; the other four targets use symlinks.
- Grok, Hermes, and Pi project directories had to exist before the installer created their symlinks. The initial attempt silently skipped those links; see the [installation caveat](compatibility.md).

The [first public CI run](https://github.com/the-shop/ts-skills/actions/runs/33956905224) passed all six jobs: Ubuntu, macOS, and Windows with Node.js 20 and 22. Each job passed the full 15-test suite. The [parent's pinned-submodule CI run](https://github.com/the-shop/ts-open-source/actions/runs/33956922315) also passed. Subsequent documentation-only release commits run the same checks; consult the [workflow history](https://github.com/the-shop/ts-skills/actions/workflows/validate.yml) for their statuses.

The public GitHub source was also discovered successfully with `npx skills@1.5.23 add the-shop/ts-skills --list`: all eight skills were listed with their standard descriptions.

### Executed model checks

Each model received four fresh fixture copies and explicit requests to read the selected local entrypoints. All eight skills are covered across the four scenarios. Tool traces were inspected for complete reference loading, changes, evidence, and combined presentation. [Sanitized machine results](model-checks.json) include exact skill-content hashes; SHA-256 covers `SKILL.md` bytes followed by `reference.toon` bytes.

| CLI / reported model | Scope and runtime checks | Complete references read | Final words: diagnosis / fix / plan / review |
| --- | --- | --- | --- |
| Claude Code 2.1.258 / `claude-opus-5[1m]` | 4/4 | 4/4 | 139 / 206 / 253 / 160 |
| Codex CLI 0.153.3 / explicit `gpt-5.5` | 4/4 | 4/4 | 88 / 94 / 166 / 111 |
| Grok CLI 1.0.13 / `grok-4.6-build` | 4/4 | 4/4 | 96 / 54 / 164 / 119 |

Claude usage records also include `claude-haiku-4-5-20251001` support calls. Model identifiers are the client-reported or explicitly requested identifiers, not an independent attestation of backend routing.

All diagnosis, plan, and review fixture files remained unchanged. Each implementation changed only the live pricing source and passed the original three assertions with the actual checkout returning 1197 cents / USD 11.97. No review run executed the unsafe script. Every run produced one combined final response rather than concatenated skill templates.

### Known limitations and failures

These are **not twelve unqualified behavioral passes**:

- Claude exceeded the explicit length limits in implementation (206 versus under 180 words) and planning (253 versus under 250). It also made an unsupported floating-point claim in the implementation explanation and phrased an inferred zero-case result as passing after the original test run had aborted. Scope and executed fix checks passed; those narrative claims did not.
- Claude and Codex review answers identified the unsafe default deletion target but included overly broad or unverified statements about `force: true`, symlinks, or downstream effects. Those additional claims are not accepted as verified findings.
- Grok retained global instructions and MCP integrations. Its review rerun retrieved an earlier smoke-review transcript through configured memory; implementation also made an external coordination claim. These runs demonstrate configured-harness file loading and task execution, **not independent reasoning or clean-room isolation**.
- An explicit `gpt-6-astra` attempt failed before task execution because the installed Codex CLI required an upgrade for that model. The machine was not upgraded; the recorded final runs used supported `gpt-5.5` instead. Startup failures are not attributed to the skills.
- Earlier exploratory runs exposed skipped overlapping references and unsupported execution claims. References were clarified, then all scenarios were rerun against the hashes recorded here. Earlier runs are not counted as current-release evidence.

All model checks ran on macOS with existing authenticated clients. Windows/Linux coverage is package-level, not model-level. Hermes, Pi, and OpenCode were installation-tested, not behaviorally tested. No automatic routing, unseen-task success rate, or provider-wide reliability claim is made. Temporary workspaces do not provide an OS security boundary; see [test isolation limits](testing.md).

Raw transcripts are intentionally excluded because configured clients may emit private paths, settings, and memory. The public fixture, runner, hashes, sanitized results, and this manual assessment are sufficient to repeat the cases with your own account. Retain human review for factual and execution claims even when a mechanical result is green.
