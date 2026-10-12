## Context

Issue #293 and the owner's decision of 2026-10-12 recorded on it. Not chosen: relying on the user to type into the new session; naming another role to start it.

## Facts

- F1 — `clear_session("self")` in the desktop app runs after the current turn ends; the cleared session then waits for input, and a message queued before it drops the clear.
- F2 — A record wakes a role only when it is from another role and addresses it (`wakes` in `src/core/chat/store.js`); the Claude `FileChanged` hook with `asyncRewake` wakes an idle session when its signal file changes, and SessionStart registers the watched paths, including after a clear.
- F3 — The chat hook's SessionStart writes the role's presence; its payload carries `source` (`startup`, `resume`, `clear`, `compact`).
- F4 — A detached child spawned from a Bash tool command survives the command's return (probe 2026-10-12: pid 25088 wrote its file 15 s later).
- F5 — `AGENTS.md` and the README say "Keel schedules nothing".

## Decisions

- D1 — The chat SessionStart hook adds `session_started` (now) and `session_source` (the payload's `source`) to the role's presence.
- D2 — `ready --wake` requires a chat role (bound, or `--role`), writes the note, and spawns `keel shift wake-wait --role <r> --since <ms> --repo <worktree>` detached, with `/` as its working directory so `check` never counts it. It polls the role's presence every 5 s (`KEEL_SHIFT_WAKE_POLL_MS`) for up to two hours (`KEEL_SHIFT_WAKE_TIMEOUT_MS`); when `session_started` is at or after `--since` and `session_source` is `clear` or `startup`, it writes, if the role's note still waits, one message from `keel-shift` in the direct group `dm-<r>--keel-shift` (created if absent) with ref `keel-shift`: `<r>: your new shift starts now (woken by the \`keel shift ready --wake\` you ran). First run \`keel context\`, then \`keel shift resume\`.` Then it exits.
- D3 — `ready` output: with `--wake`, it says the wake is armed; without it, for a role that closed no request, it says nobody is set to start the new session and names `--wake`; otherwise the coordinator line stays.
- D4 — `start <r>` by role `r` is refused: `A role does not start its own new shift; use \`keel shift ready --wake\`, which wakes it once the new session starts.`
- D5 — `resume --role <r>` applies `ready --role`'s rule: refused when this worktree is bound to another role; reads `r`'s note.
- D6 — `status` for a role note with no request: `note waiting since <t>; its own next session resumes it — woken by \`ready --wake\`, or by typing into it`.
- D7 — The protocol line becomes: Keel schedules nothing, with one exception — `keel shift ready --wake` leaves a one-shot waiter that writes a single wake record once that role's next session has started, then exits.
