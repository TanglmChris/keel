## ADDED Requirements

### Requirement: A regression check declares itself and is exempt from red-green

A red-green strategy proves a behavior by failing before the implementation and
passing after. A regression check makes the opposite claim — that something
already green is still green — and has no honest red. Requiring one of it leaves
an author two options, fabricating a red or folding the guard into the behavior
check, and both are worse than the check they replace: the first is the
dishonesty the evidence rule exists to prevent, and the second lets the gate's
shape decide how the task is decomposed.

An `M<n>` check MAY therefore carry a `(regression)` tag after its label. A
tagged check MUST still record concrete Evidence for its bare label; the
exemption is from `.red` and `.green`, not from proof. A task whose strategy is
red-green MUST retain at least one untagged check, so a strategy cannot be
emptied out by tagging every check in it.

The tag MUST be part of the compiled capsule, so the exemption is a declared
term of the contract that review and the fingerprint both see rather than a
silent skip. A check that carries no tag MUST compile exactly as it does today,
so no existing task's fingerprint moves.

#### Scenario: A regression guard stands as its own check

- **WHEN** a task under a red-green strategy declares a check tagged `(regression)` alongside an untagged behavior check
- **THEN** completion requires `.red` and `.green` only for the untagged check
- **AND THEN** the tagged check still fails completion if its bare-label Evidence is missing

#### Scenario: A red-green strategy cannot be emptied out

- **WHEN** every check in a task under a red-green strategy is tagged `(regression)`
- **THEN** the gate refuses the task and states that at least one check must carry the strategy
- **AND THEN** the diagnostic distinguishes this from missing evidence

#### Scenario: Untagged checks compile unchanged

- **WHEN** a task declares only untagged checks
- **THEN** its compiled capsule and fingerprint are identical to what the same task compiled before the tag existed
- **AND THEN** no already-recorded contract anchor is invalidated by this capability

#### Scenario: Red and green are additional to the bare label

- **WHEN** an author reads the tasks template for what a red-green strategy must record
- **THEN** it states that `.red` and `.green` entries accompany the bare `M<n>` Evidence rather than replacing it
- **AND THEN** an author following the template does not meet a missing-evidence refusal for the label itself
