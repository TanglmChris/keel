## Why

Issue #255, part of #250 (rtl_ppa_prj, 2026-10-05): the coordinator writes a status digest twice a day by hand. `keel chat <group> --since` and `keel chat search` exist, but nothing condenses what changed across groups.

## What Changes

- New `keel chat summary --since <time> [--group <g>] [--json]`. Per group, it lists by sender what each role posted since then. That covers todos opened, with whether they are still open, and todos closed. A superseded record is folded into the record that superseded it. Records still waiting on an acknowledgement are listed with who has not given it.
- The summary is built from the records' structure, not by a model. It is deterministic and offline, and it reads without marking anything read.

## Capabilities

### Modified Capabilities
- `keel-cross-host-mailbox`: a structural digest of what changed since a time.

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `scripts/validate_plugin.py`, `README.md`, the published spec, and the changelog.
