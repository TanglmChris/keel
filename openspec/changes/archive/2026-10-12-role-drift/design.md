## Context

Issue #301 and the owner's decision of 2026-10-12 recorded on it. Not chosen: pruning silently whenever `roles.json` is read; reporting only.

## Facts

- F1 — `roles.json` maps a worktree path to a role, written by `keel chat role --set`; nothing removes an entry, and two worktrees may carry the same role (rtl_ppa_prj, 2026-10-12: `iecc-design-sub` on `r007_comp`, removed, and `r008_user`).
- F2 — Presence is kept per role, not per worktree, and is touched by the chat hooks of a session started in a bound worktree.
- F3 — A session starting in a worktree with no role while others have one is told to bind one, but not which role is going unattended (#245).

## Decisions

- D1 — `src/core/chat/drift.js` exports `roleDrift(where, now)`: `removed` lists `{ role, worktree }` for each binding whose path is not in `git worktree list --porcelain` and is not a directory; `unattended` lists `{ role, waiting, lastActive }` for each bound role with `waiting` non-empty — `<n> unread addressed record(s)` and/or `shift note waiting since <t>` — whose presence `last_active` is missing or more than 2 hours old.
- D2 — `keel patrol` adds `drift` to its result and prints `drift: <role> is bound to <worktree>, which no longer exists; \`keel chat role --prune\` drops it` and `drift: <role> has <waiting> and no session active since <t|ever>; if its session runs in another worktree, bind <role> there, since nothing wakes it where it is bound`. With `--since-last`, each drift line is a snapshot entry `drift <role>`, so it is reported when it appears or changes. Drift never changes the exit status by itself outside `--since-last`.
- D3 — `keel --doctor` prints `chat roles: ok` when there is a chat store with bindings and no drift, else one `chat roles: drift - …` line per item; nothing when there is no chat store.
- D4 — `keel chat role --prune` removes every removed binding, prints `Pruned <role> from <worktree>.` per entry or `No binding points at a removed worktree.`, and with `--json` prints `{ pruned: [...] }`.
- D5 — When the worktree has no role while others have one, `keel context` adds `unattendedRoles` (role names) when any exist, the warning names them, and the session-start line reads `- chat role: none bound here while other worktrees have one; roles with nobody active where they are bound: <roles>. If this session is one of them, run \`keel chat role --set <role>\` here.`
