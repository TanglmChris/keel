## ADDED Requirements

### Requirement: A host-run tick runs the patrol when due

`keel tick` MUST be one model-free step: when `patrol:` declares a role bound to a worktree and the last recorded `next_at` is absent or has passed, it MUST fetch `origin` there and run `keel patrol --since-last --notify` as that role, then record the patrol's `next_at`; otherwise it MUST say the patrol is not due and run nothing. `keel tick task` MUST print a launchd job that calls `keel tick` every 300 seconds, and the commands that install it, and MUST create nothing. With `runner: tick` under `patrol:`, the patrolling role's reminder MUST name `keel tick` and MUST NOT ask it to re-create a session schedule.

#### Scenario: The patrol runs only when due
- **WHEN** `patrol:` declares `runner: tick` and `keel tick` runs three times, the third after the recorded `next_at` was moved into the past
- **THEN** the first and third run the patrol and record a `next_at`, and the second says the patrol is not due and runs none

#### Scenario: The launchd job is printed, not installed
- **WHEN** `keel tick task` runs
- **THEN** it prints a plist with `StartInterval` 300 and `tick` and the bound worktree in its arguments, the `launchctl bootstrap` command, and `Keel creates nothing`, and writes no file
