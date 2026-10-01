## ADDED Requirements

### Requirement: A critical statement's owned extent is structural

Keel MUST resolve an accepted critical-statement opener together with its following indented continuation and nested list-item lines. The extent MUST end before a peer list item, a blank-line-separated paragraph at the opener's level, or a Markdown heading. Keel MUST preserve the existing accepted opener shapes and MUST continue to report a colon-shaped opener as unparsed rather than silently adding syntax.

#### Scenario: A nested bullet belongs to its decision
- **WHEN** `design.md` has `- D1 — decision` followed by a deeper-indented bullet
- **THEN** a task citing `D1` receives both lines as normalized authority text

#### Scenario: A following peer decision is separate
- **WHEN** `design.md` has `- D1 — first` followed by `- D2 — second` at the same indentation
- **THEN** a task citing only `D1` does not include `D2` in its authority text

#### Scenario: A colon-shaped opener remains a diagnosed authoring error
- **WHEN** `design.md` has `- D1: statement` and a task cites `D1`
- **THEN** `task-start` reports `D1` as unparsed and names the accepted dash shape

### Requirement: An owned extent follows Markdown nesting

Keel MUST treat a `#` line nested at or beyond the opener's list-item content column as owned content rather than a closing heading, and MUST treat an unindented line that directly continues the opener's paragraph as owned. A line that opens another critical statement (`D<n>`, `F<n>`, `A<n>`, or `Q<n>` followed by a dash, bare or bold) MUST end the extent even without a bullet or a blank line.

#### Scenario: A nested `#` line does not cut the decision short
- **WHEN** a cited `- D1 — decision` has a nested detail containing an indented `#` line followed by another nested bullet
- **THEN** editing that later nested bullet moves the task fingerprint

#### Scenario: A lazy continuation belongs to its decision
- **WHEN** `D1 — decision` is followed directly, with no blank line, by an unindented line that continues the sentence
- **THEN** editing that line moves the task fingerprint

#### Scenario: An adjacent unbulleted opener is a peer
- **WHEN** `D1 — first` is followed directly by `**D2** — second` with no bullet and no blank line
- **THEN** editing `D2` does not move the fingerprint of a task citing only `D1`
