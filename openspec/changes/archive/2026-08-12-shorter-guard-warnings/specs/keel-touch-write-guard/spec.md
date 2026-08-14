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

#### Scenario: Standing warnings may be reworded for brevity without dropping an idea
- **WHEN** the durability and enforcement-boundary warning strings a guard result carries are edited for brevity
- **THEN** the result still states that the manifest is a disposable pointer and not durable authority, that OpenSpec and Git remain that authority, and that selection never derives from the manifest
- **AND THEN** the result still states that the reported status describes the manifest only, that enforcement is a runtime-hook fact Keel cannot observe, and that a written manifest is not evidence a write was checked
- **AND THEN** no wording asserts that enforcement is active, that enforcement is live, or that writes are guarded
