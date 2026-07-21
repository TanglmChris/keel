## MODIFIED Requirements

### Requirement: Dirty-worktree attribution is conservative

Keel MUST NOT attribute dirty paths to a selected task unless the caller supplies a trustworthy comparison base. Without such a base, scope attribution remains semantic review evidence. The disposable guard manifest `keel/guard.json` — the one artifact the gate contract itself permits a gate to write — MUST NOT be attributed as an outside-Touch scope failure, and changed paths under the selected change's own `openspec/changes/<change>/` directory — the authoring artifacts the gate is completing against — MUST NOT be attributed as outside-Touch scope failures either. A renamed path reported by the worktree as a single `old -> new` entry MUST be attributed as its two independent endpoints, so a rename whose old and new paths are both in Touch is not a false outside-Touch failure.

#### Scenario: Dirty worktree without base needs review
- **WHEN** task completion runs in a dirty worktree without an explicit trustworthy base
- **THEN** Keel exposes the dirty state as a warning or `needs-review`
- **AND THEN** it does not fail solely because unrelated dirty paths exist
- **AND THEN** it does not claim those paths belong to the task

#### Scenario: Explicit base enables path comparison
- **WHEN** the caller supplies a valid comparison base
- **THEN** Keel may compare changed paths to Touch
- **AND THEN** paths outside Touch produce a deterministic scope failure

#### Scenario: Nested paths match double-star Touch globs
- **WHEN** the caller supplies a valid comparison base and the task Touch list contains a `**` glob entry
- **THEN** changed paths nested arbitrarily deep under the glob's base directory are attributed inside Touch
- **AND THEN** the comparison does not report a false `outside-touch` scope failure for those paths

#### Scenario: The gate's own guard manifest is never outside Touch
- **WHEN** the caller supplies a valid comparison base and the disposable guard manifest `keel/guard.json` is present as a changed or dirty path
- **THEN** the comparison does not attribute the manifest as an outside-Touch scope failure and completion needs no prior `keel guard clear`
- **AND THEN** every other path outside Touch still produces a deterministic scope failure

#### Scenario: The selected change's authoring artifacts are never outside Touch
- **WHEN** the caller supplies a valid comparison base and changed paths exist under the selected change's own `openspec/changes/<change>/` directory
- **THEN** the comparison does not attribute those authoring artifacts as outside-Touch scope failures
- **AND THEN** paths under other changes' directories, the archive tree, `openspec/specs/`, and `openspec/schemas/` still produce deterministic scope failures when outside Touch

#### Scenario: A rename within Touch attributes to both endpoints
- **WHEN** the caller supplies a valid comparison base and a tracked file is renamed so the worktree reports one `old -> new` entry whose old and new paths are both listed in Touch
- **THEN** the comparison attributes the old and new paths independently, each inside Touch
- **AND THEN** it does not report a false `outside-touch` scope failure for the combined rename entry

#### Scenario: Keel stores no baseline
- **WHEN** `task-start` completes
- **THEN** Keel does not persist a diff snapshot, hash set, or execution baseline for later completion
