## Why

Keel #548 asks for identifiable Codex working copies stored alongside their projects. Git can create and track linked worktrees at a project-chosen path, and Codex CLI can start in that directory.

## What Changes

- Add explicit linked worktree creation with a caller-chosen path, fresh branch, and local starting commit.
- Document Codex CLI launch, Keel role binding and discovery, and Git's ordinary safe cleanup.

## Capabilities

### Modified Capabilities

- `keel-worktree-overview`: explicit creation alongside the existing read-only overview.

## Impact

Git and Codex CLI workflow. The project chooses the path. Existing Desktop-managed worktrees and their handoff lifecycle stay under Codex management.
