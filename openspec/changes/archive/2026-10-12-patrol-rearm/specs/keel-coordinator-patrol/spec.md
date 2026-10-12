## ADDED Requirements

### Requirement: The patrolling role is reminded to re-arm its schedule

`keel/config.yaml` MAY declare `patrol:` with `role:` naming a chat role and `every:` a duration of the form `<n>s`, `<n>m`, `<n>h`, or `<n>d`. In a worktree bound to that role, `keel context` MUST carry `patrol` with the role and interval, the SessionStart and compaction projection MUST state that the role runs `keel patrol` at that interval and that a session's schedule ends with the session, and `keel shift resume` MUST end with the same reminder. Keel MUST NOT create the schedule. A declaration missing either value, or with a malformed one, MUST be reported and MUST remind nobody; a worktree bound to another role MUST get no reminder.

#### Scenario: A new shift of the coordinator is reminded
- **WHEN** `patrol:` declares `role: iecc-pm` and `every: 30m`, and a worktree bound to `iecc-pm` starts a session and runs `keel shift resume`
- **THEN** `keel context --json` carries `patrol` with `iecc-pm` and `30m`, the projection names `keel patrol` and `30m`, and the resume output ends with the reminder

#### Scenario: Other roles and broken declarations are quiet
- **WHEN** the worktree is bound to `rtl`, or `every:` reads `soon`
- **THEN** no `patrol` field or reminder appears, and the malformed declaration is reported in warnings
