## ADDED Requirements

### Requirement: Declared literals and recorded Evidence are compared with whitespace runs as one space

When `keel gate task-complete` checks a declared `Fails with:`, `Detects:`, or `Measured:` literal against the recorded Evidence, it MUST read every run of whitespace on both sides as one space, and MUST fold nothing else. Each refusal for a missing literal MUST state that runs of whitespace are compared as one space.

#### Scenario: A literal with aligned spaces matches the raw output
- **WHEN** a check declares `` Fails with: `FAIL  record reachable` `` with two spaces, and its `.red` Evidence quotes the raw output `FAIL  record reachable` with two spaces
- **THEN** `keel gate task-complete` raises no `red-missing-declared-failure`

#### Scenario: Different characters are still refused
- **WHEN** the same check's `.red` Evidence quotes `FAIL record unreachable`
- **THEN** `keel gate task-complete` fails with `red-missing-declared-failure`, and the message says runs of whitespace are compared as one space
