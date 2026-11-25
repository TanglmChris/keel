## Decisions

- D1 — One asynchronous delivery loop per registered role with addressed work. Each loop waits for its current record, then follows existing deduplication, waiting and stop decisions. Separate role loops use the existing public deliver command and its exclusive role lock. A failed child yields an error for that role and does not cancel the remaining loops.
- D2 — Both tick and drain await the complete result. Preserve deterministic role ordering in output and leave the non-Codex stages and their relative order in place. Keep one subprocess at a time per dispatched role, the existing per-child timeout and output bound. Do not quote a child error message containing the command and mailbox text.
