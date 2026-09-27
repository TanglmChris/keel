## ADDED Requirements

### Requirement: Context names the refresh of an older managed protocol

`keel context` MUST read the protocol version stamped in the repository's managed block. When that version is strictly older than the running Keel, it MUST report both versions, the refresh command with the repository's inferred target, and one of three states: standing-authorized, not authorized, or deferred because a task's write guard is active. It MUST carry the same fields in its JSON result. It MUST report nothing when the stamp is equal, newer, or unreadable, or when the repository is Keel's own source. The report MUST NOT change `status`, `nextAction`, or selection.

#### Scenario: An older protocol names its refresh
- **WHEN** the managed block is stamped older than the running Keel and no authorization is declared
- **THEN** context prints one `Protocol:` line naming both versions and `keel --install --target <t>`, and says to ask before running it

#### Scenario: A declared authorization is reported on the line
- **WHEN** `authorize:` lists `protocol-refresh`
- **THEN** the line says the refresh is standing-authorized

#### Scenario: A write guard defers the refresh
- **WHEN** `keel/guard.json` exists
- **THEN** the line says the refresh is deferred while a task's write guard is active, whatever is authorized

#### Scenario: An aligned or newer protocol says nothing
- **WHEN** the stamp equals or is newer than the running Keel, or the repository is Keel's own source
- **THEN** context prints no `Protocol:` line, and its JSON carries no `protocol` field

#### Scenario: The target follows the installed surface
- **WHEN** the repository carries the Codex surface and no Claude import
- **THEN** the named command is `keel --install --target codex`
