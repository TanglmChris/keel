## Why

Issue #245 (rtl_ppa_prj, 2026-10-05): one session had three names — the host's session title, the project's role table, and its worktree — and a message sent to the documented name did not reach it. The owner decided on 2026-10-11 that the chat role is the session's identity: Keel cannot read the host's session title, so it names the bound role and warns when none is bound, and sessions address each other by role through `keel chat`.

## What Changes

- `keel context` carries a `role` field: the chat role bound to this worktree, or null.
- When this worktree has no role while another worktree of the repository has one, `keel context` warns and names `keel chat role --set <name>`. A repository that uses no chat roles gets no warning.
- The SessionStart and compaction projection names the bound role, or carries the same reminder.
- README: cross-session messages address roles, not session titles.

## Capabilities

### Modified Capabilities
- `keel-native-runtime-projection`: the projection names the chat role a session speaks as.

## Impact

`src/core/context.js`, `plugins/keel/scripts/session-start.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
