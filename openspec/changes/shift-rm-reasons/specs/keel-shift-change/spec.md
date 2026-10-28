## ADDED Requirements

### Requirement: A hand-over never removes a worktree in use, and says why an old session stayed

The session a CLI hand-off names MUST be a candidate for removal whatever the working directory `claude agents` reports for it, and a candidate's transcript MUST also be looked for under the worktree the host records for it. Before removing a session with `claude rm`, which deletes the worktree the session created, Keel MUST read the worktree the host records for that session and MUST NOT remove the session when that worktree exists and is the hand-off's worktree, a worktree bound to a role, or another listed session's working directory. Every old session a delivered hand-off leaves listed MUST be recorded on the hand-off with its reason — kept by `shift: keep_old_sessions`, its process still running, its transcript not copied, its worktree in use, or `claude rm` failing with its exit status and message — and `keel shift status` MUST name that reason for the session handed over, MUST say that opening it brings it back beside the new shift, and MUST NOT describe it as kept unless `shift: keep_old_sessions` kept it.

#### Scenario: An old session whose worktree the new shift uses stays, and status says why
- **WHEN** `verify`'s CLI session `5b14fbae` ran from a directory bound to another role, created verify's worktree as its own (the host records it as the session's `worktreePath`), and hands over with `keel shift ready --wake` in that worktree
- **THEN** the hand-over makes no `claude rm` call for `5b14fbae`, and `keel shift status` says the old session was not removed because its worktree, named by path, is in use and `claude rm` would delete it, names `claude attach 5b14fbae`, and does not say the old session was kept

#### Scenario: A failed removal is reported with the host's message
- **WHEN** after a hand-over `claude rm` of the session handed over exits 1 printing `worktree has unpushed commits`
- **THEN** `keel shift status` says the old session was not removed, naming `claude rm` exiting 1 and `worktree has unpushed commits`, and does not say it was kept
