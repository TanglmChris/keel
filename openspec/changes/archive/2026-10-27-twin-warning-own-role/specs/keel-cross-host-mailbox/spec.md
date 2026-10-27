## MODIFIED Requirements

### Requirement: Two live sessions on one role are reported

Each session that writes a role's presence MUST also record its session id, process, worktree and last activity under the role, removing its entry when it ends and dropping entries whose process is not running. When two or more of a role's recorded sessions are live, `keel context` MUST warn, and `keel chat post`, `keel chat unread` and `keel chat read` MUST warn on stderr, naming the role, each session, and that they post under one name and share one read cursor. A recorded session whose own session record names a different role MUST NOT be counted, because it has since bound that role; a session whose record names this role, or that has no record, MUST be counted.

#### Scenario: A second live session on a role is reported, and the report ends with it
- **WHEN** `verify`'s hooks run in CLI session `sess-a`, then in a second live CLI session `sess-b`, and that second process later exits
- **THEN** with one session nothing is reported; with both, `keel context` warns naming `verify`, `sess-a`, `sess-b` and the read cursor, and `keel chat post` and `keel chat unread --json` warn on stderr with valid JSON on stdout; once `sess-b` has exited the warning is gone

#### Scenario: A session that bound another role is not a twin
- **WHEN** live CLI sessions `sess-a` and `sess-b` both start in `verify`'s worktree, and `sess-b` then runs `keel chat role --set fe` in a new worktree `fe` that holds its transcript
- **THEN** `keel context` in `verify`'s worktree reports no live sessions bound to `verify`, while `sess-b` is still running
