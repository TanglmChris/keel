## ADDED Requirements

### Requirement: The Claude plugin is the npm package

Keel's Claude plugin MUST be described by a manifest at the repository root, `.claude-plugin/plugin.json`, which declares the canonical skills, the Claude agent, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved from the repository root plus the Claude-only chat hooks — UserPromptSubmit, FileChanged, and SessionEnd groups, and a second SessionStart hook, each running `mail-hook.js` — and whose version is the release version. The Claude-only hooks MUST NOT appear in `plugins/keel/hooks/hooks.json`, while Codex explicitly selects its host-compatible `plugins/keel/hooks/codex.json`. The npm package MUST ship that manifest, so that the package root is the plugin. Keel's Claude marketplace entry MUST take the plugin from the npm package `@christang/keel` at exactly the release version, MUST carry that version, and MUST NOT restate the manifest's components. The package MUST carry an extensionless executable `bin/keel` and its `npm-shrinkwrap.json`, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One package carries the plugin and its CLI
- **WHEN** the root manifest, the npm package's file list, and the Claude marketplace entry are inspected
- **THEN** the manifest's skills and agent resolve inside the repository, its hooks equal `plugins/keel/hooks/hooks.json` after resolving script paths from the root plus exactly the Claude-only chat hooks, its version is the release version, and `npm pack` includes it
- **AND THEN** the entry's source is `npm` `@christang/keel` at the release version, and the entry declares no skills, agents, or hooks

#### Scenario: The Codex-shared hooks carry no Claude-only event
- **WHEN** `plugins/keel/hooks/hooks.json` is inspected
- **THEN** it declares only SessionStart and PreToolUse and no `asyncRewake` field

#### Scenario: The packaged install carries the pinned OpenSpec
- **WHEN** an isolated Claude configuration installs Keel from the package `npm pack` produces for the tree under test, through the committed entry's shape
- **THEN** the installed plugin lists the Keel skills and both hooks, and its `node_modules/.bin/openspec` reports the version the lockfile pins

#### Scenario: A git-sourced install updates to the npm-sourced one
- **WHEN** a configuration that installed Keel from the git-sourced entry updates after the marketplace names the npm-sourced one
- **THEN** the updated plugin is the npm package's tree and carries the pinned OpenSpec

## MODIFIED Requirements

### Requirement: Native marketplaces install and update Keel in isolation
Keel MUST provide valid repo marketplace catalogs for Codex and Claude. The Codex catalog MUST reference the `plugins/keel` source, and the Claude catalog MUST reference the `@christang/keel` npm package at the release version. Keel MUST prove fresh install, update/cache refresh, discovery in a fresh session, disable/remove, and reinstall without mutating the developer's personal marketplace during tests.

#### Scenario: Codex marketplace installs Keel
- **WHEN** an isolated Codex home adds the repo marketplace and installs Keel
- **THEN** Codex lists one Keel plugin with the expected version and skill inventory
- **AND THEN** a fresh task can discover its skills and hook source

#### Scenario: Claude marketplace installs Keel
- **WHEN** an isolated Claude configuration validates the marketplace and installs Keel from the package `npm pack` produces for the tree under test
- **THEN** Claude lists one Keel plugin with the expected version and component inventory
- **AND THEN** an updated plugin applies after `/reload-plugins` or at the next session start

#### Scenario: Development cachebuster is not committed
- **WHEN** a Codex local update smoke needs a cache refresh
- **THEN** a temporary plugin copy receives one `+codex.<cachebuster>` suffix and is reinstalled through its isolated marketplace
- **AND THEN** committed manifests and marketplace entries retain release semver

## REMOVED Requirements

### Requirement: The Claude plugin is the tagged repository

**Reason**: replaced by "The Claude plugin is the npm package" (#337, owner 2026-10-18). The plugin is taken from the npm package again; the root manifest, the Claude-only hooks, the CLI and the lockfile carry over unchanged.
**Migration**: an install from the git-sourced entry updates to the npm-sourced one with `claude plugin update`.
