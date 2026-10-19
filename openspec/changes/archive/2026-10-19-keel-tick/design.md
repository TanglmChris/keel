## Context

The owner's CLI waker (2026-10-19) merges #356, #357 and #348; this is its first step, the patrol. `Keel ships no scheduler` (keel-unattended-triage) forbids a Keel command that starts or registers a recurring run, so the recurrence stays launchd's: `keel tick` is one step per call, as `keel patrol` was one step per host-task run, and `keel tick task` prints the job rather than installing it — the same split as `keel patrol task`.

## Facts

- F1 — The rendered patrol host task ran `git -C <worktree> fetch -q origin`, then `keel patrol --repo <worktree> --since-last --notify` (`src/core/patrol.js`).
- F2 — Since 5.153.0, `keel patrol --json` carries `next_at` (#356).
- F3 — `claude --bg` sessions on the owner's machine have no host scheduler of their own that outlives them; launchd runs a job with no login shell, so the job needs absolute paths and the caller's `PATH`.

## Decisions

- D1 — State lives at `<chat store>/tick/state.json` as `{ patrol: { next_at, last_run, last_exit } }`. A tick runs the patrol when `patrol:` declares a role, a worktree is bound to it, and `next_at` is absent or not later than now; it fetches `origin` in that worktree first (a fetch error is reported and does not stop the patrol), then runs `keel patrol --repo <worktree> --since-last --notify --json` and stores its `next_at`. A tick that does not run prints `patrol not due until <next_at>`.
- D2 — `--repo` names any worktree of the repository; the patrol always runs in the worktree bound to the patrolling role.
- D3 — `keel tick task` prints a launchd plist — Label `dev.keel.tick.<project>`, ProgramArguments of the absolute `node` and `bin/keel.js` paths, `tick --repo <bound worktree>`, StartInterval 300, the caller's `PATH`, and stdout/stderr logs under the chat store — followed by the two commands that install it (`cp` into `~/Library/LaunchAgents/` and `launchctl bootstrap gui/<uid>`), and `Keel creates nothing`.
- D4 — `patrol: runner: tick` is accepted; with it the patrol reminder says `keel tick` runs the patrol from the host scheduler and that no session schedule is needed. Any other `runner:` is ignored by name.
