## Context

Owner, 2026-10-14: #320 is to be measured and fixed; the shift feature is otherwise frozen. Not chosen: Keel calling the host itself (Keel launches nothing), or dropping the chat record (CLI and Codex roles still read it, and `keel shift check` counts it as the start).

## Facts

- F1 — #320 comment 6171236953: process-less desktop session, `keel shift start` 22:50:13 → no target log line until 22:53:21; `send_message` → `Resuming session` 22:53:28, first turn 22:53:37.
- F2 — `keel shift ready` on the desktop app already writes `Desktop session: <id>.` into the note (#319).
- F3 — The 5.136.0 wake prompt wakes with `get_session` → `unarchive_session` if archived → `send_message`, because auto-archive can archive an idle session (#326).

## Decisions

- D1 — `start()` reads `Desktop session:` from the waiting note and returns it beside the posted record. The CLI then prints, instead of `Woke …`: that the start was posted, that a desktop session with no running process sees no chat record (#320), and the step: call `get_session` on `<id>`; when it reports the session archived, call `unarchive_session` on it; then call `send_message` to it with the start text, quoted. `--json` carries `desktop`.
