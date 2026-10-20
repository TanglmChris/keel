## MODIFIED Requirements

### Requirement: Keel doctor reports the target surface
`keel --doctor --target <target>` MUST report Keel CLI/OpenSpec readiness, native plugin discovery and version, minimal bootstrap, canonical skill/reference inventory, applicable OpenSpec-generated action/command overlays, hook configuration/trust/activation/behavior, and continuity/gate capability levels. It MUST not require copied Keel skill/hook/adapter trees as v4 health evidence.

#### Scenario: Claude native surface is reported
- **WHEN** doctor runs for Claude in a v4 repository
- **THEN** it reports Claude plugin marketplace/install/version, canonical component inventory, SessionStart hook policy and behavior, AGENTS import/bootstrap, and OpenSpec surfaces
- **AND THEN** each behavior remains enforced, advisory, or manual from observed evidence

#### Scenario: Codex native surface is reported
- **WHEN** doctor runs for Codex with an isolated or real CODEX_HOME
- **THEN** it reports Codex plugin marketplace/install/version, canonical component inventory, hook trust/activation/behavior, bootstrap, and resolved OpenSpec command prompts
- **AND THEN** unverified hook trust or behavior remains manual

#### Scenario: CLI or plugin version mismatch is reported
- **WHEN** the native plugin and Keel CLI base versions or capabilities are incompatible
- **THEN** doctor reports both observed versions and the exact remediation
- **AND THEN** it does not report native projection as ready

#### Scenario: Alignment reference inventory is reported
- **WHEN** doctor inspects an installed Keel plugin
- **THEN** it reports the canonical alignment skill and required web, hardware, and hardware-DSL references as one inventory
- **AND THEN** it does not report v3 profile-install state as current v4 health

#### Scenario: OpenCode compatibility is reported without v4 probing
- **WHEN** doctor receives target opencode in v4
- **THEN** it reports that existing manual artifacts are compatibility-only and outside v4 native support
- **AND THEN** it does not create or claim a plugin, hook, goal, or enforced capability

### Requirement: Target adapters report behavior capabilities

Keel diagnostics MUST report behavior-oriented capabilities for continuity startup or reinjection, the `task-start`, `task-complete`, and `change-close` gates, and worktree continuity as `enforced`, `advisory`, or `manual`.

#### Scenario: Verified blocking automation is enforced
- **WHEN** Keel can confirm that a target surface is installed, enabled, trusted, and reliably blocks a Core non-pass result
- **THEN** doctor reports that behavior capability as `enforced`
- **AND THEN** the report identifies the target-native surface providing it

#### Scenario: Non-blocking automation is advisory
- **WHEN** a target surface can inject or display a Core result but reliable blocking is not established
- **THEN** doctor reports the capability as `advisory`

#### Scenario: Unverified automation is manual
- **WHEN** support, installation, enablement, trust, or blocking behavior cannot be confirmed
- **THEN** doctor reports the capability as `manual`
- **AND THEN** the report identifies the explicit Keel command required

#### Scenario: Probe does not mutate runtime configuration
- **WHEN** doctor probes target capability state
- **THEN** it does not install, enable, trust, upgrade, or rewrite target runtime configuration

## REMOVED Requirements

### Requirement: Doctor reports native single-task execution capability
**Reason**: #414 — the owner removed Keel's `/goal`, helper, task-view, and subagent projections; native capabilities need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task.
