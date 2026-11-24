## Why

The #544 native probe proved the original Codex turn can retain a typed usage failure across restart. It also observed an old background tool writing after the turn failed. Keel needs an explicit read of the original turn and terminal inventory before any recovery can reason about that state.

## What Changes

Add opt-in native observation to the managed Codex delivery receipt query. Report exact-turn result and a separate background-terminal inventory observation without loading, modifying or dispatching a thread.

## Capabilities

Extend `keel-portable-task-execution` with managed Codex observation.

## Impact

A read-only Codex CLI option and its docs. The default portable task query and the local receipt read continue to work offline. Automatic failover stays out of this slice.
