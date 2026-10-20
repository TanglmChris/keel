## REMOVED Requirements

### Requirement: Goal execution consumes gates without extending them
**Reason**: #414 — the owner removed Keel's `/goal`, helper, task-view, and subagent projections; native capabilities need no Keel projection.
**Migration**: None. The gates, fingerprints, and the `Touch` write guard bind whoever runs a task.
