# Contributing

Small changes grounded in observed agent behavior are welcome. Open an issue or pull request describing the task, the problematic behavior, and the evidence that the proposed change improves it.

## Edit the canonical files

Edit `skills/<name>/SKILL.md` and its sibling `reference.toon`. Keep the entrypoint short, references relative, metadata standard, and each skill independently installable. Do not add host-specific paths, private services, credentials, or assumptions about a particular provider.

Keep scope and evidence requirements explicit. Diagnosis must remain useful without edits. Combined skills must permit one concise answer. Do not add mandatory headings, artificial quotas, or universal rules solely to satisfy one example.

## Verify the change

1. Run `npm ci --ignore-scripts` and `npm run check`.
2. For instruction changes, run a relevant behavioral smoke case and inspect the actual tool trace and final answer.
3. Add a negative package test if fixing a validation failure. Use behavior or data assertions rather than matching a preferred paragraph verbatim.
4. Update affected documentation and the changelog.

Describe the scope, validation, and remaining limitations in the pull request. Do not upload unreviewed model transcripts or claim test coverage beyond what ran.

## Release

The package version is the release version. Set a skill's `metadata.version` and its `reference.toon` `version` to the release that last changed that skill, so unchanged skills keep the hashes their recorded evidence covers. Publish the skill repository and tag its tested commit, then update the parent repository's `ts-skills` submodule to that commit. Validate a fresh recursive clone before tagging the parent release. See the [parent repository](https://github.com/the-shop/ts-open-source) for checkout and update commands.

Contributions are provided under this repository's [MIT license](LICENSE). Identify upstream sources and preserve applicable notices when adapting third-party material.
