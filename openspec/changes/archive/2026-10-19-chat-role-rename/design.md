## Context

#376 proposed moving the binding, every group membership including `dm-*` groups, and per-role state to the new name, and registering the old name as an alias. Group membership and direct groups are derived from records (`join`/`leave`) and from the direct group's name (`dm-<a>--<b>`), and records are never rewritten or deleted (the mailbox requirement). The chat archive branch and the Slack bridge carry those records elsewhere.

## Facts

- F1 — `groupState` builds members from `join`/`leave` records; `directMembers` parses them from a `dm-` group's name; `wakes` reads `from`, `mentions`, `assignee` and the direct members (`src/core/chat/store.js`).
- F2 — `changeMember` refuses direct groups (fixed members), so no record can move a direct group's membership.
- F3 — Per-role state lives under the chat store root: `cursors/<role>/<group>`, `presence/<role>.json` and `<role>.sessions.json`, `parked/<role>.json`, `signal/<role>`, `shift/<role>.md`, `shift/history/<role>-<stamp>.md`, `shift/segments/<role>.json`, `shift/transcripts/<role>/`, `shift/queue/<role>.json`, `patrol/<role>.json`, `patrol/log/<role>.log`, the `<role>` key of `patrol/nudges.json`, and the `woken.<role>` key of `tick/state.json`.
- F4 — kaiwu-ip had already run `keel chat role --set <new>` in each worktree and added some new names to groups, so a rename has to work when `<new>` already exists.

## Decisions

- D1 — The rename is a record of identity, `renames.json` (`{ "<old>": "<new>" }`) under the chat store root. It resolves through chains: `a`→`b` then `b`→`c` maps `a` to `c`. A rename whose `<new>` is a former name of `<old>`'s chain, or whose `<old>` is already a former name, is refused.
- D2 — `readLog` maps `from`, `assignee`, each `mentions` entry, and the `target` of `join` and `leave` records through the renames, and gives a direct group's records `direct`, its mapped members. `wakes` and `signalTargets` read `direct` when present. The record files are unchanged; a renamed sender shows under its new name.
- D3 — `aliasMap` includes each former name, so `@<old>` resolves to `<new>`; `addAlias` of a former name is refused as held by `<new>`. `setRole(<old>)` is refused naming `<new>`. `currentRole` maps an override through the renames.
- D4 — Who: a worktree whose role is `<old>` or `<new>`, or `KEEL_CHAT_ROLE=owner`. Refused when `<old>` is unknown (bound nowhere, no member file, member of no group, no state), when `<old>` equals `<new>`, when either name is invalid or `keel`, and when both are bound to worktrees, since that merges two live identities.
- D5 — State moves as in F3. For a single-file state, `<old>`'s file moves only when `<new>` has none, and otherwise stays and is reported. Cursors keep the later id per group. History files and transcripts move unless a file of the same name exists. Segments concatenate. The patrol log is appended. The nudge state's `<old>` key moves when `<new>` has none. `signal/<old>` and `tick/state.json`'s `woken.<old>` are removed, since they describe the old session. `members/<old>.json` aliases are merged into `<new>`'s.
- D6 — The rename reports each moved and each kept item, and every line of `keel/config.yaml` and `keel/chat.json` in the current worktree that names `<old>` as a word, so the owner edits them. Keel does not edit them.
- D7 — `keel chat role --rename <old> <new> [--json]`.

## Risks

- Another machine sharing the groups through the archive branch or Slack does not see `renames.json`, which stays local like the rest of the store's state. Discard reason: every team that uses roles today runs on one machine. A second machine can run the same rename.
