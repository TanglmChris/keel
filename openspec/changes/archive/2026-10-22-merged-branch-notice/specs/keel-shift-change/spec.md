## ADDED Requirements

### Requirement: Resume says when the worktree is on a branch already merged

After printing a note, `keel shift resume` MUST print one line when the worktree's HEAD differs from `origin/<default>` and is an ancestor of it, naming the branch (or a detached HEAD), that it is already in `origin/<default>`, how many commits behind it is, and to start new work from `origin/<default>`. It MUST NOT fetch, and MUST print no such line when HEAD has commits `origin/<default>` lacks or no remote default branch resolves.

#### Scenario: A merged branch is named, an unmerged one is not
- **WHEN** verify's worktree is on `feat`, whose commit was pushed and fast-forwarded into the remote default branch with one more commit after it, and verify runs `keel shift ready` then `keel shift resume`
- **THEN** the resume output names `feat`, `already in origin/<default>`, and `1 commit behind`
- **AND THEN** after a new unpushed commit on `feat`, another ready and resume print no such line
