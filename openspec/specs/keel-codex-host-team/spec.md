# keel-codex-host-team Specification

## Purpose

Define owned Codex host roles, bounded transport, addressed delivery, hand-over and evidence-limited native capabilities.

## Requirements

### Requirement: A Codex host is inspected through its shared control endpoint

Keel MUST inspect the explicitly selected managed Codex host using its WebSocket control endpoint, bounded in time. It MUST report connection failures without starting another server or resuming a thread. A persisted thread reported notLoaded MUST NOT be treated as proof that a desktop session is idle.

#### Scenario: Managed service responds
- **WHEN** the configured service accepts a connection
- **THEN** Keel reports its initialization identity and the requested thread metadata

#### Scenario: Service is unavailable
- **WHEN** connection fails or the deadline expires
- **THEN** Keel reports the cause, exits nonzero and starts no replacement server

### Requirement: Managed roles have explicit session ownership

Keel MUST start Codex team roles on the managed service with a recorded thread id and worktree. It MUST refuse delivery when the host or worktree identity differs, and MUST preserve existing Claude role behavior.

#### Scenario: A role is started
- **WHEN** an authorized managed Codex role starts
- **THEN** its thread id and worktree are durably recorded for subsequent delivery

### Requirement: Delivery and hand-over do not duplicate active work

Keel MUST deliver addressed work only to the recorded managed role. It MUST persist delivery claims, retain failed work as pending and wait rather than duplicate an active turn. After verifying thread identity it MUST return an already-delivered claim before load-state checks and MUST refuse an unknown claim without resuming. For a new record only, an explicitly owned thread reported notLoaded MUST be resumed as the same thread on the same connection, then have its id, worktree and state revalidated before turn/start. Failure, identity mismatch or any unverified state MUST start no new work and MUST NOT create a replacement thread or change permissions. Hand-over MUST retain the note and require the old role to finish before starting its successor; it gains no implicit unload recovery.

#### Scenario: Delivery is repeated
- **WHEN** the same addressed record is processed twice, including after the managed thread unloads
- **THEN** one work turn is started and the duplicate returns the original claim without resuming the thread

#### Scenario: An owned role unloads between work rounds
- **WHEN** a new addressed record targets an identity-verified owned notLoaded thread
- **THEN** Keel resumes that same thread and starts a turn only after its identity and idle state are verified

#### Scenario: Recovery reveals active work or fails
- **WHEN** owned recovery reports active, fails, or returns mismatched identity
- **THEN** active work waits and failures refuse delivery, without turn/start or replacement creation

#### Scenario: A role is not owned
- **WHEN** registration, worktree or endpoint ownership cannot be verified
- **THEN** Keel neither resumes nor creates a thread for that request

### Requirement: Codex hook claims require runtime evidence

Keel MUST verify native startup, compaction and guarded tool behavior before reporting enforced Codex capabilities. Missing trust, unsupported events and unavailable runtime evidence MUST remain visible as manual or unverified.

#### Scenario: A hook is not trusted
- **WHEN** its activation and denial are not verified
- **THEN** Keel does not report it as enforced

### Requirement: Two managed roles prove the completed integration

Completion MUST include a real two-role assignment, wake, result and hand-over with evidence distinguishing actual host behavior from stand-in tests.

#### Scenario: End-to-end team run
- **WHEN** two managed roles finish the acceptance exercise
- **THEN** evidence names the role sessions, addressed records, returned result and successor without duplicate execution

### Requirement: Release rollout verifies the installed host before notification

A managed-team rollout MUST verify the published package and release, installed Keel CLI/plugin versions and an actual completed model turn through the intended default host endpoint before notifying downstream repositories. It MUST preserve current native hook trust boundaries and MUST NOT interrupt unrelated active service work.

#### Scenario: Rollout is complete
- **WHEN** publication, installed version checks and the real default-host turn pass
- **THEN** the downstream owner receives one versioned update notification with verification evidence and remaining native trust limits

#### Scenario: Connectivity still fails
- **WHEN** the default host accepts RPCs but model work does not complete
- **THEN** rollout remains incomplete and no downstream completion notice is sent

### Requirement: Successful blank role initialization supports delayed first delivery
Keel MUST preserve the exact owned thread identity across creation connection closure and delayed first use. If durable initialization cannot be verified, it MUST report that boundary and retain registration evidence rather than silently replace the thread or claim delivery succeeded.

#### Scenario: First delivery is delayed
- **WHEN** a managed role starts successfully and the creation connection closes before its first addressed record arrives
- **THEN** the same registered identity remains usable for its first work turn after normal host unloading
- **AND THEN** no substitute thread or implicit model warm-up is used

### Requirement: Foreground and background preserve owned execution identity
Keel MUST support verified serial foreground and background work on the same owned thread without duplicate writers, replacement identities or lost delivery claims. Explicit thread policy and safe restoration of an owned worktree MUST retain sandbox and approval boundaries. Merely listing a thread MUST NOT count as foreground/background acceptance.

#### Scenario: Desktop work and addressed background delivery alternate
- **WHEN** real foreground input and background delivery target the same owned thread
- **THEN** their accepted work executes serially with retained history and no repeated addressed record

#### Scenario: Foreground changes the owned worktree
- **WHEN** current thread cwd differs from its recorded owned worktree
- **THEN** normal delivery refuses until an explicit verified recovery preserves thread id, history and claims

#### Scenario: Explicit managed thread reviewer is persistent without warm-up
- **WHEN** a caller starts a managed role with an explicit user or auto_review reviewer
- **THEN** Keel persists that reviewer on the owned native thread before success, retains on-request and workspace-write, and preserves it through cold delivery and handover without a hidden model turn or global policy edit
- **AND** invalid policy requests fail before stateful RPCs while persistence failures retain the original pending thread identity without automatic replacement

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

### Requirement: Legacy managed recovery negotiates workspace roots support

Keel MUST negotiate the native capability required by a recovery request that restores runtime workspace roots, including legacy managed entries without a saved reviewer or effective policy snapshot. Existing writer, original identity, worktree, policy and delivery-claim checks MUST remain in force.

#### Scenario: Legacy recovery restores a drifted original thread

- **WHEN** an idle legacy role's original thread has a different native cwd
- **THEN** explicit recover negotiates the required capability and restores the recorded cwd and runtime workspace roots on the original endpoint without rewriting the registry or starting a turn
