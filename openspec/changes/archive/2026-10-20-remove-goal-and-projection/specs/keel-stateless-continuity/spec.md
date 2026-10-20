## REMOVED Requirements

### Requirement: Single-task automation authorization is durable but not session state
**Reason**: #414 — the owner removed Keel's `/goal`, helper, task-view, and subagent projections; native capabilities need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task.

### Requirement: Continuity never chains tasks
**Reason**: #414 — it bounded the single-task `/goal` authorization, which is removed; continuing through an approved task list is the default since 5.172.0.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task.
