## Why

Issue #376 (kaiwu-ip, 2026-10-19): the project was renamed and nine chat roles with it, such as `iecc-pm` → `kaiwu-pm-iecc`. Keel has no rename. `keel chat role --set <new>` rebinds the worktree, but everything else stays under the old name: membership of every `dm-*` group, read cursors, presence, the parked flag, shift notes, segments and transcripts, patrol state. The old name can never become an alias of the new one, because it is still a member of the old direct groups and `addAlias` refuses any known role name. So mentions of the old name reach nobody, and the new role starts empty. The owner chose on 2026-10-19 to do #376.

## What Changes

- `keel chat role --rename <old> <new>` records that `<old>` is now `<new>`. It is run from a worktree bound to either name, or as `owner`.
- Records are not rewritten. The chat reads every role field of the log — sender, member added or removed, assignee, mentions, and the members of a direct group — through the rename. So `<new>` is a member of every group `<old>` was in, the direct groups included, it is assigned `<old>`'s open todos, and `@<old>` mentions `<new>`.
- The worktree bindings and the per-role state files move from `<old>` to `<new>`: cursors (the further one wins), presence and session records, the parked flag, the shift note, history, segments, transcripts and hand-off queue, and the patrol snapshot, log and nudge state. Where `<new>` already has its own copy, `<new>`'s is kept and the rename says which of `<old>`'s it left in place.
- The old name cannot be bound again, and `KEEL_CHAT_ROLE=<old>` acts as `<new>`. Files Keel does not own that still name `<old>` (`keel/config.yaml`, `keel/chat.json`) are listed, not edited.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: a role can be renamed.

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, a new `src/core/chat/rename.js`, `scripts/validate_plugin.py`, `README.md`, one published spec, the changelog.
