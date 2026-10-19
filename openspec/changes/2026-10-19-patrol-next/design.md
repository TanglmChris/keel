## Context

#356 proposed the rule table below, overridable in `keel/config.yaml`, with `every:` staying a fixed cadence. Keel's flat config reader takes one level of `key: value` under a block, so the overrides are flat keys under `patrol:` rather than a nested `cadence:` map; `cadence: adaptive` switches them on.

## Facts

- F1 — `patrol()` (`src/core/patrol.js`) already returns each role's presence and idleness, open todos, and the run's risks (quota, since-last, nudge escalations).
- F2 — `readPatrolDeclaration` (`src/core/config.js`) validates `role` and `every` and ignores an invalid optional key with a message.

## Decisions

- D1 — Rules, first match wins: `risk` when the run found a risk; `quota` when `--quota` is at or above 90; `night` when the local time is inside `quiet: HH:MM-HH:MM` (which may wrap midnight) and there is no risk, delaying until the window ends; `busy` when a role other than the patrolling one is not idle, or an open wait or todo is assigned to a role that is not idle; `idle` otherwise. Defaults: risk 30m, quota 4h, busy 60m, idle 3h.
- D2 — `min:` and `max:` clamp the chosen delay, except that a `night` delay is left as the time to the window end; defaults are none.
- D3 — Without `cadence: adaptive`, `next` is `every:` with rule `fixed`. The text output adds one `next: <duration> (<rule>)` line; `--json` adds `next_after_s`, `next_rule` and `next_at` (local ISO time). The run log line records `next=<duration>`.
- D4 — An override that is not a duration (or, for `quiet:`, not `HH:MM-HH:MM`) is ignored with the existing patrol config message and its default is used.
