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

### Requirement: Doctor reports keel-* skills as a plugin surface

`keel --doctor` MUST report the `keel-*` behavioral skills as a plugin-delivered
inventory and MUST NOT imply the CLI installs them. When the Keel plugin (and
therefore the skills) is absent, doctor MUST report the gap with explicit
remediation to install the plugin.

#### Scenario: keel-* inventory is attributed to the plugin

- **WHEN** `keel --doctor` reports the skill surface
- **THEN** it presents the `keel-*` behavioral skills as delivered by the Keel plugin
- **AND THEN** it does not report them as CLI-installed target files

#### Scenario: Missing plugin is actionable

- **WHEN** the Keel plugin is not installed
- **THEN** doctor reports the `keel-*` skills as missing with remediation to install the plugin
- **AND THEN** it does not silently claim the skills are present

### Requirement: Doctor distinguishes keel-resolvable openspec from PATH-reachable

`keel --doctor` MUST distinguish an openspec that Keel can resolve internally from
one reachable as a bare `openspec` command on PATH. When the resolved openspec is
not PATH-reachable, doctor MUST report a warning rather than `ok` and MUST name the
working invocation.

#### Scenario: Internal-only openspec warns

- **WHEN** Keel resolves its internal openspec shim but bare `openspec` is not on PATH
- **THEN** doctor reports the openspec line as a warning, not `ok`
- **AND THEN** it names the working invocation, such as `keel openspec`

#### Scenario: PATH-reachable openspec is ok

- **WHEN** bare `openspec` is reachable on PATH
- **THEN** doctor reports the openspec line as `ok`

### Requirement: Keel install does not damage its own source repository
Keel's install and init paths MUST NOT overwrite repository content that only exists in Keel's own source repository with the consumer-facing bootstrap asset. When the target is Keel's own repository, the bootstrap write MUST be skipped and reported as skipped.

#### Scenario: Install skips the bootstrap write in Keel's own repository
- **WHEN** `keel --install` or `keel --init` runs in Keel's own source repository
- **THEN** the managed `AGENTS.md` block is left byte-identical
- **AND THEN** the command reports the skip explicitly rather than silently omitting the step

#### Scenario: Install still writes the bootstrap in a consuming project
- **WHEN** the same command runs in a project that consumes Keel
- **THEN** the managed `AGENTS.md` block is written from the bootstrap asset as before

### Requirement: Doctor reports the CLI resolution hazard in Keel's own repository

An author changing Keel's own gate, contract, or capability code runs gate commands against a CLI that may not be the code under change: a bare `keel` resolves to the installed package, not to the working tree. The failure mode is a silently stale result rather than an error, so `keel --doctor` MUST report the hazard and the working invocation when — and only when — it runs in Keel's own source repository.

#### Scenario: Source repository is told to use its own CLI
- **WHEN** `keel --doctor` runs in Keel's own source repository
- **THEN** it reports that gate commands verify the installed CLI unless invoked through the repository's own entry point, and names that invocation including the explicit repository argument it requires
- **AND THEN** the line is advisory, and reports no failure

#### Scenario: A consuming project is not shown the hazard
- **WHEN** the same command runs in a project that consumes Keel
- **THEN** the line is absent, because the installed CLI is the code under test there and the hazard does not exist

### Requirement: A dry run accounts for every write its real run would make

A dry run exists so a reader can decide whether to proceed. It is therefore held
to both directions of accuracy: it MUST name every write the corresponding real
run would perform, and it MUST NOT name a write that would not happen. A dry run
that under-reports offers a promise it does not keep, and one that over-reports
trains the reader to ignore it — both leave the reader worse off than no dry run,
because both are relied upon.

Where a real run performs a step outside the plan the dry run enumerates, that
step MUST be represented in the dry run too. Where a dry run classifies work as
pending, it MUST determine that from the same computation the real run uses,
rather than from a separate listing that can drift from it.

#### Scenario: The plan covers steps the enumerated plan does not

- **WHEN** a real run performs a write through a step outside its enumerated action plan
- **THEN** the dry run reports that step's writes alongside the enumerated ones
- **AND THEN** a reader of the dry run is not surprised by a file the real run changes

#### Scenario: A dry run does not claim writes that will not happen

- **WHEN** a dry run inspects a set of surfaces of which only some need changing
- **THEN** it names only the ones that would change, and summarises the rest as current
- **AND THEN** its counts match what the real run reports afterwards

#### Scenario: Both paths share one definition of pending work

- **WHEN** the dry run and the real run classify the same surface
- **THEN** they agree, because the classification is computed the same way in both
- **AND THEN** a change to what counts as current cannot move one without the other
