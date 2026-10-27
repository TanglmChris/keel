## Facts

- F1 — `branches.owned()` reads `roles.json` at call time and collects checkout entries from the HEAD reflog of each worktree bound to the role (`keel-merged-branches`, rule (d)). A branch is the role's only while some currently bound worktree's reflog names it.
- F2 — `keel chat role --unset` (5.206.0, #476 D4) deletes the calling worktree's entry from `roles.json` unconditionally.
- F3 — A role may be bound to several worktrees: on 2026-10-27 `keel-maint` is bound to two. A branch the other one also checked out stays reachable after one is unbound.
- F4 — `keel chat role --prune` drops bindings whose worktree is already removed. `git worktree remove` deletes `$GIT_DIR/worktrees/<name>`, the worktree's reflog with it, so by then nothing names those branches and there is nothing left to compute.

## Decisions

- D1 — Before removing a binding, `--unset` computes the stranded branches: those `branches.merged(where, role)` lists now and does not list with this worktree's binding left out. Merged, unused, and kept are judged exactly as `keel branches` judges them, against refs as last fetched; nothing is fetched.
- D2 — With stranded branches and no `--leave-branches`, `--unset` exits 2 through `ChatError`, leaves `roles.json` unchanged, and names each stranded branch (`origin/` prefixed on the remote side), `keel branches prune`, and `--leave-branches`.
- D3 — `--unset --leave-branches` unbinds and prints the stranded branches as no longer listed by `keel branches`; `--json` carries them as `left`. `--leave-branches` without `--unset` is refused.
- D4 — Out of scope, by the owner's choice of option 1 on #483: `--prune` (F4), a hand edit of `roles.json`, and recording ownership durably.
