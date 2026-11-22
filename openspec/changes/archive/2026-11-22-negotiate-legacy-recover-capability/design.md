## Context

- F1 — Keel 5.231.0 sends experimental runtimeWorkspaceRoots for legacy recovery but does not negotiate the extension unless a reviewer or effective policy snapshot exists. Basis: native 0.167.2 error reported on #550 and src/core/codex-host.js.

## Goals / Non-Goals

Restore already supported same-ID, same-endpoint recovery. Keep active/writer refusal, policy and claim handling unchanged. No desktop or production action.

## Decisions

- D1 — Request experimentalApi for recover, leaving other calls and native verification unchanged. Basis: F1 and the reported production reproduction; no new user policy decision.
- D2 — Verify real 0.167.2 using an empty-auth isolated worktree and an original legacy registry with no reviewer or policy, and then publish the verified candidate using repository-controlled full-gate. Basis: delegated narrow fix and standing release authorization. Desktop/follow-through remains #550.

## Risks / Trade-offs

Native servers still decide whether the handshake or the resume is allowed. The fix does not bypass an active source or native writer. Real desktop remains separate.

## Open Questions

None.
