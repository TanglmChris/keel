## Why

Issue #297 (rtl_ppa_prj, 5.114.0, 2026-10-12): the ping-pong guard refused the coordinator's ninth post in `dm-iecc-pm--rtl-flow` after eight alternating messages over about 2.5 hours, each pair a different piece of work, and paged the owner through Slack. In a two-member direct group strict alternation is the normal shape of work, and "any other member's post clears it" cannot happen there. Issue #298: sessions write estimated times into message text that disagree with the record's own timestamp, and `keel chat --help` is an error. Owner decisions, 2026-10-12, recorded on both issues.

## What Changes

- Ping-pong counts only when the last `pingpong` messages fall within `limits.pingpong_minutes` (default 10) of the post, and only messages after the group's latest override.
- A first trip refuses the poster without calling the owner, naming `--not-a-loop "<why>"`. A post with that option is accepted, and the reason is recorded on it as `not_a_loop`. A trip after an override that no owner post has followed calls the owner as before and accepts no override. The refusal names what clears it, including in a direct group.
- `keel chat post` and `keel chat dm` take `--stamp`, which prefixes `[MM-DD HH:MM]` from Keel's clock.
- `keel chat --help` and `-h` print the usage.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: the loop guard's time window and override, `--stamp`, and `--help`.

## Impact

`src/core/chat/guards.js`, `src/core/chat/store.js`, `src/core/chat/cli.js`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
