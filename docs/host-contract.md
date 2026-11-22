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
   - `claude --bg -n "<role> · <MM-DD HH:MM>" --permission-mode <mode> [--model <model>] [--effort <level>]` in the role's worktree;
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
| Created its own worktree (`EnterWorktree`, `claude --bg -w`) | The row's `cwd` stays where the session started; `<config>/jobs/<id>/state.json` holds `worktreePath` and `worktreeBranch`. `claude rm` deletes "a background session and its worktree" (2.1.311 help); ChipSTRIDE lost one that way (#492) | Not removed while that worktree is the new shift's, bound to a role, or another listed session's; `keel shift status` names the reason | measured 2026-10-28; scenario `shift-cli-keeps-worktree-in-use` |
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
- **Existing Codex desktop chats** are not adopted by the managed adapter. Persisted notLoaded metadata is not proof that a desktop chat is idle.

## Unverified

- Whether a `claude --bg` that timed out had started its session. Keel does not assume it did not: the next attempt first looks for one. This stays with #408.

The race between the waiter and a tick is decided by Keel's lock and claim, not by the host. Its evidence is therefore a fake host with real concurrent `keel` processes.

## In each run and release

A passing `npm test` or `--group` run ends with an `evidence:` line. It counts the scenarios that ran deterministically and those that ran against a stand-in host. A stand-in host here means a fake host program, the host's environment, a host data directory, or a hook payload. The line also says that none ran on a real host. Each GitHub release carries the same counts in an `## Evidence` section, together with the number of `measured` rows on this page. `node scripts/run_python.js scripts/validate_plugin.py --evidence` lists which scenario is which. The classification is derived from Keel's own sources (#408).

## Cross-device branch leases

With `sync: lock: true` and `device-sync` declared, `keel tick` renews only this device's live branch leases in existing worktrees and pushes work branches only under the existing push authorization. It runs from `/` with an explicit repository. The Claude prompt hook renews when a third of the TTL has passed and stays silent on failure; Codex keeps manual hook capability. A queued CLI hand-over waits while the last fetched branch lock belongs to another device. Bare-remote tests prove Git behavior and hook payload tests prove integration; they do not prove launchd scheduling or Claude activation on this machine.

On Linux a host subreaper may adopt an orphan process. A keep-awake whose original process-group leader is gone remains a shift loose end, even when the adopting parent is in the checker’s ancestry. The public `shift-check-skips-host-keep-awake` regression exercises this on the Linux validation host. Release marker writes and validation also stop at nested Git checkout boundaries; `release-skips-nested-worktrees` verifies both against a temporary real checkout.

## Managed Codex roles

`keel codex start` records the endpoint, role, worktree and thread identity in the existing chat store. `keel codex drain` and `keel tick` use existing unread/addressing/parking rules, persist one claim before starting a turn, and leave uncertain outcomes for inspection. A busy role waits; no replacement server is started after an endpoint failure. A stale creation record or lock is retained for explicit inspection, never silently removed or replayed.

| Boundary | Keel behavior | Evidence |
| --- | --- | --- |
| Two roles on one explicitly selected Unix WebSocket host | Real addressed records start completed model turns; repeated drain retains the original turn IDs | measured: Codex 0.167.2, Linux, 2026-11-17; `docs/codex-validation.md` |
| Idle hand-over | Retain old identity and note, create one successor, include note in its next delivery | measured: same host; successor returned `KEEL_REAL_HANDOVER_NOTE` |
| Busy or uncertain operation | Wait when active; do not replay a pending claim or create another successor | scenario: `codex-managed-host` |
| Native hooks | Source matches patch and Bash tools; no automatic trust or enforcement promotion | deterministic source policy tests; native interface denial measured on CLI 0.164.0, shipped activation remains unverified |

A socket that accepts RPCs does not establish model connectivity. The installed system daemon inherited an old localhost proxy and its model requests retried with `Connection failed: error sending request`; the real acceptance used the identical managed binary on an explicit isolated endpoint with the working current environment. Restarting the system daemon was excluded to preserve unrelated work. Approvals still require the owner's native host interface. Compaction remains manual.

## Default daemon repair — 2026-11-17

The owner subsequently authorized the local rollout and old-proxy repair. Immediately before restart the default managed daemon reported no loaded threads. It was restarted with the current working environment; all uppercase/lowercase HTTP_PROXY, HTTPS_PROXY and ALL_PROXY variables were absent in the replacement process. The installed managed binary remained Codex 0.167.2.

A real turn through the default `~/.codex/app-server-control/app-server-control.sock` completed with `KEEL_DEFAULT_HOST_OK` (thread `01a1e73f-05a4-74c0-8157-d2a092fd4482`, turn `01a1e73f-0613-7803-a123-abf0f494f40e`). The probe used the verified 5.229.0 source adapter and was archived after completion. This supersedes the earlier stale-proxy limitation for this machine; the earlier isolated-host measurements remain historical evidence. Other desktop chats were not adopted or interrupted, and hook trust/compaction capabilities were not promoted by the network repair.

## Owned unload recovery — issue #531

New delivery to an identity-verified managed notLoaded thread now calls thread/resume for the recorded thread on the same connection, revalidates id/cwd/state and starts work only when idle. Delivered claims return before load-state checks without resume; unknown claims refuse without replay. Active-after-resume waits, invalid recovery refuses, and no replacement thread or permission override is introduced. The default cold-load deadline is 15 seconds; explicit --timeout is honored. Other RPC defaults remain five seconds and the model-free drain child has a 40-second bound.

Real Codex 0.167.2 acceptance on 2026-11-17 completed PM's first turn, observed notLoaded, received an execution role's actual AND truth-table file and GATE_OK test, then completed PM's second result turn on the same identity. PM thread `01a1e76a-0424-7912-aa02-3431a7412571` completed second turn `01a1e76b-f2a3-78a2-bcfe-6d0f52df46a3` with `PM_RESULT_ACK_0001`; PM had two turns and execution role one. Duplicate records started no extra work. The second model turn took 61.827 seconds, exceeding the initial observer window; read-only verification confirmed completion without a second start. Test probes were archived. This is actual host evidence, distinct from the stand-in CLI checks.

### Blank managed initialization (5.229.2 / #537)

A fresh Codex 0.167.2 thread can disappear after its creation connection closes before its first turn: read reports `thread not loaded` and same-id resume reports `no rollout found`. Native `thread/name/set` materializes the blank thread. Keel uses that operation with the role name and rechecks identity before successful start or successor hand-over, retaining the created id on uncertain initialization. No model warm-up, permission override or substitute thread is used; already-lost registrations require explicit owner disposition.

Real public-CLI acceptance created `01a1e794-ffe7-7c90-9ac3-c78395a02fea`, closed the creation connection for at least190 seconds, observed notLoaded, then completed its first actual turn `01a1e797-f6ba-7451-8d27-27044dbc6509` with `FIRST_READY` on the identical thread. It had exactly one turn, and duplicate delivery created none. The probe was archived; isolated name/archive controls and the failed unnamed baseline are retained in the change evidence. This is actual host evidence, separate from the stand-in CLI regression.


## Measured native shared frontend — Keel 5.230.0

On 2026-11-17, Linux App 26.1023.51421 connected through its build-specific native
WebSocket URL to the same persistent Codex 0.167.2 backend used by managed roles.
Actual rendered input, managed busy waiting, native Guide during an item/started
sleep, normal tool completion, App-closed backend execution and real reopened UI
were verified on one original owned fixture. Reviewer/cwd/history/claim retention
and duplicate refusal were checked; 16 public host tests passed separately from
the real measurements. No production role was migrated, no Goal stopped, and the
original App/backend were not restarted. This does not promote hook/compaction
trust, prove macOS, or provide an atomic global Quit fence.

The public start reviewer option is explicit and per-thread; native persistence
uses no hidden model warm-up. The recover command only restores the recorded
owned id/cwd on its existing endpoint and preserves registry claims; foreign
writer refusal remains authoritative. A private frontend profile still uses the
backend's project-trust store: one temporary test entry required separate owner
approval and exact cleanup. See the current [connection/rollback runbook](cli-team.md#native-shared-desktop-connection)
and [actual-host evidence](codex-validation.md#shared-app-reviewer-and-owned-cwd--2026-11-17).

### Explicit owned Codex onboarding

`inspect-registration`/`register` and `inspect-migration`/`migrate` consume explicit
owner-approved original tuples and retain native policy; they neither discover
arbitrary chats nor authenticate the caller's authority reference. Inspection
may load/subscribe the same id without settings overrides or model work. Active
same-runtime registration preserves the current turn. A migration requires the
deployment owner to hold source input admission; native writer protection and
verified source/target history govern handoff. Keel does not implement an App
admission barrier or route its frontend.

`migration-status` reads visibility and durable outcome without resuming.
Unknown intent prevents automatic handoff retry; explicit `--reconcile` verifies
an already loaded original target before registry CAS. This is not proof of
mailbox read, business-task completion, frontend deployment or production
acceptance. [The team runbook](cli-team.md) documents exact commands and refusal
paths; [native validation](codex-validation.md) separates native and stand-in
measurements.
