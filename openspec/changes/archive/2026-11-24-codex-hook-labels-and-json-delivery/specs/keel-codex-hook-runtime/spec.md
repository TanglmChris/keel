## Purpose

Make Keel's Codex hooks recognizable in native review and preserve their responses through a pipe.

## ADDED Requirements

### Requirement: Codex reports distinct Keel hook purposes

The Codex integration SHALL declare four distinct labels using a native supported field. Each label SHALL identify its Keel purpose and distinguish the startup mailbox notification from the prompt notification.

#### Scenario: Native hook discovery
- **WHEN** Codex loads the plugin
- **THEN** its hook metadata exposes all four labels with the original lifecycle events and commands

### Requirement: Hook JSON survives output backpressure

Session projection and write guard hooks MUST allow their declared JSON responses to finish writing before they exit.

#### Scenario: The receiving pipe is temporarily full
- **WHEN** a session projection or guard decision is larger than the pipe's immediately available capacity
- **THEN** native-shaped consumers can read a complete JSON response with the same projection or permission decision
