## ADDED Requirements

### Requirement: Managed host bindings do not select continuity authority

Codex managed-role bindings in the chat store MUST describe only local endpoint, worktree, thread and delivery lifecycle state. They MUST NOT select an OpenSpec owner, grant task authority, or replace keel context. Starting a role MUST NOT adopt an unrelated desktop chat.

#### Scenario: An addressed record wakes a managed role
- **WHEN** Keel drains a waking unread record for an owned Codex role
- **THEN** the work input retains the chat data-only warning and requests repository authority inspection before acting
- **AND THEN** the binding does not select or authorize an OpenSpec task
