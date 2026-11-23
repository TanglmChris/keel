## Context

- D1 — Compare the existing host integrations and distinguish host documentation, current installation observations, dated real-host behavior, and stand-in test results.
- D2 — Keep source coordination and tracked progress independent of an execution instance. #544's contract requires tick-boundary switching in the normal case and effect reconciliation, old writer fencing, and policy-preserving recovery for resource failure.

## Readiness questions

For each candidate examine busy/idle, persistent identity, native queue, writer release, approval boundary, working directory, progress and exhaustion. Show where OpenSpec is currently wired into the flow, so downstream implementation can identify equivalent evidence for the optional workflow.

## Ownership

The task, dispatch and recovery implementation remains owned by [Keel #544](https://github.com/TanglmChris/keel/issues/544). The source of truth for an active implementation must be its own task contract.
