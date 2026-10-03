## Context

Issue #201 records the 2026-10-03 playground run. Cursors are one record id per member and group (`cursors/<role>/<group>`), and only `keel chat <group>` and `keel chat read` move them. The wake hooks deliberately move none, so a woken session that answers from its notice never marks anything read.

## Goals / Non-Goals

**Goals:**
- A record a member has answered stops appearing as unread for that member.

**Non-Goals:**
- Per-record read state. The cursor stays a single id.
- Making a hook or `keel chat notice` advance a cursor.

## Decisions

- **F1** — In the 2026-10-03 run, claude-a's cursor in `lab` stayed at `20261002T134239866Z-owner-9af8cd` through four replies, and its fifth notice listed five records addressed to it, four of them already answered. Basis: the playground's `cursors/claude-a/lab` and the Claude A session transcript.
- **D1** — When a post carries `reply_to`, Keel advances the poster's cursor in that group to the replied-to record after writing the reply. When `keel chat done <id>` closes a todo, Keel advances the closer's cursor to the todo. A cursor only moves forward, so a reply to an older record leaves later records unread, and a reply to a record already behind the cursor changes nothing.
  
  Basis: the owner chose "reply marks read" on 2026-10-03 over marking only the replied-to record, which would need per-record read state.

## Risks / Trade-offs

- Replying to a record also marks every earlier record in that group as read for the poster, including ones it never saw. The owner accepted this: a member answering a later record has, in practice, moved past the earlier ones, and the alternative changes the store's layout.
