## MODIFIED Requirements

### Requirement: Native plugin diagnostics are behavior-probed
Keel MUST distinguish manifest presence, marketplace discovery, installation, enablement, hook configuration, trust/policy, activation, and observed projection behavior instead of collapsing them into one installed flag. Checks that can only be satisfied inside Keel's own source repository MUST be scoped to that repository and MUST NOT be presented to a consuming project as a failure it can act on.

#### Scenario: Manifest exists but plugin is not installed
- **WHEN** the source manifest is valid but the runtime has not installed the plugin
- **THEN** doctor reports source-valid and runtime-missing separately

#### Scenario: Plugin installed but hook untrusted
- **WHEN** the runtime lists the plugin but skips its untrusted or policy-blocked hook
- **THEN** doctor reports skills available and SessionStart projection manual
- **AND THEN** it identifies the trust/policy boundary without changing it

#### Scenario: Behavior smoke succeeds
- **WHEN** an isolated supported runtime starts a fresh session and receives the expected disposable context projection
- **THEN** release evidence may report that exact version/surface as behavior-verified
- **AND THEN** later doctor runs still downgrade when current trust/activation cannot be observed

#### Scenario: Development-only source check is scoped to Keel's own repository
- **WHEN** doctor runs in a project that consumes Keel rather than in Keel's own source repository
- **THEN** it does not report the plugin source manifest check, whose path `keel --init` never creates
- **AND THEN** no remediation line directs the author to install a plugin that is already installed

## ADDED Requirements

### Requirement: Keel install does not damage its own source repository
Keel's install and init paths MUST NOT overwrite repository content that only exists in Keel's own source repository with the consumer-facing bootstrap asset. When the target is Keel's own repository, the bootstrap write MUST be skipped and reported as skipped.

#### Scenario: Install skips the bootstrap write in Keel's own repository
- **WHEN** `keel --install` or `keel --init` runs in Keel's own source repository
- **THEN** the managed `AGENTS.md` block is left byte-identical
- **AND THEN** the command reports the skip explicitly rather than silently omitting the step

#### Scenario: Install still writes the bootstrap in a consuming project
- **WHEN** the same command runs in a project that consumes Keel
- **THEN** the managed `AGENTS.md` block is written from the bootstrap asset as before
