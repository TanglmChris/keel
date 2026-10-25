## Facts

- F1 — `src/core/tick.js` runs each due patrol as `keel patrol --repo <worktree> --since-last --notify --json`, plus the disk and quota flags (#456). It passes no `--issues`.
- F2 — `routeIssues` in `src/core/patrol.js` returns before routing when it has no issue list. `conditionHolds` reports an `issue #<n> closed` wait as unchecked without one. The patrol's text output then says `pass --issues to check it`. The tick runs the patrol with `--json` and prints none of it.
- F3 — Keel already runs `gh`: `src/core/chat/archive.js` asks `gh repo view` for the repository's visibility.
- F4 — `gh issue list` has no sort flag. With gh 2.101.0 on this Mac, `gh issue list --state all --search "sort:updated-desc" --limit 3 --json number,state,updatedAt` returned #473, #469, #468, newest update first. `gh issue view 473 --json number,title,state,labels,updatedAt` returned one object of the same shape as a list entry.
- F5 — The patrol dedupes each routed update by the ref `issue:#<n>@<updatedAt>`. Passing an update a second time sends nothing.

## Decisions

- D1 — The tick needs issue state when `issue_roles:` in the patrol worktree's `keel/config.yaml` has at least one readable route, or when any chat group holds an open wait whose condition is `issue #<n> closed`. Then, before the first due patrol runs, it runs once, in that patrol's worktree:
  - `gh issue list --state all --search "sort:updated-desc" --limit 100 --json number,title,state,labels,updatedAt`;
  - for each waited issue the list did not return, `gh issue view <n> --json number,title,state,labels,updatedAt`.
  It writes the combined array to `tick/issues.json` in the chat store and passes `--issues <that file>` to every patrol it runs in that step. When nothing needs it, it runs no `gh` and passes no `--issues`. A patrol that is not due causes no fetch.
- D2 — Each `gh` call has a 60-second timeout. When `gh` cannot start, exits non-zero, or prints something that is not a JSON array (or object, for `view`), the issue state is `failed`, with a reason naming the call and its first line of error. Whatever was read is still passed. The states are `read` (every call succeeded), `failed`, and `unneeded`. The tick keeps the last state and its text in `tick/state.json` as `issues`, and prints one line when the state differs from the last one, as it does for quota (#456 D3).
- D3 — `keel --doctor` prints an `issue checks` line when `tick/state.json` holds an issue state: `ok` with the time of the last read for `read`, `not checked` with the recorded reason for `failed`, and `ok` saying nothing needs them for `unneeded`. With no recorded state it prints nothing, since then no tick has run here.
- D4 — The 100-issue window is fixed, not configurable. The patrol runs at most once per tick, and the list is sorted by last update, so only issues updated in that interval matter for routing. Waited issues are fetched by number whatever their age.
