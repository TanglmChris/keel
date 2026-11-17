## ADDED Requirements

### Requirement: Managed Codex hand-over uses explicit owned identity

Managed Codex roles MUST use keel codex handover with a retained note and old thread history in the existing chat store. The operation MUST wait while the verified owned thread is active, and MUST record a pending claim before creating one successor. The successor MUST receive the retained note with its next addressed delivery. Claude shift behavior MUST remain unchanged.

#### Scenario: A role is still busy
- **WHEN** the managed thread is active during a hand-over request
- **THEN** Keel reports waiting and starts no successor

#### Scenario: A successor receives context
- **WHEN** an idle managed role hands over and its successor receives addressed work
- **THEN** the successor input contains the retained hand-over note and the old identity remains in history
