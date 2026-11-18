## ADDED Requirements

### Requirement: Explicit owned thread onboarding

Keel SHALL preserve the original thread id, persistent history, delivery claims, worktree and authorized policy when explicitly migrating a managed endpoint or registering an authorized dedicated frontend thread. Keel MUST reject unverified ownership, conflicting bindings, policy mismatches and unknown native outcomes without creating replacement threads or replaying uncertain deliveries.

#### Scenario: Existing original identity is retained
- **WHEN** an owner explicitly admits the exact role/thread/worktree/endpoint tuple and native verification succeeds
- **THEN** onboarding retains that identity and policy without a thread/start or warm-up turn

#### Scenario: Native writer or policy is unverified
- **WHEN** the required source handoff, native writer ownership or policy cannot be established
- **THEN** Keel reports the failed prerequisite and does not claim successful onboarding or replace the thread

### Requirement: Onboarding is explicit and preserves native policy

Keel MUST inspect an exact authorized original role/thread/worktree/endpoint tuple into a versioned plan before applying registration or migration. Registration SHALL require a unique pre-existing canonical worktree binding and no conflicting current, historical or pending thread ownership. It MUST atomically create registration without changing native settings, history or worktree bindings. Subsequent managed delivery and recovery SHALL preserve the observed native policy, including read-only review; registered frontend handover MUST refuse replacement creation.

#### Scenario: Active same-runtime frontend is registered
- **WHEN** an explicitly authorized original thread is active on the selected runtime and its identity and policy can be inspected by id-only rejoin
- **THEN** registration leaves the running turn untouched and later delivery reports waiting rather than starting parallel work

#### Scenario: Explicit plan is stale or conflicts
- **WHEN** role binding, registry identity, native worktree/policy or unique thread ownership fails verification
- **THEN** apply fails without overwriting registration or starting a model turn

#### Scenario: Read-only reviewer receives work
- **WHEN** the original read-only frontend is registered and receives an addressed record
- **THEN** native read-only policy remains effective, actual work can complete, and repeated record delivery returns the original outcome without another turn

### Requirement: Endpoint migration has a verified native handoff

Keel MUST migrate only an idle original source without pending input, tools or Goal; it MUST preserve source native writer protection and require target original persistent history and effective policy. Before native handoff it SHALL persist a transition intent. Only after target verification and registry comparison SHALL it atomically change the endpoint and append audit; prior history, role fields and delivery claims MUST remain unchanged. Unknown outcomes MUST remain inspectable and MUST NOT trigger blind retry, rollback claims or replacement creation.

#### Scenario: Another source subscriber retains the writer
- **WHEN** source unsubscribe does not release the native writer and target resume refuses
- **THEN** the old registration remains and the transition is reported unknown for explicit inspection, without restarting any process

#### Scenario: Source contains active work or pending input
- **WHEN** source turn, queue, terminal or Goal prevents a safe handoff
- **THEN** Keel refuses before transition intent without canceling or consuming the work

#### Scenario: Explicit reconciliation follows uncertain commit
- **WHEN** a migration outcome is unknown and the caller explicitly requests reconciliation
- **THEN** Keel verifies an already loaded original target, original completed-history prefix, native policy and source release before a registry CAS; an unloaded target causes refusal without retrying acquisition
