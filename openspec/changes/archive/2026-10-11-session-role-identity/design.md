## Context

Issue #245 and the owner's decision of 2026-10-11 recorded on it.

## Facts

- F1 — `currentRole` in `src/core/chat/store.js` returns the role bound to a worktree in the repository's `roles.json`, or `KEEL_CHAT_ROLE`; `readRoles` returns the whole binding map.
- F2 — The SessionStart hook reads `keel context --json` and prints a projection; it has no role line today.
- F3 — Keel cannot observe the host's session title.

## Decisions

- D1 — `keel context` adds `role: <name>` when one is bound and `role: null` otherwise, on every result.
- D2 — The warning `This worktree has no chat role while other worktrees here have one; sessions address each other by role. Bind one with \`keel chat role --set <name>\`.` is added only when `roles.json` binds at least one other worktree.
- D3 — The projection prints `- chat role: <r> (other sessions address this one by it).` when bound, and the warning as a `- chat role:` line when D2 applies; nothing otherwise.
