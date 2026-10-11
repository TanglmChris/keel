## Why

Issues #260 and #242 (rtl_ppa_prj, 2026-10-05/06). In a multi-session project, work moves only when the coordinator hands it out; on 2026-10-06 every role sat idle for over seven hours, `verify` waited on a commit that had landed at 00:16, and nobody noticed. Handoffs dropped their second step, and "a new commit appeared in issue #157" relied on someone watching. The coordinator's workaround, a session-scoped cron with a free-text prompt, expires and is host-specific. Owner decisions, 2026-10-11: a `keel patrol` command that posts its own notices, deduped against the chat; waiting conditions declared as chat records; #242's issue-label routing folded in; scheduling stays with the host.

## What Changes

- `keel chat wait <group> --commit <sha> [--remote <name>] [note]` or `--issue <n> --closed [note]` records what a role is waiting for; `keel chat waits [--json]` lists the ones not yet met. A wait wakes nobody.
- `keel patrol [--issues <file>] [--idle <duration>] [--json]`, run as the coordinator's role: marks each wait whose condition now holds as met and sends the waiting role a direct message; with `issue_roles:` declared in `keel/config.yaml` and `gh` output passed with `--issues`, sends each mapped role one direct message per issue update; lists each role's presence and open todos. It fetches nothing, schedules nothing, and writes nothing when nothing is new.
- Exit status: 0 when it wrote nothing, 2 when it sent a notice, 1 on an error, so a host scheduler wakes the model only when something happened.

## Capabilities

### New Capabilities
- `keel-coordinator-patrol`: declared waits and a host-scheduled patrol that notifies the roles whose conditions are met.

## Impact

`src/core/patrol.js` (new), `src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/config.js`, `bin/keel.js`, `keel/config.yaml` (comments), `README.md`, `scripts/validate_plugin.py`, a new published spec, and the changelog. Re-arming a schedule across shift changes is a later step, as the owner decided.
