## Why

rtl_ppa_prj runs long-lived sessions for its roles, and at a phase boundary each one is cleared and restarted from durable state. On 2026-10-05 its PM drafted the procedure (rtl_ppa_prj #213): the PM triggers it, each session wraps up and clears itself, and the PM sends a cold-start message. A pilot with the spec session worked. Every step was manual: the readiness check was to become a project script (rtl_ppa_prj #217), and the handoff text went into issue comments.

On 2026-10-05 the owner decided that Keel's shift change replaces that procedure. The project's PM only tells a session to change shift, and the rest runs through Keel. The handoff context is kept in a temporary file Keel manages, so the next shift cold-starts from it.

## What Changes

- New `keel shift` command, one subcommand per step:
  - `request <role>`: the coordinator asks a role to change shift. It is a todo assigned to the role in their direct group, so it wakes the role.
  - `check`: a read-only readiness check of the current worktree. It reports uncommitted changes, commits on no remote, a task whose write guard is still active, live processes running in the worktree, temporary linked worktrees, and open todos or unread messages addressed to the role. It exits 1 if any are present.
  - `ready`: runs the check, stores the outgoing session's shift note, and closes the request. It then tells the session to clear itself.
  - `start <role>`: the coordinator wakes the cleared role with a cold-start message, refused until the role's note is waiting.
  - `resume`: the new shift prints the note, moves it to history, and tells the coordinator it is on shift.
  - `status`: lists each role's shift state.
- The shift note lives in the chat store, outside every worktree, so it is never committed. It exists from `ready` until `resume`. While a note waits, the role's session-start notice says so.
- A guide, `docs/shift-change.md` and its Chinese counterpart, describes the procedure.

## Capabilities

### New Capabilities
- `keel-shift-change`: a coordinated shift change for a role's session.

## Impact

New `src/core/shift.js`, a dispatch line in `bin/keel.js`, a line in the help, `src/core/chat/notice.js`, `scripts/validate_plugin.py`, two guides, README links, the published spec, and the changelog.
