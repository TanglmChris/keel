## Context

5.159.0 (#376) maps each record's role fields through `renames.json` as `readLog` reads them, including the `target` of `join` and `leave`. `groupState` then replays those records in order.

## Facts

- F1 — kaiwu-ip's `iecc` log holds `join iecc-pm`, later `join kaiwu-pm-iecc`, then `leave iecc-pm` (the migration of 2026-10-19). Mapped, that replays as join, join, leave of `kaiwu-pm-iecc`.

## Decisions

- D1 — `readLog` leaves a `join`/`leave` record's `target` as written and gives it `member`, the target read through the renames. `groupState` replays the records under `target` and then maps the resulting members through `member`.
- D2 — A merged role is listen-only only if every name it merges was listen-only, so a full member's access is never lowered by a merged listener.
