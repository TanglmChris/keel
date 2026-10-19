## Why

Issue #393: the owner's end-to-end test of 5.164.0 on 2026-10-19 left keel-maint's CLI hand-off `pending` for over eight minutes after the session had ended its turn. 5.162.0 (#388) waits for the old session's job `state` to be `done`, but `state` is the host's label of the session's last message, not whether its turn has ended: a final reply that describes pending work leaves it `working` for good. The premise was inferred; measured, a session blocked on a question reads `status: waiting`, `state: blocked`.

## What Changes

- The hand-over decides on `claude agents`' `status` alone: a session gone, stopped, or `idle` has finished; `busy`, `waiting` and anything else wait. `state` is no longer read.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`: the CLI hand-over waits on the session's status.

## Impact

`src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md` and its zh-CN twin, one published spec, the changelog.
