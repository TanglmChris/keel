## ADDED Requirements

### Requirement: Observe the original managed Codex turn and terminal inventory

With an explicitly requested native observation, the managed receipt query SHALL read the original native thread, verify its worktree and use the exact acknowledged turn identity. It SHALL distinguish usage exhaustion evidenced by the typed turn error from other failures and report the native background-terminal inventory separately. Missing identity, host evidence or partial inventory SHALL remain unknown where applicable. The query SHALL issue only read requests and SHALL NOT infer old-writer release or verified task completion.

#### Scenario: The original thread recorded a usage failure and still has tools
- **WHEN** the role has handed over and the old acknowledged turn reports a typed usage-limit failure with a background terminal present
- **THEN** the query reports resource exhaustion and a present background terminal for the original thread without resuming or changing it

#### Scenario: Submission or native evidence is incomplete
- **WHEN** a receipt is incomplete or existing native observations do not identify the exact turn or terminal inventory
- **THEN** the query reports the corresponding result as unknown without attempting replacement or replay
