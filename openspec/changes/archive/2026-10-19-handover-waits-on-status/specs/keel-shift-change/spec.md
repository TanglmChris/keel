## MODIFIED Requirements

### Requirement: A CLI session changes its own shift through the waker's queue

In a Claude Code CLI session, `keel shift ready --wake` MUST record the session id and process in the note, queue the hand-off in the chat store, arm no clear waiter, leave a detached hand-over waiter that carries the hand-over out every few seconds until the entry is no longer pending or two hours pass, and say that the session should end its turn. `keel tick` MUST carry out any queued hand-off as well, and the two MUST NOT start two sessions for one entry. A hand-over MUST leave the entry while `claude agents` shows the old session's status as anything but idle — busy, or waiting for input such as a session blocked on a question — and MUST NOT read its job state, which labels the last message rather than whether the turn has ended; once its status is idle, or it is stopped or gone it MUST retire the old session by stopping it with `claude stop`, keeping its conversation, renaming it `<role> · shifted <date time>` by resuming it with `claude --bg --resume <session id> "/rename <name>"` and no other flag until `claude agents` shows the name, and stopping it again, and only then start a new session with `claude --bg -n <role> --permission-mode <mode>` and a prompt to run `keel shift resume`, in the role's worktree, recording `delivered` with the new session id or `failed` with the reason, once per entry. A rename that does not show MUST be recorded and MUST NOT stop the hand-over. `keel shift status` MUST list each hand-off with its state and the command that reopens the old session, and the patrol MUST report a failed hand-off, or one pending over 15 minutes, as a risk.

#### Scenario: The waker hands a CLI shift over once the old session is idle
- **WHEN** `verify`'s CLI session `5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea` (job id `5b14fbae`) runs `keel shift ready --wake`, and `claude agents --json --all` shows it busy, then waiting for input with state `blocked`, then idle with state `working`, with no `keel tick` run
- **THEN** the note records the session id and a waiter was started with no `CLAUDE*` variable in its environment; nothing is stopped or started while it is busy or waiting; once it is idle, though its state still reads `working`, the calls are, in order, `stop 5b14fbae`, `--bg --resume 5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea "/rename verify · shifted …"`, `stop 5b14fbae`, and `--bg -n verify --permission-mode auto` with a `keel shift resume` prompt in verify's worktree; status shows it delivered with the new session and `claude attach 5b14fbae`

#### Scenario: The tick and the waiter start one session
- **WHEN** a hand-over lock younger than two minutes exists for `verify` and `keel tick` runs, and then the lock is removed and `keel tick` runs twice
- **THEN** the first tick starts nothing; the second starts one session and the third none

#### Scenario: A rename that does not show does not stop the hand-over
- **WHEN** the old session's name never changes after the `/rename` resume
- **THEN** the new session still starts, and status shows the hand-off delivered with the rename recorded as not shown

#### Scenario: A failed hand-off is a risk
- **WHEN** the new session cannot start
- **THEN** status shows the hand-off failed with the reason, and `keel patrol` reports it as a risk
