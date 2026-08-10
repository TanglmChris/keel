## MODIFIED Requirements

### Requirement: Dirty-worktree attribution is conservative

Keel MUST NOT attribute dirty paths to a selected task unless a trustworthy comparison base exists. A base supplied by the caller is one; a dirty-path set Keel itself recorded when the task started is another, and `keel gate task-complete` MUST use that recorded set when the caller supplies no base, refusing a path that is dirty now, was not dirty when the task started, and lies outside the selected task's Touch. When no base is supplied and no set was recorded, scope attribution remains semantic review evidence, because an absent record is not a record that nothing was dirty. An explicitly supplied base MUST take precedence over the recorded set, since the two answer different questions and the caller asked the broader one.

A path that was already dirty when the task started is exempt from attribution only while its content stays the one recorded at task start; the requirement text MUST say so, so a reader learns the limit from the specification rather than from a write that was never reported. A path whose content changed since task start MUST be attributed even though the path itself was already dirty, because the comparison Keel MUST make is content, not name — a bare path is not what the task changed, its content is. The disposable guard manifest `keel/guard.json` — the one artifact the gate contract itself permits a gate to write — MUST NOT be attributed as an outside-Touch scope failure, and changed paths under the selected change's own `openspec/changes/<change>/` directory — the authoring artifacts the gate is completing against — MUST NOT be attributed as outside-Touch scope failures either. A changed path that a **completed** task of the same change declares in its own Touch MUST NOT be attributed to the selected task, and that exclusion MUST be reported rather than applied silently, because a base comparison cannot establish which task wrote a path. A renamed path reported by the worktree as a single `old -> new` entry MUST be attributed as its two independent endpoints, so a rename whose old and new paths are both in Touch is not a false outside-Touch failure.

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
- **WHEN** a path outside Touch was already dirty when the task started and its content at completion still matches the content recorded then
- **THEN** completion does not attribute it to the selected task

#### Scenario: A path already dirty at task start whose content changed is attributed
- **WHEN** a path outside Touch was already dirty when the task started, and its content at completion no longer matches the content recorded then
- **THEN** completion attributes it to the selected task as outside Touch
- **AND THEN** this holds regardless of whether the path is currently dirty for the same reason it was dirty at task start or a different one — only the content comparison decides

#### Scenario: An explicit base takes precedence over the recorded set
- **WHEN** task completion runs with an explicit trustworthy base and a recorded task-start dirty set both available
- **THEN** the comparison answers against the supplied base
- **AND THEN** a path changed since that base but already dirty at task start is still attributed

#### Scenario: The unattributed-dirty warning keeps naming its paths
- **WHEN** completion reports dirty paths it did not attribute to the selected task
- **THEN** it names those paths rather than only counting them
- **AND THEN** a rename's two endpoints both appear, so the warning remains usable as the only surface that shows what the worktree parser produced

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

#### Scenario: A completed task's uncommitted work is not the next task's scope failure
- **WHEN** the caller supplies a valid comparison base and a changed path outside the selected task's Touch is declared in the Touch of another task of the same change that is checked complete
- **THEN** the comparison does not attribute that path to the selected task
- **AND THEN** it reports the exclusion, naming the path and the completed task that declares it, because a base comparison cannot establish which task wrote the path

#### Scenario: An unfinished task's Touch grants nothing
- **WHEN** a changed path outside the selected task's Touch is declared only by a task of the same change that is not checked complete, or by no task at all
- **THEN** the path still produces a deterministic `outside-touch` scope failure
- **AND THEN** a task whose Touch is `none` contributes no path claims

#### Scenario: A rename within Touch attributes to both endpoints
- **WHEN** the caller supplies a valid comparison base and a tracked file is renamed so the worktree reports one `old -> new` entry whose old and new paths are both listed in Touch
- **THEN** the comparison attributes the old and new paths independently, each inside Touch
- **AND THEN** it does not report a false `outside-touch` scope failure for the combined rename entry

#### Scenario: Keel stores no baseline
- **WHEN** `task-start` completes
- **THEN** Keel does not persist a diff snapshot or an execution baseline for later completion
- **AND THEN** the one hash set it does persist is the per-path content signature this same requirement's dirty-at-task-start exemption depends on, scoped to that attribution and nothing broader
