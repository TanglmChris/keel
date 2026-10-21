## ADDED Requirements

### Requirement: The suite states what kind of evidence ran
The runner MUST classify every registered scenario as deterministic or as run against a stand-in host, and MUST derive the stand-in markers from Keel's own sources. When `--all` or `--group` passes, it MUST print an `evidence:` line that gives both counts, says `none on a real host`, and names `docs/host-contract.md`. The two counts MUST add up to the verified count.

#### Scenario: A scenario that reaches a stand-in through a helper, a hook payload or a script is counted as one
- **WHEN** `validate_plugin.py --evidence` runs against the registry
- **THEN** `shift-cli-self-shift`, `chat-claude-hooks`, `codex-receiving` and `update-pack-install` are listed as run against a stand-in host, and `version-alignment` as deterministic
- **AND THEN** the two counts add up to the number of registered scenarios

#### Scenario: A passing run states its evidence
- **WHEN** `validate_plugin.py --group docs` passes
- **THEN** its last line starts with `evidence:`, its two counts add up to the verified count, and it says `none on a real host` and names `docs/host-contract.md`

### Requirement: Each release's notes carry its evidence
`validate_plugin.py --evidence --markdown` MUST print an `## Evidence` section without running any scenario. The section gives:
- the deterministic and stand-in-host counts;
- the number of rows `docs/host-contract.md` records as measured on a real host;
- the scenarios that can skip.

The publish workflow MUST append that section to each release's notes.

#### Scenario: A release's notes carry the evidence section
- **WHEN** the publish workflow writes a release's notes
- **THEN** it appends the output of `validate_plugin.py --evidence --markdown`, whose `## Evidence` section gives both counts, the measured-row count, and the scenarios that can skip
