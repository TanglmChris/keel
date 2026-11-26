## ADDED Requirements

### Requirement: Bounded resume of managed Codex threads
The managed delivery and recovery paths SHALL request original thread metadata without hydrating historical turns. They SHALL retain the existing thread, admission checks, native policy and uncertain delivery semantics.

#### Scenario: Cold resume with history larger than the transport limit
- **WHEN** native full-history resume exceeds the allowed response size
- **THEN** managed delivery can resume the verified original and create one turn for its addressed record
- **AND** another delivery for that record reuses the recorded turn
