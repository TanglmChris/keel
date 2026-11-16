## Why

Issue #524 (Keel 5.227.0, filed by the owner's account on 2026-11-11): the launchd job `keel tick task` prints sets `WorkingDirectory` to the repository's main checkout, although it already passes `--repo <repo>`. Because the tick runs every 300 s with its cwd inside the main checkout, any tool that refuses to touch the main checkout while a process has its cwd there counts each tick as a holder. In one consumer repository an hourly "fast-forward the main checkout when idle" job deferred a full hour each time the two overlapped. Taken up at the owner's request on 2026-11-12 ("解524").

## What Changes

- **The printed job runs from the filesystem root:** `WorkingDirectory` is `/`, and `--repo` still names the main checkout (or, where it cannot stand in, the bound worktree, as #503 and #509 print it).
- **Nothing the tick runs depends on its cwd.** Every child it starts that needs a repository names one (`git -C`, `cwd: <worktree>`, `claude --bg --resume` in the role's worktree), the host's `claude agents --json --all` answers the same from `/` as from the checkout, and `armWake` already runs its waiter from the root.
- **Unchanged:** an installed plist stays valid until the owner re-runs `keel tick task` and its install commands (Keel registers nothing); `keel --doctor` still checks `--repo` and any `WorkingDirectory` it finds, so an old plist is accepted and a new one passes.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/tick.js`, `scripts/validation/shift.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog.
