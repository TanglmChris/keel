## Context

- F1 — The #550 field report measured matching turn IDs with different full projections on 0.167.2 and 0.171.0. Matching versions produced equal full digests. [Evidence](https://github.com/TanglmChris/keel/issues/550#issuecomment-7097102219).
- F2 — App Server `thread/read` and paginated full `thread/turns/list` do not resume the thread. `thread/unsubscribe` removes the caller's subscription. Source shutdown follows an idle grace period, 60 seconds by default in [0.171.0](https://github.com/openai/codex/blob/rust-v0.171.0/codex-rs/core/src/config/mod.rs#L4007). A native writer refused acquisition during this interval in #550.

## Goals and scope

Address both failures using the approved role, existing endpoints, original plan fields and native writer protection. Production routing and host configuration remain deployment-owned.

## Decisions

- D1 — During inspection and again before durable intent in apply, cold-read target identity and compare every page of the full persisted history against the source snapshot or exact plan. Keep the existing verification after release and resume. Use the existing digest without removing data fields or enforcing a version number. Revalidate the source immediately before intent to catch progress made during target preflight.
- D2 — After journaling intent and receiving `unsubscribed`, poll the original source with non-subscribing reads under a single monotonic deadline. Require the original ID/worktree and locally `notLoaded`. Continue polling only while idle. Default to 75 seconds for this phase, giving the native 60-second grace period time to finish shutdown, while an explicit existing `--timeout` bounds this phase as well as individual RPCs.
- D3 — Target writer protection remains authoritative after the observation. Timeout, loss of observation or native rejection after intent keeps the original registration and an inspectable unknown outcome. Keep explicit reconciliation with an already loaded target and no automatic replay, rollback or override.

## Risks and trade-offs

Cold history reads may add I/O. A long or pinned native listener may exceed the wait window, leaving an unknown transition for operator reconciliation. A source can reacquire after its observation, so the native writer refusal remains mandatory.

## Open Questions

None.
