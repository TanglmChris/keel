## Why

Issue #503, filed 2026-11-07 by the owner, who has since asked for the open issues to be worked. `keel tick task` renders the launchd job around the worktree the patrol role is bound to at the moment it is run, and writes that path as both `--repo` and `WorkingDirectory`. A worktree under `.claude/worktrees/` is a checkout Keel creates and prunes, so the installed job outlives the path it names: when the role is bound elsewhere or the worktree is pruned, launchd keeps firing every 300 s, `keel tick` cannot read `keel/config.yaml`, the only trace is `tick/tick.err`, hand-offs and wakes stop, and `keel --doctor` reports `launchd: ok` because it checks only the node. Measured 2026-11-08: the installed `dev.keel.tick.keel` names `keel-optimization-maintenance-0cb8d4` while `keel-maint` is bound to `keel-maint-cli`; it still works only because the old worktree has not been pruned yet.

## What Changes

- **`keel tick task` names the repository's main checkout** as `--repo` and `WorkingDirectory`, not the role's worktree. `keel tick` already resolves the bound worktree from `roles.json` on every run, so rebinding the role needs no new job. When the main checkout cannot stand in (no main checkout, or its `keel/config.yaml` declares no `patrol:`), the job names the bound worktree as before and the printed text says why.
- **`keel tick` skips a bound worktree whose directory no longer exists** and uses the next bound one that does; when none does it says so and names `keel chat role --prune`, instead of starting the patrol in a missing directory.
- **`keel --doctor` checks the directories a `dev.keel.*` job runs in** (`--repo` and `WorkingDirectory`), not only its node: a missing directory is a `launchd` problem naming the file, the path and the command that re-creates the job, and so is a directory under `.claude/worktrees/`, which Keel regenerates.
- **The docs state the rule once:** a launchd job must not name a path under `.claude/worktrees/` or inside a `.venv`, because both are regenerated.
- Not changed: installed plists are not touched, since Keel creates nothing; the owner re-runs `keel tick task`. No `keel tick install` / `uninstall`: Keel registers nothing, and adding that would be a product decision for the owner.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/tick.js`, `src/core/launchd.js`, `bin/keel.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog. Downstream scripts that install their own launchd jobs (the kaiwu `flow/*_agent.sh` pattern from the issue) are outside this repository; the rule in the docs is what they can follow.
