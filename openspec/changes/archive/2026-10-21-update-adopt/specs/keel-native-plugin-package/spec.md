## ADDED Requirements

### Requirement: An update names the sessions on an older plugin and adopts the idle ones on request
`keel --update` MUST name the Claude Code background sessions started before the installed Keel plugin's `lastUpdated`. With `--adopt` it MUST restart each idle one with `claude stop`, waiting for its process to exit, then `claude --bg --resume <session id>` with no prompt and no other flag. It MUST leave a busy or waiting session, one whose worktree has `keel/guard.json`, and its own session, and name them.

#### Scenario: Adopting restarts only the idle sessions on the older plugin
- **WHEN** after the Claude plugin update, `claude agents --json` lists an idle, a busy, and a guarded session started before `lastUpdated`, an idle one started after it, and the session running the command, and `keel --update --adopt` runs
- **THEN** only the idle older session is stopped and, once its process has exited, resumed with `--bg --resume <its id>` and nothing else
- **AND THEN** the line names it as adopted and the busy and guarded sessions as left, and the command exits 0

#### Scenario: Without adopting, the older sessions are only named
- **WHEN** the same sessions are listed and `keel --update` runs without `--adopt`
- **THEN** no session is stopped or resumed
- **AND THEN** one line names the sessions started before the update and that `keel --update --adopt` restarts the idle ones
