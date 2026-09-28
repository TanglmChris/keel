## REMOVED Requirements

### Requirement: The Claude plugin is the published package

**Reason**: The Claude plugin now installs from the tagged repository tree, which is the form Anthropic's official directory accepts.
**Migration**: The next `claude plugin update` moves an npm-sourced install to the git-sourced one; nothing is needed from the user.

## MODIFIED Requirements

### Requirement: Native marketplaces install and update Keel in isolation
Keel MUST provide valid repo marketplace catalogs for Codex and Claude. The Codex catalog MUST reference the `plugins/keel` source, and the Claude catalog MUST reference the Keel repository at the release tag, whose tree contains it. Keel MUST prove fresh install, update/cache refresh, discovery in a fresh session, disable/remove, and reinstall without mutating the developer's personal marketplace during tests.

#### Scenario: Codex marketplace installs Keel
- **WHEN** an isolated Codex home adds the repo marketplace and installs Keel
- **THEN** Codex lists one Keel plugin with the expected version and skill inventory
- **AND THEN** a fresh task can discover its skills and hook source

#### Scenario: Claude marketplace installs Keel
- **WHEN** an isolated Claude configuration validates the marketplace and installs Keel from a git copy of the tree under test
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
- **WHEN** the SessionStart hook runs from inside the Claude plugin's tree and `KEEL_CLI` is unset
- **THEN** it invokes the package's own `bin/keel.js` rather than the `keel` on PATH

#### Scenario: CLI is missing or incompatible
- **WHEN** the plugin cannot run a compatible `keel --version` and capability preflight
- **THEN** it reports the exact missing/incompatible prerequisite and explicit install or update command
- **AND THEN** hooks do not fabricate context, gates, or completion

#### Scenario: OpenSpec is resolved through Keel
- **WHEN** Keel initializes, validates, or diagnoses OpenSpec
- **THEN** it uses the package-local compatible OpenSpec command before any standalone fallback
- **AND THEN** doctor reports the selected path and version, reading the declared version from `npm-shrinkwrap.json` before `package-lock.json`

## ADDED Requirements

### Requirement: The Claude plugin is the tagged repository

Keel's Claude plugin MUST be described by a manifest at the repository root, `.claude-plugin/plugin.json`, which declares the canonical skills, the Claude agent, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved from the repository root, and whose version is the release version. Keel's Claude marketplace entry MUST take the plugin from the Keel GitHub repository at the tag `v<version>` of the release version, MUST carry that version, and MUST NOT restate the manifest's components. The repository MUST carry an extensionless executable `bin/keel` and a committed lockfile, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One tree carries the plugin and its CLI
- **WHEN** the root manifest and the Claude marketplace entry are inspected
- **THEN** the manifest's skills and agent resolve inside the repository, its hooks equal `plugins/keel/hooks/hooks.json` after resolving script paths from the root, and its version is the release version
- **AND THEN** the entry's source is the Keel repository at `v<version>`, and the entry declares no skills, agents, or hooks

#### Scenario: The git install carries the pinned OpenSpec
- **WHEN** an isolated Claude configuration installs Keel from a git copy of the tree under test through the committed entry's shape
- **THEN** the installed plugin lists the Keel skills and both hooks, and its `node_modules/.bin/openspec` reports the version the lockfile pins

#### Scenario: An npm-sourced install updates to the git-sourced one
- **WHEN** a configuration that installed Keel from the npm-sourced entry updates after the marketplace names the git-sourced one
- **THEN** the updated plugin is the git-sourced tree and carries the pinned OpenSpec

### Requirement: Each release states its official directory entry

Keel MUST produce, for a release version and the commit its tag points at, the entry Anthropic's official plugin directory would list: the plugin name, the root manifest's description, a category, the homepage, and a `url` source naming the Keel repository pinned to that commit. The release job MUST append that entry to the release notes. Producing it MUST be local and MUST NOT submit anything.

#### Scenario: The entry is pinned to the release commit
- **WHEN** `scripts/official_entry.js` is run with a version and a 40-character commit sha
- **THEN** it prints an entry whose source is the Keel repository URL pinned to that sha, and whose description equals the root manifest's

#### Scenario: A malformed pin is refused
- **WHEN** the version is not `X.Y.Z` or the sha is not 40 hexadecimal characters
- **THEN** the script exits non-zero and prints no entry

#### Scenario: The release notes carry the entry
- **WHEN** the release job creates the release for a landed version
- **THEN** it appends the entry for that version and the tag's commit to the notes
