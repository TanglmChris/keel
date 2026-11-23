## MODIFIED Requirements

### Requirement: Endpoint migration has a verified native handoff

Keel MUST migrate only an idle original source without pending input, tools or Goal; it MUST preserve source native writer protection and require target original persistent history and effective policy. Inspection and apply SHALL verify target identity and complete persistent history with non-subscribing reads before writing transition intent. Before native handoff it SHALL persist that intent. After source unsubscribe it SHALL observe the original source as unloaded within a bounded wait before attempting target acquisition. Only after target verification and registry comparison SHALL it atomically change the endpoint and append audit; prior history, role fields and delivery claims MUST remain unchanged. Unknown outcomes MUST remain inspectable and MUST NOT trigger blind retry, rollback claims or replacement creation.

#### Scenario: Target cold history cannot verify the plan
- **WHEN** the native target reports a different identity, worktree or full history during inspection or before apply intent
- **THEN** Keel refuses before source unsubscribe, does not resume the target and leaves the registry untouched

#### Scenario: Source unload follows unsubscribe asynchronously
- **WHEN** the original source is idle and reports its subscription canceled while the thread remains loaded
- **THEN** Keel waits using bounded read-only observations at the original source, and attempts acquisition once only after observing that same source thread unloaded

#### Scenario: Another source subscriber retains the writer
- **WHEN** the original source cannot be verified unloaded within the deadline, or target acquisition is otherwise rejected by the native writer
- **THEN** the old registration remains and the transition is reported unknown for explicit inspection, without restarting any process or retrying acquisition

#### Scenario: Source contains active work or pending input
- **WHEN** source turn, queue, terminal or Goal prevents a safe handoff
- **THEN** Keel refuses before transition intent without canceling or consuming the work

#### Scenario: Explicit reconciliation follows uncertain commit
- **WHEN** a migration outcome is unknown and the caller explicitly requests reconciliation
- **THEN** Keel verifies an already loaded original target, original completed-history prefix, native policy and source release before a registry CAS; an unloaded target causes refusal without retrying acquisition
