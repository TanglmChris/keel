# keel-native-plugin-package Specification

## Purpose
Define how Keel ships as one native plugin for Codex and Claude: one canonical plugin source, the marketplaces that install and update it, how the plugin and its CLI stay compatible (on Claude, as the published package that carries its own CLI), the SessionStart and write-guard hooks it packages, and what project setup declares about keeping it current.
## Requirements
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
### Requirement: Native marketplaces install and update Keel in isolation
Keel MUST provide valid repo marketplace catalogs for Codex and Claude. The Codex catalog MUST reference the `plugins/keel` source, and the Claude catalog MUST reference the published package that contains it. Keel MUST prove fresh install, update/cache refresh, discovery in a fresh session, disable/remove, and reinstall without mutating the developer's personal marketplace during tests.

#### Scenario: Codex marketplace installs Keel
- **WHEN** an isolated Codex home adds the repo marketplace and installs Keel
- **THEN** Codex lists one Keel plugin with the expected version and skill inventory
- **AND THEN** a fresh task can discover its skills and hook source

#### Scenario: Claude marketplace installs Keel
- **WHEN** an isolated Claude configuration validates the marketplace and installs Keel from a local copy of the package under test
- **THEN** Claude lists one Keel plugin with the expected version and component inventory
- **AND THEN** an updated plugin applies after `/reload-plugins` or at the next session start

#### Scenario: Development cachebuster is not committed
- **WHEN** a Codex local update smoke needs a cache refresh
- **THEN** a temporary plugin copy receives one `+codex.<cachebuster>` suffix and is reinstalled through its isolated marketplace
- **AND THEN** committed manifests and marketplace entries retain release semver

### Requirement: Plugin and CLI compatibility is explicit
On Claude, Keel's native plugin MUST run the CLI it ships with. On Codex, it MUST treat the separately installed `@christang/keel` CLI and the OpenSpec dependency as executable prerequisites. It MUST diagnose missing, older, newer-incompatible, and matching CLI/plugin versions without installing or upgrading them silently.

#### Scenario: Matching CLI is ready
- **WHEN** plugin base version, Keel CLI base version, OpenSpec minimum, and required capabilities are compatible
- **THEN** skills and hooks may invoke Keel Core commands

#### Scenario: The Claude plugin runs its own CLI
- **WHEN** the SessionStart hook runs from inside the published package and `KEEL_CLI` is unset
- **THEN** it invokes the package's own `bin/keel.js` rather than the `keel` on PATH

#### Scenario: CLI is missing or incompatible
- **WHEN** the plugin cannot run a compatible `keel --version` and capability preflight
- **THEN** it reports the exact missing/incompatible prerequisite and explicit install or update command
- **AND THEN** hooks do not fabricate context, gates, or completion

#### Scenario: OpenSpec is resolved through Keel
- **WHEN** Keel initializes, validates, or diagnoses OpenSpec
- **THEN** it uses the package-local compatible OpenSpec command before any standalone fallback
- **AND THEN** doctor reports the selected path and version, reading the declared version from `npm-shrinkwrap.json` before `package-lock.json`

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

### Requirement: Self-update defaults to the published registry package

`keel --update` MUST default its fetch source to the published `@christang/keel`
npm registry package — a registry-type spec — so self-update succeeds in
environments that disable git-type package fetches. An explicit `--source`
argument or the `KEEL_UPDATE_SOURCE` environment variable MAY still select a git
spec for installing an unreleased build, but the shipped default MUST NOT be a
git-type spec.

#### Scenario: Default update packs the registry package
- **WHEN** `keel --update` runs with no explicit `--source` or `KEEL_UPDATE_SOURCE`
- **THEN** the planned pack source is the published registry package `@christang/keel`
- **AND THEN** the default source is not a git-type spec and needs no git-type fetch

#### Scenario: Explicit git source is still honored for development
- **WHEN** a user passes `--source github:TanglmChris/keel` or sets `KEEL_UPDATE_SOURCE` to a git spec
- **THEN** update packs that explicit git spec instead of the registry default
- **AND THEN** the explicit override takes precedence over the registry default

### Requirement: The Claude plugin is the published package

Keel's Claude marketplace entry MUST take the plugin from the published `@christang/keel` npm package. It MUST pin the package version to the entry's own version, and both MUST equal the release version. The entry MUST act as the plugin's manifest. It MUST declare the canonical skills, the Claude agent, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved inside the package. The package MUST carry an extensionless executable `bin/keel` and a published lockfile, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One artifact carries the plugin and its CLI
- **WHEN** the Claude marketplace entry is inspected
- **THEN** its source is the `@christang/keel` npm package, pinned to the release version, and its own version is that same release version
- **AND THEN** its skills, agent, and hooks resolve to files the published package contains

#### Scenario: The entry's hooks cannot drift from the plugin's
- **WHEN** the entry's inline hooks are compared with `plugins/keel/hooks/hooks.json`
- **THEN** each event, matcher, script, and timeout is equal after the entry's script paths are resolved from the package root

#### Scenario: The package runs as a plugin
- **WHEN** the repository is packed
- **THEN** the packed set contains `bin/keel` with an executable mode, and contains `npm-shrinkwrap.json`

### Requirement: Project setup declares Claude plugin auto-update

On the Claude target, `keel --init` and `keel --install` MUST declare auto-update for the Keel marketplace in the project's `.claude/settings.json`. The declaration is an `extraKnownMarketplaces` entry named `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`. The merge MUST preserve every other setting, MUST keep an existing entry's source, and MUST NOT overwrite an `autoUpdate` value the project already states. `keel --uninstall` MUST remove the entry only when it is exactly the one Keel writes. `keel --doctor` MUST report whether auto-update is declared on, declared off, or not declared, and MUST NOT claim to observe whether the host performs updates.

#### Scenario: Init declares auto-update
- **WHEN** `keel --init --target claude` runs in a repository with no `.claude/settings.json`
- **THEN** the file declares `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`

#### Scenario: Existing settings are kept
- **WHEN** `.claude/settings.json` already holds other settings, or a `keel-marketplace` entry with its own source or `autoUpdate: false`
- **THEN** install keeps those settings, that source, and that `false`
- **AND THEN** running install again changes nothing

#### Scenario: Uninstall removes only Keel's entry
- **WHEN** `keel --uninstall --target claude` runs
- **THEN** an entry equal to Keel's is removed, and one the project changed is kept

#### Scenario: Doctor reports the declaration
- **WHEN** `keel --doctor --target claude` runs
- **THEN** a `plugin auto-update` line reports declared on, declared off by the project, or not declared with the command that declares it

#### Scenario: Other targets are untouched
- **WHEN** `keel --init --target codex` runs
- **THEN** no `.claude/settings.json` is written
