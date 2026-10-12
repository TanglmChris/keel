## ADDED Requirements

### Requirement: A host-run session does not act as the worktree's role

When a session's first prompt starts with `<scheduled-task`, the chat hooks MUST restore the role's presence to what it was before that session's SessionStart, and from then on that session's hooks MUST NOT write presence, inject chat notices, or wake it, and its SessionEnd MUST leave presence unchanged. A session whose first prompt is anything else MUST behave as before.

#### Scenario: A scheduled run leaves the role's presence alone
- **WHEN** a session starts in `verify`'s worktree and its first prompt starts with `<scheduled-task name="patrol">`, and it then ends
- **THEN** `verify`'s presence after the prompt equals what it was before the start, the prompt's hook output carries no chat notice, and after the end `verify`'s presence is unchanged
