## Facts

- F1 — On 2026-10-22 on this Mac, Claude Code 2.1.x was running `caffeinate -i -t 300` as PID 3456 with parent 13691. 13691 is the `claude` process that is also the parent of the shell running this session's commands. So the keep-awake is a sibling of the checking command, and its parent is one of the checker's ancestors.
- F2 — `liveProcesses` in `src/core/shift.js` excludes the checking process, its ancestors, and its process group. A sibling is in none of these, so the keep-awake is listed. All 5 CLI-era keel-maint notes carry a "Left as is … caffeinate -i -t 300" block. In 2 of 3 sampled outgoing shifts the session spent an extra `ps` call proving the process's parentage before forcing past it.
- F3 — The `/keel:shift` requirement in `keel-shift-change`, `plugins/keel/commands/shift.md`, and both `docs/shift-change` pages tell the session to let the host's keep-awake stay with `--force-reason`.

## Decisions

- D1 — `keel shift check` does not list a process whose command's program basename is `caffeinate` and whose parent is an ancestor of the checking process. Every other process is listed as before, including:
  - a `caffeinate` whose parent is not such an ancestor, for example one orphaned or started by another session;
  - any other program the session's host process started.
- D2 — `/keel:shift`, its requirement, and the docs stop telling the session to force past the host's keep-awake. The step about processes now covers only a process the session started: stop it, or ask the owner.
