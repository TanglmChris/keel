## Why

Issue #350 (rtl_ppa_prj coordinator `iecc-pm`, 2026-10-18): `keel patrol` exits 2 whenever it sent a notice, marked a wait met, nudged, or reported a change, and the coordinator's schedule wakes its model on exit 2. A pure state change — the remote tip moving, a role becoming active — or a notice already delivered to another role then costs a large-context model turn with nothing to do; on 2026-10-18 101 of 140 logged runs exited 2 (#356).

## What Changes

- Exit 2 means the coordinator has something to act on: a risk this run, or a wait of the patrolling role's own that is now met.
- New exit 3: patrol recorded or delivered something — a wait met for another role, a routed issue update, a nudge, or a reported change — and the coordinator need not act.
- `keel patrol --help` and the rendered host task document 3.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`: the exit status separates "act" from "state moved".

## Impact

`src/core/patrol.js`, `scripts/validate_plugin.py`, one published spec, the changelog. A host task rendered before this release does not name exit 3; re-render it with `keel patrol task`.
