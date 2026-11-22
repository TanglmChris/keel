## Context
- F1 — mapRecord returns early for empty renames before deriving direct, while wakes derives the same participants directly from the group. Basis: Keel #552 and src/core/chat/store.js.

## Goals / Non-Goals
Expose identical canonical participants in unread, group peek and show. Keep original records, cursors, and wake policy.

## Decisions
- D1 — Move derivation of direct participants ahead of the empty-rename fast path. Continue to canonicalize and deduplicate through current rename mapping and only project for direct groups. Basis: existing rename projection and issue #552.
- D2 — Verify all requested public surfaces with both absent and populated rename maps, ordinary direct messages, no-wake and ordinary group messages, and original durable bytes. Publish a patch via the repository gate and provide evidence for Kaiwu public consumer acceptance. Basis: delegated request and standard publication authority.

## Risks / Trade-offs
Public JSON gains the existing direct field consistently. No storage migration or recipient inference at the downstream layer is required.

## Open Questions
None.
