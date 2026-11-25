## Why

The managed Codex mailbox scans roles sequentially and waits for each delivery subprocess. Issue #544 asks for proof that a slow or uncertain role cannot delay the first delivery of an independent healthy role.

## What Changes

Run the existing managed mailbox delivery path independently for each eligible role. Preserve delivery order, one in-flight attempt per role, claims, and stop-on-unknown behavior.
