## Facts

- F1 — `task(where)` in `src/core/tick.js` takes `patrolWorktree(where)` and throws its `why` when it has no worktree; with no declaration `patrolWorktrees` returns one item with `declaration: null, worktree: null` and the reason "declares no `patrol:`", or the config's own messages when it could not read one.
- F2 — `stableRepo(where)` returns the main checkout only if it exists and its `keel/config.yaml` declares a `patrol:`, since that is the file `keel tick --repo` reads for the patrol (#503 D1).
- F3 — `tick()` runs `wakeEnded` and `handOver` before it looks at any patrol, and for no declaration returns a patrol result `{ran: false, why}`; the scenarios that carry hand-overs through `keel tick --repo` in the `shift_scratch` repository, which declares no patrol, already pass.
- F4 — `readPatrolDeclarations(dir)` returns `declarations` and `messages`; a declaration it cannot read yields a message and no declaration.

## Decisions

- D1 — "No patrol declared" means `declarations` is empty and `messages` is empty, read from the calling worktree's config. Then `task()` does not throw: it names the main checkout when it exists, else the calling worktree, and `worktree` in its result is null.
- D2 — `stableRepo` takes the main checkout without a declaration in that case, because no patrol is read from it; with a declaration the rule of #503 stands.
- D3 — The printed text for a repository with no patrol says it declares no `patrol:` and that each run resumes ended sessions and carries hand-overs out, and keeps the sentence that Keel creates nothing. When the main checkout cannot stand in, the fallback sentence keeps its #503 form without the advice to declare a `patrol:` there.
- D4 — Any `messages` with no declaration still throws them, as before.
