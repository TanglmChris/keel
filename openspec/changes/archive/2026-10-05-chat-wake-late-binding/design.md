## Context

Issue #187. Owner request 2026-10-05: binding a role must not require reloading the plugin.

## Facts

- F1 — Claude Code documents `watchPaths` as a SessionStart-only output; CwdChanged and FileChanged have no decision control (code.claude.com/docs/en/hooks, read 2026-10-05).
- F2 — `keel chat hook session-start` returns nothing when the worktree has no role (`hook` in `src/core/chat/notice.js`), so such a session watches no file for the rest of its life.
- F3 — The FileChanged hook resolves the role from the worktree on every call, so it already honors a role bound after the session started, provided some watched file changes.
- F4 — Roles are bound per worktree in the store's `roles.json`, keyed by the worktree path.

## Decisions

- D1 — SessionStart in a repository worktree always returns `signal/worktree/<id>` in `watchPaths`, where `<id>` is the first 16 hex digits of the SHA-256 of the worktree path, plus `signal/<role>` when a role is bound. With no role it returns `watchPaths` alone and no `additionalContext`. Outside a repository it stays silent.
- D2 — `writeRecord` appends the record id to `signal/worktree/<id>` for every worktree that `roles.json` binds to a role the record wakes, beside the existing `signal/<role>`. The waker LaunchAgent keeps watching `signal/<role>`, which is unchanged.
- D3 — A role set through `KEEL_CHAT_ROLE` is fixed when the session starts, so it is already covered by `signal/<role>`.
