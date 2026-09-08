## ADDED Requirements

### Requirement: A declared failure signature is enforced against the recorded red

When a check declares a failure signature, `keel gate task-complete` MUST require
the check's `.red` Evidence to contain that literal string, and MUST name the
check and the string it did not find when it does not.

A check that declares no signature MUST be completed exactly as it is today.

`keel gate task-start` MUST report, alongside the red-green obligation, which of
the checks owing a red declared a signature and which did not.

Keel MUST NOT judge whether a declared signature is an adequate one.

#### Scenario: A red that does not show the declared failure is refused

- **WHEN** a check declares a failure signature and its `.red` Evidence does not contain that string
- **THEN** `keel gate task-complete` fails
- **AND THEN** it names the check and the string that is missing

#### Scenario: A red showing the declared failure completes

- **WHEN** a check declares a failure signature and its `.red` Evidence contains that string
- **THEN** the declared signature raises no problem

#### Scenario: An undeclared check is unaffected

- **WHEN** a red-green check declares no failure signature
- **THEN** completion requires exactly the concrete `.red` and `.green` Evidence it required before

#### Scenario: The obligation names which checks declared a signature

- **WHEN** `keel gate task-start` reports the red-green obligation for a task
- **THEN** it names which of the checks owing a red declared a failure signature and which did not
