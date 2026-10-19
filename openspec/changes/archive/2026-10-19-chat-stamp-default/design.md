## Context

#349 offered a default stamp with `--no-stamp`, or a `chat: stamp: always` setting in `keel/config.yaml`. A default reaches every project without a declaration, and the time is Keel's own clock, so stamping by default adds no estimate anyone could get wrong.

## Facts

- F1 — `stamped()` (`src/core/chat/cli.js`) prefixes `[MM-DD HH:MM]` only when `--stamp` is given, for `post` and `dm`.
- F2 — Records Keel itself posts (patrol, shift wake, the Slack bridge) go through the store, not `stamped()`, and are unaffected.

## Decisions

- D1 — `post` and `dm` stamp unless `--no-stamp` is given; `--stamp` is kept as a no-op for existing callers, and both together are refused.
- D2 — A text whose first characters already match `[MM-DD HH:MM]` is left as it is, so an author or a script that stamps by hand is not doubled.
- D3 — A stamp must not change what a text means: a reply that opens with a stamp and then `done` or ✅ still closes the todo it answers, and a text whose first line opens a Markdown block (`#`, a list bullet, `>`, a code fence, a numbered item, a table row) gets the stamp on its own line above it.
