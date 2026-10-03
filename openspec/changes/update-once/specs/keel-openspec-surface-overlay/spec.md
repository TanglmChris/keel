## ADDED Requirements

### Requirement: A protocol refresh brings every installed target's overlays forward

`keel --install` and `keel --init`, whatever `--target` selects, MUST refresh Keel's overlays on the existing OpenSpec surfaces of every target installed in the repository, discovered from repository surfaces as doctor discovers them. They MUST create no surface for a target the repository does not carry. Doctor MUST report an overlay whose version marker differs from the running CLI as stale, attributed to its target, with the refresh command, rather than as healthy.

#### Scenario: A Claude refresh also refreshes Codex overlays
- **WHEN** a repository carries Claude and Codex surfaces whose overlays are at an older version and `keel --install --target claude` runs
- **THEN** every Claude and Codex overlay carries the running version, with exactly one overlay per surface and upstream content unchanged

#### Scenario: An absent target stays absent
- **WHEN** a repository carries only Claude surfaces and `keel --install --target claude` runs
- **THEN** no Codex or OpenCode surface is created

#### Scenario: Doctor names a stale overlay
- **WHEN** a Codex overlay's version marker is older than the running CLI
- **THEN** doctor's Codex overlay line reports it stale, names the refresh command, and does not report `ok`
