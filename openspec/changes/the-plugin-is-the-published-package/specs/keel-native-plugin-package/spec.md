## ADDED Requirements

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

## MODIFIED Requirements

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
