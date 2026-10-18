## Context

#359 offered two fixes, a retry and the host's stderr in the `failed` line; they are independent and both are taken. The retry copies the Codex rule (#329), which the owner accepted on 2026-10-14.

## Facts

- F1 — `updateClaudePlugin` (`bin/keel.js`) runs `claude plugin marketplace update <market>` then `claude plugin update <id>` through `runHostSteps`, which stops at the first nonzero step and reports `exited <status>` only; `hostRun` captures stderr and the report drops it.
- F2 — `updateCodexPlugin` retries its marketplace refresh once through `hostFails` (#329).
- F3 — On 2026-10-18 the Claude refresh failed once and passed on a direct rerun, twice in one day (#359).

## Decisions

- D1 — The Claude marketplace refresh runs at most twice; a pass on either attempt goes on to `claude plugin update`, and two failures report `failed`, naming the command, `failed twice`, and the second attempt's reason. `claude plugin update` is not retried.
- D2 — A failed host step's reason is its spawn error, or `exited <status>` followed by `: <last non-empty stderr line>` when there is one; only the last line, so the status line stays one line.
