## Why

An upper-layer client that queries a Keel todo cannot tell whether its native delivery was acknowledged without branching into the Codex CLI. Issue #544 calls for the same task query across execution hosts.

## What Changes

- Add a host-neutral delivery observation to the existing todo JSON query, using a durable managed receipt when one exists.
- Keep the recorded chat closure, actual task completion, and any recovery decision independent of delivery.
