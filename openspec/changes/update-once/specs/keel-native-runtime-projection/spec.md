## MODIFIED Requirements

### Requirement: Keel reports runtime versions and does not manage them

Keel's hooks and session projections MUST NOT install, update, pin, or resolve a plugin or CLI version, and MUST NOT offer to. Their scope over the runtime is limited to reporting what they observe, running a newer installed copy of their own script as the hand-off requirement allows, and naming the host command the reader may choose to run. Only the owner-run `keel --update` MAY install or update a plugin or CLI, and only through the hosts' documented commands.

#### Scenario: The report does not act
- **WHEN** a version disagreement is reported
- **THEN** Keel performs no installation, update, or version resolution
- **AND THEN** any remedy it names is the host's own documented command, presented as the reader's decision

#### Scenario: A hook never installs
- **WHEN** any Keel hook runs, whether or not a newer version is published or installed
- **THEN** it runs no package manager, marketplace, or plugin command and makes no network request

## ADDED Requirements

### Requirement: A Claude hook runs the newest installed compatible copy of itself

Each Keel hook script in the Claude plugin MUST, before its own logic, read the host's local install record beside the plugin. When that record names this plugin at another install path that exists, whose plugin version is greater than the running one with the same major version, and which contains the same script, the script MUST run that copy with the same arguments, standard input, and environment, plus a marker naming the running version and the new plugin root, and MUST relay its standard output, standard error, and exit status unchanged. In every other case — no record, an unreadable record, the same or an older version, a different major version, a missing script, a spawn failure, a timeout, or a run that is already a hand-off — it MUST run its own logic exactly as without this requirement. Reading the record MUST be local and offline. On Codex, which resolves the plugin root per hook call, the hand-off MUST NOT occur.

#### Scenario: An installed update runs in the existing session
- **WHEN** a hook script loaded from version A runs while the install record names the same plugin at an existing version B greater than A with the same major
- **THEN** version B's copy of that script runs with the same input and its output is what the host receives

#### Scenario: A hand-off does not hand off again
- **WHEN** the script runs with the hand-off marker set
- **THEN** it runs its own logic without consulting the record

#### Scenario: An incompatible or missing install runs the loaded logic
- **WHEN** the recorded version has a different major, its tree lacks the script, its path does not exist, or spawning it fails
- **THEN** the loaded script's own logic runs and the host receives the same output it would have without this requirement

#### Scenario: An aligned session pays no hand-off
- **WHEN** the install record names the running package root
- **THEN** no process is spawned

### Requirement: The write guard keeps the loaded logic while a task is active

The Claude write guard MUST NOT hand off to a newer installed copy while the repository it resolves has a guard manifest, and MUST hand off on its first call after the manifest is gone. A guard that hands off and whose newer copy fails to run MUST enforce with its own logic rather than allow the write.

#### Scenario: An active task keeps its guard
- **WHEN** a newer compatible plugin is installed and `keel/guard.json` exists in the repository
- **THEN** the loaded guard decides, and a write outside Touch is denied exactly as before the install

#### Scenario: The guard adopts the update after the task
- **WHEN** the manifest is removed and the next edit is checked
- **THEN** the newer guard copy decides that edit

#### Scenario: A failed hand-off does not open the guard
- **WHEN** the guard would hand off and the newer copy cannot be spawned
- **THEN** the loaded guard's own decision is returned

### Requirement: An adopted update is silent unless a reload is still needed

When the session projection runs as a hand-off, it MUST report versions as the copy that ran. It MUST compare the loaded plugin tree with the running one on skill content, agent content, and declared hooks; when all are equal it MUST add nothing, and when any differs it MUST add one line on both channels stating that hooks now run the new version, naming what differs, and naming `/reload-plugins` as the only remaining step.

#### Scenario: A compatible update is silent
- **WHEN** a handed-off SessionStart finds the loaded and running trees equal in skills, agents, and declared hooks, and the CLI and protocol versions agree with the running version
- **THEN** the projection adds no version or update line

#### Scenario: Changed skills ask only for a reload
- **WHEN** a handed-off SessionStart finds the skills differ
- **THEN** it adds one line naming the running version, that skills changed, and `/reload-plugins`, and does not name an update command
