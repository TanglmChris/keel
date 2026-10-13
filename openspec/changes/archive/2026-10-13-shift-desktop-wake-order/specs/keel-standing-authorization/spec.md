## ADDED Requirements

### Requirement: Restoring a session after a desktop shift is a named authorization

`authorize:` MAY declare `shift-restore`, with no scope. It covers exactly two actions of a session started by a shift change in the Claude desktop app, taken right after `keel shift resume`: turning that session's Remote Control back on, and renaming that session back to its working title. It MUST NOT cover any other session, clearing, starting, or archiving a session, or any repository action. `keel --doctor` MUST list it like the other names, and the accepted-names message for an unrecognized entry MUST include it.

#### Scenario: shift-restore is accepted and listed
- **WHEN** `authorize:` lists `commit` and `shift-restore`
- **THEN** the declaration is readable, and `keel --doctor` lists `shift-restore`

#### Scenario: A scoped shift-restore is refused
- **WHEN** `authorize:` lists `shift-restore:anything`
- **THEN** the declaration authorizes nothing, and the message names `shift-restore:anything`
