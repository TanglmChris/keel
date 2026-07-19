# keel-native-plugin-package Specification

## Purpose
TBD - created by archiving change native-plugin-packaging. Update Purpose after archive.
## Requirements
### Requirement: Keel has one canonical dual-runtime plugin source
Keel 4.0.0 MUST package one plugin at `plugins/keel` with native Codex and Claude manifests, one canonical portable skill/reference tree, and default-discovered hook assets. It MUST NOT generate per-target copies of the same skill or protocol authority.

#### Scenario: Codex manifest is native
- **WHEN** the plugin source is inspected or installed by the supported Codex baseline
- **THEN** `plugins/keel/.codex-plugin/plugin.json` has valid native metadata, name `keel`, version `4.0.0`, and the canonical skills path
- **AND THEN** it uses default hook discovery rather than an unsupported explicit hooks field

#### Scenario: Claude manifest is native
- **WHEN** the plugin source is validated or installed by the supported Claude baseline
- **THEN** `plugins/keel/.claude-plugin/plugin.json` has valid native metadata, name `keel`, version `4.0.0`, and the same canonical skills/hooks inventory

#### Scenario: Skill authority is singular
- **WHEN** the package, repository, or installed plugin inventory is inspected
- **THEN** every Keel skill and reference has one canonical source under `plugins/keel/skills`
- **AND THEN** no `src/skills` or `dist/<target>/skills` copy is current authority

### Requirement: Native marketplaces install and update Keel in isolation
Keel MUST provide valid repo marketplace catalogs for Codex and Claude that reference the same `plugins/keel` source and MUST prove fresh install, update/cache refresh, discovery in a fresh session, disable/remove, and reinstall without mutating the developer's personal marketplace during tests.

#### Scenario: Codex marketplace installs Keel
- **WHEN** an isolated Codex home adds the repo marketplace and installs Keel
- **THEN** Codex lists one Keel plugin with the expected version and skill inventory
- **AND THEN** a fresh task can discover its skills and hook source

#### Scenario: Claude marketplace installs Keel
- **WHEN** an isolated Claude configuration validates the marketplace and installs Keel
- **THEN** Claude lists one Keel plugin with the expected version and component inventory
- **AND THEN** update and restart semantics pick up a changed temporary test version

#### Scenario: Development cachebuster is not committed
- **WHEN** a Codex local update smoke needs a cache refresh
- **THEN** a temporary plugin copy receives one `+codex.<cachebuster>` suffix and is reinstalled through its isolated marketplace
- **AND THEN** committed manifests and marketplace entries retain release semver

### Requirement: Plugin and CLI compatibility is explicit
Keel's native plugin MUST treat the separately installed `@christang/keel` CLI and OpenSpec dependency as executable prerequisites. It MUST diagnose missing, older, newer-incompatible, and matching CLI/plugin versions without installing or upgrading them silently.

#### Scenario: Matching CLI is ready
- **WHEN** plugin base version, Keel CLI base version, OpenSpec minimum, and required capabilities are compatible
- **THEN** skills and hooks may invoke Keel Core commands

#### Scenario: CLI is missing or incompatible
- **WHEN** the plugin cannot run a compatible `keel --version` and capability preflight
- **THEN** it reports the exact missing/incompatible prerequisite and explicit install or update command
- **AND THEN** hooks do not fabricate context, gates, or completion

#### Scenario: OpenSpec is resolved through Keel
- **WHEN** Keel initializes, validates, or diagnoses OpenSpec
- **THEN** it uses the package-local compatible OpenSpec command before any standalone fallback
- **AND THEN** doctor reports the selected path and version

### Requirement: Shared SessionStart hook is safe and optional
The plugin MUST package one common command-based SessionStart hook that projects current Keel context when supported and trusted. The hook MUST remain correct to skip and MUST NOT write project/OpenSpec state, start a task/goal, or block unrelated work.

#### Scenario: Trusted hook projects context
- **WHEN** a supported Codex or Claude session starts with the plugin enabled, hook trusted/allowed, and compatible CLI available
- **THEN** the hook invokes shared Keel projection and injects concise current context using that runtime's supported output shape
- **AND THEN** the projection identifies itself as disposable

#### Scenario: Hook is unavailable
- **WHEN** the hook is disabled, untrusted, policy-blocked, unsupported, times out, or lacks a compatible CLI
- **THEN** the session remains usable through the minimal bootstrap and explicit `keel context`
- **AND THEN** no capability is reported as enforced

### Requirement: V4 migration removes only known packaged duplication
Keel MUST remove custom manifest, builder, generated dist, adapters, duplicate protocol/skill copies, and target-copy installer behavior only after native parity is proven. Migration MUST preserve user-modified legacy files and existing OpenCode files.

#### Scenario: Known generated file is retired
- **WHEN** a legacy path matches a known packaged Keel version and its native replacement passes
- **THEN** migration may remove the redundant path and record it in release evidence

#### Scenario: User-modified legacy file is preserved
- **WHEN** a legacy installed or generated path differs from every known packaged version
- **THEN** migration leaves it unchanged and reports its exact path and manual choice

#### Scenario: OpenCode is left outside v4
- **WHEN** migration encounters `.opencode` Keel files
- **THEN** it preserves them and reports compatibility-only status
- **AND THEN** no v4 OpenCode plugin, hook, marketplace, or acceptance path is generated

### Requirement: Keel 4.0.0 release surfaces stay aligned
The npm package, Codex manifest, Claude manifest, applicable marketplace metadata, bootstrap/protocol markers, capability schema, changelog, migration diagnostics, and tests MUST report one compatible Keel 4.0.0 base version.

#### Scenario: Package and plugins agree
- **WHEN** release artifacts are inspected
- **THEN** npm and both plugin manifests report base version `4.0.0`
- **AND THEN** no current artifact advertises Keel 3.x as its protocol

#### Scenario: Package contents are thin
- **WHEN** the packed npm tarball is inspected
- **THEN** it includes the CLI/Core, OpenSpec schema assets, `plugins/keel`, required migration/validation scripts, README, and license metadata
- **AND THEN** it excludes custom target `dist` trees and duplicate skill/protocol authority

### Requirement: Continuity projection is compaction-aware
The plugin's session continuity projection MUST distinguish the runtime-reported start source and MUST reinject a recomputed, disposable continuity pointer after a compaction, using only OpenSpec and Git as input.

#### Scenario: Compact source reinjects the task pointer
- **WHEN** a session starts with a compact source while a selection is recomputable
- **THEN** the projection surfaces the recomputed selection, the selected task's recorded Contract fingerprint line when present, and the exact next command
- **AND THEN** the fingerprint is labeled as recorded, not verified, and no drift verdict is claimed

#### Scenario: Unknown source falls back safely
- **WHEN** the start source is absent, unrecognized, or a clear
- **THEN** the projection falls back to the generic startup view
- **AND THEN** the hook still never writes, never blocks, and exits zero

#### Scenario: Projection stays a pointer
- **WHEN** any continuity projection is emitted
- **THEN** it remains line-bounded and contains pointers and commands rather than task authority payloads
- **AND THEN** OpenSpec and Git remain the only durable recovery authority

### Requirement: Pre-compaction preservation is probed, not assumed
Keel MUST NOT claim or rely on a pre-compaction hook ability without behavioral probe evidence, and MUST declare post-compact reinjection as the fallback when the surface is absent or unverified.

#### Scenario: Probed ability is used honestly
- **WHEN** a behavioral probe proves the runtime's pre-compaction surface can carry a continuity instruction
- **THEN** the plugin may use it and the capability reports the observed level
- **AND THEN** the evidence backing the claim is recorded

#### Scenario: Unverified surface stays manual
- **WHEN** the pre-compaction contract is absent, disabled, or unverified
- **THEN** the shipped behavior is post-compact reinjection only
- **AND THEN** doctor reports the pre-compaction capability as manual with the reason

#### Scenario: Unsupported targets document the manual command
- **WHEN** the target has no verified compaction hook surface
- **THEN** guidance documents the manual `keel project --event compaction` reinjection command
- **AND THEN** no native compaction automation is claimed for that target

### Requirement: Installed markers and shipped documentation agree with the package surface
The managed-block marker version MUST have exactly one canonical source in the repository, install code MUST derive its marker from that source, and shipped documentation MUST describe the actual package layout and development flow.

#### Scenario: Marker version is single-sourced
- **WHEN** installation writes or refreshes a managed block
- **THEN** the marker version comes from the one canonical source
- **AND THEN** validation fails if the marker literal is restated elsewhere in the repository

#### Scenario: Detection stays version-agnostic
- **WHEN** installation, upgrade, or uninstall detects an existing managed block
- **THEN** any marker version is recognized
- **AND THEN** conservative upgrade and uninstall semantics are unchanged

#### Scenario: Documentation matches the surface
- **WHEN** shipped documentation describes the repository layout or development flow
- **THEN** it references only surfaces that exist in the package
- **AND THEN** validation fails on references to retired surfaces

