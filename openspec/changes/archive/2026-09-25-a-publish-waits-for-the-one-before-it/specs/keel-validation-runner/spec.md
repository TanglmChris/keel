# keel-validation-runner

## ADDED Requirements

### Requirement: The publish workflow serializes

The suite SHALL assert that `.github/workflows/publish.yml` declares a single `concurrency` group for
the whole workflow and declares `cancel-in-progress: false`, and SHALL name whichever is missing.

#### Scenario: A missing concurrency group is refused

- **WHEN** the workflow declares no `concurrency` group
- **THEN** the check fails, stating that simultaneous releases publish concurrently

#### Scenario: A cancelling group is refused

- **WHEN** the workflow declares a concurrency group without `cancel-in-progress: false`
- **THEN** the check fails, stating that the default cancels a queued publish

#### Scenario: A per-ref group is refused

- **WHEN** the group expression varies per release
- **THEN** the check fails, because a group that differs per run serializes nothing
