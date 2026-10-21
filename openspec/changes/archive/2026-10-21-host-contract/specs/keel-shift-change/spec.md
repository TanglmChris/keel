## ADDED Requirements

### Requirement: The CLI hand-over and wake keep to the measured host contract
A hand-over MUST NOT `claude rm` a session whose recorded process is still running; it waits for that process to exit, bounded, and keeps the session listed when it does not. When `claude agents --json --all` cannot be read or `claude` is missing, the pending hand-off MUST record why, and `keel shift status` and the patrol risk MUST name it. A tick MUST mark an ended role woken only when the resume succeeded, retry a failed resume at most three times, and not retry a removed session.

#### Scenario: The old session is removed only after its process exits
- **WHEN** a hand-over stops the old session, whose process exits a moment after `claude stop` returns
- **THEN** `claude rm` of that session runs only after the process has exited
- **AND THEN** when the process is still running past the wait, the session is not removed and stays listed

#### Scenario: A host that cannot be listed is named
- **WHEN** `claude` is missing, or `claude agents --json --all` prints no list, while a hand-off is pending
- **THEN** the hand-off stays pending and `keel shift status` names that cause

#### Scenario: A failed wake is retried a bounded number of times
- **WHEN** a role's CLI session has ended, a record addressed to it waits, and resuming it fails
- **THEN** the next tick tries again, up to three attempts for that record, and a session `claude agents` no longer lists is not tried again
