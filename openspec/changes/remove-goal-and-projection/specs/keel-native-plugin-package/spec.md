## MODIFIED Requirements

### Requirement: The Claude plugin is the npm package

Keel's Claude plugin MUST be described by a manifest at the repository root, `.claude-plugin/plugin.json`, which declares the canonical skills, the Claude-only command `plugins/keel/commands/shift.md`, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved from the repository root plus the Claude-only chat hooks — UserPromptSubmit, FileChanged, and SessionEnd groups, and a second SessionStart hook, each running `mail-hook.js` — and whose version is the release version. The Claude-only hooks MUST NOT appear in `plugins/keel/hooks/hooks.json`, while Codex explicitly selects its host-compatible `plugins/keel/hooks/codex.json`. The npm package MUST ship that manifest, so that the package root is the plugin. Keel's Claude marketplace entry MUST take the plugin from the npm package `@christang/keel` at exactly the release version, MUST carry that version, and MUST NOT restate the manifest's components. The package MUST carry an extensionless executable `bin/keel` and its `npm-shrinkwrap.json`, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One package carries the plugin and its CLI
- **WHEN** the root manifest, the npm package's file list, and the Claude marketplace entry are inspected
- **THEN** the manifest's skills and command resolve inside the repository, its hooks equal `plugins/keel/hooks/hooks.json` after resolving script paths from the root plus exactly the Claude-only chat hooks, its version is the release version, and `npm pack` includes it
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
