## ADDED Requirements

### Requirement: Project setup declares Claude plugin auto-update

On the Claude target, `keel --init` and `keel --install` MUST declare auto-update for the Keel marketplace in the project's `.claude/settings.json`. The declaration is an `extraKnownMarketplaces` entry named `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`. The merge MUST preserve every other setting, MUST keep an existing entry's source, and MUST NOT overwrite an `autoUpdate` value the project already states. `keel --uninstall` MUST remove the entry only when it is exactly the one Keel writes. `keel --doctor` MUST report whether auto-update is declared on, declared off, or not declared, and MUST NOT claim to observe whether the host performs updates.

#### Scenario: Init declares auto-update
- **WHEN** `keel --init --target claude` runs in a repository with no `.claude/settings.json`
- **THEN** the file declares `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`

#### Scenario: Existing settings are kept
- **WHEN** `.claude/settings.json` already holds other settings, or a `keel-marketplace` entry with its own source or `autoUpdate: false`
- **THEN** install keeps those settings, that source, and that `false`
- **AND THEN** running install again changes nothing

#### Scenario: Uninstall removes only Keel's entry
- **WHEN** `keel --uninstall --target claude` runs
- **THEN** an entry equal to Keel's is removed, and one the project changed is kept

#### Scenario: Doctor reports the declaration
- **WHEN** `keel --doctor --target claude` runs
- **THEN** a `plugin auto-update` line reports declared on, declared off by the project, or not declared with the command that declares it

#### Scenario: Other targets are untouched
- **WHEN** `keel --init --target codex` runs
- **THEN** no `.claude/settings.json` is written
