## ADDED Requirements

### Requirement: The overlay states the invocation that resolves

Every Keel OpenSpec surface overlay MUST state that the OpenSpec CLI is invoked through Keel in a
repository where a bare `openspec` may not resolve, and MUST point at the Keel diagnostic that
reports which case a given installation is.

Keel MUST state this in its own overlay block and MUST NOT edit the OpenSpec-authored body of the
file the overlay is appended to.

#### Scenario: An installed surface names the working invocation

- **WHEN** Keel installs or updates an OpenSpec command or skill surface
- **THEN** its Keel overlay names `keel openspec` as the invocation to use
- **AND THEN** it points at `keel --doctor` for whether a bare `openspec` resolves

#### Scenario: The upstream body is untouched

- **WHEN** Keel writes an overlay into an OpenSpec-authored file
- **THEN** the text outside the overlay block is unchanged
