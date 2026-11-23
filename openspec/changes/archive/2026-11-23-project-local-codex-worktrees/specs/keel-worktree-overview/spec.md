## ADDED Requirements

### Requirement: Create a project-associated linked worktree explicitly

Keel SHALL create a native Git linked worktree from an explicit path and new branch at the selected repository's HEAD or an explicit local commit reference. Relative paths SHALL resolve from the selected checkout. The command SHALL report the created path, branch, and base commit and SHALL allow the existing overview and role binding to see the linked worktree. It MUST NOT force an existing path or branch, copy working edits, or fetch.

#### Scenario: An explicitly located worktree is ready for Codex CLI
- **WHEN** a repository owner requests a new branch and a path next to the selected checkout
- **THEN** the command creates a linked checkout at the selected commit and reports its path for Codex CLI, isolated from the original checkout's uncommitted work
- **AND THEN** the existing overview and role binding recognize the worktree under that repository only

#### Scenario: The path or branch conflicts
- **WHEN** the path is occupied or the new branch conflicts with an existing branch
- **THEN** the command fails naming the occupied destination or Git's branch conflict and leaves existing checkouts and edits intact
