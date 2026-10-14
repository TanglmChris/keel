## Why

Issue #316 (rtl_ppa_prj, 2026-10-13): the coordinator parks role `iecc-design` until the next release by archiving its desktop session. `keel patrol --nudge` kept nudging it over three old mentions, then reported `iecc-design has not answered 2 nudges` to the coordinator as a risk, and will keep repeating it. Nothing is wrong; the role is parked. Keel cannot see that a desktop session is archived, so it needs to be told. Owner, 2026-10-14: an explicit park command.

## What Changes

- `keel chat role --park <role> [--reason <text>]` records that a bound role is parked on purpose; `keel chat role --unpark <role>` ends it and summarizes what waited meanwhile. A park also ends by itself once a session runs as that role again.
- While a role is parked, `keel patrol --nudge` sends it nothing and reports no unanswered-nudge risk for it, and binding drift does not report it as unattended. The patrol's role line says `parked`, so a park and its end each show once as a change.
- A post, direct message, or todo that wakes a parked role tells the poster it is parked, since when, why, and by whom, instead of reporting it offline or naming a desktop wake step.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: a role can be parked, and posts say so.
- `keel-coordinator-patrol`: the patrol leaves a parked role alone.

## Impact

`src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/chat/drift.js`, `src/core/patrol.js`, `scripts/validate_plugin.py`, both chat docs, two published specs, the changelog.
