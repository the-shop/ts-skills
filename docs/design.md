# Design and composition

## Read only what is selected

Each `SKILL.md` contains discovery metadata and routing instructions. When selected, the agent reads `reference.toon` in full. Other skill references remain unloaded unless their skills are also selected. Each bundle is self-contained so individual installation cannot break a shared-file dependency.

YAML frontmatter is retained because it is part of the [Agent Skills specification](https://agentskills.io/specification). The entrypoint routing block and the reference use [TOON](https://github.com/toon-format/spec). Markdown documentation and ordinary user responses remain free to use the most suitable format.

## Preserve obligations, combine presentation

Every reference contains four common contract fields:

| Field | Obligation |
| --- | --- |
| `scope` | Stay within the requested outcome and existing authorization. |
| `evidence` | Separate observations, hypotheses, proposals, changes, and unverified results. |
| `composition` | Combine relevant obligations and shared evidence into one response. |
| `unavailable` | Use equivalent tools and report missing capabilities accurately. |

These small fields are repeated intentionally so a single installed skill works on its own. The detailed steps and completion conditions are specific to each skill.

Combining skills does not require concatenating their outputs. For example, one observed reproduction and one code reference can satisfy context tracing, root-cause evidence, and verification. Do not repeat that evidence under three headings. Use headings or tables only when they help the user or the requested format requires them.

## Diagnosis is a complete outcome

`ts-rootcause` distinguishes two modes:

- Diagnosis finishes with a supported cause, or a clearly bounded uncertainty and the missing discriminating check. It needs no code edit or post-fix reproduction.
- Implementation finishes when the authorized fix is applied and the original symptom is rechecked after the change, with appropriate regression evidence. If a required runtime is unavailable, the implementation remains unverified in that respect.

This boundary also applies to `ts-review` and `ts-plan`. An analysis request does not silently become implementation. When the user requests both planning and implementation, completing the plan does not create a new approval requirement.

## Evidence remains substantive

Compact reporting does not lower the standard of proof. A hypothesis needs observations that distinguish it from credible alternatives. A changed integration needs its real reachable endpoint, UI flow, or data path exercised; compilation or mocks alone do not establish that wiring. A handoff records when and where evidence was obtained so a successor can identify stale assumptions.

## Requirements before automation

`ts-elon` preserves the order: question requirements, try deletion, simplify survivors, accelerate, then automate. It does not require inventing a human owner, discarding an explicit user requirement without agreement, or deleting a fixed percentage of a system. Removing an unnecessary step is useful; meeting a deletion quota is not the outcome.
