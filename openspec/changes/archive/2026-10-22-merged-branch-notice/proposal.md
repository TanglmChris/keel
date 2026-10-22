## Why

Issue #446, approved by the owner on 2026-10-21 under the shift freeze, as a small extension of #347's note check. A new shift's session starts in the role's worktree on whatever branch the previous shift left. That is almost always that shift's own branch, which `land` has already merged.

On 2026-10-21 this session started 7 commits behind `origin/main`. It then spent a tool call to learn why `AGENTS.md` read an older protocol. The SessionStart hook made it worse. In Keel's own repository it named `keel --install --target claude`, and it cited a Protocol: line that `keel context` does not print there.

## What Changes

- **`keel shift resume` says when the worktree is on a merged branch.** When HEAD is behind `origin/<default>` and already contained in it, resume prints one line. The line names the branch, says it is already merged, gives how many commits behind it is, and says to start new work from the default branch. Resume fetches nothing.
- **The startup hook stops naming a refresh in Keel's source repository.** There, a protocol block behind the runtime means the checked-out branch is behind, so the hook says so. It does not name `keel --install` or the Protocol: line.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`
- `keel-native-runtime-projection`

## Impact

`src/core/shift.js`, `plugins/keel/scripts/session-start.js`, `scripts/validation/shift.py`, `scripts/validation/hosts.py`, `scripts/validation/registry.py`, the published specs, and the changelog.
