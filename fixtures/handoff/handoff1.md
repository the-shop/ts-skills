<<<REQUEST n_lines=1>>>
Configure a nightly CSV exporter for Morgan: semicolon delimiter, 50 rows per page, files in out/, Morgan as the owner contact. Do not implement it yet.
<<<END REQUEST>>>

STATE: Configuration only. No exporter code, schedule, or out/ directory exists yet (checked with `ls` in this directory).

DONE: The configuration decisions below were confirmed with the user.

NOT-DONE: Choose the data source, columns, and schedule time; then implement the exporter.

RESUME: Ask the user for the data source and columns, then create export.mjs in this directory.

OPEN QUESTIONS: What time should the export run? Ask the user.

<<<FACTS v1>>>
- delimiter: semicolon (;) (as-of: agent-1 / 2026-10-18T09:00Z)
- page-size: 50 rows (as-of: agent-1 / 2026-10-18T09:00Z)
- output-dir: out/ (as-of: agent-1 / 2026-10-18T09:00Z)
- owner-contact: Morgan (as-of: agent-1 / 2026-10-18T09:00Z)
<<<END FACTS>>>
