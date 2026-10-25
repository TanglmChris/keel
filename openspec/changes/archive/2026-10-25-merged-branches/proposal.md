## Why

Issue #469, approved by the owner on 2026-10-25, who also settled its design. Parallel sessions each branch for their tasks, and once a task is merged into `main` or into an integration branch, nobody deletes its branch:

- kaiwu-ip had 110 remote branches on 2026-10-19. 76 already in `main` were deleted by hand.
- A coordinating session has cleaned up after each batch since then. It has missed some, because each deletion needs the same manual checks: is the branch merged, is it checked out anywhere, whose is it.
- On 2026-10-25, 9 of 16 remote branches and 7 of 47 local ones were already merged and still present.

With that many branches, `git branch` stops telling anyone which work is live.

## What Changes

- **`keel branches` lists the role's merged task branches.** It lists the local and remote branches that are safe to delete, each with its sha and the trunk that contains it, and deletes nothing. A branch qualifies only when all of these hold:
  - its tip is contained in a remote trunk branch;
  - no worktree has it checked out;
  - the role's own worktree has checked it out;
  - it is neither a trunk nor in the keep list.
- **`keel branches prune` deletes them under a standing authorization.** With `delete-branch:merged` declared under `authorize:`, it fetches, recomputes the list, and deletes each qualifying branch, local and remote. Before each deletion it records the time, role, sha, branch, and side in Keel's store, and it prints the command that restores the branch. Without the declaration it deletes nothing, lists what it would delete, names the declaration, and exits 3.
- **`branches:` in `keel/config.yaml`.** `trunk:` names the branches, beyond the remote default branch, that count as merged into, such as a team's integration branch. `keep:` names the branch globs never to delete.
- **Pointers, never deletions, elsewhere.** `keel shift check` and `keel shift resume` name the role's merged branches and `keel branches`, and `keel --doctor` reports a count. None of them deletes anything, and none makes the check fail. The gates stay read-only.

## Capabilities

### New Capabilities
- `keel-merged-branches`

### Modified Capabilities
- none

## Impact

The change touches:
- new `src/core/branches.js`;
- `src/core/config.js` (the `branches:` declaration and the `delete-branch:merged` action), `bin/keel.js` (the command and the doctor line), `src/core/shift.js` (the check and resume pointers);
- `keel/config.yaml` (documentation), `README.md`, `README.zh-CN.md`, the validation scenarios, the new spec, and the changelog.
