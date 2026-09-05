# Compatibility and installation

## What is portable

The installed payload is two UTF-8 text files per skill. YAML frontmatter provides standard `name`, `description`, `license`, and string-valued `metadata`. Discovery phrases belong in `description`; there is no custom top-level `triggers` field.

References are relative to their own skill directory. A selected skill does not depend on the other seven, a shared external reference, a particular shell, absolute machine paths, provider APIs, internal services, or a TOON runtime. Agents can use equivalent file, search, execution, and data tools available in their environment.

The skills do not grant tools or permissions. A host that can only read files can apply analysis procedures but cannot verify a running application. That limit must remain visible in the result.

## Install through the Skills CLI

```sh
# Choose skills and target agents interactively.
npx skills add the-shop/ts-skills

# Inspect available skills without installing.
npx skills add the-shop/ts-skills --list

# Select one skill and a target agent.
npx skills add the-shop/ts-skills --skill ts-verify --agent codex
```

The CLI's `--global` option selects user-wide installation. Omit it for project installation. See the [upstream CLI reference](https://github.com/vercel-labs/skills) for supported agents, current destinations, updates, removal, and telemetry settings. The published repository is the source; no npm package is published by this project.

The six release installation targets are:

| Agent | CLI identifier |
| --- | --- |
| Claude Code | `claude-code` |
| Codex | `codex` |
| Grok | `grok` |
| Hermes | `hermes-agent` |
| Pi | `pi` |
| OpenCode | `opencode` |

Installation support means the files can be placed for a host. It does not mean every host/model pair was behaviorally tested. The exact executed checks are in [release evidence](validation.md).

With Skills CLI 1.5.23, project-mode symlink installation for Grok, Hermes, and Pi skips the agent-specific link if the corresponding `.grok`, `.hermes`, or `.pi` project directory does not already exist. Initialize the intended host's project directory first, or install manually. Check that both skill files are readable at the final destination; the install summary alone is not sufficient evidence.

## Install manually

1. Clone or download this repository.
2. Choose a directory such as `skills/ts-rootcause`.
3. Copy that complete directory into your host's documented skill location. Use its project location when you want to limit scope to one project.
4. Reload skills or restart the host if required.
5. Invoke the local skill and confirm that the host reads its sibling `reference.toon`.

Copying only `SKILL.md` leaves an incomplete skill. If another copy of the same skill is already installed, inspect the host's precedence rules and deliberately select which copy to retain.

## Host-neutral invocation

```text
Read skills/ts-rootcause/SKILL.md and use it to diagnose this failure.
Do not implement a fix. Give one concise explanation with evidence.
```

Replace that path with the installed entrypoint. Native slash commands, implicit selection, and automatic reference loading vary by host. Our behavioral smoke suite explicitly requests the checked-out entrypoints; it does not establish automatic routing accuracy.

## Environment limits

Package validation and reference resolution are tested independently of model behavior. CI's Windows and Linux checks do not prove that a remote model obeys instructions on those operating systems. Conversely, a successful model run on macOS does not substitute for package checks on Windows. Missing tools or unavailable application runtimes should produce a precise limitation, not a fabricated passing result.
