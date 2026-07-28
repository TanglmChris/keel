## ADDED Requirements

### Requirement: The consumer bootstrap names the record-write exemption

The bootstrap is the whole resident protocol a consumer repository receives, and
it is the only place many consumers will ever read what Touch bounds. Saying
Touch is the write boundary "for product files" is accurate but relies on the
reader inferring what the qualifier excludes; the inference that actually gets
made is that the task's own `tasks.md` must be declared in Touch, which is the
misreading that produced a reported defect.

The bootstrap MUST name the exemption outright: a task's own change directory is
writable without being declared in Touch. Because the block is under a byte
budget, the room MUST be found by dropping lower-value content rather than by
raising the budget — the budget exists so resident context stays cheap, and
raising it to fit each addition removes the pressure that keeps it short.

#### Scenario: A consumer learns the exemption from the bootstrap alone

- **WHEN** a consumer repository's installed bootstrap is read
- **THEN** it states that Touch bounds product writes and that the change's own directory is exempt
- **AND THEN** a reader does not have to infer the exemption from a qualifier

#### Scenario: The block stays within its budget

- **WHEN** the bootstrap block is measured after the exemption is named
- **THEN** it is still under the byte and line budgets, which are unchanged
- **AND THEN** the content dropped to make room is named in the change that dropped it
