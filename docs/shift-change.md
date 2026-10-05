# Shift change

A long-running role's session collects context until it is cleared. A shift change does that at a moment of your choosing, so nothing is lost. The outgoing session wraps up and leaves a note, then clears itself, and the new shift starts from the note.

With `keel chat` roles bound, each step is also a record in the direct group between the coordinator, usually a PM role, and the role. Each record wakes the session it is for, and the history stays reviewable. With no chat role, a shift change still works. `check`, `ready`, and `resume` need nothing but the repository. The coordinator tells the session by whatever channel it has, and the new session runs `keel shift resume`. No bot or Slack is involved either way: chat roles are local names in the repository's git common directory.

## The steps

| Who | Command | What it does |
|---|---|---|
| coordinator | `keel shift request <role> [text]` | With chat roles: posts a shift request to the role as a todo, which wakes it. Without them, tell the session any way you like. |
| role | `keel shift check` | Read-only. Lists loose ends and exits 1 if there are any. |
| role | `keel shift ready "<note>"` | Stores the note and closes the request, if there is one. Refused while `check` reports anything, unless `--force-reason "<why>"` is given. The note can also come from `--file` or stdin. |
| role | clear the session | Desktop app: `clear_session("self")`, which you approve, or `/clear`. CLI: `/clear`. Codex: a new session. Keel runs none of these. |
| coordinator | `keel shift start <role> [next step]` | With chat roles: refused until the role's note waits, then wakes the cleared role. Without them, tell the new session to run `keel shift resume`. |
| role (new shift) | `keel context`, then `keel shift resume` | Prints the note and moves it to history. With a chat role, also tells the coordinator the role is on shift. |
| anyone | `keel shift status` | Each role's state: requested, note waiting, or resumed. |

## What `check` looks at

- Uncommitted changes.
- Commits on no remote. Skipped, with a note, when the repository has no remote.
- An active task write guard (`keel/guard.json`).
- Processes whose working directory is inside the worktree, other than the session running the check.
- Temporary worktrees in a Claude scratchpad of a session started in this worktree. Other temporary worktrees, such as another session's, are listed as notes and do not block.
- Open todos assigned to the role, and unread messages that would wake it.

A project can run its own checks beside it, such as build products under a scratch directory, from a script that calls `keel shift check` first.

## The note

Write what the next shift needs to cold-start: what you were doing, the next step, what you are waiting on, and where things are (branch, files, issues). The note lives in the repository's git common directory: `keel-chat/shift/<role>.md` for a role, or `keel-chat/shift/worktree/<name>-<id>.md` for a worktree with no chat role. That is outside every worktree, so it is never committed. It exists from `ready` until `resume`.

While it waits, `keel context` and the session-start projection say so on every host. A session that starts by itself, rather than through `start`, still finds it.

The note is not where work left undone is tracked. Put follow-ups in the project's tracker and cite them in the note. It is not `keel/HANDOFF.md` either, and `keel context` does not read it.
