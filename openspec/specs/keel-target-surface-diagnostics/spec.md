## Purpose

Define Keel diagnostics for target-specific OpenSpec command, skill, completion-gate, and overlay health surfaces.
## Requirements
### Requirement: Keel doctor reports the target surface
`keel --doctor --target <target>` MUST report Keel CLI/OpenSpec readiness, native plugin discovery and version, minimal bootstrap, canonical skill/reference inventory, applicable OpenSpec-generated action/command overlays, hook configuration/trust/activation/behavior, and continuity/gate/goal/helper capability levels. It MUST not require copied Keel skill/hook/adapter trees as v4 health evidence.

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

Keel diagnostics MUST report behavior-oriented capabilities for continuity startup or reinjection, the `task-start`, `task-complete`, and `change-close` gates, optional goal/task view, worktree continuity, and bounded-subagent context or return as `enforced`, `advisory`, or `manual`.

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

### Requirement: Target adapters consume shared Keel Core

Every target-native hook, command, or plugin that projects continuity or gates MUST call the shared Keel Core contract and MUST NOT implement target-local OpenSpec completion policy.

#### Scenario: Adapter mapping may vary by runtime
- **WHEN** two targets use different lifecycle events for continuity reinjection
- **THEN** both expose the same Keel behavior capability and Core result schema
- **AND THEN** the native event names remain adapter details

#### Scenario: Unsupported behavior falls back explicitly
- **WHEN** a target version lacks an equivalent event
- **THEN** the adapter leaves the capability `manual`
- **AND THEN** required execution remains available through the explicit Core command

### Requirement: Codex prompt diagnostics respect CODEX_HOME

Keel MUST resolve Codex command prompts from `CODEX_HOME` when the environment variable is set, and from the user's `.codex` home only when it is unset.

#### Scenario: Isolated Codex prompt home is used

- **WHEN** tests run `keel --init --target codex` and `keel --doctor --target codex` with `CODEX_HOME` pointing to a temporary directory
- **THEN** Codex prompt checks use that temporary directory
- **AND THEN** the test does not read or write the user's real `.codex/prompts` directory

#### Scenario: Missing Codex prompts are visible

- **WHEN** `keel --doctor --target codex` runs with no `opsx-*.md` prompts in the resolved Codex prompt directory
- **THEN** the report marks the Codex command entries as missing
- **AND THEN** the report tells the user to run `keel --init --target codex` or `openspec update --force` to refresh the OpenSpec command surface

### Requirement: Documentation states target-specific limitations

Keel documentation and installed agent protocol text MUST describe effective target capability levels and explicit fallback without making permanent target-name claims that become false as native runtimes evolve.

#### Scenario: Runtime limitation is documented as a capability
- **WHEN** a target cannot prove automatic continuity or gate enforcement
- **THEN** resident protocol text or doctor output identifies the affected behavior as `advisory` or `manual`
- **AND THEN** it identifies the explicit Keel Core command that preserves the workflow

#### Scenario: Runtime upgrade does not require protocol fiction
- **WHEN** a target adds a new lifecycle event in a later version
- **THEN** Keel may update that adapter's probe and event mapping
- **AND THEN** the portable protocol and Core gate semantics remain unchanged

### Requirement: Unsupported hooks are not invented

Keel MUST NOT report a continuity or gate capability as automated or enforced without an installed target-native surface and evidence appropriate to the claimed level.

#### Scenario: Missing adapter state is explicit
- **WHEN** Keel initializes, installs, checks, or diagnoses a target without a usable adapter surface
- **THEN** no unrelated target's hook files are created
- **AND THEN** the behavior capability is `manual` rather than a fabricated installed or enforced state

#### Scenario: Disabled or untrusted hook downgrades
- **WHEN** a hook exists but is disabled, untrusted, or its activation cannot be verified
- **THEN** Keel does not report `enforced`
- **AND THEN** doctor explains the conservative downgrade

### Requirement: Missing Keel overlays are visible

Keel doctor MUST distinguish missing apply/archive overlay markers from unsupported hook gates and missing OpenSpec command files.

#### Scenario: Missing overlay marker is reported

- **WHEN** an apply/archive OpenSpec file exists without the Keel overlay marker
- **AND WHEN** `keel --doctor --target <target>` runs
- **THEN** the report marks the Keel apply/archive overlay as missing
- **AND THEN** the report tells the user to run `keel --init --target <target>` or `keel --install --target <target>` to refresh the overlay

### Requirement: Native plugin diagnostics are behavior-probed
Keel MUST distinguish manifest presence, marketplace discovery, installation, enablement, hook configuration, trust/policy, activation, and observed projection behavior instead of collapsing them into one installed flag.

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

### Requirement: Doctor reports native single-task execution capability
`keel --doctor --target <target>` MUST report goal discovery, explicit activation, continuation, resume, clear or stop behavior, transcript evidence limits, helper restriction enforcement, and observed fallback level separately.

#### Scenario: Codex goal behavior is verified
- **WHEN** isolated Codex probes demonstrate activation, continuation, pause or clear, resume, fingerprint drift stop, and one-task termination
- **THEN** doctor may report goal execution as `enforced`
- **AND THEN** the report includes the observed client and feature configuration

#### Scenario: Claude goal behavior is verified
- **WHEN** isolated Claude probes demonstrate trusted activation, transcript evidence, clear, resume, fingerprint drift stop, and one-task termination
- **THEN** doctor may report goal execution as `enforced`
- **AND THEN** hook trust and managed-policy evidence are reported separately

#### Scenario: Goal exists but activation is not callable
- **WHEN** the target supports `/goal` but Keel cannot safely activate it in the current surface
- **THEN** doctor reports `advisory` and the exact explicit user action
- **AND THEN** version presence alone does not report `enforced`

#### Scenario: Helper restriction is incomplete
- **WHEN** a target cannot prevent nested delegation or repository writes and byte-stability cannot be proven
- **THEN** doctor reports helper execution as `manual`
- **AND THEN** goal execution remains usable without helpers

#### Scenario: OpenCode is inspected
- **WHEN** doctor runs for OpenCode under v4
- **THEN** it reports native goal and helper automation as unsupported manual compatibility
- **AND THEN** it does not search for or recommend v4 OpenCode plugin artifacts

