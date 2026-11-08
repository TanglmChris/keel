## MODIFIED Requirements

### Requirement: A host-run tick runs the patrol when due

`keel tick` MUST be one model-free step: for each role `patrol:` declares that is bound to a worktree that exists and whose last recorded `next_at` is absent or has passed, it MUST fetch `origin` there and run `keel patrol --since-last --notify` as that role, then record that role's `next_at`; for each other declared role it MUST say the patrol is not due and run nothing. A role bound to several worktrees MUST use the first, in sorted order, whose directory exists; a role whose bound worktrees are all gone MUST get a line saying they no longer exist and naming `keel chat role --prune`, and no patrol run. `keel tick task` MUST print a launchd job that calls `keel tick` every 300 seconds and the commands that install it, and MUST create nothing. The job MUST name the repository's main checkout as `--repo` and as `WorkingDirectory`, so that binding the role elsewhere or pruning a worktree does not change what the installed job names; only when the repository has no main checkout, or its `keel/config.yaml` declares no `patrol:`, MUST it name the worktree the role is bound to, and the printed text MUST then say why. With `runner: tick` under `patrol:`, the patrolling role's reminder MUST name `keel tick` and MUST NOT ask it to re-create a session schedule.

#### Scenario: The patrol runs only when due
- **WHEN** `patrol:` declares `runner: tick` and `keel tick` runs three times, the third after the recorded `next_at` was moved into the past
- **THEN** the first and third run the patrol and record a `next_at`, and the second says the patrol is not due and runs none

#### Scenario: The launchd job is printed, not installed
- **WHEN** `keel tick task` runs from the main checkout
- **THEN** it prints a plist with `StartInterval` 300 and `tick` and the main checkout as `--repo` and as `WorkingDirectory`, the `launchctl bootstrap` command, and `Keel creates nothing`, and writes no file

#### Scenario: A job printed from a worktree names the main checkout
- **WHEN** `keel tick task` runs from a linked worktree under `.claude/worktrees/` to which the patrol role is bound, and the main checkout's `keel/config.yaml` declares the `patrol:`
- **THEN** the plist's `--repo` and `WorkingDirectory` are the main checkout and neither names the worktree

#### Scenario: Binding the role elsewhere needs no new job
- **WHEN** `keel tick task` is printed from worktree A bound to the role, the role is then bound to worktree B instead, and `keel tick --repo <the printed repository>` runs
- **THEN** the patrol runs in B, and `keel tick task` printed from B is identical to the one printed from A

#### Scenario: A repository whose main checkout cannot stand in keeps the worktree and says why
- **WHEN** the main checkout's `keel/config.yaml` declares no `patrol:` and the role's bound worktree declares one, and `keel tick task` runs there
- **THEN** the plist names the bound worktree, and the printed text says that the main checkout declares no `patrol:`

#### Scenario: A bound worktree that is gone is skipped
- **WHEN** `roles.json` binds the patrol role to a directory that does not exist and to one that does, and `keel tick` runs; and then only the missing one remains bound
- **THEN** the first run executes the patrol in the existing worktree; the second runs none, exits 0, and prints a line saying the bound worktree no longer exists and naming `keel chat role --prune`

## ADDED Requirements

### Requirement: Keel's launchd jobs name directories that outlive a worktree

`keel --doctor` MUST check, for each `dev.keel.*` LaunchAgent, the directory its `WorkingDirectory` names and the one following `--repo` in its program arguments. It MUST report as a `launchd` problem each that does not exist or lies under a `.claude/worktrees/` directory, which Keel prunes, naming the file, the path and the command that re-creates the job. `launchd: ok` MUST be printed only when no job has such a problem, and the report MUST NOT change the exit status.

#### Scenario: Doctor reports a job whose directory is gone
- **WHEN** the LaunchAgents directory holds `dev.keel.tick.x.plist` whose `--repo` and `WorkingDirectory` name a directory that does not exist, and `keel --doctor` runs, and then the plist names the main checkout
- **THEN** the first run prints a `launchd` problem line naming `dev.keel.tick.x.plist`, the missing directory and `keel tick task`; the second prints `launchd: ok`

#### Scenario: Doctor reports a job that runs in a regenerated worktree
- **WHEN** the plist's `--repo` and `WorkingDirectory` name an existing directory under `.claude/worktrees/`, and `keel --doctor` runs
- **THEN** it prints a `launchd` problem line naming the file, that directory and `keel tick task`, and `keel --doctor`'s exit status is the one it has without the job

#### Scenario: A job with no repository argument is checked only for its node
- **WHEN** a `dev.keel.*` plist names an existing node and has neither `WorkingDirectory` nor `--repo`
- **THEN** `keel --doctor` prints `launchd: ok`
