# keel-worktree-overview Specification

## Purpose

A read-only overview of every worktree of a repository for a coordinator: Git state, chat role and presence, and referenced issues, with nothing fetched and nothing written.

## Requirements

### Requirement: One read-only command lists every worktree's state

`keel worktrees` MUST list every worktree of the repository with its path, its branch or that its head is detached, its short head, its upstream with ahead and behind counts as of the last fetch, its last commit's subject and time, its number of uncommitted paths, its bound chat role with that role's presence, and the issue numbers referenced as `#<n>` by commits on its head that the default branch does not contain. It MUST say that ahead and behind are as of the last fetch and name the default branch it compared against. A worktree whose directory is missing MUST be listed as missing. `--json` MUST print the same as data. The command MUST NOT fetch, and MUST NOT write to the repository or the chat store.

#### Scenario: Two worktrees are listed with their state
- **WHEN** a repository has worktrees `a` with role `pm` on branch `feature` one commit ahead of its upstream with a commit mentioning `#12`, and `b` on a detached head with one uncommitted file and no role
- **THEN** `keel worktrees --json` lists both, `a` with branch `feature`, ahead 1, issues `[12]`, role `pm` and its presence, and `b` with no branch, dirty 1, and no role
- **AND THEN** the text output names the default branch and says the counts are as of the last fetch, and the chat store's files are unchanged

#### Scenario: A missing worktree is listed as missing
- **WHEN** a worktree's directory was deleted without `git worktree remove`
- **THEN** `keel worktrees` lists it as missing and still lists the others

### Requirement: Issue update times come only from what the caller passes

`keel worktrees --issues <file>` MUST read a JSON array of objects with `number` and `updatedAt`, such as `gh issue list --json number,updatedAt` prints, and show each referenced issue's `updatedAt` from it, or none when absent. A file that cannot be read or parsed MUST be refused, naming the file, with exit 1. Keel MUST NOT fetch issue data itself.

#### Scenario: Passed issue times are shown
- **WHEN** `--issues` names a file holding `[{"number": 12, "updatedAt": "2026-10-05T08:00:00Z"}]`
- **THEN** worktree `a`'s issue 12 is shown with that time

#### Scenario: An unreadable issues file is refused
- **WHEN** `--issues` names a file that does not exist, or one that is not JSON
- **THEN** the command exits 1 naming the file

### Requirement: Create a project-associated linked worktree explicitly

Keel SHALL create a native Git linked worktree from an explicit path and new branch at the selected repository's HEAD or an explicit local commit reference. Relative paths SHALL resolve from the selected checkout. The command SHALL report the created path, branch, and base commit and SHALL allow the existing overview and role binding to see the linked worktree. It MUST NOT force an existing path or branch, copy working edits, or fetch.

#### Scenario: An explicitly located worktree is ready for Codex CLI
- **WHEN** a repository owner requests a new branch and a path next to the selected checkout
- **THEN** the command creates a linked checkout at the selected commit and reports its path for Codex CLI, isolated from the original checkout's uncommitted work
- **AND THEN** the existing overview and role binding recognize the worktree under that repository only

#### Scenario: The path or branch conflicts
- **WHEN** the path is occupied or the new branch conflicts with an existing branch
- **THEN** the command fails naming the occupied destination or Git's branch conflict and leaves existing checkouts and edits intact
