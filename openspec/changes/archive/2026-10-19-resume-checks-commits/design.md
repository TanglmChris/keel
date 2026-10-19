## Context

#347 suggested `git fetch` and then an ancestry check per commit. Keel fetches nothing (the patrol's F4, which the rendered patrol task meets by fetching in its own step), so the check reads the remote-tracking refs as they are and says when they were last fetched; a session that wants current refs fetches first.

## Facts

- F1 — `resume` (`src/core/shift.js`) prints the note text and moves it to history; nothing reads the note's content.
- F2 — Worktrees of one repository share `refs/remotes/`, so a push from any of them updates the refs every role's resume reads.

## Decisions

- D1 — A token of 7–40 hex digits holding at least one letter and one digit is a commit id, so a date such as `20261018` is not; `<branch> @ <sha>` (spaces optional) is a pair. Each is listed once, in note order.
- D2 — The default branch is `refs/remotes/origin/HEAD`'s target, else `origin/main`, else `origin/master`. A sha that does not resolve to a commit is `not found`; one that is an ancestor of the default branch is `already in origin/<default>`; for a pair, a branch with no `origin/<branch>` is `branch gone`, and one whose tip is not the named sha is `branch moved: now <short>`. Several marks join with `; `.
- D3 — The list is headed `Commits the note names, against the remote-tracking refs (not fetched; last fetch <time or never>):` and is omitted when the note names none; `--json` carries it as `commits`.
