## Context

#354 offered a shorter query limit or only naming the slow call; the owner chose the shorter limit plus an honest failure line (2026-10-18).

## Facts

- F1 — `hostRun` (`bin/keel.js`) spawns every host call with `timeout: 5 * 60 * 1000`; `hostJson` returns null on an error, a nonzero exit, or unparsable output; `claudeKeel`/`codexKeel` return null both for that and for a list without Keel, and `updateClaudePlugin`/`updateCodexPlugin` report null as `absent`.
- F2 — Each Claude update lists twice (before, after) and each Codex update three times (before, after the refresh for the hook comparison, after `plugin add`).
- F3 — Measured 2026-10-18: `codex plugin list --json` (codex-cli 0.163.0) returned in 1.1, 1.2 and 1.4 s; the 2026-10-14 normal runs took 2–3 s.

## Decisions

- D1 — `hostQuery` runs a `plugin list --json` with a limit of `KEEL_UPDATE_QUERY_TIMEOUT_MS` or 30 000 ms, and returns the parsed JSON, `absent` when the executable does not resolve (`ENOENT`), or a failure reason: `timed out after <n> s`, `exited <status>`, or `printed no JSON`.
- D2 — A failed query before the update reports the component `failed`, naming `<host> plugin list --json` and the reason, and runs no host step. A failed query after a step (Codex's hook comparison, either host's final check) also reports `failed`: the step ran, but the result is unverified, and the exit status is nonzero because a step that ran failed.
- D3 — Under `--dry-run` a failed query is not reported; the planned commands use the default ids, as for an absent host.
- D4 — The update commands keep `hostRun`'s five minutes.
