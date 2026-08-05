## ADDED Requirements

### Requirement: The triage command is discoverable from `--help`

`keel --help` MUST list `keel triage` in its `Usage:` block, naming both `--labels` and `--issue`,
so that the command's flags are discoverable from the terminal and not only from `README.md`.

#### Scenario: Help lists the triage command
- **WHEN** a user runs `keel --help`
- **THEN** the `Usage:` block includes a `keel triage` line
- **AND THEN** that line names both `--labels` and `--issue`
