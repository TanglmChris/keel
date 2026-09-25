## ADDED Requirements

### Requirement: A disposition marker is recognized only where it opens its clause

A Review `Findings` disposition marker MUST be recognized only where it opens its clause — preceded
by the start of the value, a line break, or sentence-ending punctuation. A marker preceded by a word
MUST NOT be read as a disposition, because it is part of that sentence rather than the head of a
clause, and the commonest such sentence states the opposite of what the marker means.

The rule MUST apply both to the scan that captures a disposition's evidence and to the scan that
detects that a disposition is present, so the two cannot disagree about what a marker is: a marker
counted as present while supplying no evidence would accept a finding as disposed with nothing
behind it.

Narrowing MUST NOT be able to pass silently. Where a marker is no longer recognized, the finding
carries no disposition and is refused by the rule that already requires one, and that refusal MUST
name the opening requirement so an author whose marker sits mid-sentence is told why.

#### Scenario: A negated mention is not a disposition
- **WHEN** a `Findings` entry says a finding is *not* resolved here and closes with a durable owner
- **THEN** the negated phrase is not read as a resolution claim, and no resolution evidence is
  demanded of the word following it
- **AND THEN** the durable owner is accepted, so the entry completes

#### Scenario: A marker opening a clause still parses
- **WHEN** a marker is preceded by the start of the value, a line break in wrapped prose, or
  sentence-ending punctuation
- **THEN** it is read as a disposition exactly as before
- **AND THEN** its evidence is held to the same requirements

#### Scenario: A marker that opens no clause is refused, not ignored
- **WHEN** a `Findings` entry's only marker is preceded by a word
- **THEN** the entry is refused for carrying no disposition
- **AND THEN** the diagnostic names the requirement that a marker open its clause
