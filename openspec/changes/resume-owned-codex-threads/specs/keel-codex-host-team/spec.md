## MODIFIED Requirements

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
