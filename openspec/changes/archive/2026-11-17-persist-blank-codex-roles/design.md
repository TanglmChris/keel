## Context
F1 — #537 reports blank registered threads lost after about three minutes, with thread/read raising thread not loaded rather than returning notLoaded. Basis: https://github.com/TanglmChris/keel/issues/537, downstream report dated 2026-11-17; not yet locally reproduced.
F2 — 5.229.1 starts a thread and closes its connection before any turn. Basis: src/core/codex-host.js start path.
## Goals / Non-Goals
Verify delayed first use and preserve the exact owned identity. No production adoption, thread replacement, arbitrary RPC-error fallback or hidden model initialization turn.
## Decisions
D1 — Diagnose first using isolated fresh temporary repositories and owned threads, closing each observation connection; record delayed thread/read and exact-id thread/resume outcomes. Basis: owner-authorized kaiwu issue priority and #537 reproduction contract. No implementation before the persistence mechanism is verified.
## Hidden Knowledge / Assumptions
None.
## Coupled Iteration Contract
None.
## Risks / Trade-offs
Observation connections can change unloading; keep them closed during delay. Unknown identities remain unmodified. Model turns are not required for initial diagnosis; no paid warm-up or substituted role is authorized.
## Open Questions
None.

## Verified repair basis
F3 — An unnamed fresh role loses its rollout after disconnect; same-id resume fails. Native name/set and archive/unarchive each survive 190 seconds and resume the same ID with zero turns. Basis: 1.1 evidence/blank-loss.json and evidence/native-persistence-controls.json; Codex0.167.2. This resolves Q1.
D2 — Initialize each newly created owned thread with thread/name/set using the visible role name before reporting managed success, then verify read identity. Apply to start and handover successors. Basis: F3; native naming is one operation, avoids an archive lifecycle and invokes no model. Preserve permissions and use existing bounded RPC deadlines.
D3 — Persist the actual created ID in pending creation/handover evidence before initialization. If naming or validation fails, preserve pending state and refuse duplicate creation; do not reinterpret missing rollouts as recoverable idle or change existing lost registrations. Basis: existing ownership/unknown-outcome contract and #537.
D4 — Prove public initialization failure handling and delayed real first work before publishing5.229.2 and updating the authorized local installations. Basis: owner priority for formal kaiwu team deployment.
