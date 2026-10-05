## MODIFIED Requirements

### Requirement: The bridge runs unattended but stays visible and controllable

`keel chat bridge install` MUST write a user LaunchAgent plist (`RunAtLoad`, `KeepAlive`, absolute node and CLI paths) and load it with `launchctl`; `uninstall`, `start`, and `stop` MUST unload or load it; `pause <duration>` MUST make the running bridge disconnect and queue until the time passes; `status` MUST report installed, running, connected, paused, served projects, last event, ignored count, and unposted count. `start` MUST retry a bootstrap that fails because an unload is still in progress until it succeeds or a bounded wait ends, MUST fail naming launchctl's output when the service still cannot be loaded, and MUST NOT report success for a failed bootstrap; `stop` and `install` MUST wait, bounded, until launchd has unloaded the service. For a status file written by a bridge launchd started, and where launchd reports the service's state, `status` MUST report the bridge as not running when the service is unloaded or its pid differs from the status file's. The running bridge MUST write its status, post an online notice to mapped channels on start and a stopped notice on clean stop, reconnect with backoff after a disconnect or a `refresh_requested`, and exit so launchd restarts it when Keel's package version changes. For a Slack-enabled project the session-start notice MUST include one bridge status line.

#### Scenario: Pause queues and resume delivers
- **WHEN** `keel chat bridge pause 2s` runs, `rtl` posts during the pause, and the pause expires
- **THEN** the fake server receives nothing during the pause and the message once afterwards

#### Scenario: Install writes a loadable agent
- **WHEN** `keel chat bridge install` runs with the launchctl and LaunchAgents seams pointed at test doubles
- **THEN** the plist exists with `RunAtLoad`, `KeepAlive`, and `chat bridge run`, and the launchctl double was asked to bootstrap it

#### Scenario: The session learns the bridge is down
- **WHEN** a Slack-enabled project has no running bridge and the SessionStart chat hook runs for a bound role
- **THEN** its notice contains a line stating the bridge is not running

#### Scenario: Start after stop waits for the unload
- **WHEN** a launchctl double fails the first two bootstraps after a bootout with `5: Input/output error`, and `keel chat bridge stop` then `keel chat bridge start` run
- **THEN** `start` exits 0, the double was asked to bootstrap three times, and it reports the service loaded

#### Scenario: A bootstrap that never succeeds is reported
- **WHEN** the launchctl double fails every bootstrap with `5: Input/output error`
- **THEN** `keel chat bridge start` exits non-zero and names launchctl's output

#### Scenario: A stale status file is not reported as running
- **WHEN** a status file written under launchd names a live pid but the launchctl double reports the service unloaded, or loaded with another pid
- **THEN** `keel chat bridge status --json` reports `running: false`
