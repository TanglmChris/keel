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
