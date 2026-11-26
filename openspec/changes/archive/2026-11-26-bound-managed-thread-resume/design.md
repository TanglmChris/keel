## Decisions
- D1 — Use the installed native `excludeTurns` on the managed delivery and recovery resume requests. Both consume only metadata. Keep the same thread, settings and all native identity checks, including explicit refusal.
- D2 — Reproduce the prior frame limit in the public managed CLI and verify the same role and turn receipt are used on a duplicate dispatch. Onboarding's separate history audit is outside this change.
