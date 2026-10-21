## Context

`handOver` in `src/core/shift.js` (5.183.0) is called by two runners: the detached waiter, which `keel shift ready --wake` leaves running, and `keel tick`. For each entry in the `pending` state, it takes a per-role lock file (`queue/<role>.lock`, created with `wx`). The lock is treated as stale after two minutes. Holding the lock, the runner:

1. re-reads the entry;
2. checks the old session against `claude agents --json --all`;
3. retires the old session with `claude stop`;
4. starts the new session with `claude --bg -n "<role> · <MM-DD HH:MM>"`;
5. writes `delivered` or `failed`;
6. removes old sessions.

Every host call is bounded at 60 s (5.183.0, #408 D2).

## Findings

- **F1. A `failed` entry is never touched again.** The only path back is a person noticing the patrol risk and running `keel chat wake now <role>`.
- **F2. The lock can be taken from a runner that is still working.** The lock spans the whole hand-over. With hung host calls, `stop` (60 s) + `--bg` (60 s) passes two minutes before `delivered` is written. Another runner then deletes the lock as stale, re-reads a `pending` entry, and starts again.
- **F3. A runner that dies after `claude --bg` but before writing leaves `pending`.** Nothing records that a start was attempted, so the next runner repeats it.
- **F4. Host facts.** Measured 2026-10-21 against Claude Code 2.1.304, read-only `claude agents --json`: rows carry `name`, `cwd`, `startedAt` (epoch ms), `sessionId`, `status`, `state`, `pid`, `id`, and `kind`. A session started by a hand-over is named `<role> · <MM-DD HH:MM>` and runs with the role's worktree as `cwd`.

## Decisions

- **D1** — Claim, then work. Under the lock, a runner re-reads the entry. It moves on only if the entry is still actionable and the old session has finished. It then writes `state: "starting"`, `runner_pid` (its own pid), `starting_at` (ISO local time), and `attempts` (previous + 1), and releases the lock before any `stop` or `--bg`. The lock is now held for milliseconds, so its two-minute staleness can no longer cover a live runner (F2). A second runner sees `starting` and skips it.
- **D2** — A `starting` entry is settled, never restarted blind. On a later step, a `starting` entry needs settling when `runner_pid` is not running, or `starting_at` is more than 10 minutes old. Ten minutes is more than the bounded worst case: four 60 s calls plus the 15 s exit wait, plus removals. To settle it, the runner checks for a session already started (D3). If one is found, the entry is `delivered` with it. If none is found, the entry becomes `failed` with "the hand-over runner stopped before the new session started", and D4 then applies (F3).
- **D3** — The existence check. A listed row counts as this hand-off's new session when all of these hold:
  - its `name` starts with `<role> · `;
  - its `cwd` resolves to the entry's worktree;
  - its `startedAt` is no earlier than `starting_at` minus 5 s, to allow for clock rounding;
  - its `sessionId` is not the old session's.

  The check runs before every retry start and when a `starting` entry is settled. An adopted session is recorded like a started one: `new_session`, `new_name`, and `adopted: true`. Old sessions are removed as after any delivery.
- **D4** — Bounded retry of a failed hand-off. On each step, the runner returns a `failed` entry to the D1 claim when all of these hold:
  - it records `attempts` below 3;
  - the old session is not running again, meaning its row has no `status` or is gone.

  Entries written before this release carry no `attempts` and are never retried. Retrying a stale failure from days ago on upgrade would start a session nobody asked for now. If the old session is running again, for example because a person resumed it, the entry stays `failed` and records `not retried: the old session is running again`, with `attempts` set to 3. Retries happen on the tick, because the waiter exits once its entry leaves `pending`. A retry therefore happens at the tick's interval.
- **D5** — Recovery is named, not new. After three attempts, the `keel shift status` line and the patrol risk end with `; resume the old session with \`keel chat wake now <role>\``. No command is added, so the shift freeze (2026-10-14) holds.
- **D6** — Evidence. Two scenarios exercise this through the real `keel tick` and waiter processes, running concurrently against the fake `claude`. They are added wherever #409's split places shift scenarios.
  - One scenario covers the race and the settled `starting` entry. Two ticks and a waiter start together. A runner is killed mid-`--bg`.
  - The other covers bounded retry, success on a later attempt, a resumed old session, and the pre-release entry.

  The race is decided by Keel's lock and claim, not by host behaviour. The fake host is therefore the right subject, and `docs/host-contract.md` records it as a scenario.

## Risks

- A person who starts a session by hand, named `<role> · …`, in the role's worktree after a claim would be adopted. Only the hand-over uses that name pattern, so this is accepted.
- pid reuse could make a dead runner look alive. The 10-minute limit in D2 bounds that.
