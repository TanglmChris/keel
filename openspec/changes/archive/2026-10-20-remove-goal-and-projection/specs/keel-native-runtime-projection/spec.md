## MODIFIED Requirements

### Requirement: Native projections consume the fingerprinted task capsule
Every native worktree view and every external-agent brief MUST be derived from the same freshly compiled `keel-task-capsule/v1` used by Core gates and MUST include the contract fingerprint needed to detect stale views.

#### Scenario: Projection includes executable boundaries
- **WHEN** a projection is requested for a selected task
- **THEN** it includes capsule schema, fingerprint, objective, resolved Acceptance, Read, Touch, verification strategy and checks, stop/autonomy boundary, and prohibitions applicable to that projection
- **AND THEN** it does not independently parse task Markdown

#### Scenario: Stale projection is rejected
- **WHEN** the current capsule fingerprint differs from the task's recorded start fingerprint
- **THEN** Keel rejects the projection as stale
- **AND THEN** native completion cannot update durable OpenSpec state

#### Scenario: OpenCode remains manual-compatible
- **WHEN** OpenCode consumes a v4 task during this change
- **THEN** it may use the compact artifact and explicit Keel CLI manually
- **AND THEN** this capability does not require an OpenCode-specific hook, goal, plugin manifest, or automation path

## REMOVED Requirements

### Requirement: Goal and task-view projection requires explicit activation
**Reason**: #414 — the owner removed the goal, task-view, helper, and subagent projections; the host's native `/goal`, task list, and subagents need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task, native goal or subagent included; `keel agents brief` keeps the external-CLI brief.

### Requirement: Subagent projection preserves Keel ownership
**Reason**: #414 — the owner removed the goal, task-view, helper, and subagent projections; the host's native `/goal`, task list, and subagents need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task, native goal or subagent included; `keel agents brief` keeps the external-CLI brief.

### Requirement: Authorized goal projection has a disposable lifecycle
**Reason**: #414 — the owner removed the goal, task-view, helper, and subagent projections; the host's native `/goal`, task list, and subagents need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task, native goal or subagent included; `keel agents brief` keeps the external-CLI brief.

### Requirement: Helper projection cannot transfer Keel ownership
**Reason**: #414 — the owner removed the goal, task-view, helper, and subagent projections; the host's native `/goal`, task list, and subagents need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task, native goal or subagent included; `keel agents brief` keeps the external-CLI brief.

### Requirement: Change checklist projects as a disposable native tasks view
**Reason**: #414 — the owner removed the goal, task-view, helper, and subagent projections; the host's native `/goal`, task list, and subagents need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task, native goal or subagent included; `keel agents brief` keeps the external-CLI brief.
