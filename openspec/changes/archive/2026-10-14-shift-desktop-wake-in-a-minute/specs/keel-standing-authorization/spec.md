## MODIFIED Requirements

### Requirement: A session's own shift change on the desktop app is a named authorization

`authorize:` MAY declare `self-shift`, with no scope. It covers exactly the four steps `keel shift ready --wake` prints on the Claude desktop app, after that `ready` stored the note: creating or updating the wake task it names, starting it with `run_scheduled_task`, renaming the session, and clearing it. It MUST NOT cover deciding to change shift, which stays where the protocol places it; any other session; archiving; or any repository action. `keel --doctor` MUST list it, and the accepted-names message MUST include it.

#### Scenario: self-shift is accepted and listed
- **WHEN** `authorize:` lists `commit` and `self-shift`
- **THEN** the declaration is readable, and `keel --doctor` lists `self-shift`

#### Scenario: A scoped self-shift is refused
- **WHEN** `authorize:` lists `self-shift:anything`
- **THEN** the declaration authorizes nothing, and the message names `self-shift:anything`
