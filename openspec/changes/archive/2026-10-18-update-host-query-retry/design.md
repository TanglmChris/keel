## Context

#365 offered a retry, a longer limit, or no change. The retry matches the marketplace refreshes (#329, #359) and keeps a lasting hang bounded at twice the limit; a 90 s limit would make every hang cost 90 s.

## Facts

- F1 — `hostQuery` (`bin/keel.js`) runs `plugin list --json` once with `KEEL_UPDATE_QUERY_TIMEOUT_MS` or 30 s and reports `timed out after <n> s` on `ETIMEDOUT` (#354).
- F2 — Measured 2026-10-18 (codex-cli 0.163.0, proxy 127.0.0.1:7890): 58.2 s once, then 1.21 s and 0.89 s.

## Decisions

- D1 — `hostQuery` retries a query that timed out once, with the same limit; a second timeout reads `timed out twice, after <n> s each`. Other failures — a nonzero exit, no JSON, a spawn error — are reported on the first attempt, since nothing suggests they pass on a retry.
