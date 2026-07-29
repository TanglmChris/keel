## MODIFIED Requirements

### Requirement: Apply surface enforces Keel task ownership

The apply overlay MUST require the current agent to select the task or small contiguous task group, obey the selected task contract, and personally review evidence before marking tasks complete. The overlay MUST direct the agent to consult the repository's standing authorization rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared.

#### Scenario: Apply overlay prevents ownership transfer

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says the current agent remains the Keel task owner
- **AND THEN** the overlay says target-native subagents return report/evidence only and cannot mark tasks complete

#### Scenario: Apply overlay routes confirmation to the declaration

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says a standing-authorized action proceeds without a per-occurrence confirmation
- **AND THEN** the overlay says an undeclared action still requires the confirmation it requires today
- **AND THEN** the overlay says a standing authorization never substitutes for a gate, evidence, or Review

### Requirement: Archive surface enforces Keel archive ownership

The archive overlay MUST require the current agent to own sync/archive decisions and completion-gate review. The overlay MUST direct the agent to consult the repository's standing authorization for the archive action rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared.

#### Scenario: Archive overlay prevents archive delegation

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says the current agent owns final sync/archive decisions
- **AND THEN** the overlay says target-native subagents cannot archive, sync, change acceptance, or bypass completion gates

#### Scenario: Archive overlay routes confirmation to the declaration

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says a repository that standing-authorizes `archive` does not need the per-occurrence archive confirmation
- **AND THEN** the overlay says the completion gate and follow-up ownership checks still run unchanged
