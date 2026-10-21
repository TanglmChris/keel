## Facts

- F1 — `readIssueRoles` (`src/core/config.js`) reads each `issue_roles:` line with `/^(.+?):\s+([a-z0-9][a-z0-9-]{0,31})$/`, strips one pair of surrounding quotes from the label, and stores `routes.set(label, role)`. A later line with the same label silently replaces an earlier one.
- F2 — `routeIssues` (`src/core/patrol.js`) is the only reader. It maps each label of an issue through `routes.get`, deduplicates the roles, skips the patrolling role itself, and posts one direct message per role, deduped by ref `issue:#<n>@<updatedAt>` against the direct group.
- F3 — Today a key `design + dmc_rmw` is read as one label spelled `design + dmc_rmw`. GitHub label names may contain spaces and `+` (`c++`), so the separator must not be a bare `+`.
- F4 — `keel --doctor` does not read `issue_roles:`, and nothing but patrol consumes `routes`.

## Decisions

- D1 — A key is split on `/\s+\+\s+/` (a `+` with whitespace on both sides) into a label set. `c++` and `a+b` stay single labels. A key wrapped in one pair of `"` or `'` is one label verbatim and is not split, as today.
- D2 — A set with an empty member (`design + `) or a repeated member (`design + design`) is an unreadable line: reported, routing nothing. The order of members does not matter; `a + b` and `b + a` are the same set, and a later line with the same set replaces the earlier one, as a repeated label does today (F1).
- D3 — `readIssueRoles` returns `routes` as an array of `{ labels, role }` in declaration order. `routeIssues` keeps the routes whose every label the issue carries, then drops any kept route whose label set is a strict subset of another kept route's set, then sends to the remaining roles exactly as today (dedupe by role, skip the patrolling role, ref dedupe). Suppression happens before the patrolling-role skip, so a combined route to the patrolling role still silences the single-label route it refines.
- D4 — The unreadable-line warning names both shapes: `is not \`<label>: <role>\` or \`<label> + <label>: <role>\``.
- D5 — `keel --doctor` gains nothing. The issue asked how doctor reports two routes that send one issue to roles of different teams; doctor cannot see an issue's labels, and two non-nested matching routes are legitimate (one issue for two teams, or `flow` beside `design`). The nested case, the one that mis-routes, is resolved by D3 rather than reported.
