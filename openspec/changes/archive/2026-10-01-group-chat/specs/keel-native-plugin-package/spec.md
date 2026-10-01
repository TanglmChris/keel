## MODIFIED Requirements

### Requirement: The Claude plugin is the tagged repository

Keel's Claude plugin MUST be described by a manifest at the repository root, `.claude-plugin/plugin.json`, which declares the canonical skills, the Claude agent, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved from the repository root plus the Claude-only chat hooks — UserPromptSubmit, FileChanged, and SessionEnd groups, and a second SessionStart hook, each running `mail-hook.js` — and whose version is the release version. The Claude-only hooks MUST NOT appear in `plugins/keel/hooks/hooks.json`, which Codex also loads. Keel's Claude marketplace entry MUST take the plugin from the Keel GitHub repository at the tag `v<version>` of the release version, MUST carry that version, and MUST NOT restate the manifest's components. The repository MUST carry an extensionless executable `bin/keel` and a committed lockfile, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One tree carries the plugin and its CLI
- **WHEN** the root manifest and the Claude marketplace entry are inspected
- **THEN** the manifest's skills and agent resolve inside the repository, its hooks equal `plugins/keel/hooks/hooks.json` after resolving script paths from the root plus exactly the Claude-only chat hooks, and its version is the release version
- **AND THEN** the entry's source is the Keel repository at `v<version>`, and the entry declares no skills, agents, or hooks

#### Scenario: The Codex-shared hooks carry no Claude-only event
- **WHEN** `plugins/keel/hooks/hooks.json` is inspected
- **THEN** it declares only SessionStart and PreToolUse and no `asyncRewake` field

#### Scenario: The git install carries the pinned OpenSpec
- **WHEN** an isolated Claude configuration installs Keel from a git copy of the tree under test through the committed entry's shape
- **THEN** the installed plugin lists the Keel skills and both hooks, and its `node_modules/.bin/openspec` reports the version the lockfile pins

#### Scenario: An npm-sourced install updates to the git-sourced one
- **WHEN** a configuration that installed Keel from the npm-sourced entry updates after the marketplace names the git-sourced one
- **THEN** the updated plugin is the git-sourced tree and carries the pinned OpenSpec
