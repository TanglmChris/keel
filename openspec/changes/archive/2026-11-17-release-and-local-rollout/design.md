## Context

- F1 — Candidate b03529b3 contains verified 5.229.0 product source and closed implementation changes; latest npm and GitHub release are 5.228.0 on 2026-11-17.
- F2 — The publish workflow lands the owner's same-repository PR only when exact-head full-gate passes, then publishes npm and creates its release. The agent does not merge.
- F3 — The default daemon loaded-thread list is empty before rollout; its inherited localhost:7890 proxy caused model connection failures. Current execution environment has no proxy and the identical isolated binary completed model work.

## Goals / Non-Goals

Publish 5.229.0, align installed CLI/plugins, repair default daemon connectivity, and notify kaiwu-ip last. Do not implement #527, upgrade unrelated dependencies, adopt desktop chats or silently trust changed hooks.

## Decisions

- D1 — Owner explicitly authorized publication, local CLI/plugin updates, old-proxy repair and notification to kaiwu-ip after all work passes on 2026-11-17. This includes necessary installation and an idle-service restart, not interruption of unrelated active work.
- D2 — Use repository-controlled landing and publication; verify npm availability and installed component versions. Existing candidate behavior tests are reused; run CI on the exact published head.
- D3 — Restart only after rechecking loaded sessions, using the current working environment without stale proxy. Prove a real completed model turn on the default endpoint. Changed hook definitions still require native trust review; installation alone is not enforcement.
- D4 — Send one concrete versioned update notice to the existing kaiwu-ip owner only after release, local version and host checks pass; request that repository's normal update/validation rather than editing its implementation.

## Risks / rollback

Registry read-side propagation can lag. Retain previous package and hook trust state; do not forge trust hashes. Service restart is refused while unrelated work is active. Any failure retains evidence and prevents the final notification. No material product choice remains open.

The default-host repair is independent of npm read-side propagation and may run while publication waits. Its real-host probe uses the already verified 5.229.0 source adapter; installed CLI agreement is still checked separately in 2.1 before downstream notification.
