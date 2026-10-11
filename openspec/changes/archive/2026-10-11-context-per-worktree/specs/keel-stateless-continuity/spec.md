## MODIFIED Requirements

### Requirement: Keel resolves continuity conservatively
Keel MUST resolve continuity in the order explicit selection, valid HANDOFF override, a read-only role's `idle`, unique actionable OpenSpec inference among the changes that belong to this worktree, then a non-ready status. Keel MUST classify authoring, executable task, and change-close owners as actionable, MUST NOT let storage-only zero-task backlogs compete with them, and MUST NOT use Git dirty state to choose a change or task.

#### Scenario: Explicit selection wins
- **WHEN** `keel context` receives a valid explicit change or task selection
- **AND WHEN** a different valid HANDOFF or inferred owner exists
- **THEN** the result selects the explicit owner
- **AND THEN** `selection.source` is `explicit`

#### Scenario: HANDOFF overrides inference
- **WHEN** no explicit selection is supplied
- **AND WHEN** a valid HANDOFF names a durable owner and action
- **THEN** the result uses that owner and action
- **AND THEN** `selection.source` is `handoff`

#### Scenario: Unique actionable OpenSpec state is inferred
- **WHEN** no explicit selection or HANDOFF exists
- **AND WHEN** exactly one authoring, executable-task, or change-close owner is actionable
- **THEN** the result selects that owner and action
- **AND THEN** `selection.source` is `inferred`

#### Scenario: Incomplete authoring remains actionable
- **WHEN** a scaffold or proposal has required OpenSpec artifacts still pending
- **THEN** context may identify its authoring action
- **AND THEN** it is not hidden merely because it has no executable task yet

#### Scenario: Storage-only standing backlog does not create ambiguity
- **WHEN** a change directory contains no proposal, design, specs, or task checkboxes and serves only as a zero-task follow-up store
- **THEN** context excludes it from actionable inference and reports a warning
- **AND THEN** explicit selection can still inspect it

#### Scenario: Invalid no-task change blocks instead of disappearing
- **WHEN** a change has authored proposal, design, specs, or a tasks artifact but cannot produce a valid next authoring, task, or close action
- **THEN** context reports it as blocked or ambiguous with the missing authority
- **AND THEN** it is not treated as a harmless storage-only backlog

#### Scenario: Multiple candidates are not guessed
- **WHEN** no explicit selection or HANDOFF exists
- **AND WHEN** multiple actionable OpenSpec owners or next actions are plausible
- **THEN** the result status is `ambiguous`
- **AND THEN** the result explains the candidates without selecting one

#### Scenario: Dirty paths are warnings only
- **WHEN** Git reports uncommitted paths
- **THEN** the context result may include those facts in `warnings`
- **AND THEN** the dirty paths do not determine `selection`

## ADDED Requirements

### Requirement: A change that belongs to another worktree does not set this session's status

A change MAY declare its owner role as `owner: <role>` under the Keel-owned key of its OpenSpec change configuration. Inference MUST count a change as belonging to this worktree unless it belongs elsewhere: when it declares an owner role and this worktree is not bound to that role, or, when it declares none, when another worktree's branch has commits touching the change's directory beyond the default branch and this worktree's `HEAD` has none. Dirty state MUST NOT decide it. Inference MUST run over the changes that belong to this worktree as it would over all of them, and MUST report each change that belongs elsewhere with its status and its owner role or worktree and branch, without letting it make this session `blocked`, `ambiguous`, or `ready`. When every active change belongs elsewhere the status MUST be `idle`. Explicit selection MUST still reach a change that belongs elsewhere.

#### Scenario: Another worktree's blocked change is context, not a block
- **WHEN** worktree `review` has no change of its own and worktree `rtl` has committed a change on its branch that fails to compile
- **THEN** `keel context` in `review` reports `idle` and lists that change as blocked in worktree `rtl`
- **AND THEN** `keel context` in `rtl` still reports it `blocked`

#### Scenario: A declared owner role decides
- **WHEN** a change declares `owner: verify` and is present in two worktrees bound to `rtl` and `verify`
- **THEN** inference selects it in the `verify` worktree and lists it as belonging to `verify` in the `rtl` worktree

#### Scenario: Explicit selection reaches a change that belongs elsewhere
- **WHEN** `keel context --change` names a change that belongs to another worktree
- **THEN** Keel selects it

### Requirement: A read-only role infers nothing

`keel/config.yaml` MAY declare `read_only_roles:`, a list of chat role names whose sessions own no change. When this worktree's bound role is listed, `keel context` without explicit selection or a HANDOFF MUST report `idle` with one reason naming the role, MUST NOT list candidates, and MUST carry a `readOnly` field naming the role; the session-start and post-compaction note MUST report that no change is selected for a read-only session instead of asking to select an owner. An entry that is not a role name MUST be reported and ignored. Explicit selection and HANDOFF MUST keep their precedence.

#### Scenario: A review session is quiet
- **WHEN** `read_only_roles:` lists `review`, the worktree is bound to `review`, and two active changes exist
- **THEN** `keel context` reports `idle` with the read-only reason and no candidates
- **AND THEN** the session-start note says no change is selected for the read-only session and does not ask to select an owner

#### Scenario: Explicit selection still works in a read-only session
- **WHEN** a read-only session runs `keel context --change <c>`
- **THEN** Keel selects `<c>`
