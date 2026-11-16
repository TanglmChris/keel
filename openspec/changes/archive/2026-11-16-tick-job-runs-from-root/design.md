## Facts

- F1 — `task()` in `src/core/tick.js` writes `WorkingDirectory` as the same `repo` it passes after `--repo`; the tick takes its repository from `--repo`, not from its cwd (`tick --repo`).
- F2 — The children a tick starts name their directory: `git -C <worktree>`, `spawnSync(node, args, { cwd: found.worktree })` for the patrol, `claude --bg --resume` with `cwd: entry.worktree`, and `armWake`'s waiter with `cwd` the root; `claude agents --json --all`, `stop` and `rm` address sessions by id, and `agents --json --all` returned the same 29 rows from `/` and from the main checkout (probed 2026-11-12).
- F3 — `keel --doctor` reads `WorkingDirectory` and `--repo` of each `dev.keel.*` plist (`src/core/launchd.js`) and its scenario rewrites both to the directory under test, so a plist whose `WorkingDirectory` is `/` passes it.

## Decisions

- D1 — `WorkingDirectory` is `/` rather than `$HOME`: a plist cannot expand `$HOME`, the path would be baked in per machine, and `/` is what `armWake` already uses for a process that must not sit in a checkout.
- D2 — Only the printed plist changes. The explanatory text keeps saying which directory `--repo` names and adds that the job runs from `/`.
