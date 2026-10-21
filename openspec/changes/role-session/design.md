## Facts

- F1 — Measured 2026-10-21 with Claude Code 2.1.304. A session started with `claude --bg -w <name>` from the main checkout received three SessionStart hooks; this table shows the worktree signal each one watched:

  | Hook source | Watched signal | Worktree |
  |---|---|---|
  | `startup` | `worktree/f2bd450ce3d386fc` | `probe-424` (correct) |
  | `resume` | `worktree/1cbbb9dd30699ea1`, plus `codex-issues` | main checkout (wrong) |
  | `compact` | `worktree/f2bd450ce3d386fc` | `probe-424` (correct) |

  The transcript stayed in the project directory of the `-w` worktree throughout.
- F2 — keel-maint-2 `375d5fd8` was resumed at 09:18 and recorded as `codex-issues`:
  - presence: `cli_session` 375d5fd8, `cli_worktree` the main checkout;
  - `sessions/375d5fd8.json`: `role: codex-issues`;
  - `codex-issues.sessions.json` lists it.
- F3 — `keel chat <command>` calls `touchPresence(where, role)` for the role bound to the command's worktree. Its `cliFields` read the caller's `CLAUDE_CODE_SESSION_ID`, so:
  - a visiting session becomes the role's session (#415 step 1);
  - a caller that is not a Claude CLI session writes `cli_session: null`.
- F4 — `keel chat role --set` only writes the binding. The session's record and the role's segments are written at SessionStart, so a session that binds a role later is never recorded (`keel chat wake now keel-maint-2`: "has recorded no Claude Code CLI session").
- F5 — `resumeCli` resumes whatever session is recorded. `claude agents --json --all` lists stopped sessions with no `status`, and a removed one not at all (measured for #397).

## Decisions

- D1 — `hookLocation(payload)`:
  1. Locate `payload.cwd`.
  2. If `payload.transcript_path`'s parent directory name equals the host's sanitized path (`/[^A-Za-z0-9]/` → `-`) of another worktree that `git worktree list` gives for this repository, locate that worktree instead.
  3. With no transcript path or no match, keep `payload.cwd`.
- D2 — A `keel chat` command touches the role's presence in full only when the calling session's record (`sessions/<CLAUDE_CODE_SESSION_ID>.json`) names that role. Otherwise it updates `state` and `last_active` and keeps every recorded session field and the session list.
- D3 — `role --set` in a Claude Code session does four things:
  - writes the session's record with the role, decided and not a host run;
  - touches presence in full;
  - records the session's transcript as the role's segment (the host's file for this session under the worktree's project directory);
  - prints that hooks watch what they watched at start, so a session started in a worktree with no role is woken through its worktree signal (chat-wake-late-binding D1).
- D4 — `resumeCli` first reads `claude agents --json --all`. When the list parses and lacks the recorded session id, it resumes nothing and returns the reason. An unreadable list keeps today's behaviour, resuming as before.
- D5 — No repair of existing records is written by hand. A role's next SessionStart, `role --set`, or owned command rewrites them, and codex-issues' entry ages out when its recorded process exits.
