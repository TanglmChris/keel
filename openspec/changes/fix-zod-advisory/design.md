## Context

- F1 — On 2026-11-17 npm audit reports GHSA-mrhx-c7xc-m3w5 for locked transitive Zod 4.4.3. The reviewed advisory identifies versions below 4.6.6 as affected; npm serves compatible 4.6.7.
- F2 — OpenSpec 1.14.0 declares zod ^4.4.3. Its schema/config modules accept arrays of requirements, scenarios, workflows and other user-controlled configuration; several are unbounded arrays. This establishes validation exposure, not an exercised remote exploit or unbounded-memory proof.
- D1 — Owner requested #528 repair and #526 tracker closure. Update only Zod to patched compatible 4.6.7 within the current OpenSpec dependency graph, with no new direct dependency, override, or OpenSpec upgrade. Basis: current owner instruction and F1/F2.
- D2 — Audit absence is the defect regression; dependency compatibility is separately proved by existing public OpenSpec validation and the full suite. Do not run destructive memory-exhaustion payloads or claim an exploit was demonstrated.
- D3 — #531 is a distinct authorized downstream lifecycle issue and will have its own OpenSpec owner. The next patch release can include both verified fixes; #527 remains deferred.

## Risks and boundaries

A dependency version alone is not compatibility evidence. Keep the OpenSpec version and every unrelated locked package unchanged. Stop on a wider dependency diff or changed schema semantics; do not use npm audit fix. Existing audit evidence is historical and stays in archives. Closure of #528 requires the patched package to reach the published/local install flow, not only an edited JSON file.
