## ADDED Requirements

### Requirement: A CLI session changes its own shift through the waker's queue

In a Claude Code CLI session, `keel shift ready --wake` MUST record the session id and process in the note, queue the hand-off in the chat store, arm no clear waiter, and say that `keel tick` hands over once the session is idle. `keel tick` MUST leave a queued hand-off while the old session is busy; once it is idle or gone it MUST stop it with `claude stop`, keeping its conversation, and start a new session with `claude --bg -n <role> --permission-mode <mode>` and a prompt to run `keel shift resume`, in the role's worktree, recording `delivered` with the new session id or `failed` with the reason, once per entry. `keel shift status` MUST list each hand-off with its state and the command that reopens the old session, and the patrol MUST report a failed hand-off, or one pending over 15 minutes, as a risk.

#### Scenario: The waker hands a CLI shift over once the old session is idle
- **WHEN** `verify`'s CLI session `5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea` (job id `5b14fbae`) runs `keel shift ready --wake`, and `keel tick` runs while `claude agents --json` shows it busy, then idle, then again
- **THEN** the note records the session id; the first tick does nothing and status shows the hand-off pending; the second stops job `5b14fbae` and starts `claude --bg -n verify --permission-mode auto` with a `keel shift resume` prompt in verify's worktree; status shows it delivered with the new session and `claude attach 5b14fbae`; the third starts nothing

#### Scenario: A failed hand-off is a risk
- **WHEN** the new session cannot start
- **THEN** status shows the hand-off failed with the reason, and `keel patrol` reports it as a risk
