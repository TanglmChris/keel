## Why

Issue #408, approved by the owner on 2026-10-21. The CLI shift and wake path depends on how Claude Code reports sessions. Several of those assumptions were corrected only after measurement on the real host (5.162–5.169), and no single place states the contract, its evidence, and its gaps. The issue asks for a minimal closed loop on the CLI shift path first.

An inventory of the suite on 2026-10-21 found that every hand-over check runs against a fake `claude`, and found these gaps:

- **A session can be removed while its process is still running.** On Claude Code 2.1.304, measured on 2026-10-21, a stopped session's row loses `status` and `pid` at 0.32 s, `claude stop` returns at 0.98 s, and the process exits at about 3.2 s. A hand-over stops the old session and then runs `removeOldSessions`, which selects rows without a `status`. Since 5.178.0, the default `keep_old_sessions: 0` makes the session just handed over eligible, so it can be removed while its process is still running, and its transcript copied before the final writes. The fake's `stop-lag` mode, which models #395, is never switched on.
- **A session listing that fails is silent.** It leaves a hand-off pending with no reason given. The host calls have no timeout. A missing `claude` prints a raw `ENOENT`.
- **A failed wake is never retried.** A tick marks the role woken even when the resume failed.
- **The waiting-for-input state had two conflicting records.** One said `idle`/`working`; the other said `waiting`/`blocked`. Re-measured on 2.1.304, both an AskUserQuestion and a tool-permission prompt report `status: waiting`, `state: blocked`, with `waitingFor` `input needed` and `permission prompt` respectively. Keel already treats `waiting` as not finished, so no behaviour changes there.

## What Changes

- **`removeOldSessions` waits before removing.** It waits up to 15 s for the recorded process of the session just handed over to exit before running `claude rm` and copying the transcript. It never removes a row whose process is still running; such a row stays listed until the next hand-over.
- **Host failures are named.** The host calls get a timeout. An unreadable listing, or a missing `claude`, is recorded on each pending hand-off, and both `keel shift status` and the patrol risk name it. `keel chat wake now` names a missing `claude` plainly.
- **Ticks retry failed wakes, within limits.** A tick marks a role woken only after a successful resume, and retries a failed resume at most three times for the same record. It never retries a removed session.
- **The contract is written down.** A new page, `docs/host-contract.md`, states the observed states and failure cases of the CLI path, Keel's behaviour in each, and the evidence behind each: deterministic test, test against a fake host, real-host measurement with version and date, or unverified.
- **Stale test settings are removed.** The suite stops setting `KEEL_SHIFT_RENAME_WAIT_MS` and `KEEL_SHIFT_STOP_WAIT_MS`, which nothing reads since 5.168.0.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/shift.js`, `src/core/tick.js`, `src/core/chat/notice.js`, `docs/host-contract.md`, `scripts/validate_plugin.py`, the published spec, and the changelog. Desktop and Codex paths are out of scope for this first loop, as the issue suggests.
