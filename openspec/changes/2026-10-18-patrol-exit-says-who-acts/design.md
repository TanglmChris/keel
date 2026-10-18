## Context

#350 suggested exit 2 only for what the coordinator must handle and 0 or a distinct code for state recorded and told to nobody. A distinct code keeps the run log and an auditing caller able to tell "nothing" from "something for others".

## Facts

- F1 — `src/core/patrol.js` sets `EXIT_WROTE` (2) when there are notices, held waits, since-last changes, nudges, or risks.
- F2 — Risks (`result.risks`) are what `--notify` sends to the coordinator (#307 part 3 D3); notices and nudges go to other roles, whose own signals wake them.
- F3 — A wait the patrolling role declared itself is marked met without a message (`unless the waiter is the patrolling role`), so the exit status is the only way its run tells it.

## Decisions

- D1 — `EXIT_ACT` = 2 when `result.risks` is non-empty or a held wait's `from` is the patrolling role; `EXIT_RECORDED` = 3 when otherwise anything was written, nudged, or reported changed; 0 when nothing was; 1 on error.
- D2 — `--help` and the rendered host task's step 3 name 3 alongside 0 and 2; the task ends without output on 0, 2 and 3 as before. The session-schedule reminder's "wake the model only on exit 2" stays true and is unchanged.
