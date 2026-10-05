## Why

Issue #187, found while connecting rtl_ppa_prj on 2026-10-05: the owner messaged the spec session through Slack, the record and its signal arrived, and the session never woke. Claude Code takes `watchPaths` only from SessionStart, and Keel returns one only when the worktree already has a role. The spec session was started before its role was bound, so it watched nothing, and only a plugin reload or a new session would fix it. The owner asked that a role bound later not need a reload.

## What Changes

- SessionStart in any worktree of a repository returns a per-worktree signal path in `watchPaths`, and the role's signal path as well when a role is bound. A worktree with no role still gets no notice text.
- A record that wakes a role also appends to the per-worktree signal of each worktree bound to that role, so a session that started before its worktree's role was bound wakes on the next record addressed to it.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: SessionStart watches a per-worktree signal; waking records touch it.

## Impact

`src/core/chat/{notice,store}.js`, `scripts/validate_plugin.py`, the published spec, and the changelog. A session already running when this ships still needs one restart, because its SessionStart has run.
