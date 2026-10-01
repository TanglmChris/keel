## ADDED Requirements

### Requirement: Ordinary helper choice does not activate a native goal

Keel MUST require explicit activation for native goals while ordinary bounded helper use is independent of this skill trigger.

#### Scenario: Ordinary help does not activate a goal
- **WHEN** the model chooses a helper in ordinary authorized work
- **THEN** no native goal is created by that choice

