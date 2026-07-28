## MODIFIED Requirements

### Requirement: Keel has one canonical dual-runtime plugin source
Keel MUST package one plugin at `plugins/keel` with native Codex and Claude manifests, one canonical portable skill/reference tree, and default-discovered hook assets. It MUST NOT generate per-target copies of the same skill or protocol authority.

#### Scenario: Codex manifest is native
- **WHEN** the plugin source is inspected or installed by the supported Codex baseline
- **THEN** `plugins/keel/.codex-plugin/plugin.json` has valid native metadata, name `keel`, the package version, and the canonical skills path
- **AND THEN** it uses default hook discovery rather than an unsupported explicit hooks field

#### Scenario: Claude manifest is native
- **WHEN** the plugin source is validated or installed by the supported Claude baseline
- **THEN** `plugins/keel/.claude-plugin/plugin.json` has valid native metadata, name `keel`, the package version, and the same canonical skills/hooks inventory

#### Scenario: Skill authority is singular
- **WHEN** the package, repository, or installed plugin inventory is inspected
- **THEN** every Keel skill and reference has one canonical source under `plugins/keel/skills`
- **AND THEN** no `src/skills` or per-target skills copy is current authority

## REMOVED Requirements

### Requirement: Keel 4.0.0 release surfaces stay aligned

**Reason**: it required every release surface to report base version `4.0.0`,
which stopped being true at 4.1.0 and has been false through five minor
releases. Its alignment half is carried by
`keel-expectation-slice-evidence-gates / Shipped version markers agree with the
package version`, which states the invariant without a literal; its packaging
half — that the tarball is thin and excludes retired trees — is asserted by the
`thin-native-install` and package-hygiene checks.

**Migration**: none. Both manifests are shipped markers and are covered by the
replacement invariant by construction.
