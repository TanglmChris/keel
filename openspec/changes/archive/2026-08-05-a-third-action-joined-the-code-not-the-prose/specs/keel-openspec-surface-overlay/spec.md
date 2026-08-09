## MODIFIED Requirements

### Requirement: Keel refreshes existing overlays idempotently

Keel MUST replace an existing managed overlay block instead of duplicating it, and MUST skip missing OpenSpec files during `keel --install` instead of creating incomplete generated surfaces.

#### Scenario: Install refreshes an existing overlay

- **WHEN** an initialized target has an apply/archive/sync OpenSpec file with an outdated Keel overlay block
- **AND WHEN** `keel --install --target <target>` runs
- **THEN** the file contains exactly one current Keel overlay block
- **AND THEN** other OpenSpec-generated content remains present

#### Scenario: Install skips missing OpenSpec files

- **WHEN** `keel --install --target <target>` runs before OpenSpec has generated apply/archive/sync files
- **THEN** Keel does not create placeholder OpenSpec apply/archive/sync files
- **AND THEN** `keel --doctor --target <target>` reports the missing overlay or missing surface with remediation

### Requirement: Thin CLI owns OpenSpec initialization and overlays only

After native plugin migration, `keel --init/--install` MUST use official OpenSpec 1.5.0 to initialize or refresh action skills/commands, install Keel schema and managed authoring/apply/archive/sync overlays, and merge minimal bootstrap guidance. It MUST NOT copy Keel plugin skills, hooks, adapters, or full protocol assets into target-specific project trees.

#### Scenario: Codex init uses plugin plus official OpenSpec
- **WHEN** a Codex project with the Keel plugin runs `keel --init --target codex`
- **THEN** OpenSpec action skills/prompts, Keel schema/overlays, and minimal bootstrap are ready
- **AND THEN** Keel skills/hooks remain supplied by the installed plugin

#### Scenario: Claude init uses plugin plus official OpenSpec
- **WHEN** a Claude project with the Keel plugin runs `keel --init --target claude`
- **THEN** OpenSpec action skills/commands, Keel schema/overlays, AGENTS bootstrap/import, and plugin diagnostics are ready
- **AND THEN** no `.claude/skills/keel-*`, `.claude/hooks/keel-*`, or adapter copy is created by the CLI

#### Scenario: Plugin is missing
- **WHEN** init succeeds for schema/OpenSpec/bootstrap but the native plugin is absent
- **THEN** doctor reports the partial state and native plugin install remediation
- **AND THEN** explicit Keel Core commands remain available
