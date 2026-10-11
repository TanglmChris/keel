## ADDED Requirements

### Requirement: A protected branch is pushed only with the user's approval of that push

`authorize:` MAY declare `push-protected:<branch glob>` or `push-protected:<branch glob>@<role>`, more than once. The glob MUST use branch-name characters and `*`, and the role MUST be a chat role name; anything else MUST be refused as malformed, and a bare `push` beside it MUST be refused naming both. `keel --doctor` MUST report `push-protected` with its globs and roles and state that the Claude write guard asks the user for each push to them.

#### Scenario: A protected branch is reported
- **WHEN** `authorize:` lists `push:claude/*` and `push-protected:main@iecc-pm`
- **THEN** `keel --doctor` reports `push-protected` scoped to `main@iecc-pm` and that each push to it is asked

#### Scenario: A malformed protected entry is refused
- **WHEN** `authorize:` lists `push-protected:main@Not A Role`, or a bare `push` beside `push-protected:main`
- **THEN** `keel --doctor` exits non-zero naming the entry
