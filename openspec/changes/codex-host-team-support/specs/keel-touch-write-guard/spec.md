## ADDED Requirements

### Requirement: Native Codex patches share the Touch evaluator

The Codex hook source MUST match native apply_patch and Bash events. Native patch Add File, Update File, Delete File and Move to paths MUST use the existing resolved repository-scope Touch evaluator. A patch with an uninspectable path set under an active guard MUST fail closed. Bash pushes MUST use the existing push authorization policy. Source configuration and direct payload tests MUST NOT establish production hook trust or enforcement.

#### Scenario: A move escapes Touch
- **WHEN** an otherwise allowed patch moves a file to a repository path outside Touch
- **THEN** the guard denies the patch before execution and names the destination

#### Scenario: Runtime trust is unknown
- **WHEN** the shipped hook has no current native activation and blocking evidence
- **THEN** capability reporting retains manual Codex enforcement
