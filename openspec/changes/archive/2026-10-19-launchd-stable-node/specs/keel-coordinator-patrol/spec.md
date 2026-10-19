## ADDED Requirements

### Requirement: Keel's launchd jobs name a node that outlives an upgrade

The LaunchAgents that `keel tick task` prints and `keel chat wake add` and the chat bridge write MUST name, as their first program argument, the `node` on `PATH` whose real path is the running node's, and `process.execPath` only when none is; and MUST leave every directory inside a Claude plugin cache out of their `PATH`. `keel --doctor` MUST report each `dev.keel.*` LaunchAgent whose first program argument does not exist, naming the file, the missing path and the command that re-creates it, and MUST report none as a problem when every such path exists.

#### Scenario: The printed job names the symlink, not its target
- **WHEN** `keel tick task` runs under a node reached through `<bin>/node`, a symlink to a versioned directory, with a plugin cache directory first on `PATH`
- **THEN** the plist's first program argument is `<bin>/node`, and its `PATH` holds `<bin>` and no plugin cache directory

#### Scenario: The chat waker's LaunchAgent does the same
- **WHEN** `keel chat wake add` writes its LaunchAgent under the same conditions
- **THEN** its first program argument is `<bin>/node` and its `PATH` holds no plugin cache directory

#### Scenario: Doctor reports a job whose node is gone
- **WHEN** the LaunchAgents directory holds `dev.keel.tick.x.plist` naming a node path that does not exist, and `keel --doctor` runs, and then the plist names an existing path
- **THEN** the first run prints a `launchd` problem line naming `dev.keel.tick.x.plist`, the missing path and `keel tick task`; the second prints `launchd: ok`
