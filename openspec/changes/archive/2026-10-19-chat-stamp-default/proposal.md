## Why

Issue #349 (rtl_ppa_prj coordinator `iecc-pm`, 2026-10-18): `--stamp` (#298 D3) puts Keel's clock into a message, but it is opt-in, so posts and replies written without it carry hand-typed times — one reply said "12:0x" when it was 12:50. That project expects every message to carry a time (its rule G19), so authors either remember `--stamp` every time or type the time themselves.

## What Changes

- `keel chat post` and `keel chat dm`, `--reply-to` included, stamp `[MM-DD HH:MM]` from Keel's clock by default; `--no-stamp` opts out, and `--stamp` stays accepted.
- A text that already opens with a `[MM-DD HH:MM]` stamp is not stamped again; `--stamp` with `--no-stamp` is refused.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: the stamp is the default.

## Impact

`src/core/chat/cli.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
