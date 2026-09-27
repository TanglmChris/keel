## ADDED Requirements

### Requirement: Doctor reports the OpenSpec that wrote the surfaces

`keel --doctor` MUST report, when any OpenSpec skill surface carries a `generatedBy` stamp, the highest such version beside the OpenSpec Keel runs. It MUST warn when the surfaces are newer. The warning MUST state that `keel --init` leaves them unrewritten, and MUST name `keel --install` as the refresh that does not touch them.

#### Scenario: Newer surfaces are named with their remedy
- **WHEN** the surfaces were written by a newer OpenSpec than Keel runs
- **THEN** doctor prints an `OpenSpec surfaces` warning naming both versions, `keel --init`'s refusal, and `keel --install`

### Requirement: Doctor reports an auto-update declaration only one checkout carries

When `.claude/settings.json` declares Keel plugin auto-update and the repository is a Git work tree that does not track that file, `keel --doctor` MUST report the declaration as a warning, and MUST name `git add .claude/settings.json`.

#### Scenario: An untracked declaration is named
- **WHEN** `.claude/settings.json` declares `autoUpdate: true` and is untracked
- **THEN** the `plugin auto-update` line is a warning naming `git add .claude/settings.json`
- **AND THEN** once the file is tracked, the line is `ok`

### Requirement: Doctor's protocol remedy does not rewrite OpenSpec surfaces

When the repository's managed protocol is behind the running Keel, `keel --doctor` MUST name `keel --install --target <t>` as the refresh. It MUST NOT name `keel --init`, which also rewrites OpenSpec's surfaces.

#### Scenario: A repository behind its install is sent to install
- **WHEN** the repository declares an older protocol than the running Keel
- **THEN** doctor's `protocol` warning names `keel --install --target <t>` and does not name `keel --init`
