## Facts

- F1 — The archive timer in `run()` (`src/core/chat/bridge.js`) logs `<project>: <refused>` for every refused sync and `<project>: archive sync failed: <message>` for every thrown one, every 10 minutes while connected. `archive.sync` returns `refused: "this repository has no remote"` for a repository with no remote (`pushDecision`, `src/core/chat/archive.js`).
- F2 — Each Socket Mode `hello` queues `conn.onHello()`, the catch-up, and logs `catch-up failed: <message>` when it throws (`socketSession`). A reconnect sends a new `hello`.
- F3 — `callWithRetry` (`src/core/chat/slack.js`) treats `missing_scope` as final and rethrows the `SlackError`, whose message is `Slack <method> failed: <error> (HTTP <status>)`. Slack's `missing_scope` response carries `needed` (comma-separated scopes) and `provided`.
- F4 — On 2026-10-25 the log held 2944 of the first kind and 278 of the second (issue #460, Keel 5.197.1).
- F5 — `scripts/fake_slack.py` cannot answer a method with a chosen error yet.

## Decisions

- D1 — A `failed(key, line)` / `cleared(key, line)` pair on the bridge context remembers the last line logged per key. `failed` logs only a line that differs from the remembered one. `cleared` logs only when the key had a failure, then forgets it. The keys are `archive:<project>` and `catch-up:<connection>`, the connection being the shared app or a role's app. A recovery line is `<project>: archive sync works again` or `catch-up works again`, with the role's app named for a role connection.
- D2 — `SlackError` takes `needed` and `provided` from Slack's response and keeps them as fields. When `needed` is present, the message reads `Slack <method> failed: missing_scope: needs <needed> (HTTP <status>)`. `provided` stays a field and is not printed, because it can be long and the fix only needs what is missing.
- D3 — `KEEL_CHAT_ARCHIVE_EVERY_MS`, a whole number of milliseconds, overrides the 10-minute interval. Any other value keeps 10 minutes. It is a test seam and is not documented for users.
- D4 — The fake server gains `fail(method, body)`, which answers every call of `method` with `body` until `fail(method, None)`.
