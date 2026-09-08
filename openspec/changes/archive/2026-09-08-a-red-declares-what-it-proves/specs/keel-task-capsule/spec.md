## ADDED Requirements

### Requirement: A check may declare the failure its red must show

A verification check MAY declare the failure signature its red is expected to
produce, as a `Fails with:` clause at the end of the check followed by a literal
in inline code. The declaration is part of the check text and is therefore
covered by the contract fingerprint.

Keel MUST refuse a declaration on a check that can have no red, and MUST refuse a
`Fails with:` marker that names no literal, rather than ignoring either.

#### Scenario: A declared signature compiles into the contract

- **WHEN** a check ends with `Fails with:` and an inline-code literal
- **THEN** the compiled capsule carries that literal as the check's failure signature
- **AND THEN** changing the literal moves the contract fingerprint

#### Scenario: A declaration on a check with no red is refused

- **WHEN** a check tagged `(regression)`, or any check under a strategy outside the red-green set, declares a failure signature
- **THEN** `keel gate task-start` fails and names the check
- **AND THEN** the message states that the check records no red for the signature to describe

#### Scenario: A marker naming no literal is refused

- **WHEN** a check carries a `Fails with:` marker with no inline-code literal after it
- **THEN** `keel gate task-start` fails and names the check
- **AND THEN** the message states that the signature is written as a literal in inline code
