# Changelog

## 0.2.0 — 2026-10-18

- ts-handoff: add keyed facts between `<<<FACTS v1>>>` delimiters, where a newer value for a key replaces the older line, and the bundled standard-library `merge_facts.py` that carries the original request forward, stamps `as-of`, and keeps replaced and over-cap lines in separate audit blocks.
- Run the merge script's Python suite from `npm test`; maintainer checks now need Python 3.8+.
- Add a `handoff` behavioral smoke case with a fixture brief and a deterministic check. Smoke skill hashes now also cover extra skill files; two-file skills keep their earlier hashes.
- Version only the changed skill: ts-handoff is 0.2.0, the other seven stay at 0.1.0 with unchanged hashes.

## 0.1.0 — 2026-09-05

- Publish eight portable engineering discipline skills: context, thinking, planning, root-cause investigation, review, verification, handoff, and the five-step requirements method.
- Use standard YAML discovery metadata and compact TOON routing with self-contained reference files.
- Separate diagnosis-only and implementation completion conditions.
- Permit combined responses while preserving substantive evidence requirements.
- Add strict format validation, standalone installation checks, portability tests, and opt-in behavioral smoke fixtures.
