## ADDED Requirements

### Requirement: A tick job does not need a patrol

`keel tick task` MUST print a launchd job for a repository whose `keel/config.yaml` declares no `patrol:`, naming the main checkout when it exists, and MUST say that the job runs no patrol: each run resumes ended sessions and carries hand-overs out. A `patrol:` Keel cannot read MUST still be refused with its message, and a declared patrol MUST keep the behavior of the existing job requirements.

#### Scenario: A repository with no patrol gets a job
- **WHEN** `keel/config.yaml` declares no `patrol:` and `keel tick task` runs from the main checkout, and again from a linked worktree under `.claude/worktrees/`
- **THEN** both exit 0 and print a plist whose `--repo` and `WorkingDirectory` are the main checkout, name no worktree, and say that the repository declares no `patrol:` and that the job resumes ended sessions and carries hand-overs out

#### Scenario: An unreadable patrol is still refused
- **WHEN** `keel/config.yaml` has a `patrol:` with a role and no `every:`, and `keel tick task` runs
- **THEN** it exits non-zero and prints the config's message, not a job

#### Scenario: The job's tick carries a hand-over out with no patrol
- **WHEN** the repository declares no `patrol:` and a CLI hand-off is pending, and the printed job's command, `keel tick --repo <main checkout>`, runs
- **THEN** it exits 0 and the hand-off is delivered
