## ADDED Requirements

### Requirement: A session a hand-over replaced is told and cannot begin new work

When a role's hand-over is `delivered` and names a session as the old one, the chat hook MUST tell that session so, first, on `SessionStart` and `UserPromptSubmit`, and `keel gate task-start` and `keel shift ready` MUST refuse it, naming the new session and writing no guard, anchor or queue entry. Judgment MUST use the hand-over record only; the new session, a session with no id and `task-complete` MUST NOT be refused for this reason.

#### Scenario: The old session is told when it starts or is prompted
- **WHEN** a hand-over has been delivered and the chat hook runs for the old session's id on `SessionStart` and on `UserPromptSubmit`
- **THEN** each output starts with a line naming the role, the new session and the instruction to tell the user, and the hook run for another session id has no such line

#### Scenario: The old session cannot start a task or hand over again
- **WHEN** the old session runs `keel gate task-start` and `keel shift ready --wake`
- **THEN** the gate result is `fail` with a problem naming the new session, `ready` exits non-zero with the same words, and no guard manifest is written and the queue entry is unchanged

#### Scenario: Other sessions are not refused for this reason
- **WHEN** the same commands run with another session id, and with no session id
- **THEN** neither output carries the replaced-session wording
