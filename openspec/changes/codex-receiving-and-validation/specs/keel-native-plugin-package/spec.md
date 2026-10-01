## ADDED Requirements

### Requirement: Codex declares executable host-compatible hook commands

The Codex plugin manifest MUST explicitly select a Codex hook configuration whose command strings include the executable, script path and arguments. It MUST retain continuity and existing guard declarations and add mailbox receiving at SessionStart and UserPromptSubmit. It MUST NOT register FileChanged, watchPaths or asyncRewake; Claude's existing manifest and hook declarations MUST remain unchanged by this Codex-specific adaptation.

#### Scenario: Native Codex discovery preserves script arguments
- **WHEN** Codex discovers the installed plugin's hooks
- **THEN** its reported commands include the declared script paths and event arguments rather than only `node`

#### Scenario: No trust is silently granted
- **WHEN** the plugin is newly installed or a hook definition changes
- **THEN** its non-managed hooks remain subject to Codex's trust review and Keel documents the manual review step
