## ADDED Requirements

### Requirement: Resident-block content is checked as topics, not as prose

The resident-block check MUST distinguish a required entry that names a command, marker, or identifier from one that states a topic in prose. A command or marker MUST be matched literally, so a rename fails the check. A topic MUST be matched by pattern, so the block's wording can be improved — which it must be, because the block is under a line and byte budget — without a validator edit. The diagnostic MUST name which kind of entry was missing.

#### Scenario: Rewording a topic keeps the check green
- **WHEN** a resident block states a required topic in different words while keeping its concepts in one statement
- **THEN** the check passes without any validator edit
- **AND THEN** the same holds for every caller of the check, not just the baseline run

#### Scenario: Deleting a topic still fails
- **WHEN** a required topic's statement is removed from the resident block
- **THEN** the check fails and names the missing topic
- **AND THEN** a rewrite that merely mentions one of the topic's words does not satisfy it

#### Scenario: Renaming a command still fails
- **WHEN** a required entry names a command, marker, or identifier and the block no longer contains it exactly
- **THEN** the check fails, because a resident block that names a command must name the one that exists
- **AND THEN** the diagnostic distinguishes this from a missing topic
