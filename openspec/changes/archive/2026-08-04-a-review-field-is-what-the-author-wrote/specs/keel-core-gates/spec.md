## ADDED Requirements

### Requirement: A Review entry is the text written under its label
A Review entry inside a task's `Evidence` — `Status`, `Acceptance check`, `Scope check`, `Findings` — MUST be read as the whole text the author wrote under its label: the label line plus every following line, ending at the next Review entry at the same or shallower indentation. A gate MUST NOT judge a Review entry by its first line alone, because the text below the first line is text the author recorded and the gate did not read.

The bound MUST be the sibling entry. A Review entry MUST NOT absorb the entry that follows it, nor any evidence line outside the Review block, so that reading the author's whole entry cannot let one entry be satisfied by another's text.

Widening the read MUST NOT widen what is accepted. The disposition markers, the durable-owner forms, the accepted `Status` vocabulary, the concreteness rule, and every diagnostic code and message MUST be exactly what they were; the only verdicts that may change are those that turn on text the gate previously discarded.

#### Scenario: A durable owner below the first line is read
- **WHEN** a Review `Findings` wraps across several lines and names its durable owner on a line below the first
- **THEN** `task-complete` accepts the owner
- **AND THEN** the verdict is the one it returns for the identical text joined onto a single line

#### Scenario: A finding written below a none first line is not invisible
- **WHEN** a Review `Findings` reads `none` on its first line and records a finding with no disposition on a line below it
- **THEN** `task-complete` refuses it with `finding-owner`
- **AND THEN** the finding is not treated as absent because the first line said `none`

#### Scenario: A Review entry stops at its sibling
- **WHEN** a Review `Findings` wraps and another Review or Evidence entry follows it
- **THEN** the following entry's text is not read as part of `Findings`
- **AND THEN** a `Findings` that carries no disposition of its own is still refused, whatever the entries below it contain

#### Scenario: An unwrapped Review entry is unchanged
- **WHEN** every Review entry of a task occupies exactly one line
- **THEN** each entry's value, and every resulting verdict, problem code, and message, is what it was before the bound gained its continuation lines
