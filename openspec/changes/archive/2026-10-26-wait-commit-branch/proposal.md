## Why

Issue #477, approved by the owner on 2026-10-26. `keel chat wait <group> --commit <sha>` holds once any `refs/remotes/<remote>/` ref contains the commit (`conditionHolds` in `src/core/patrol.js`). The common wait in a multi-branch team is "until my commit reaches main". That wait is met as soon as the author pushes their own feature branch, and the waiting session is woken early. kaiwu-ip hit it on 2026-10-26 (kaiwu-ip#429): a wait for f941bb54 to reach main was met at once, while f941bb54 was only on a feature branch.

## What Changes

- **`--branch <name>`** limits a commit wait to one remote branch. It holds only when `refs/remotes/<remote>/<name>` contains the commit. The condition reads `commit <sha> on <remote>/<name>`.
- **A wait without `--branch` says it means any branch.** The condition stays `commit <sha> on <remote>`, so stores shared with older Keel keep working. The registration echo, `keel chat waits`, and the patrol's met notice render it as `on any branch of <remote>`.
- **Declared trunks are the default** (owner, 2026-10-26). When `keel/config.yaml` declares `branches:` with at least one `trunk:`, a commit wait without `--branch` is registered against the trunks: the remote's default branch and each declared trunk. It holds when any of them contains the commit, and reads `commit <sha> on <remote>/<a> or <remote>/<b>`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/patrol.js`, `src/core/branches.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the README in both languages, the `keel/config.yaml` comment on `branches:`, the published spec, and the changelog.
