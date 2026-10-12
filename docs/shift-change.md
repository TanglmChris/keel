# Shift change

A long-running role's session collects context until it is cleared. A shift change does that at a moment of your choosing, so nothing is lost. The outgoing session wraps up and leaves a note, then clears itself, and the new shift starts from the note.

With `keel chat` roles bound, each step is also a record in the direct group between the coordinator, usually a PM role, and the role. Each record wakes the session it is for, and the history stays reviewable. With no chat role, a shift change still works. `check`, `ready`, and `resume` need nothing but the repository. The coordinator tells the session by whatever channel it has, and the new session runs `keel shift resume`. No bot or Slack is involved either way: chat roles are local names in the repository's git common directory.

## The steps

| Who | Command | What it does |
|---|---|---|
| coordinator | `keel shift request <role> [text]` | With chat roles: posts a shift request to the role as a todo, which wakes it. Without them, tell the session any way you like. |
| role | `keel shift check` | Read-only. Lists loose ends and exits 1 if there are any. |
| role | `keel shift ready "<note>"` | Stores the note and closes the request, if there is one. Refused while `check` reports anything, unless `--force-reason "<why>"` is given. The note can also come from `--file` or stdin. |
| role, working in another worktree | `keel shift ready --role <role> "<note>"` | Files the note under the role and closes its request, from a worktree bound to no role (#290). Without `--role`, `ready` in an unbound worktree is refused while any role's request is open, so a note cannot land where no request will find it. |
| role | clear the session | Desktop app: `clear_session("self")`, which you approve, or `/clear`. CLI: `/clear`. Codex: a new session. Keel runs none of these. |
| coordinator | `keel shift start <role> [next step]` | With chat roles: refused until the role's note waits, then wakes the cleared role. Without them, tell the new session to run `keel shift resume`. |
| role (new shift) | `keel context`, then `keel shift resume` | Prints the note and moves it to history. With a chat role, also tells the coordinator the role is on shift. A new session in a worktree bound to no role reads the role's note with `keel shift resume --role <role>`. |
| anyone | `keel shift status` | Each role's state: requested, note waiting, or resumed. A worktree note says which worktree should run `keel shift resume`; a role still requested names any worktree note written since. |

## Changing your own shift

A role that no request named — the coordinator going last, or any session that decides to change its own shift — runs `ready` like any role, but nobody is set to start its new session, and `ready` says so. It cannot `keel shift start` itself, which is refused. `status` says its note is resumed by its own next session: type into it, or use `keel shift ready --wake` (below).

`keel shift ready --wake` closes that gap. Besides storing the note, it leaves a detached one-shot waiter. When the role's next session starts — a SessionStart after a clear or a fresh start, later than the `ready` — the waiter writes one message from `keel-shift` to the role, telling it to run `keel context` and `keel shift resume`, and exits. On Claude that message wakes the new session like any other. The waiter writes nothing if the note was already resumed, and gives up after two hours. It is the one exception to "Keel schedules nothing": it never recurs. It needs a chat role, and it sees only a session that opens in a worktree bound to that role; a new session elsewhere still needs someone to type into it.

## The coordinator's own shift

The coordinator goes last (#289). On Claude nothing wakes a cleared session, so a coordinator that clears before starting the others leaves the whole team waiting until someone types into its new session. Its `keel shift check` therefore lists every role whose note waits and that it has not started since, and its `ready` is refused until it runs `keel shift start` for them, or gives `--force-reason`. Then it runs `ready` with its own note like any role, which `status` and the new session's projection show. When its new shift runs `keel shift resume`, the output names any role still waiting for `start`.

Session state a clear destroys and Keel cannot see — scheduled jobs such as a patrol, Remote Control — belongs in the note, so the next shift can re-create it; with `patrol:` declared, the new shift is reminded of the patrol anyway.

## What `check` looks at

- Uncommitted changes.
- Commits on no remote. Skipped, with a note, when the repository has no remote.
- An active task write guard (`keel/guard.json`).
- Processes whose working directory is inside the worktree, other than the session running the check.
- Temporary worktrees in a Claude scratchpad of a session started in this worktree. Other temporary worktrees, such as another session's, are listed as notes and do not block.
- Open todos assigned to the role, and unread messages that would wake it.
- For a role that requested shift changes: roles whose note waits and that it has not started since (`unstarted`).

A project can run its own checks beside it, such as build products under a scratch directory, from a script that calls `keel shift check` first.

## The note

Write what the next shift needs to cold-start: what you were doing, the next step, what you are waiting on, and where things are (branch, files, issues). The note lives in the repository's git common directory: `keel-chat/shift/<role>.md` for a role, or `keel-chat/shift/worktree/<name>-<id>.md` for a worktree with no chat role. That is outside every worktree, so it is never committed. It exists from `ready` until `resume`.

While it waits, `keel context` and the session-start projection say so on every host. A session that starts by itself, rather than through `start`, still finds it.

The note is not where work left undone is tracked. Put follow-ups in the project's tracker and cite them in the note. It is not `keel/HANDOFF.md` either, and `keel context` does not read it.
