## Facts

- F1 — Probes, 2026-10-21, Claude Code 2.1.304 with `remoteControlAtStartup: true`. The owner looked at the claude.ai, desktop, and phone lists:
  - `probe-418 · stop` (stopped) still read as a session;
  - `probe-418 · rcoff` (`/remote-control`, then stopped) still read as a session;
  - `probe-418 · rm` (stopped, then `claude rm`) was gone.
- F2 — `claude rm` of a session started with no `-w` in an existing worktree left that worktree in place (session `627abac9` in `probe-418-stop`, measured). Removing the session that created a worktree with `-w` also removed the worktree. A hand-over starts its session in the role's worktree without `-w`.
- F3 — `removeOldSessions` in `src/core/shift.js` (#397, #401) already removes stopped sessions beyond `keep` with `claude rm`, and only after `keptCopyOf` has written Keel's copy of the transcript. The session just handed over is one of them. `keel shift status` already prints `keel shift history <role> --show <id>` for an old session that was removed.
- F4 — `readShiftDeclaration` reads `shift:`, but `CONFIG_DECLARATIONS` does not list it, and `keel/config.yaml` does not document it.

## Decisions

- D1 — The default of `keep_old_sessions` becomes 0, and an unreadable value falls back to 0. The removal path is unchanged.
- D2 — `ready --wake` reads the declaration. With nothing kept, it says a waiter stops the session and removes it once Keel holds the transcript, and names `keel shift history <role> --show <id>`. With a number declared, it keeps the `claude attach` sentence.
- D3 — `shift` is appended to `CONFIG_DECLARATIONS` after `patrol`, and `keel/config.yaml` gains its block in that place. The header then names thirteen declarations.
