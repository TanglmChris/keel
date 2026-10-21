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
| Resumed after being started with `claude --bg -w` | SessionStart reports the directory it was launched from as both `cwd` and `transcript_path`. That transcript path names a file that does not exist, because the session keeps writing `<id>.jsonl` in its worktree's project directory (2.1.304, probe of 2026-10-21, #441) | The chat hook uses the transcript that exists, `<config>/projects/*/<session_id>.jsonl`, and takes the worktree from that file's project directory | measured; scenario `chat-hook-follows-session-worktree` |
| Resumed with no prompt | Process starts idle; no turn | `keel --update --adopt` uses this to restart idle sessions on a new plugin | measured; scenario `update-adopts-idle-sessions` |

## Failures and recovery

| Case | Keel does | Evidence |
|---|---|---|
| Waiter and tick reach the same hand-off at the same moment | A runner holds the role's lock only to claim the entry as `starting` (its process and time), then releases it before any host call; the others act only on an unclaimed entry, so one session is started | scenario `shift-cli-handover-claims-once` (two ticks and a waiter started together); `shift-cli-self-shift` (a held lock) |
| Waiter gone | `keel tick` carries out any pending hand-off | scenario `shift-cli-self-shift` |
| Runner dies while starting the new session | The claim stays `starting`. Once its process is gone, or after 10 minutes, the next runner adopts a listed session named `<role> · …` in the role's worktree started since the claim, and starts nothing; with none listed the entry is `failed` and retried as below | scenario `shift-cli-handover-claims-once` |
| New session fails to start | Hand-off `failed` with the host's message; patrol risk. The tick tries again up to three start attempts per entry, adopting a session already listed instead of starting one; after the third, status and the patrol name `keel chat wake now <role>`, which resumes the stopped old session. Not retried once the old session runs again, nor for an entry that records no attempt count, written by an older Keel | scenario `shift-cli-retries-failed-handover`; `shift-cli-self-shift` |
| Hand-off pending over 15 minutes | Patrol risk, naming the cause when the host could not be asked | scenario `shift-cli-names-host-failure` (the cause); the 15-minute rule is unverified |
| Wake fails to resume | The tick tries again on its next runs, up to three attempts per addressed record; a newer record starts again | scenario `tick-retries-failed-wake` |
| A note or chat record cannot be written | `ready` stops before queueing, so no hand-off runs without its note | unverified |

## Outside this contract

- **The Claude desktop app path** (scheduled-task wake, `clear_session`, Remote Control restore) is not maintained for this team. The owner moved the team to background CLI sessions on 2026-10-19.
- **Codex** has no automated hand-over or wake. A Codex shift ends with "start a new session in this worktree", which a person does. Keel makes no host call there to verify.

## Unverified

- Whether a `claude --bg` that timed out had started its session. Keel does not assume it did not: the next attempt first looks for one. This stays with #408.

The race between the waiter and a tick is decided by Keel's lock and claim, not by the host. Its evidence is therefore a fake host with real concurrent `keel` processes.

## In each run and release

A passing `npm test` or `--group` run ends with an `evidence:` line. It counts the scenarios that ran deterministically and those that ran against a stand-in host. A stand-in host here means a fake host program, the host's environment, a host data directory, or a hook payload. The line also says that none ran on a real host. Each GitHub release carries the same counts in an `## Evidence` section, together with the number of `measured` rows on this page. `node scripts/run_python.js scripts/validate_plugin.py --evidence` lists which scenario is which. The classification is derived from Keel's own sources (#408).
