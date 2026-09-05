# Testing

## Package checks

```sh
npm ci --ignore-scripts
npm run check
```

These commands validate all eight entrypoints and their TOON references, then run Node's test runner. The development dependencies are pinned in `package-lock.json`. The installed skills themselves have no JavaScript dependency.

Checks cover supported metadata, skill identity, a 180-word entrypoint budget, strict TOON decoding and round trips, missing references, reference confinement, standalone relocation, paths containing spaces, Windows line endings, and local documentation links. Negative cases deliberately corrupt temporary copies and require rejection. Temporary files are removed by their owning tests.

The CI matrix runs the same checks on Ubuntu, macOS, and Windows with Node.js 20 and 22. No provider credentials are required for this matrix.

## Behavioral smoke cases

The separate smoke runner invokes an installed, authenticated CLI. It can consume provider quota and is opt-in; `npm test` never calls a model.

```sh
node scripts/smoke.mjs claude diagnosis
node scripts/smoke.mjs codex implementation
node scripts/smoke.mjs grok plan

# Optionally select a model supported by that CLI/account.
node scripts/smoke.mjs codex review YOUR_MODEL_ID
```

`YOUR_MODEL_ID` is a placeholder for a model available to your account. Supported case names are `diagnosis`, `implementation`, `plan`, and `review`. The runner adapts CLI flags for Claude Code, Codex, and Grok; those clients and credentials are maintainer test prerequisites, not skill requirements. CLI flag support may change, so a startup failure is a harness-compatibility issue until investigated.

| Case | Skills | Observable checks |
| --- | --- | --- |
| Diagnosis | context, rootcause, verify | Trace the live price calculation; leave the faulty fixture unchanged. |
| Implementation | rootcause, verify | Correct only the live pricing source; pass the checkout checks without changing tests. |
| Plan | elon, context, think, plan, handoff | Inspect constraints; propose an appropriately small plan without implementation. |
| Review | review, verify | Identify unsafe deletion from a text-only script sample; make no changes or execution claims. |

Every run copies a fixture and selected skills to a new temporary workspace. It requests the actual entrypoints and references rather than injecting the full reference text. Checkout fixtures contain an intentionally unused correct implementation to test whether the agent traces the code that runs.

A temporary workspace is not an operating-system security sandbox. Claude and Grok can execute tools with the invoking account's access; all clients inherit environment variables and credentials. The runner disables supported configuration sources where available, but global instructions, memory, or MCP integrations can remain active. Use an isolated account or container with only the intended provider credentials for an independent clean-room trial. Do not put secrets in fixtures.

The review fixture is named `cleanup.mjs.txt` so routine JavaScript test discovery cannot execute its intentionally unsafe example. Do not execute that file. The runner never executes it.

The runner saves the prompt, stdout, stderr, final answer, file-change checks, and skill-content hashes in the run's temporary directory. A result pointer is saved in ignored `.artifacts/`. These transcripts may include local configuration or paths; inspect them before sharing.

## Interpret results honestly

`mechanicalPass` checks process completion, a nonempty final answer, unchanged copied skills, and permitted top-level fixture changes. It does not monitor writes outside that set and is not an LLM quality score. A person or independent reviewer must inspect:

- tool traces showing the entrypoints and complete references were read;
- factual correctness and evidence from the fixture;
- diagnosis/review/plan scope and authorized implementation;
- response length and combined presentation;
- unsupported claims about checks, execution, or environment behavior.

An unavailable provider, invalid CLI flag, timeout, malformed output extraction, or denied tool is reported separately from a skill failure. A changed skill invalidates prior behavior results for that skill hash. Preserve failed-run evidence; do not quietly redefine acceptance to obtain green.

Smoke tests are small, selected examples. They do not establish universal model compliance, automatic skill selection, comparative effectiveness, or a success rate on unseen tasks. The [release evidence](validation.md) records the tested versions and limitations.
