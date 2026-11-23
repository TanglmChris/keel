## Context

- F1 — Codex App documents its managed location as `$CODEX_HOME/worktrees`; it distinguishes CLI-created Git worktrees from those it manages. [Official worktree documentation](https://learn.chatgpt.com/docs/environments/git-worktrees).
- F2 — Codex CLI 0.171.0 advertises `-C, --cd <DIR>`. Keel's overview and role binding already operate on linked Git worktrees and their common Git directory.

## Decisions

- D1 — `keel worktrees add --repo <repo> --path <path> --branch <new-branch> [--base <ref>] [--json]` uses the selected checkout as the base for relative paths and defaults the starting point to its HEAD. It uses Git's native linked-checkout creation with a new branch and returns the realized path, branch and start commit. Keel checks the destination first because Git can create a branch before reporting a checkout conflict. Git refuses branch conflicts; there is no force, reuse, shell evaluation, fetch, or implicit copying of local edits. There is no global storage convention or configuration migration.
- D2 — Operators launch Codex using `codex -C` with the returned path and can bind a role once in the linked checkout. Existing discovery remains read-only. Cleanup uses Git's non-forced worktree removal and preserves the branch. The workflow applies to CLI-created worktrees. Desktop Worktree/Handoff stays host-managed.

## Risks and trade-offs

Git worktree creation runs the repository's normal Git behavior, including configured checkout hooks. Failures report Git's reason so any local residue can be inspected before rerunning.

## Open Questions

None.
