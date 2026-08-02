## MODIFIED Requirements

### Requirement: Dirty-worktree attribution is conservative

Keel MUST NOT attribute dirty paths to a selected task unless a trustworthy comparison base exists. A base supplied by the caller is one; a dirty-path set Keel itself recorded when the task started is another, and `keel gate task-complete` MUST use that recorded set when the caller supplies no base, refusing a path that is dirty now, was not dirty when the task started, and lies outside the selected task's Touch. When no base is supplied and no set was recorded, scope attribution remains semantic review evidence, because an absent record is not a record that nothing was dirty. An explicitly supplied base MUST take precedence over the recorded set, since the two answer different questions and the caller asked the broader one.

A path that was already dirty when the task started is not attributed to that task even if the task modified it again, and the requirement text MUST say so, so a reader learns the limit from the specification rather than from a write that was never reported.

The disposable guard manifest `keel/guard.json` — the one artifact the gate contract itself permits a gate to write — MUST NOT be attributed as an outside-Touch scope failure, and changed paths under the selected change's own `openspec/changes/<change>/` directory — the authoring artifacts the gate is completing against — MUST NOT be attributed as outside-Touch scope failures either. A changed path that a **completed** task of the same change declares in its own Touch MUST NOT be attributed to the selected task, and that exclusion MUST be reported rather than applied silently, because a base comparison cannot establish which task wrote a path. A renamed path reported by the worktree as a single `old -> new` entry MUST be attributed as its two independent endpoints, so a rename whose old and new paths are both in Touch is not a false outside-Touch failure.

#### Scenario: Dirty worktree without base or record needs review
- **WHEN** task completion runs in a dirty worktree with no explicit trustworthy base and no recorded task-start dirty set
- **THEN** Keel exposes the dirty state as a warning or `needs-review`
- **AND THEN** it does not fail solely because unrelated dirty paths exist
- **AND THEN** it does not claim those paths belong to the task

#### Scenario: A write outside Touch is refused without the caller asking
- **WHEN** a task records its dirty-path set at task start, a path outside its Touch becomes dirty afterwards, and task completion runs with no explicit base
- **THEN** completion fails naming that path as outside Touch
- **AND THEN** the refusal does not require the caller to have supplied a comparison base

#### Scenario: A path already dirty at task start is not attributed
- **WHEN** a path outside Touch was already dirty when the task started
- **THEN** completion does not attribute it to the selected task
- **AND THEN** the outcome is the same whether or not the task modified that path again

#### Scenario: An explicit base takes precedence over the recorded set
- **WHEN** task completion runs with an explicit trustworthy base and a recorded task-start dirty set both available
- **THEN** the comparison answers against the supplied base
- **AND THEN** a path changed since that base but already dirty at task start is still attributed

#### Scenario: The unattributed-dirty warning keeps naming its paths
- **WHEN** completion reports dirty paths it did not attribute to the selected task
- **THEN** it names those paths rather than only counting them
- **AND THEN** a rename's two endpoints both appear, so the warning remains usable as the only surface that shows what the worktree parser produced
