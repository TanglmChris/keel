## Context

The rtl_ppa_prj procedure (#213, 2026-10-05) and the owner's decisions of the same day: Keel's shift change replaces it, with trigger, readiness check, and cold-start commands. The handoff context goes into a temporary file Keel keeps, so a cold start can read it.

## Facts

- F1 — The rtl_ppa_prj pilot of 2026-10-05: spec ran a readiness review, cleared itself with the desktop app's `clear_session("self")` after the owner approved, and recovered its state from issue comments after the PM's cold-start message.
- F2 — A cleared Claude Code session fires SessionStart again, so the chat hook's notice and watch list apply to the new shift (chat-wake-late-binding).
- F3 — A todo assigned to a role, and any record in a direct group, wakes that role. A reply opening with `done` closes the todo it answers (`src/core/chat/store.js`).
- F4 — `keel/HANDOFF.md` is a pointer override that must not carry session state (keel-stateless-continuity), and `keel context` never infers continuity from memory or transcripts.

## Decisions

- D1 — Six subcommands, one per step: `request`, `check`, `ready`, `start`, `resume`, and `status`. Each step is a chat record, so it wakes the right session, reaches Slack where a group is bridged, and is reviewable afterwards.
- D2 — Request, readiness, cold start, and the on-shift acknowledgement are records in the direct group between the coordinator and the role. The request is a todo carrying the ref `keel-shift`. `ready` replies `done`, which closes it, and later steps find the request by that ref.
- D3 — The shift note is free text the outgoing session writes: what it was doing, the next step, what it waits on, and where (branch, files, issues). It is stored at `<git-common-dir>/keel-chat/shift/<role>.md`, outside every worktree, so it is never committed. `resume` moves it to `shift/history/<role>-<stamp>.md`. It is not a follow-up owner: work left undone still goes to the project's tracker, and the note may cite it. It is not `HANDOFF.md` either, and `keel context` does not read it (F4). The chat notice points to it, and the new shift opens it explicitly.
- D4 — `check` judges only what Keel can observe. Uncommitted changes (`git status --porcelain`). Commits reachable from HEAD that no remote-tracking ref contains, skipped with a note when the repository has no remote. An active write guard (`keel/guard.json`). Processes whose working directory is inside the worktree, found through `/proc` where present and `lsof` otherwise, excluding this process's own ancestors (the session itself) and bare interactive shells such as a terminal tab left open there, whose running commands are listed by their own entries. Linked worktrees other than this one and the main one whose path lies under a temporary directory. Open todos assigned to the role, other than the shift request, and unread records that would wake it. Any item makes it not ready (exit 1). Project-specific checks run beside it, as rtl_ppa_prj's script will (#217).
- D5 — `ready` refuses while `check` reports items, unless `--force-reason <text>` states why the items may stay. The reason goes into the note and the reply. It refuses an empty note. It prints how to clear the session on each host (`clear_session("self")` in the desktop app, `/clear` in the CLI, a new session in Codex), and runs none of them.
- D6 — `start` refuses until the role's note is waiting, so a coordinator cannot wake a shift with nothing to resume. The cold-start message says: run `keel context`, then `keel shift resume`, then continue. An optional text adds the next step.
- D7 — While a note waits, the role's session-start notice carries one line saying so and naming `keel shift resume`. The notice is the second channel. The coordinator's `start` message is the wake.
