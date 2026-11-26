## Decisions

- F1 — An ended Claude session is eligible only through its existing role binding, presence and addressed record. The Claude waker skips every managed Codex role. The two host paths operate on separate roles.
- D1 — Start managed delivery, attempt eligible Claude wakes and persist the wake outcome before waiting for the managed receipt. Run shift hand-over and patrol after both. A later tick must observe an already recorded successful wake even when the earlier tick is still waiting for Codex.
- D2 — Keep each host's existing retry and ownership checks. This change addresses independently assigned work. The user-owned choice of a restricted result submission path and production handover of the same task remain with issue #544.
