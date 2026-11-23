## Context

[Dated baseline](../archive/2026-11-23-cross-harness-readiness-baseline/evidence/baseline.md) identified existing native records to reuse and missing host evidence. Keel #544 owns the full cross-harness and workflow change.

## Scope and contract draft

1. A logical task keeps one ID across executions. For chat-backed work, use the existing immutable todo ID. Carry the owner, worktree, goal and acceptance references and resolution authority. Keep Git SHA, native turn receipt and tool acknowledgment as evidence references where available.
2. An execution identifies a specific attempt and generation. Native session IDs are adapter references. Delayed or duplicate events from a superseded generation can contribute audit evidence, while only the current generation can advance projected state. Task status and results must stay retrievable without choosing an adapter in the caller.
3. Distinguish work waiting to run, running, waiting for review, waiting for resources, unknown effects and verified completion. Delivery acknowledgment and claimed completion are inputs. Completing the task requires evidence appropriate to the accepted work. Preserve project-only and open-work state if the projection cannot determine an outcome.
4. At a normal tick boundary, an executing task keeps its owner. Before moving to a new execution, verify the task and output checkpoint and that protected native work has finished. If usage is exhausted or the executor exits, reconcile the last known worktree and any pending effects, prove the old execution cannot still write, and consider only previously configured executors within the same authority, data and budget limits. No automatic replay while effects are unknown.
5. Default lightweight vs. heightened workflow is a separate application policy. Existing OpenSpec ownership, gates, review and selected tasks remain in force while the project transitions. An alternative evidence source must prove the same acceptance requirements for its own selected tasks.

## Verification slices

- Shared record and projection: use the same caller against native receipts with overlapping IDs, duplicate/late events and restart between durable writes. Preserve task identity and completed results and distinguish approval, resource wait and uncertain effects.
- Tick and recovery: prove one writer and one effective transition on real Claude and Codex. Include usage exhaustion during file writes and tool calls, unavailable candidate, disconnect during acknowledgement, late source completion and restart. Require proof of writer release before dispatching the next attempt.
- Risk policy and workflow: validate that newly selected ordinary work can progress without OpenSpec artifacts, and sensitive cases still require their accepted authority, verification and recovery checks.

## Unresolved native evidence

Choose the portable input/output schema only after identifying actual reliable receipts for Claude execution ownership, stopped writers and pending tools, and the matching Codex signals. Codex's writer protection is limited to the relevant native thread and does not fence the same worktree against a different harness. A cross-harness implementation must bind the protection to the shared resource or hold until independently verified safe. No execution task is selected from this draft.
