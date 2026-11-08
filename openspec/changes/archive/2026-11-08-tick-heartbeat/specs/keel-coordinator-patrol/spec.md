## ADDED Requirements

### Requirement: A silent tick is reported from its own state

`keel tick` MUST record `last_tick` in `tick/state.json` on every run, including a run whose patrol is not due. `keel --doctor` MUST report `tick` as ok with that time, and as a problem when it is older than 15 minutes or, for a repository declaring `runner: tick`, was never recorded. The report MUST read only that file, never `~/Library/LaunchAgents` or `launchctl`. A repository that declares no tick and has no `last_tick` MUST get no line.

#### Scenario: Every run leaves a heartbeat
- **WHEN** `keel tick` runs twice and the second run's patrol is not due
- **THEN** `last_tick` is present after the first run and later after the second, and the patrol's `next_at` and `last_run` are unchanged by the second

#### Scenario: A silent tick is a doctor problem
- **WHEN** `tick/state.json` is a real one whose `last_tick` is two hours old, and `keel --doctor` runs
- **THEN** it prints a `tick` problem line naming that time and `keel tick task`, and with a `last_tick` one minute old it prints `tick` ok

#### Scenario: A declared tick that never ran is a doctor problem
- **WHEN** the repository declares `runner: tick` and `tick/state.json` has no `last_tick`
- **THEN** `keel --doctor` prints a `tick` problem line saying it has never run

#### Scenario: A repository without a tick is not checked
- **WHEN** no `patrol:` declares `runner: tick` and `tick/state.json` has no `last_tick`
- **THEN** `keel --doctor` prints no `tick` line

#### Scenario: A session starts knowing its tick is silent
- **WHEN** the heartbeat is stale and the SessionStart hook runs
- **THEN** its context contains a line saying the tick has not run since that time, and with a fresh heartbeat it contains no such line
