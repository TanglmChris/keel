## ADDED Requirements

### Requirement: Bound native turn observation independently of transcript size

The managed receipt observation SHALL request lightweight paginated native turns without the turn items. It SHALL check successive pages for the exact saved turn ID and leave that turn unknown when the query budget ends or the cursor cannot safely continue.

#### Scenario: Recent turns precede the delivery
- **WHEN** the recorded turn is on a later page of native history
- **THEN** observation reads its outcome without asking for the transcript or turn items

#### Scenario: Native pagination cannot progress
- **WHEN** the cursor repeats or there is no matching turn within the read budget
- **THEN** the original receipt is preserved and the turn observation is unknown
