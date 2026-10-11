## Context

Issues #260 and #242; owner decisions of 2026-10-11 recorded on both, refined the same day (patrol posts its own notices; waits are chat records).

## Facts

- F1 — Chat records are files under `<git common dir>/keel-chat/groups/<g>/log/`; `writeRecord` writes the fields in `FIELD_ORDER`, and only `message`, `todo`, and `system` are readable — they alone make unread and wake.
- F2 — `directPost` posts in the direct group between two roles, creating it, and a direct message wakes its recipient.
- F3 — `notice.presenceOf` reports a role's presence and last activity; `store.openTodos` lists open todos with assignees.
- F4 — Keel fetches nothing and schedules nothing (AGENTS.md, Unattended runs); `keel triage` and `keel worktrees` take `gh` output from the caller.

## Decisions

- D1 — A `wait` record carries `condition`: `commit <sha> on <remote>` (remote defaulting to `origin`) or `issue #<n> closed`, from the waiting role, in a group it belongs to. It is not readable (F1).
- D2 — A wait is met when a `met` record targets it. `keel chat waits` lists waits with none.
- D3 — `keel patrol` requires a bound role and reads every group that role can read. A commit condition holds when the commit resolves and a `refs/remotes/<remote>/` ref contains it; an issue condition holds when `--issues` lists that issue with state `CLOSED`; without `--issues`, issue conditions are left unchecked and reported so.
- D4 — For a held condition, patrol writes `met` targeting the wait and, unless the waiter is the patrolling role, sends the waiter a direct message naming the condition and the wait id.
- D5 — `issue_roles:` maps a label to a role, one `<label>: <role>` per line; an unreadable line is reported and routes nothing. For each issue in `--issues` carrying a mapped label, patrol sends the role one direct message with ref `issue:#<n>@<updatedAt>`, unless a record with that ref already exists in that direct group. The first patrol therefore notifies each mapped open issue once.
- D6 — The digest lists notices sent, held conditions, unchecked conditions, and each bound role's presence, last activity, and open todo count; a role whose last activity is older than `--idle` (default `30m`) is marked idle. Idleness never changes the exit status.
- D7 — Exit 0 when patrol wrote nothing, 2 when it wrote at least one record, 1 on an error.
