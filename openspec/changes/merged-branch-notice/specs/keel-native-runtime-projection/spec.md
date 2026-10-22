## MODIFIED Requirements

### Requirement: The session projection reports runtime version alignment

Keel MUST compare three versions: the version of the plugin executing the SessionStart hook, the version of the `keel` CLI it invokes, and the protocol version stamped in the repository's managed block. It MUST report a disagreement on both the human channel and the model payload. When the hook invokes the CLI its own package ships, Keel MUST also compare the `keel` on PATH, because that is the copy the agent's commands resolve first. The report MUST name the remedy of each version older than the newest one it read: the host's plugin update for the plugin or the CLI, and the protocol refresh `keel --install --target <target>`, with the target chosen as `keel context` chooses it, for the protocol; it MUST NOT name the plugin update when only the protocol is older. In Keel's own source repository — `package.json` named `@christang/keel` beside a `plugins/keel` directory — the protocol block is the checked-out branch's own version, so the report MUST say that an older one means the branch is behind its default branch, and MUST NOT name `keel --install` or a Protocol: line. Comparison MUST be exact string equality, MUST be local and offline, and MUST NOT consult any remote source for a newer release.

#### Scenario: A stale runtime is reported on both channels
- **WHEN** the executing plugin, the CLI, and the repository's stamped protocol version are not all equal
- **THEN** the projection names each discovered version and states that they disagree
- **AND THEN** the statement appears on the human channel as well as the model payload, because updating the runtime is the person's action

#### Scenario: An aligned runtime says nothing
- **WHEN** every discoverable version is equal
- **THEN** the projection adds no version line to either channel
- **AND THEN** the rest of the projection is byte-identical to what it would have been without this capability

#### Scenario: A mismatch names how an update applies
- **WHEN** a version disagreement is reported
- **THEN** the report states that a session's hooks are fixed when it loads the plugin, so an updated plugin applies after `/reload-plugins` or at the next session start
- **AND THEN** it does not say that an update applies only after restarting

#### Scenario: A shadowing CLI on PATH is reported
- **WHEN** the hook runs the CLI its package ships, and the `keel` on PATH reports a different version
- **THEN** the drift report names that PATH version and states that it shadows the plugin's CLI for the agent's commands
- **AND THEN** it names removing the global package or updating it to the plugin's version, and runs neither

#### Scenario: No CLI on PATH is not drift
- **WHEN** the hook runs the CLI its package ships and no `keel` is on PATH
- **THEN** the projection adds no version line on that account

#### Scenario: A lagging protocol names the protocol refresh
- **WHEN** the plugin and the CLI report the same version and the repository's stamped protocol version is older
- **THEN** the drift report names `keel --install --target` with the repository's target
- **AND THEN** it does not name the plugin update command

#### Scenario: Keel's source repository names the branch, not a refresh
- **WHEN** the plugin and the CLI report the same version, the repository's stamped protocol version is older, and the repository is Keel's source repository
- **THEN** the drift report says the protocol block is the checked-out branch's version and that the branch is behind its default branch
- **AND THEN** it names neither `keel --install` nor a Protocol: line
