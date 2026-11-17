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

Keel MUST deliver addressed work only to the recorded managed role. It MUST persist delivery claims, retain failed work as pending and wait rather than duplicate an active turn. Hand-over MUST retain the note and require the old role to finish before starting its successor.

#### Scenario: Delivery is repeated
- **WHEN** the same addressed record is processed twice
- **THEN** one work turn is started and the duplicate is reported as already delivered

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
