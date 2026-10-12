## Context

Issues #289, #290, #291 and the owner's decisions of 2026-10-12 recorded on them. Not chosen: queued automatic starts after the coordinator clears (#289; Keel schedules nothing) and filing automatically under the only open request (#290; a guess).

## Facts

- F1 — In `src/core/shift.js`, a role's note is `shift/<role>.md` from `ready` until `resume`; `start` posts a `keel-shift` message in the direct group and leaves the note; a worktree with no role writes `shift/worktree/<name>-<id>.md`.
- F2 — `ready` writes under `currentRole` and closes that role's open requests; `check` lists loose ends and `ready` refuses while any exist unless `--force-reason`.
- F3 — `describe` prints `keel shift start <row.role>` for every row with a note, including `worktree <name>-<id>` rows.
- F4 — A note's header names the worktree it was written in: `Written <stamp> in <path>.`

## Decisions

- D1 — `check` for role R adds an `unstarted` item for each role S ≠ R whose note waits, whose latest shift request came from R, and for which no `keel-shift` record from R in their direct group is newer than the note. `ready` therefore refuses until R starts them, as for any loose end.
- D2 — `resume` for role R lists, after the note, `Still waiting for \`keel shift start\`: S, …` for the same set, and adds `waiting` to its JSON.
- D3 — The request text gains a step, and `ready`'s output a line, naming host-session state a clear destroys (scheduled jobs, Remote Control) as something to carry in the note.
- D4 — `ready --role <r>`: refused unless `r` has an open shift request; refused when this worktree is bound to another role. The check and the note use `r`; the note is `shift/<r>.md`, and `r`'s open requests close.
- D5 — `ready` without `--role` in a worktree with no chat role, while any role request is open, is refused: `This worktree has no chat role, and shift requests are open for <roles>; if this session is one of them, run \`keel shift ready --role <r> …\`.`
- D6 — `status`: a worktree-note row reads `note waiting since <t>; no chat role there, so tell the session in <path> to run \`keel shift resume\``, the path from F4; a role row with an open request and no note adds `a worktree note was written since: <name>` for worktree notes newer than the request.
