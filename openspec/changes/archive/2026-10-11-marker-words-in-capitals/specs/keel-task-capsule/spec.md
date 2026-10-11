## ADDED Requirements

### Requirement: Marker words read as unfilled only in capitals

Keel's concreteness test MUST judge a field, check, or Evidence entry unfilled when, outside inline code, it carries an angle-bracket slot `<…>` or one of the marker words `TODO`, `TBD`, or `PLACEHOLDER` written in capitals as a whole word. The same words in lowercase or mixed case MUST NOT make the text unfilled, because in that form they are ordinary prose. Every concreteness judgement Keel makes MUST use this one set.

#### Scenario: A lowercase marker word is prose
- **WHEN** a task's `M<n>` Evidence line reads "With `--ack` on post and todo, the record is acknowledged", or a check names "each todo and its placeholder text"
- **THEN** the concreteness test judges it filled, and the gate reports no unfilled slot

#### Scenario: A capitalised marker word is still a slot
- **WHEN** a task's `M<n>` check reads `node test.js TODO` or carries `PLACEHOLDER` outside inline code
- **THEN** the gate reports it non-concrete and names the matched word

#### Scenario: An angle-bracket slot is still a slot
- **WHEN** a task's `M<n>` check carries `<value>` outside inline code
- **THEN** the gate reports it non-concrete and names `<value>`
