## Decisions
- D1 — A registry without a deliveries field is a supported initial/legacy state. Only a missing field or a missing own key in a valid claim map establishes absence. Present unusable claim values are ambiguous; an invalid map or conflicting record identity is reported explicitly.
- D2 — Read and dispatch share receipt classification. Under the role lock, refuse an unknown or invalid claim before contacting the host, preserve its exact bytes, and retain identity verification for a valid duplicate and fresh dispatch.
- D3 — Test against real CLI calls, native turn counts and persisted registration bytes. Kaiwu owns production migration and its timer.

## Alignment
The downstream evidence and existing no-replay contract specify the decision. No new public state or automatic repair is needed.
