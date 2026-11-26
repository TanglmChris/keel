# A team of Claude Code CLI sessions

The desktop path of `keel chat`, `keel shift` and `keel patrol` relies on the Claude desktop app: its scheduled tasks run the patrol, and its session tools wake and clear sessions. A team can instead run each role as a background session of the Claude Code CLI (`claude --bg`), with no desktop app running (#369). This page is that path, end to end. Measured on Claude Code 2.1.303. In Chinese: [cli-team.zh-CN.md](cli-team.zh-CN.md).

## What does what

| Need | Desktop app | CLI |
|---|---|---|
| One session per role | an app session in the role's worktree | `claude --bg -n <role>` in the role's worktree |
| Wake an idle session | a mention, an assigned todo or a direct message | the same: the chat's file hook wakes an idle background session |
| Wake a session that has ended | `send_message` to the session | `keel chat wake now <role>`, or `keel tick` once per new record |
| Run the patrol on a schedule | a host scheduled task (`host_task:`) | `keel tick`, run by launchd (`runner: tick`) |
| Change shift | the session clears itself; a waiter wakes the new shift | a waiter stops the old session and starts a new one named for its start; `keel tick` does the same if the waiter is gone |
| Open a previous shift's conversation | the archived app session | `claude attach <id>` on the stopped session |

## Setting up a role

1. Create the role's worktree and run `claude` there once, interactively, to accept the trust prompt. Trust is per directory and is not inherited from a trusted parent: `claude --bg` in a directory nobody trusted fails with `Workspace not trusted`, and so does every later start there, including the one a shift change makes.
2. Start the session in the background: `claude --bg -n <role>`. The name is the session's title in `claude agents`.
3. In that session, bind the role: `keel chat role --set <role>`. From then on its presence records the CLI session's id and process, which is what lets Keel resume or replace it.

Run one session per role. If a second session is bound to the same role — for example a `claude --resume` of a session that is still running — both post under one name and share one read cursor, so whichever reads first hides records from the other. `keel context`, and `keel chat post`, `dm`, `todo`, `unread` and `read` on stderr, warn while two live sessions are bound to one role. Stop one of them.

Use `keel chat show <todo-id> --json` to read a task by its original todo ID.
The `task` member returns that ID, its chat `state` of `open` or `closed` and
the `closureRecordId` of the closing chat record, or null. The query leaves
read cursors untouched. Closure records a member's report of completion.
Keep the task's verification evidence separately.

The sibling `delivery.state` is `acknowledged` for a durable native receipt,
`unknown` for an ambiguous receipt, or `unobserved` when no evidence is available.
It is local delivery evidence only. The query contacts no runtime.

For a newly delivered managed Codex todo, the caller can collect the reviewer's
designated final answer with `keel chat show <todo-id> --collect --json`.
The reviewer returns a JSON object with the exact `taskId` and a string
`result` in its final message. Keel checks the assigned role, original endpoint
generation, thread, worktree and completed turn. The caller can then read
`result.text` offline with the ordinary show command. Receipt of a report
leaves verification and closure to the caller. A refused collection produces
no new result. An older delivery without a result-enabled receipt keeps its
original reporting path.

## Waking

An idle background session is woken like any Claude session: only a mention, an assigned todo or a direct message wakes it, and everything else waits for its next prompt.

A session that has ended — stopped, or its process gone — sees nothing. `keel chat post` and `keel patrol` say which addressed roles are in that state and name the step: `keel chat wake now <role>` resumes the role's recorded session with `claude --bg --resume <session id>` and a prompt to read its unread records. It passes no other flag, because any flag given with `--resume` starts a copy with a new session id instead of continuing the same one; the resumed session keeps its saved options, its permission mode included.

`keel tick` does the same by itself, once per new record: on each run it resumes every role whose CLI session has ended while a record that wakes it waits, and it does not resume that role again until a newer one arrives. A parked role (`keel chat role --park`) is left alone.

## The patrol, run by `keel tick`

`keel tick` is one model-free step for a host scheduler to call every few minutes. On each run it resumes ended sessions (above), carries out queued shift hand-offs (below), and runs the coordinator's `keel patrol --since-last --notify` — after a `git fetch` — only once the previous patrol's recommended next run has passed. When `issue_roles:` declares a route or a role waits for an issue to close, it first fetches issue state with `gh` and passes it to the patrol as `--issues`, so `gh` must be on the job's `PATH` and logged in; a failed fetch is said once in `tick/tick.log`, and `keel --doctor` prints an `issue checks` line (#473). Keel schedules nothing: launchd recurs it.

```yaml
patrol:
  role: pm
  every: 30m
  runner: tick
  cadence: adaptive
```

`runner: tick` tells the coordinator's new sessions and `keel shift resume` that the patrol runs outside the session, so they are not reminded to re-create a schedule. `keel tick task` prints the launchd job — a plist that calls `keel tick --repo <the repository's main checkout>` every 300 s from the filesystem root (so no tool that waits for the checkout to be idle counts a tick as a holder, #524), and every run finds the worktree each declared role is bound to (so binding a role elsewhere needs no new job), logging to `tick/tick.log` in the chat store — with the two commands that install it and the one that removes it. Keel installs nothing; run the commands yourself. The plist carries the `PATH` of the shell that printed it, so `claude` and `git` must be on it then, minus any Claude plugin cache directory, which belongs to one release. It runs the `node` found on that `PATH` that is the same binary as the one that printed it, such as `/opt/homebrew/bin/node` rather than its versioned `Cellar` target, so a `brew upgrade` does not break the job; `keel chat wake add` and the chat bridge do the same. A launchd job must not name a path under `.claude/worktrees/` or inside a `.venv`, because both are regenerated and the job then fails every interval with no trace but `tick/tick.err`; the printed job names the main checkout for that reason, and names the bound worktree, saying so, only when the main checkout declares no `patrol:`. `keel --doctor` prints a `launchd` line for each `dev.keel.*` LaunchAgent and names any whose node, `--repo` or `WorkingDirectory` no longer exists or lies under `.claude/worktrees/`, with the command that re-creates it.

A repository that declares no `patrol:` gets the same job: `keel tick task` prints it naming the main checkout and says that each run then resumes ended sessions and carries hand-overs out and runs no patrol, which is all a repository without a coordinator needs (#509). A `patrol:` Keel cannot read is still refused with its message, not taken for none.

Every `keel tick` run records `last_tick` in `tick/state.json`, including a run whose patrol is not due, because the patrol's own `last_run` moves only once per patrol. `keel --doctor` prints a `tick` line from it: ok with the time of the last run, or a problem when that is more than 15 minutes old (three of the job's intervals) or when the repository declares `runner: tick` and no run was ever recorded. The patrolling role's session start says the same in one line, and `keel context --json` carries it as `patrol.tick`. This is the only way to learn that the job is not running, since a tick that does not run cannot say so; it reads this one file and asks the host nothing, so it does not tell why: a laptop that slept shows the same line as a job that was never loaded (#510).

Every patrol prints a `next:` line with its recommended next run, and `keel tick` waits for it. Without `cadence: adaptive` that is `every:` (rule `fixed`). With it, the first rule that holds sets it:

| Rule | When | Default |
|---|---|---|
| `risk` | the patrol reported a risk | `30m` |
| `quota` | `--quota` is at 90 or above | `4h` |
| `night` | now is inside `quiet:` (for example `23:00-08:30`) | until the window ends |
| `busy` | another role is active, or an active role holds an open todo or wait | `1h` |
| `idle` | otherwise | `3h` |

Each default can be overridden by a flat key under `patrol:` (`risk: 15m`), and `min:` and `max:` clamp every rule but `night`.

## Changing shift

A CLI session cannot clear itself, so a shift change replaces the session instead. The role runs `keel shift check` and `keel shift ready --wake "<note>"` as on any host. In a CLI session, `ready --wake` records the session in the note (`CLI session:` and `CLI process:`) and queues a hand-off in the chat store, leaves a detached waiter that carries it out, then tells the session to end its turn.

The waiter looks the session up in `claude agents` every few seconds (`keel tick` does the same on each run, as the fallback when the waiter has died; a lock keeps the two from starting two sessions, and a repository needs no tick for its shift changes). While `claude agents` shows the session busy, or waiting for input — it is blocked on a question to you — it waits: a hand-over never cuts a conversation off. It reads the status, not the job state, which labels the session's last message rather than whether its turn has ended (#393). Once the session is idle, stopped, or gone, it stops it with `claude stop`, which keeps the conversation, and does not resume it. Then it starts a new session in the same worktree with `claude --bg -n "<role> · <MM-DD HH:MM>" --permission-mode <mode> [--model <model>] [--effort <level>]` and the prompt to run `keel context` and `keel shift resume`. The new shift starts with a clean context, a new session id, and a name of its own: the role and the local time it started, so no two shifts share a name in `claude agents` or on claude.ai. The old session keeps the name it started with. It is not renamed, because renaming took a resume, and a session running with Remote Control writes its claude.ai title back over a rename (#399). The mode comes from `keel/config.yaml`, and is `auto` when nothing is declared:

With `sync: lock: true`, a queued hand-off starts no session while another device holds the branch of the role's worktree by the last fetched lock: the entry records `waiting_on: branch <b> is held by <holder> until <time>`, which `keel shift status` shows and the patrol reports once it has been pending over 15 minutes (#526). Each tick also renews the branch locks this device holds. With `device-sync` declared, renewal checks that the remote still names this device as the live holder, then pushes the work branch only under `push` or a matching `push:<glob>` and never `push-protected`. A push or renewal failure leaves the lease to lapse and is reported once. The prompt hook renews only after a third of the TTL, never pushes the work branch, and stays silent on failure.

```yaml
shift:
  permission_mode: auto   # default, acceptEdits, auto, plan or bypassPermissions
  keep_old_sessions: 0    # old shifts left listed per role; 0, the default, keeps none
  model: opus             # optional: start the new shifts on this model instead of the owner's default
  effort: high            # optional: low, medium, high, xhigh or max; passed only when declared
```

The new session starts on the model you would get yourself (#500). Left to the host, the call gets whatever model the host picks: on 2026-11-01 the shifts it started ran sonnet although `model` in the user's `settings.json` said opus. So the call carries `--model` after `--permission-mode`, taking the first of these that names one: `shift: model:`, the `ANTHROPIC_MODEL` environment variable, `model` in the worktree's `.claude/settings.local.json`, in its `.claude/settings.json`, then in `settings.json` of the Claude config directory (`CLAUDE_CONFIG_DIR`, else `~/.claude`). A file that is missing, not valid JSON, or whose `model` is not a string names nothing and the next one is tried; managed policy settings are not read. When none names a model the call names none, as before. `--effort` is passed only when `effort:` declares it, so the host's own per-model `effortLevel` still applies. `keel shift status` shows the model the delivered shift started on and which source named it; a `model:` or `effort:` Keel cannot read is named there and ignored. A resumed session keeps the options it was saved with.

Each shift change stops the old session. After a hand-over, the newest `keep_old_sessions` of the role's stopped sessions stay listed for `claude attach`, and each older one is removed with `claude rm` once Keel's store holds a copy of its transcript (#397). Nothing is kept when nothing is declared (#418): the shift just handed over is removed too (unless its worktree is in use, below), so it no longer appears in `claude agents` or on claude.ai beside the current one, where a stopped session read like a live one. `claude rm` of a session started in an existing worktree leaves the worktree in place. A session that created its own worktree, with `EnterWorktree` or `claude --bg -w`, is different: `claude rm` deletes that worktree, so Keel leaves such a session listed while its worktree is the new shift's, bound to a role, or another listed session's (#492). `keel shift ready --wake` says so up front when the session's worktree is the new shift's or bound to a role, instead of promising a removal; a session kept only because another listed session runs in its worktree is named by `keel shift status` afterwards, since `ready` makes no `claude agents` call (#506). Only a session with a transcript, the host's or Keel's copy, counts: one that was never given a prompt has none, takes no slot, and stays (#401). A session is the role's when it ran in one of the role's worktrees, or when Keel keeps its transcript under the role, so a renamed or moved worktree does not strand its old sessions (#462). A takeover Keel did not carry out — a session you opened by hand that runs `keel shift resume` — removes them the same way: resuming a note a CLI session wrote, from a Claude Code session, removes the role's old sessions under the same rules and names them (#462). Nothing is lost: `claude rm` leaves the host's transcript, Keel keeps its own copy, and `keel shift history <role> --show <session id>` prints the whole conversation of any shift, listed or not.

`keel shift status` lists each hand-off as pending, delivered (with the new session's id) or failed (with the error), and how to reopen the old session: `claude attach <first 8 characters of its id>`, or, once it has been removed, `keel shift history <role> --show <id>`. It also names the older sessions the hand-over removed. An old session the hand-over left listed is named with the reason: kept by `keep_old_sessions`, its process still running, its transcript not copied, its worktree in use, or `claude rm` failing with the host's message; opening it brings it back beside the new shift (#492). A hand-off that failed, or is still pending after 15 minutes, is a patrol risk, so the coordinator hears of it. `keel tick` tries a failed start again, up to three attempts in all, and after the last one status names `keel chat wake now <role>`, which resumes the stopped old session. A worktree nobody trusted is one way to fail: the new session cannot start there.

On the CLI, `keel shift resume` asks for nothing to be restored: the new session already carries the role's name, and the desktop steps that `self-shift` and `shift-restore` authorize do not apply.

## Permissions

The tick runs outside every session and needs no session permission. The sessions themselves run `keel` and `git` commands through Bash. A session started by a hand-off runs in the declared `permission_mode`, and a resumed session keeps the mode it was started with. So start each role's first session in the mode you want it to keep, and give it the `permissions.allow` entries its work needs, as you would for an unattended desktop session. The desktop-only entries (`mcp__ccd_session_mgmt__*`, `mcp__scheduled-tasks__*`) and the `self-shift` and `shift-restore` declarations are not needed.

The patrol reports a branch or detached head with local-only commits older than 24 hours, and a stash older than 24 hours, as a standing risk. It uses local refs only, excludes uncommitted paths, and sends unchanged risks once under `--since-last --notify`. Scoped patrols report their covered roles; the repository patrol also covers branches without worktrees and stashes. `keel --doctor` shows the device id, held branch locks, expiry, last renewal, and whether the tick has run or the Claude prompt hook renews.

Review each Keel hook by plugin source, event and command in `/hooks`. See [the hook review table](updating.md#review-keel-hooks-in-codex).

## Project-local Codex worktrees

Choose a location beside the checkout and a fresh task branch. The starting
point defaults to the selected checkout's HEAD. Pass `--base <ref>` to choose
another local commit. Relative paths are resolved from `--repo`.

```sh
keel worktrees add --repo /path/to/project --path ../project-worktrees/review --branch codex/review --json
codex -C /path/to/project-worktrees/review
```

Use the `path` returned by the first command. To bind a Keel role, run
`keel chat role --set review` from that worktree. Discover all linked checkouts
and their bindings with `keel worktrees --repo /path/to/project`. Reopen an
existing checkout with `codex -C <path>`.

The command requires an unused path and branch. Review and preserve any local
edits before cleanup. After the Codex session has ended, inspect the checkout with
`git -C <path> status` and use `git -C /path/to/project worktree remove <path>`.
Git's ordinary removal refuses an unclean checkout and keeps its branch.
If stale Keel bindings remain after removal, `keel chat role --prune` drops
bindings to removed worktrees in this repository.

Codex Desktop's Worktree mode and Handoff manage their own checkouts under
`$CODEX_HOME/worktrees`. The command above creates a Git checkout for the CLI workflow.

## Managed Codex roles

Create a distinct Git worktree per role. Start a Codex app-server with the intended network environment, or use the existing managed daemon. Keel connects to it and never starts a replacement automatically:

```bash
codex app-server --listen unix:///path/to/team.sock
keel codex start --repo /path/to/role-worktree --role worker --socket /path/to/team.sock --json
keel codex status --repo /path/to/role-worktree --role worker --json
keel codex drain --repo /path/to/repository --json
keel codex handover --repo /path/to/role-worktree --role worker --note "Completed work, remaining work, and authority" --json
```

With no `--socket`, start selects `$CODEX_HOME/app-server-control/app-server-control.sock` (normally `~/.codex/...`); later operations use the recorded endpoint. `keel tick` drains the same addressed unread records using the existing mailbox rules. Keel schedules nothing; the owner's scheduler must run tick. Stop an older `keel chat wake` watcher before using the managed adapter for the same role, to keep a single delivery owner.

Successful `start` and hand-over successors receive the native thread name matching their role before Keel reports the new identity as managed. This native metadata write persists a blank thread without an implicit model turn, so its first delivery may arrive after the creating connection closes and the host unloads it. The created id is retained in pending initialization evidence if naming or identity validation fails. A pre-existing lost blank id with no rollout cannot be resumed; Keel preserves its registry and reports the error rather than silently replacing it.

Choose a thread-level reviewer explicitly at creation when needed:

```bash
keel codex start --repo /path/to/role-worktree --role worker --socket /path/to/team.sock --approvals-reviewer auto_review --timeout 30000 --json
```

`--approvals-reviewer user|auto_review` belongs to `start`. `user` routes approval
requests to the human; `auto_review` uses the native automatic reviewer. Both
retain `on-request` and `workspace-write`. The explicit choice is stored with the
owned role and carried into cold delivery and hand-over successors. Native
`thread/settings/update` persists it before a new identity is reported managed,
including a blank thread with zero model turns. Calls without the flag retain
their existing behavior. This option requires a host supporting the native
reviewer and settings APIs; it uses experimental API negotiation for roles with
an explicit choice.

A mismatched native reviewer, approval policy or sandbox fails before work
starts. Persistence failures retain the pending original/successor id for
inspection, and a timed-out creation remains unknown instead of being retried.
An explicit timeout controls each RPC budget; the example allows 30 seconds for
cold native setup. Inspect the retained record and host after a failure before
deciding the next action.

`deliver --role worker --record <stable-id> --text <text>` also accepts explicit work. The record id is an idempotency key: a repeated delivered id starts no second turn; uncertain results remain pending for inspection. Busy roles return waiting and require a later drain/tick. Read status to inspect approval waits; use the native Codex interface for approval decisions. An unavailable host is reported without replacement. For a new record, an identity-verified owned notLoaded thread is resumed as the same thread and rechecked before work starts; active work still waits. Already-delivered claims return without loading it, and unknown claims refuse without replay. Cold resume has a 15-second default budget; an explicit `--timeout` remains authoritative, and the stock drain gives its child 40 seconds for the bounded RPC sequence. Existing desktop chats and hand-over do not gain automatic recovery. After an uncertain creation or hand-over, inspect the host and retained registry instead of deleting the record and trying again.

For an explicitly owned role whose native cwd drifted, run `keel codex recover --repo /path/to/role-worktree --role worker --json`. This restores the original thread's cwd/runtime workspace roots through native resume on its recorded endpoint; it does not migrate endpoints or adopt desktop threads. Active work returns waiting without resume. Native writer refusal, unknown state, policy or identity mismatch and timeout require inspection; a failed/unknown recovery may have changed native cwd, but the original role/history/delivery claims remain unchanged and no model turn or replacement is started. Success verifies the same id/cwd and the recorded native policy for registered/migrated roles, or on-request/workspace-write and any explicit reviewer for legacy roles; verify actual execution with the next authorized delivery. It does not recover App project/sidebar attachment or bypass a live foreign writer.

Codex hand-over uses `keel codex handover`, preserving the old thread and note in the existing chat store's managed-role history. The successor receives that note on its next addressed delivery. Claude's `keel shift` lifecycle stays unchanged. Existing dedicated frontend threads require the explicit registration plan below; there is no automatic desktop discovery/adoption. Hook trust and unproven guard/compaction enforcement remain unchanged. See `docs/codex-validation.md` for dated real-host evidence and limitations.


Use `keel codex status --repo <path> --role <role> --record <id> --json` to inspect a delivery receipt from the local registry while the host is offline. Acknowledged claims return the original thread and turn when recorded. Older claims can have a null thread. Unknown submissions keep their claims. Verification of the task still requires evidence of the actual outcome.

Add `--observe` to read the original native turn from the recorded endpoint.
`observation.state` reports `resource-exhausted` for the typed usage-limit failure,
a native turn state when known, or `unknown`. The separate `backgroundTerminals`
value is `present`, `none-observed`, or `unknown`. Treat the two observations as
point-in-time evidence. A terminal turn or an empty inventory cannot certify writer release.

## Native shared desktop connection

Keel 5.230.0 was measured with Linux App 26.1023.51421 and native backend 0.167.2.
The default desktop App's stdio runtime and an independent daemon are separate
writers even when both list the same history. Connect the foreground App to the
same native backend as its managed roles; pinning a chat or reading its id does
not establish this. This is an explicit native host setup, not an automatic Keel
switch. Other App builds and macOS need their own capability/acceptance check.

For the measured build, a dedicated profile can use the process-local native
WebSocket route, without restarting an existing App. Choose private directories,
the installed App executable, and the already running authenticated team's
absolute socket path. The native daemon owns execution, credentials and config;
Keel neither starts a second dispatcher nor changes the original App connection.

```sh
CODEX_ELECTRON_USER_DATA_PATH="/path/to/private-team-profile" \
CODEX_HOME="/path/to/private-team-home" \
CODEX_APP_SERVER_WS_URL="ws+unix://localhost/absolute/path/team.sock:/rpc" \
/path/to/installed/ChatGPT --user-data-dir="/path/to/private-team-profile"
```

The directories must belong to this dedicated window; an already running instance
with the same profile may receive the launch instead. A force-CLI override defeats
the native URL route. Verify the actual connection and role identity before work.
Never copy authentication files to make a private profile work. The optional
ChatGPT Local Work executor was unauthenticated in the disposable test profile;
that does not establish support for that unrelated feature.

Private frontend state does **not** isolate backend project trust. Opening a new
project may register its trust in the backend's config. Review that native trust
decision with the owner; do not promise zero global changes. Our isolated test
paused on that delta, obtained explicit permission for its sole temporary project
entry, and restored the exact original config afterward. Production trust entries
must not be silently removed or rewritten as cleanup.

Use only existing owned role ids after their actual source turns/tools have
finished and the old writer has released them. Keep the registered endpoint and
claim/history records. `recover` restores cwd on that same endpoint; it is not an
endpoint migration command. A foreign daemon's notLoaded or goal:null does not
prove source App idle. Writer refusal, unknown operation outcome or identity drift
stops recovery; do not force, delete the registry or create a replacement id.

Foreground busy work makes managed delivery return waiting until a later tick.
In this App, input during backend busy work uses native **Guide** and updates the
current turn; it can change the requested answer. It is not a guaranteed separate
queued task. For independent work, use a stable addressed record and normal
managed delivery after idle. Native queue/add accepts duplicate client UUIDs, so
it is not an idempotency substitute for the managed claim ledger.

Before production, prove real foreground input/backend follow-up, both busy
directions, unchanged id/cwd/policy/claims, and backend execution while this App
is normally closed. Then reopen and inspect the actual reply. Close only the
dedicated App after its accepted turns/tools finish; the native backend keeps
running. Rollback is a normal safe exit of that window and the original launcher
without these process variables. If a safe exit is unavailable, preserve work and
report it; do not kill the App, restart the backend or reset global settings.
The original all-idle restart route remains a separate explicitly authorized
operation. See [real-host evidence](codex-validation.md) and
[issue #541](https://github.com/TanglmChris/keel/issues/541).

## Register an authorized original Codex frontend (#547)

Bind the unique existing worktree/role first with `keel chat role --set review` in
that worktree. The deployment owner must already authorize the exact original
thread, worktree, role and native endpoint. `--authority` records that reference;
it is the caller's assertion, not an ACL or permission inferred from a DM/name.
Do not run `start --thread`: start creates a new thread.

```sh
keel codex inspect-registration --repo /path/to/owned-worktree --role review --thread ORIGINAL_THREAD_ID --socket /path/to/selected.sock --authority https://example.com/approved-role-list > /tmp/owned-registration.json
cat /tmp/owned-registration.json
keel codex register --plan /tmp/owned-registration.json --json
```

Inspect rejoins only that original native id without setting overrides, model
work or replacement creation; native resume may load/subscribe it. Active work
on the same runtime may be registered without an artificial idle window. Apply
rechecks canonical unique binding, effective approval/reviewer/sandbox/roots,
thread identity and conflicting current/historical/pending managed ids, then
atomically creates registration without replacing an existing record or binding.
Keep plans private: they include runtime endpoints and identity summaries.

The native policy snapshot controls later idle/cold delivery and recovery. Native
read-only review stays read-only; drift refuses work rather than granting write
access. Registered frontend `handover` refuses replacement; an authorized
successor workflow is separate. A stored DM, native accepted turn, model receipt,
`keel chat read` acknowledgement and business-task completion are distinct. Do
not claim a mailbox cursor advanced merely because delivery or a model reply
succeeded. Ordinary coordination does not authorize business code changes.

## Migrate one owned endpoint (#546)

The deployment owner must hold admission for this exact source role through its
handoff: finish its actual turns/tools/input, preserve pending delivery claims,
and connect its frontend to the approved target runtime. This is not a whole-App
idle requirement. The CLI cannot prevent independent foreground input or change
App routing. `notLoaded` on a foreign host does not prove source release.

```sh
keel codex inspect-migration --repo /path/to/owned-worktree --role worker --to-socket /path/to/approved-target.sock --authority https://example.com/approved-migration > /tmp/owned-migration.json
cat /tmp/owned-migration.json
keel codex migrate --plan /tmp/owned-migration.json --json
keel codex migration-status --plan /tmp/owned-migration.json --json
```

The plan fixes the old registry digest, tuple, complete paginated persistent
history and effective policy. Inspection and apply both read the target's
identity and full paginated history before persisting intent or releasing the
source. A missing history field can cause this check to fail across native versions.
Migration requires an idle source, empty input queue/background terminals and no
Goal. After durable intent it unsubscribes only its own source connection and
waits for the source to report the same thread as `notLoaded`. The default wait
limit is 75 seconds. An explicit `--timeout <ms>` sets the limit for the unload
wait and for individual RPCs. A timeout preserves the original registration for
inspection. Native writer protection still governs target acquisition. Target
must retain the same persistent ID/history and approved policy. Only endpoint and migration
audit change; existing history, custom fields and all delivery claims survive,
including uncertain claims that remain blocked from replay. New delivery/recover
checks the recorded migration policy even for an older default managed role.

A failure after intent is **unknown**, not a promise that native state rolled
back. Inspect `migration-status`; repeating migrate does not retry handoff.
Explicitly use `migrate --plan /tmp/owned-migration.json --reconcile` only after
examining the outcome. Reconciliation checks an already loaded original target,
source release, original completed-history prefix and effective policy before a
registry comparison/commit. It preserves any newer target work. An unloaded
target refuses without native acquisition: the deployment owner must first
verify/rejoin that exact id under its native recovery authority, then reconcile.
If registry data changed concurrently, inspect the conflict rather than edit or
replace records. An interrupted final journal write can reconcile an exactly
matching already-applied registry without rewriting it.

Native built-in profile provenance may change between null and `:read-only` or
`:workspace-write` during cold loading; only the matching implicit representation
is normalized. Effective approval, reviewer, sandbox fields, roots and custom
profiles remain exact. A blank native thread may not cold-persist an explicit
approval before its first real turn: a changed policy refuses migration. There
is no hidden warm-up or policy repair. Frontend routing, project trust, service
layout and production rollout require their own exact deployment authority.
