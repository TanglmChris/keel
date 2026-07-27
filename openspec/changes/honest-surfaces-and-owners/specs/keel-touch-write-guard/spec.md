## ADDED Requirements

### Requirement: The guard manifest is declared ignorable local state

The write-guard manifest is per-clone session state, not project content. Keel's install and init paths MUST declare it ignorable so an ordinary gate run leaves no undeclared untracked file, and MUST do so without overwriting a project's own ignore file.

#### Scenario: Install declares the manifest ignorable
- **WHEN** `keel --install` or `keel --init` runs in a project with no `keel/.gitignore`
- **THEN** it scaffolds one declaring the guard manifest
- **AND THEN** a subsequent passing `task-start` leaves no undeclared untracked path behind

#### Scenario: An existing ignore file is not overwritten
- **WHEN** the project already has a `keel/.gitignore`
- **THEN** install leaves that file byte-identical and reports the skip rather than merging into it

## MODIFIED Requirements

### Requirement: Guard capability is reported from observed evidence
Keel MUST report the write-guard surface per target from observed evidence, MUST NOT claim `enforced` without behavioral probe evidence, and MUST state the enforcement boundary honestly. The guard command's own result MUST carry that boundary too, so a written manifest is never read as observed enforcement.

#### Scenario: Doctor reports the guard surface
- **WHEN** `keel --doctor` runs for the Claude target
- **THEN** it reports the guard hook surface, manifest state, and capability level derived from observed evidence
- **AND THEN** hook-file presence alone reports advisory, not enforced

#### Scenario: Guard status describes the manifest, not enforcement
- **WHEN** `keel guard start` or `keel guard status` reports a written manifest
- **THEN** the result states that the status describes the manifest and that enforcement depends on a runtime hook Keel cannot observe from the repository
- **AND THEN** no wording in the result asserts that writes are currently being checked

#### Scenario: Unguardable writes are documented
- **WHEN** guard capability is reported or documented
- **THEN** the file-edit-tools-only boundary is stated explicitly
- **AND THEN** `Bash` and other indirect writes are identified as disciplinary, not guarded

#### Scenario: Unsupported targets report manual
- **WHEN** the target is Codex or OpenCode
- **THEN** the guard capability reports manual with the reason
- **AND THEN** no unverified native enforcement claim is made
