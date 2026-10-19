## Context

#388 renames the retired session by resuming it with `/rename`, measured on a session that had been stopped some seconds earlier. The waiter stops and resumes within milliseconds, which was not measured. #395 measured it.

## Facts

- F1 — `claude stop <id>` returns before the session's process has exited. Resumed 2 s after the stop, a throwaway haiku session (Claude Code 2.1.303) printed `note: woke session 205e4307 with its saved options (-n, --permission-mode, --model).` and kept its id; resumed immediately after the stop, it printed `note: session 205e4307 is already running in the background, so this started a copy as a647e64f.` and the copy, not the original, took the name.
- F2 — On the real hand-over (keel-maint, 2026-10-19 21:30) the copy `429de332` was left running with `status: idle` under the shifted name, the original `b4d145a2` stopped with its old name, and the queue entry read `renamed: null` after the 30 s rename wait ran out.

## Decisions

- D1 — `retire()` polls `claude agents --json --all` after the first `claude stop` until the old session's row has no `status` or is gone, for at most `KEEL_SHIFT_STOP_WAIT_MS` (default 30 s). Only then does it resume the session with `/rename`. If the row still has a `status` at the bound, it does not resume (a resume would start a copy, F1); the rename is recorded as not shown, it stops the session again, and the hand-over goes on. The new session is started either way, as a rename was already best effort (#388 D4).
