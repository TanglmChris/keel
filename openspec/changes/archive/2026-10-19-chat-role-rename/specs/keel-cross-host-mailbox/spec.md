## ADDED Requirements

### Requirement: A role can be renamed

`keel chat role --rename <old> <new>` MUST record that `<old>` is now `<new>`, run from a worktree bound to either name or as `owner`, and MUST refuse an unknown `<old>`, equal or invalid names, a cycle of renames, and a rename when both names are bound to worktrees. Records MUST NOT be rewritten: every role field read from the log — sender, member added or removed, assignee, mentions, and the members of a direct group — MUST read `<old>` as `<new>`, so `<new>` belongs to every group `<old>` was in, holds its open todos, and is mentioned and woken by `@<old>`. The worktree bindings and the per-role state — read cursors, presence, the parked flag, shift notes, history, segments, transcripts and hand-off queue, and patrol state — MUST move to `<new>`, keeping `<new>`'s own copy where one exists and reporting what it kept. `<old>` MUST NOT be bound again, `KEEL_CHAT_ROLE=<old>` MUST act as `<new>`, and lines of `keel/config.yaml` and `keel/chat.json` that still name `<old>` MUST be listed and left unedited.

#### Scenario: A renamed role keeps its groups, todos, state and mentions
- **WHEN** `verify`, a member of group `soc` and of direct group `dm-rtl--verify` with an open todo, a read cursor and a shift note, is renamed to `check` from its worktree
- **THEN** `keel chat group list` shows `check` in both groups, `keel chat todos --mine` in that worktree lists the todo, records it had read stay read, `keel shift status` shows the note under `check`, a new `@verify` from `rtl` wakes `check`, `keel chat role --set verify` is refused naming `check`, and a `patrol: role: verify` line in `keel/config.yaml` is listed

#### Scenario: A rename onto a role that already exists keeps the new role's state
- **WHEN** `--set check` was run in `verify`'s worktree before the rename, so `check` already has a cursor of its own, and `verify` is renamed to `check` from that worktree
- **THEN** the rename succeeds, keeps the later cursor per group, and an alias `--alias verify` on any role is refused as held by `check`
