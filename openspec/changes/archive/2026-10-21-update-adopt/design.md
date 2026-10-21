## Facts

- F1 — Every `skill_listing` attachment below was read from transcripts on 2026-10-21. kaiwu-lead `0e12b6cb` (started 08:45Z on 5.170.0) lists `keel:keel-run-single-task-goal`. `ef20932c` (started 12:51Z by a hand-over, with 5.175.0 installed) lists the five current skills only.
- F2 — Probe `7321f913` was started with 5.177.0 installed. After `keel --update` installed 5.178.0 (`lastUpdated` `2026-10-21T00:49:40Z`), the probe was stopped and resumed:
  - `claude stop` then `claude --bg --resume <full id> "/compact"`: the resume and compact SessionStart hooks report `plugin 5.178.0`, and neither carries the "hooks now run the installed plugin … in place of the loaded …" line a stale process prints.
  - `claude --bg --resume <full id>` with no prompt prints `(idle — send a prompt to start)`, and adds only `bridge-session` and `cost-state` records to the transcript: no turn.
- F3 — `claude agents --json` rows carry `startedAt` (ms), which a resume moves to the new process's start (the probe read 08:53 after its 08:52 resume). `claude plugin list --json` carries `lastUpdated` for the installed Keel plugin.
- F4 — `claude stop` returns before the process exits (#395). A resume before the exit starts a copy, so the waker waits on the pid (5.167.0).
- F5 — The update fake in the suite answers `agents --json` with no output, and the suite's default `KEEL_UPDATE_CLAUDE` names no executable.

## Decisions

- D1 — A session is on an older plugin when it is a background row whose `startedAt` is before the installed plugin's `lastUpdated`. That covers sessions started before an update, whichever version they loaded.
- D2 — `--adopt` restarts only idle rows. It skips:
  - busy and waiting rows, so no turn is cut;
  - a row whose `cwd` has `keel/guard.json`, which follows #204's rule to keep the loaded guard under a manifest;
  - the row whose `sessionId` is `CLAUDE_CODE_SESSION_ID`, since stopping itself would kill the command.

  For each row it restarts, it runs `claude stop`, waits up to 15 s for the pid to exit, then runs `claude --bg --resume <sessionId>` in the row's `cwd`, with no prompt and no flag. A flag would start a copy under a new id.
- D3 — Without `--adopt`, the update prints one `claude sessions` line only when older sessions exist, and nothing when the list cannot be read. With `--adopt`, an unreadable list, a stop that does not end the process, or a failed resume is `failed`. `--dry-run` prints the commands it would run.
- D4 — `--adopt` is opt-in rather than part of every update, because a restart reconnects Remote Control under a new address that a remote viewer has to reopen.
