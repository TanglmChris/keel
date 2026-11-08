## Facts

- F1 — `tick(where, now)` in `src/core/tick.js` reads `tick/state.json`, runs `wakeEnded` and `handOver`, then the due patrols. The file written by a real run holds `patrol` (`next_at`, `last_run`, `last_exit`), `quota_state` and `issues`; `last_run` moves once per patrol, hourly with `cadence: adaptive`, so nothing in it moves every five minutes.
- F2 — `bin/keel.js` `printTickIssueChecks` already reads `tick/state.json` for `keel --doctor`; `printDoctorLine(name, status, text)` takes `ok`, `not checked` and `problem`.
- F3 — `keel context` builds `context.patrol` (`role`, `every`, `runner`, `hostTask`) in `src/core/context.js`; `plugins/keel/scripts/session-start.js` turns it into the `- patrol:` line.
- F4 — The job `keel tick task` renders runs every 300 s (`StartInterval`). Measured 2026-11-08: `tick.log` of this repository advanced at 5-minute steps after the reinstall, and its modification time stood at 2026-11-07 11:46 during the outage — a trace launchd leaves, not one Keel writes or reads.
- F5 — `readPatrolDeclarations(dir).declarations` lists the `patrol:` items with their `runner`.

## Decisions

- D1 — `tick()` writes `last_tick` (local ISO time) first, before any wake or hand-over, so a run that fails later still counts as a run. It merges into the existing state and changes no other field.
- D2 — A tick is silent when `last_tick` is older than 15 minutes, three of the rendered job's intervals. The value is a constant in `tick.js` and is stated in the docs; a job installed with another interval is not known to Keel.
- D3 — The check applies when `last_tick` exists, or when some `patrol:` item declares `runner: tick` and none was ever recorded (state `never`). Otherwise it says nothing, so repositories that do not use a tick see no new line.
- D4 — `keel --doctor` prints `tick`: `ok` with `last ran <time>`; `problem` with `has not run since <time> (<minutes> min ago)` and the repair (re-run `keel tick task` and its install commands, or the machine was asleep), or `has never run here although keel/config.yaml declares runner: tick`. An unparseable `last_tick` is reported as stale with the raw value.
- D5 — `keel context` adds `patrol.tick = { state, at }` when D3 applies. The SessionStart hook adds one line only for `stale` and `never`; `ok` adds nothing.
- D6 — Only `tick/state.json` is read. No host file, no `launchctl`.
- D7 — Limit, written in the docs: a sleeping or powered-off machine also shows as silent; the report says since when, and a person judges why.
