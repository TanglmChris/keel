## ADDED Requirements

### Requirement: The overlay diagnostic reports every managed action

`keel --doctor` MUST report the OpenSpec surface overlay across every action Keel manages, derived from the same list the projection uses rather than from a hardcoded pair. A diagnostic naming a fixed subset becomes wrong the moment the managed set changes, and it becomes wrong silently.

#### Scenario: A newly managed action cannot be left out of the diagnostic
- **WHEN** Keel manages the overlay for an action
- **THEN** `keel --doctor` reports that action's overlay state
- **AND THEN** the reported label is derived from the managed action list, so it names sync alongside apply and archive
