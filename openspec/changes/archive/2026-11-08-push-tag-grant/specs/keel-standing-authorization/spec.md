## ADDED Requirements

### Requirement: A tag push is granted by its own scoped name

`authorize:` MAY declare `push-tag:<tag glob>` or `push-tag:<tag glob>@<role pattern>`, more than once. The glob MUST use tag-name characters and `*`, and a bare `push-tag`, a malformed glob or a malformed role pattern MUST be refused naming the required form. A `push-tag:` entry MUST NOT make a bare `push` beside it a mixed declaration, because it widens no branch.

#### Scenario: Doctor reports the grant and says it is enforced
- **WHEN** `authorize:` lists `push-tag:v*` and `push-tag:cbb-parked-*@kaiwu-pm-cbb`
- **THEN** `keel --doctor` reports `push-tag` authorized and scoped to `v*`, names the role-limited entry, and says the Claude write guard enforces it

#### Scenario: A wrong form is refused naming the form
- **WHEN** `authorize:` lists a bare `push-tag`, `push-tag:v$` or `push-tag:v*@Not`
- **THEN** `keel --doctor` fails and names `push-tag:<tag glob>`

#### Scenario: A bare push beside a tag grant is not mixed
- **WHEN** `authorize:` lists `push` and `push-tag:v*`
- **THEN** `keel --doctor` accepts the declaration
