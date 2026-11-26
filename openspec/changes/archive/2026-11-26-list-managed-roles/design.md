## Decisions
- D1 — Enumerate the repository's local registration files, including parked and malformed rows. Use the effective park marker and current binding. Return stable role ordering, per-row state, recorded worktree, thread and socket. An invalid row is diagnostic and never eligible for dispatch; expose no claim bodies or prompts.
- D2 — Operate offline without locks, mailbox initialization, host probes or dispatch. An empty registry yields an empty array. This describes recorded identity only; liveness and writer ownership need independent verification.

## Alignment
Kaiwu requested the read-only inputs and fields in #577, with production validation delegated to Flow. The response envelope and diagnostic codes are implementation choices. No permission, resource or dispatch changes.
