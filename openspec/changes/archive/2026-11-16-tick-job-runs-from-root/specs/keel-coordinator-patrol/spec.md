## MODIFIED Requirements

### Requirement: A host-run tick runs the patrol when due

`keel tick` MUST be one model-free step: for each role `patrol:` declares that is bound to a worktree that exists and whose last recorded `next_at` is absent or has passed, it MUST fetch `origin` there and run `keel patrol --since-last --notify` as that role, then record that role's `next_at`; for each other declared role it MUST say the patrol is not due and run nothing. A role bound to several worktrees MUST use the first, in sorted order, whose directory exists; a role whose bound worktrees are all gone MUST get a line saying they no longer exist and naming `keel chat role --prune`, and no patrol run. `keel tick task` MUST print a launchd job that calls `keel tick` every 300 seconds and the commands that install it, and MUST create nothing. The job MUST name the repository's main checkout as `--repo` and MUST run from the filesystem root (`WorkingDirectory` `/`), so that no tool that waits for a checkout to be idle counts the job as a holder of it, and so that binding the role elsewhere or pruning a worktree does not change what the installed job names; only when the repository has no main checkout, or its `keel/config.yaml` declares no `patrol:`, MUST it name the worktree the role is bound to, and the printed text MUST then say why. With `runner: tick` under `patrol:`, the patrolling role's reminder MUST name `keel tick` and MUST NOT ask it to re-create a session schedule.

#### Scenario: The patrol runs only when due
- **WHEN** `patrol:` declares `runner: tick` and `keel tick` runs three times, the third after the recorded `next_at` was moved into the past
- **THEN** the first and third run the patrol and record a `next_at`, and the second says the patrol is not due and runs none

#### Scenario: The launchd job is printed, not installed
- **WHEN** `keel tick task` runs from the main checkout
- **THEN** it prints a plist with `StartInterval` 300 and `tick`, the main checkout as `--repo`, `/` as `WorkingDirectory`, the `launchctl bootstrap` command, and `Keel creates nothing`, and writes no file

#### Scenario: A job printed from a worktree names the main checkout
- **WHEN** `keel tick task` runs from a linked worktree under `.claude/worktrees/` to which the patrol role is bound, and the main checkout's `keel/config.yaml` declares the `patrol:`
- **THEN** the plist's `--repo` is the main checkout, its `WorkingDirectory` is `/`, and neither names the worktree

#### Scenario: Binding the role elsewhere needs no new job
- **WHEN** `keel tick task` is printed from worktree A bound to the role, the role is then bound to worktree B instead, and `keel tick --repo <the printed repository>` runs
- **THEN** the patrol runs in B, and `keel tick task` printed from B is identical to the one printed from A

#### Scenario: A repository whose main checkout cannot stand in keeps the worktree and says why
- **WHEN** the main checkout's `keel/config.yaml` declares no `patrol:` and the role's bound worktree declares one, and `keel tick task` runs there
- **THEN** the plist names the bound worktree, and the printed text says that the main checkout declares no `patrol:`

#### Scenario: A bound worktree that is gone is skipped
- **WHEN** `roles.json` binds the patrol role to a directory that does not exist and to one that does, and `keel tick` runs; and then only the missing one remains bound
- **THEN** the first run executes the patrol in the existing worktree; the second runs none, exits 0, and prints a line saying the bound worktree no longer exists and naming `keel chat role --prune`

### Requirement: A tick job does not need a patrol

`keel tick task` MUST print a launchd job for a repository whose `keel/config.yaml` declares no `patrol:`, naming the main checkout as `--repo` when it exists and running from `/`, and MUST say that the job runs no patrol: each run resumes ended sessions and carries hand-overs out. A `patrol:` Keel cannot read MUST still be refused with its message, and a declared patrol MUST keep the behavior of the existing job requirements.

#### Scenario: A repository with no patrol gets a job
- **WHEN** `keel/config.yaml` declares no `patrol:` and `keel tick task` runs from the main checkout, and again from a linked worktree under `.claude/worktrees/`
- **THEN** both exit 0 and print a plist whose `--repo` is the main checkout and whose `WorkingDirectory` is `/`, name no worktree, and say that the repository declares no `patrol:` and that the job resumes ended sessions and carries hand-overs out

#### Scenario: An unreadable patrol is still refused
- **WHEN** `keel/config.yaml` has a `patrol:` with a role and no `every:`, and `keel tick task` runs
- **THEN** it exits non-zero and prints the config's message, not a job

#### Scenario: The job's tick carries a hand-over out with no patrol
- **WHEN** the repository declares no `patrol:` and a CLI hand-off is pending, and the printed job's command, `keel tick --repo <main checkout>`, runs
- **THEN** it exits 0 and the hand-off is delivered
