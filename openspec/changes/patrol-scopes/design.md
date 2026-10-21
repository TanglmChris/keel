## Facts

- F1 — `readPatrolDeclaration` (`src/core/config.js`) reads `patrol:` with `configMap`, a flat `key: value` reader, so one role, one `every:`, one `host_task:`, one `model:`, one cadence, and one `runner:`. Six callers read it: `keel context` (the `patrol` field and its reminder), `keel shift resume` (the closing reminder), `keel patrol task` (`hostTask`), `recommendNext` (cadence), and `keel tick` (`patrolWorktree`, `task`).
- F2 — `keel patrol` runs as the role bound to its worktree (`store.requireRole`). Everything it covers besides that role's own waits is repository-wide:
  - `patrol()` lists every bound role's presence;
  - `nudgeRoles` considers every bound role but the patroller, with throttling state in `patrol/nudges.json` keyed by role;
  - `routeIssues` sends to every role a route names, deduped only within the direct group between this patroller and the target;
  - `sinceLast` snapshots every `shift <role>` and `role <role>` entry, the remote default ref, the primary checkout, drift, and disk;
  - `handOffRisks` lists every role's failed or hung hand-off.
- F3 — `keel tick` runs at most one patrol, in the worktree bound to the declared role, with its due time in `tick/state.json` `patrol`.
- F4 — kaiwu-ip, 2026-10-21: `patrol: role: kaiwu-pm-iecc, every: 60m`. Its chat groups `iecc` and `rmw` have these members:
  - `iecc`: the IECC team plus kaiwu-chief, kaiwu-flow, kaiwu-layout, and kaiwu-lead;
  - `rmw`: kaiwu-pm-rmw, kaiwu-review-rmw, and kaiwu-spec-rmw.

  A role can therefore belong to two coordinators' scopes.

## Decisions

- D1 — `patrol:` may be a list of mappings, each item opened by `- role: <role>` and carrying the same keys as today's single mapping, plus `scope:`. The single mapping keeps its meaning: one patrolling role with whole-repository scope. An item Keel cannot read is reported by name and patrols nothing, and the other items still apply. A role declared twice is unreadable after its first item.
- D2 — `scope: group:<name>` limits a declaration to the members of chat group `<name>`, as the group's log gives them at run time. A declaration without `scope:` is unscoped. Scope accepts only the `group:` form; any other form makes the item unreadable.
- D3 — Which roles a declaration covers (owner, 2026-10-21):
  - A scoped declaration covers its group's members.
  - The unscoped declaration covers the roles that are in no declared scope.
  - A role in two scopes is covered by both. Nudge throttling stays per role in the shared `patrol/nudges.json`, so such a role is nudged at most once per window, by whichever coordinator runs first, and that coordinator receives the escalation.
  - The patroller never covers itself.
- D4 — Repository-wide items belong to one declaration: the unscoped one if declared, otherwise the first declared (owner, 2026-10-21). These items are the remote default ref, the primary checkout, drift, disk, and quota. Other declarations neither snapshot nor report them.
- D5 — Each covered-role item follows D3: presence rows, `role <r>` and `shift <r>` snapshot entries, nudges and their escalations, hand-off risks, and issue routing. A route's target outside the patroller's coverage is not sent. A ref already present in a direct group between the target and any declared patrolling role is not sent again, so a role covered twice gets one message per update.
- D6 — `keel context`, the SessionStart projection, and `keel shift resume` remind the bound role of its own declaration. `keel patrol task` picks the declaration to render in this order:
  1. the one `--role <role>` names, a new option;
  2. the one whose role is bound to the calling worktree;
  3. the single declaration, if there is exactly one, as today.

  Otherwise it refuses and names the declared roles and `--role`.
- D7 — `keel tick` runs each declared patrol that is due, in its role's bound worktree, with its due time kept per role under `tick/state.json` `patrols`. The single mapping's existing `patrol` entry is read as that role's. `keel tick task` keeps one launchd job per repository; it needs some bound worktree of a declared role, taking the first.
- D8 — `recommendNext` reads the cadence of the running role's own declaration.
- D9 — A patrol run by a role that `patrol:` does not declare behaves as today: it covers every role and owns the repository-wide items. Only declared roles are scoped.
- D10 — A `scope:` group that has no members at run time covers nobody, and the run reports it as a warning naming the group.
