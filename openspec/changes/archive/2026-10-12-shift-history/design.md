## Context

Issue #304 and the owner's decision of 2026-10-12 recorded on it. Not chosen: renaming and archiving the old session and opening a new one per shift (the session id changes, which breaks scheduled tasks and Remote Control addressing it, and archiving can remove a shared worktree).

## Facts

- F1 — Clearing keeps the session id and starts a new transcript file; the PM session has three (10-04 → 10-06, 10-06 → 10-12, from 10-12 16:51) (2026-10-12).
- F2 — `search_session_transcripts` finds a sentence from the current segment and nothing from an earlier one; the old conversation returns only through the host's "Resume previous session".
- F3 — `clear_session` refuses a session serving Remote Control; `remoteControlActive` was true for five rtl_ppa_prj sessions.
- F5 — Claude Code keeps a session's transcripts under `<config dir>/projects/<cwd with every non-alphanumeric character replaced by ->/<uuid>.jsonl` (config dir `CLAUDE_CONFIG_DIR`, else `~/.claude`); each record carries `cwd` and `timestamp`, and a scheduled run's first user message starts with `<scheduled-task` (2026-10-12, the PM worktree's six files).
- F4 — Claude Code hook payloads carry `transcript_path`; a transcript is JSON lines whose `user` and `assistant` records hold `message.content` as a string or as parts with `type: text`.

## Decisions

- D1 — On SessionStart and UserPromptSubmit of a session bound to a role and not a host run, when the payload has an absolute `transcript_path`, the hook updates `<chat root>/shift/segments/<role>.json` (`{ "segments": [{ transcript, started, ended }] }`): nothing when the last segment has that transcript; otherwise it sets the last segment's `ended` to now and appends `{ transcript, started: now, ended: null }`.
- D2 — SessionStart saves the segments file as it was in the session's record beside the presence it saves (#300); a first prompt that marks the session a host run restores both.
- D3 — `keel shift history [<role>]` (the bound role by default; refused without one) prints the role's segments newest first, `<started> → <ended|now>  <transcript>` with `(missing)` for a file no longer on disk, followed by its past shift notes from `shift/history/<role>-*.md`. `--json` prints `{ role, segments, notes }`.
- D4 — `--grep <text>` scans each existing segment's `user` and `assistant` text, case-insensitively, and prints per segment up to three matches as `<timestamp> <role of speaker>: …<120 characters around the match>…`; it exits 1 when nothing matches.
- D6 — The owner asked on 2026-10-12 that earlier history be searchable too. `keel shift history` therefore also reads the Claude transcript directory of every worktree bound to the role (F5), takes each file's first and last `timestamp` as its range, leaves out a file whose first user message starts with `<scheduled-task`, and merges these with the recorded segments, keyed by file path, newest first. A file found only this way shows `(found)` in place of a recorded range. Codex transcripts are not read.
- D5 — `ready` for a role adds `This shift's conversation stays in its transcript; \`keel shift history <role>\` finds it after the clear.`; the clear hint adds `A session serving Remote Control cannot be cleared: turn Remote Control off, clear, then turn it back on.`
