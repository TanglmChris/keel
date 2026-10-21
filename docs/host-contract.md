# Host contract: the Claude Code CLI shift and wake path

Keel's CLI shift change and wake depend on what Claude Code reports about its background sessions. This page records what Keel assumes about the host, what Keel does in each case, and the evidence behind each case. Evidence takes one of four forms:

- **scenario**: a test in `scripts/validate_plugin.py`. It runs the real `keel` against a fake `claude` whose answers have the measured shapes.
- **measured**: observed on the real host, with the version and date.
- **deterministic**: Keel's own code or lock, with no host in the loop.
- **unverified**: neither of the above.

CI runners have no Claude Code, so no scenario touches the real host. Real-host measurements use throwaway probe sessions (`claude --bg -w probe-…`), which are removed afterwards. They never touch a working session (#408).

## Path

1. **`keel shift ready --wake`** runs in a CLI session. It stores the note, queues a hand-off with the session id and its process (`CLI session:`, `CLI process:`), and leaves a detached waiter.
2. **The waiter, or `keel tick`, carries out the hand-off once the old session has finished.** It runs these steps:
   - `claude stop <id>`;
   - `claude --bg -n "<role> · <MM-DD HH:MM>" --permission-mode <mode>` in the role's worktree;
   - removing old sessions with `claude rm`, as `shift: keep_old_sessions:` allows (0 by default).
3. **The new session runs `keel shift resume`.**
4. **A role whose CLI session has ended, with a record addressed to it, is woken** by `keel chat wake now <role>` or by the tick. Either runs `claude --bg --resume <id> "<pointer>"`.

## Observations and behaviour

The first three sessions were measured on 2026-10-21 with Claude Code 2.1.304, using `claude agents --json`:

| Session | Host reports | Keel does | Evidence |
|---|---|---|---|
| Busy with a turn | `status: busy` | Waits; no hand-over | scenario `shift-cli-self-shift` |
| Blocked on a question to the owner (AskUserQuestion) | `status: waiting`, `state: blocked`, `waitingFor: input needed` | Waits; never interrupts | measured; scenario `shift-cli-self-shift` |
| Blocked on a tool-permission prompt | `status: waiting`, `state: blocked`, `waitingFor: permission prompt` | Waits; never interrupts | measured |
| Finished its turn | `status: idle`; `state` labels the last message (`done`, or `working` when the reply described pending work, #393) | Hands over. `state` is never read | measured (#393); scenario `shift-cli-self-shift` |
| Stopping | Row without `status` or `pid` at 0.32 s; `claude stop` returns at 0.98 s; process exits at about 3.2 s (2.1.303: 0.83 s / 0.66 s / 2.68 s, #395) | `claude rm` of the session just handed over waits up to 15 s for the process its note recorded. A session whose process still runs is never removed and stays listed. | measured; scenario `shift-cli-removes-after-exit` |
| Stopped | Row without `status` | Treated as finished. Old shifts beyond `keep_old_sessions` are removed once Keel holds their transcript | scenario `shift-cli-keeps-old-sessions` |
| Removed (`claude rm`) | No row in `claude agents --json --all` | A wake does not resume it, and says so | scenario `chat-wake-skips-removed-session` |
| Session list unreadable or `claude` missing | Exit nonzero, no JSON, timeout, or ENOENT | The hand-off stays pending, and `keel shift status` and the patrol risk name the cause. A wake names a missing `claude`. Every host call is bounded (`KEEL_SHIFT_HOST_TIMEOUT_MS`, default 60 s). | scenario `shift-cli-names-host-failure` |
| Resumed after being started with `claude --bg -w` | SessionStart reports the directory it was launched from as `cwd` | The chat hook takes the worktree from the transcript's host project directory | measured; scenario `chat-hook-follows-session-worktree` |
| Resumed with no prompt | Process starts idle; no turn | `keel --update --adopt` uses this to restart idle sessions on a new plugin | measured; scenario `update-adopts-idle-sessions` |

## Failures and recovery

| Case | Keel does | Evidence |
|---|---|---|
| Waiter and tick reach the same hand-off | One hand-over lock per role; a lock older than 2 minutes is taken over; one session is started | deterministic; scenario `shift-cli-self-shift` (run one after the other) |
| Waiter gone | `keel tick` carries out any pending hand-off | scenario `shift-cli-self-shift` |
| New session fails to start | Hand-off `failed` with the host's message; patrol risk; the stopped old session stays listed, and `keel chat wake now <role>` resumes it | scenario `shift-cli-self-shift` |
| Hand-off pending over 15 minutes | Patrol risk, naming the cause when the host could not be asked | scenario `shift-cli-names-host-failure` (the cause); the 15-minute rule is unverified |
| Wake fails to resume | The tick tries again on its next runs, up to three attempts per addressed record; a newer record starts again | scenario `tick-retries-failed-wake` |
| A note or chat record cannot be written | `ready` stops before queueing, so no hand-off runs without its note | unverified |

## Not covered by this loop

The following are unverified:
- the Claude desktop app path (scheduled-task wake, `clear_session`, Remote Control restore);
- Codex;
- a real concurrent race between the waiter and a tick;
- re-queueing a `failed` hand-off.

They stay with #408.
