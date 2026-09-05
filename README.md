# TS Skills

Eight engineering discipline skills from The Shop: understand the system, question the plan, investigate the cause, and verify the result.

Each skill is independently installable. A small `SKILL.md` routes to a sibling `reference.toon` only when the skill is selected. The instructions require no particular model, operating system, shell, MCP server, or orchestration service.

## Install

Select the skills and agents you want:

```sh
npx skills add the-shop/ts-skills
```

Install one skill for Claude Code and Codex:

```sh
npx skills add the-shop/ts-skills --skill ts-rootcause --agent claude-code codex
```

The [Skills CLI](https://github.com/vercel-labs/skills) supports other agents and project or global installation. Inspect its choices before replacing an existing skill with the same name. Node.js is needed for this installer, not for reading or using the skills.

For manual installation, copy a complete `skills/ts-…` directory into your agent's configured skill directory. Keep `SKILL.md` and `reference.toon` together. See [compatibility and installation](docs/compatibility.md) for the distinction between format support, installation checks, and executed model tests.

## Choose a skill

| Skill | Use it to | Example request |
| --- | --- | --- |
| [ts-context](skills/ts-context/SKILL.md) | Trace the code that actually runs | “Find where this request is handled.” |
| [ts-think](skills/ts-think/SKILL.md) | Compare credible approaches using evidence | “Which of these designs fits our constraints?” |
| [ts-plan](skills/ts-plan/SKILL.md) | Plan from the verified current state | “Plan the migration before changing anything.” |
| [ts-rootcause](skills/ts-rootcause/SKILL.md) | Diagnose a failure or implement an authorized fix | “Explain this bug; do not fix it yet.” |
| [ts-review](skills/ts-review/SKILL.md) | Find material risks in a change | “Review this diff and its callers.” |
| [ts-verify](skills/ts-verify/SKILL.md) | Ground completion claims in fresh checks | “Verify this fix through the real entrypoint.” |
| [ts-handoff](skills/ts-handoff/SKILL.md) | Leave usable continuation notes | “Record what is done and how to resume.” |
| [ts-elon](skills/ts-elon/SKILL.md) | Question, delete, simplify, accelerate, automate | “Scrub this workflow before we automate it.” |

Invoke skills using your agent's supported syntax, or name them in a request. Slash commands such as `/ts-elon` are host features, not part of the file format. In a host with only file-reading tools, ask it to read the selected `SKILL.md`; that entrypoint directs it to the full reference.

## Work together without repeated templates

For a diagnosis:

> Use ts-context, ts-rootcause, and ts-verify. Diagnose the incorrect total, show the evidence, and do not edit files. Give one concise response.

For an implementation:

> Use ts-rootcause and ts-verify. Fix the incorrect total, rerun the reproduction, and report the change and checks together.

For a proposed process:

> Use ts-elon and ts-plan. Question the proposed components, keep the necessary requirements, and plan the simplest implementation.

Skills combine their relevant obligations into one workflow. Evidence can serve multiple skills and should appear once. The user's requested output format takes precedence over a skill's suggested presentation. Diagnosis, review, and planning have completion conditions that do not require edits.

## Why two files?

`SKILL.md` keeps standard [Agent Skills YAML metadata](https://agentskills.io/specification) and a compact TOON routing block. `reference.toon` holds the workflow, evidence requirements, and completion conditions in [Token-Oriented Object Notation](https://github.com/toon-format/spec).

The model reads TOON as text; no decoder is required at runtime. Our development checks use the official decoder to catch malformed tables and truncation. This layout reduces the initial entrypoint size; it does not promise a fixed token saving or guarantee that every host loads files lazily. See [design and composition](docs/design.md).

## Validation

Maintainer checks need Node.js 20 or newer:

```sh
npm ci --ignore-scripts
npm run check
```

CI runs package checks on Linux, macOS, and Windows with Node.js 20 and 22. The [test guide](docs/testing.md) explains the static checks, temporary-workspace behavioral smoke cases, failure interpretation, and how to repeat them. [Release evidence](docs/validation.md) records what was actually tested and its limits.

## Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for small, evidence-backed changes and test expectations. [CHANGELOG.md](CHANGELOG.md) records releases. This repository is the independently usable skill collection inside [the-shop/ts-open-source](https://github.com/the-shop/ts-open-source).

## License and provenance

[MIT](LICENSE). These are revised editions of The Shop's locally maintained `ts-*` discipline instructions. This repository begins with the public subset; it contains no private repository history or internal harness hooks.

`ts-elon` keeps its historical name and the five-step method it refers to. It implies no affiliation with or endorsement by Elon Musk. Agent Skills and TOON are separate projects; links identify the formats used, not an endorsement of this collection.
