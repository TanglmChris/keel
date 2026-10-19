## ADDED Requirements

### Requirement: A session changes its own shift with one slash command

The Claude plugin MUST ship `/keel:shift`, a command file at `plugins/keel/commands/shift.md` that has the session run `keel shift check`, deal with each item it reports or ask the owner, write the hand-off note, and run `keel shift ready --wake --file -` with the note on stdin through a quoted heredoc, and then do what `ready` prints for the host. It MUST tell the session to tell a keep-awake process the host started under it, such as `caffeinate`, from a process the session started, to let the first stay with `--force-reason` naming it, and to stop the second or ask the owner. The `keel shift` commands and flags it names MUST be ones `keel shift` accepts.

#### Scenario: The command's own steps hand a shift over
- **WHEN** the command file's `keel shift` lines run in order in a clean worktree bound to `verify`
- **THEN** `keel shift check` exits 0, `keel shift ready --wake --file -` stores the note given in the heredoc at `keel-chat/shift/verify.md` and prints that the wake is armed, and the command's text names `caffeinate` and `--force-reason`
