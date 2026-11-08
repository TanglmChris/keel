## Why

Issue #509, opened 2026-11-08 and ordered by keel-maint at the owner's request the same day ("你自己排序继续走"; the owner chose to file it: "开 issue，让 tick 任务不再依赖 patrol 声明").

`keel tick task` fails when `keel/config.yaml` declares no `patrol:` (`throw new TickError(found.why)`), so a repository that wants only what `keel tick` does outside the patrol — resuming a role's ended session once a record addresses it, and carrying a hand-over out when its waiter is gone — must declare a patrol to get a job. `tick()` itself does not need it: it runs `wakeEnded` and `handOver` first and reports "declares no `patrol:`" for the patrol part, and `keel tick` in such a repository has run that way before (the log of this repository holds ten such lines from before it declared one). Keel's own repository declares its patrol for that reason, by its comment, not for the patrol it runs (#509 body).

## What Changes

- **`keel tick task` renders a job for a repository that declares no patrol.** It names the main checkout as `--repo` and `WorkingDirectory` (as #503 does for a declared patrol), and the printed text says the repository declares no `patrol:`, so each run resumes ended sessions and carries hand-overs out and runs no patrol.
- **A declaration Keel cannot read still refuses**, with its message: an unreadable `patrol:` is a mistake to show, not a repository that declares none.
- **A declared patrol behaves as before** (#503): main checkout when it declares the patrol, else the bound worktree, saying so; a declared role with no existing bound worktree still refuses.
- Not changed: `keel tick` itself; nothing is installed; Keel's own `patrol:` stays (the owner decides that after this lands).

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/tick.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog.
