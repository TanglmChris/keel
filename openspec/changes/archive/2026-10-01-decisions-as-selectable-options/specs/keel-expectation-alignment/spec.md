## ADDED Requirements

### Requirement: Enumerable decisions are offered as selectable options

When Keel's agent asks the user for a decision whose answers can be enumerated, and the host offers a structured-choice surface, the resident protocol and the alignment skill MUST direct the agent to ask through that surface, with the recommended option first and marked as recommended. Open questions, and hosts with no such surface, MUST remain free to use prose. The portable skill text MUST NOT name a host-specific tool.

#### Scenario: The resident protocol states the rule
- **WHEN** a reader opens the managed block of `AGENTS.md` at `## User-facing communication`
- **THEN** it directs enumerable decisions through the host's structured-choice surface where one is offered, recommendation first, with prose kept for open questions and hosts without the surface

#### Scenario: The alignment skill states the rule host-neutrally
- **WHEN** a reader opens `keel-align-expectations`' Deep path, in source and in the shipped plugin copy
- **THEN** it carries the same rule and names no host-specific tool such as `AskUserQuestion`
