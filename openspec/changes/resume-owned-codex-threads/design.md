## Context

- F1 — #531 records two explicitly managed roles on Codex 0.167.2. After PM's first completed turn its metadata became notLoaded; Keel rejected the result and even repeated delivered records. Explicit same-thread thread/resume followed by a second real turn succeeded.
- F2 — Current deliver validates id/cwd but checks idle/active before persisted claims, and has no owned-thread resume path. The operation lock already reloads the registry before host mutation.
- D1 — Owner requested priority repair of #531 while kaiwu waits. Resume only the recorded, identity-verified managed thread, on its recorded endpoint and within the existing role lock. No replacement thread, desktop adoption, approval bypass or permission expansion. Basis: current owner instruction and #531 boundaries.
- D2 — After identity verification, delivered claims return without resume; pending/unknown claims refuse before resume. For new work only, notLoaded triggers thread/resume with threadId and serviceName keel, followed by identity/state validation. Active waits; failed/invalid resume refuses before turn/start. Hand-over does not gain an implicit resume path.
- D3 — Stand-in public CLI tests cover edge/refusal cases; actual two-role acceptance must show a first completed PM turn, verified unload, execution-role result and a second completed PM turn on the identical thread. Source-only first RPC acceptance is insufficient.

## Risks / boundaries

Keep one connection for resume and turn/start. Preserve durable pending claims, lock cleanup and existing worktree/socket validation. User asked to prioritize #531; #528 remains independently implemented and its final suite runs on the shared candidate. No unresolved material product choice remains.

- F3 — The real owned cold resume exceeded the existing five-second RPC deadline without starting a turn; the server finished loading the same thread and a subsequent verified delivery succeeded. Recovery therefore needs a bounded load-specific default.

Cold resume uses a 15-second default while an explicit --timeout remains authoritative for every RPC. Existing connection/status defaults stay five seconds. The model-free drain parent allows 40 seconds, covering initialize/read/resume/turn deadlines and process overhead; this changes no permissions, thread identity or uncertain-claim replay policy.
