## ADDED Requirements

### Requirement: Doctor expects no OpenSpec command files on Claude and OpenCode

For the Claude and OpenCode targets, `keel --doctor` MUST report the OpenSpec commands line `ok` when no OpenSpec command file exists, saying that Keel generates the workflows as skills only, and MUST report it `duplicate` when command files remain, naming their count, their location, and `keel --init --target <target>` as the remedy. The Keel overlay line MUST count the managed skills plus the command files that exist, and MUST NOT count an absent command file as a missing overlay.

#### Scenario: A skills-only repository reads healthy

- **WHEN** `keel --init --target claude` has run and `keel --doctor --target claude` runs
- **THEN** the OpenSpec commands line reads `ok` and says the workflows are skills only
- **AND THEN** the Keel overlay line reads `ok` with `4/4`

#### Scenario: Leftover command files read as duplicates

- **WHEN** `.claude/commands/opsx/apply.md` exists beside the skills and `keel --doctor --target claude` runs
- **THEN** the OpenSpec commands line reads `duplicate`, names 1 command file under `.claude/commands/opsx`, and names `keel --init --target claude`
