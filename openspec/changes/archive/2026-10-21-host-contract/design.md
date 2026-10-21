## Facts

All measured on 2026-10-21 with Claude Code 2.1.304, using throwaway `claude --bg -w` probes started from the main checkout and removed afterwards.

- F1 — Session states reported by `claude agents --json`:

  | Probe | status | state | waitingFor |
  |---|---|---|---|
  | blocked on AskUserQuestion | `waiting` | `blocked` | `input needed` |
  | blocked on a tool-permission prompt (`--permission-mode default`, Bash) | `waiting` | `blocked` | `permission prompt` |
  | finished turn | `idle` | `done` | — |

  This supersedes the `idle`/`working` record in the archived cli-shift-handover design F1.
- F2 — Timeline of `claude stop` on an idle probe, sampled every 0.1 s:

  | Time | What changed |
  |---|---|
  | 0.32 s | the row has no `status` and no `pid` |
  | 0.98 s | `stop` returns |
  | about 3.2 s | the process exits |

  This is consistent with #395 on 2.1.303 (0.66 / 0.83 / 2.68 s).
- F3 — `handOver` runs `retire` (stop), starts the new session, then `removeOldSessions`. That function selects rows with no `status`, so the session just handed over qualifies while its process still runs. Its transcript is copied at that moment.
- F4 — `listAgents`, `stop`, `--bg`, and `rm` in `shift.js` run with no timeout. A failed listing returns `[]` from `handOver`, and no reason is recorded.
- F5 — `tick.js` `wakeEnded` sets `state.woken[role]` whatever `resumeCli` returned.
- F6 — In the suite, the `stop-lag` and `no-rename` fake modes are never enabled, and `KEEL_SHIFT_RENAME_WAIT_MS` and `KEEL_SHIFT_STOP_WAIT_MS` are set but read by nothing since 5.168.0.

## Decisions

- D1 — `removeOldSessions(claude, where, entry, keep)`:
  - For the session just handed over, it first waits up to `KEEL_SHIFT_EXIT_WAIT_MS` (default 15000) for `entry.pid` to exit.
  - Any row to be removed whose process is still running (`entry.pid` for that session, or the row's own `pid`) is skipped and stays listed.
  - The transcript copy and `claude rm` follow the exit.
- D2 — Host calls in the hand-over get `timeout` (`KEEL_SHIFT_HOST_TIMEOUT_MS`, default 60000). When the listing cannot be read:
  - `handOver` writes `waiting_on` on each pending entry;
  - `describeHandOff` and `handOffRisks` print it;
  - ENOENT reads "claude was not found; put it on PATH or name it with KEEL_CLAUDE".

  `resumeCli` reports ENOENT the same way.
- D3 — `wakeEnded`:
  - It records `state.wake_attempts[role] = { record, count }`.
  - `woken[role]` is set on success, on a `removed` result, or on the third failure for the same record. A newer record starts the count again.
- D4 — `docs/host-contract.md` holds the matrix for the CLI path. The columns are condition, host observation, Keel's behaviour, and evidence, where evidence names a scenario, a fake test, a measurement (version and date), or `unverified`. It ends with what this loop does not cover: Desktop, Codex, and real concurrent races. The page is in English only; `docs-zh-match-english` checks only Chinese pages that exist.
- D5 — The suite's stale env settings go. The `stop-lag` fake mode is exercised by D1's scenario rather than removed.
