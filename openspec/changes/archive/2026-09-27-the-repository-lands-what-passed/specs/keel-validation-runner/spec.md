# keel-validation-runner

## ADDED Requirements

### Requirement: A pending publish waits instead of being cancelled

The suite SHALL assert that `publish.yml`'s concurrency group declares `queue: max`, and SHALL refuse a
group without it, because the default keeps one pending run and cancels the rest.

#### Scenario: A group without a queue is refused

- **WHEN** the publish workflow's concurrency group omits `queue: max`
- **THEN** the check fails, stating that a pending publish would be cancelled by the next one

### Requirement: The repository lands only what passed

The suite SHALL assert that `publish.yml` lands a pull request only when it is owner-authored, from this
repository, into `main`, and its head commit passed `full-gate`; that the landing job checks out no code;
that the merge names the tested head commit; and that a landed version is published before it is tagged.

#### Scenario: A merge without the check is refused

- **WHEN** the landing job merges without reading the `full-gate` check-run or without matching the head commit
- **THEN** the check fails, stating that it merges without confirming `full-gate`

#### Scenario: Checking out pull request code is refused

- **WHEN** the landing job gains a checkout step, or drops the owner or same-repository filter
- **THEN** the check fails, stating that pull request code could run with a write token

#### Scenario: Tagging before publishing is refused

- **WHEN** the publish job creates the tag or release before `npm publish`
- **THEN** the check fails, stating that a failed publish would be left tagged and never retried
