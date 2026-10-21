## Why

Issue #408, second loop. On 2026-10-21 the owner chose the remaining CLI items: retry a failed hand-off, and duplicate suppression under real concurrency. The issue's acceptance asks for evidence that "重复事件不重复启动工作", and for "重试有上限及可恢复路径". 5.183.0 shipped the first loop and left both unverified in `docs/host-contract.md`.

Reading `handOver` in `src/core/shift.js` (5.183.0) shows three gaps:

- **A failed hand-off is never retried.** `handOver` only acts on entries in the `pending` state. Once the new session fails to start, the entry stays `failed` for good. The old session is already stopped, so the role has no running session until someone notices the patrol risk and resumes the old session by hand.
- **The hand-over lock can be taken from a live runner.** The per-role lock file covers the whole hand-over: `claude stop`, `claude --bg`, the 15 s exit wait, and each `claude rm`. Each of those host calls is bounded at 60 s. A runner hung on host calls can therefore still hold the lock past two minutes. At two minutes the waiter or the tick deletes the lock as stale, while the entry is still `pending`, and starts a second session.
- **A runner that dies while starting leaves the entry `pending`.** Examples are the waiter being killed or the machine sleeping through the call. If its `claude --bg` had already started the new session, the next runner sees `pending` and starts another.

The host gives Keel enough to tell whether a session was already started. Measured on 2026-10-21 against Claude Code 2.1.304, `claude agents --json` rows carry `name`, `cwd`, `startedAt` (ms), `sessionId`, `status`, `state`, `pid`, `id`, and `kind`. A hand-over names its new session `<role> · <MM-DD HH:MM>` in the role's worktree.

## What Changes

- **A runner claims the entry before it starts anything.** It holds the lock only long enough to change the entry from `pending` to `starting`, recording its process id and the time. The lock is released before any host call. Another runner acts only on a `pending` entry, so it never starts a second session, however long the claimed hand-over takes.
- **A runner first checks for a session that already exists.** This applies to an entry whose runner is gone, or that has been `starting` for more than ten minutes, and to any retry. The runner looks for a listed session named `<role> · …` in the role's worktree that started after the claim. If one exists, it is adopted as the delivered session and nothing new is started.
- **The tick retries a failed hand-off.** It makes up to three start attempts per entry, with the existence check before each one. After the third failure the entry stays `failed`. `keel shift status` and the patrol risk then name the recovery: `keel chat wake now <role>`, which resumes the stopped old session.
- **The contract page is updated.** `docs/host-contract.md` moves the waiter/tick race and failed-hand-off recovery from "unverified" to their scenarios. Its unverified list keeps the desktop app path and Codex.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

The change touches:
- `src/core/shift.js`;
- `docs/host-contract.md`;
- `docs/cli-team.md`, where the status line wording changes;
- the validation scenarios;
- the published spec;
- the changelog.

The scenarios go wherever `scripts/validate_plugin.py` places shift scenarios once #409's split has landed. While keel-maint-2 holds the `validate-plugin-split` lock, nothing is added to that file. No new command is added, so the shift feature freeze holds: the recovery path is the existing `keel chat wake now`.
