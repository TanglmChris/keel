## Context

F1 — Projection currently requires `--authorize subagent` and infers implementation from a declared tier. Basis: src/core/projection.js on 5.85.0.
F2 — The delegate precondition checks only guard-file existence. Basis: delegationRefusal; guardStatus already verifies live task authority.
F3 — Goal activation and read-only helper byte-stability checks are separate public surfaces. Basis: src/core/goal.js and helper.js.
F4 — This host prohibits proactive spawning unless user or applicable AGENTS/skill explicitly requests delegation. Repository rules cannot override it. Basis: current host developer policy; runtime evidence must distinguish permission, projection and actual launch.

## Goals / Non-Goals

Goals: implement the owner's #190 decision without extra permission for execution organization.
Non-goals: scheduling, ownership transfer, cross-runtime delegation, changing goal activation or automatically choosing models.

## Decisions

D1 — Read-only helper projection needs no subagent activation authorization or delegation declaration; it remains report/evidence only. Basis: owner's explicit #190 decision.
D2 — Add optional `--subagent-mode helper|implementation` to lifecycle projection. This is the current agent's posture selection, not a user permission. Default is helper; legacy `--authorize subagent` with a resolved tier retains the old delegate posture for compatibility. Explicit helper overrides that legacy inference. Basis: unambiguous write boundaries and compatibility.
D3 — Implementation posture requires a selected implementation task with nonempty Touch and guardStatus active, matching change/task/fingerprint. Tier declaration becomes optional metadata. Invalid declared tiers still refuse implementation, never unrelated read-only help. Basis: existing task authorization and guard boundaries, owner's decision not to constrain organization preference.
D4 — Existing capsules keep their schema and fingerprints; no automatic default tier is invented. Projection carries implementation posture and optional metadata outside the durable capsule. Basis: upgrade must not drift every active task solely because the organization policy changed.
D5 — Align source and installed schema, skills, overlays, bootstrap and resident protocol. State host limits distinctly and never claim CLI projection spawned or enforced a helper. Goal activation remains explicit. Basis: #190 acceptance.
D6 — Verify positive and negative CLI behavior, old behavior unrelated to delegation, and a real bounded read-only helper only where host authorization exists. A declined/unavailable host launch is recorded as a limitation, not worked around. Basis: F4 and #190 evidence requirements.

## Hidden Knowledge / Assumptions

None. Scope and policy follow the owner decision; no private precedent store is available.

## Risks / Trade-offs

Legacy tier configurations remain accepted; callers can choose helper posture explicitly. A matching manifest proves the guard pointer is valid, not that a host hook enforced writes. Host limitations remain authoritative. Native goal skill edits clarify trigger scope rather than expanding skill capability.

## Open Questions

None.
