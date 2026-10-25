## Why

Issue #473, approved by the owner on 2026-10-26. `keel tick` runs each due patrol as `keel patrol --repo <worktree> --since-last --notify --json` and passes no `--issues`. Without that list the patrol routes no issue update to the roles `issue_roles:` names, and every `keel chat wait --issue <n> --closed` stays unchecked. The patrol says so in one line of its own output, which the tick discards.

kaiwu-ip moved its coordinator patrol to `keel tick` on 2026-10-22 (kaiwu-ip#399). From then on no `issue_roles` update was routed and no issue wait was checked. It was found on 2026-10-25, when someone asked why a session waiting for an issue to close was never woken (kaiwu-ip#429). Commit waits need only git, which the tick has, and were unaffected.

## What Changes

- **The tick fetches issue state with `gh` when something needs it** (owner, 2026-10-26). Something needs it when `keel/config.yaml` declares a readable `issue_roles:` route, or when a chat group holds an open `issue #<n> closed` wait. The tick then lists the repository's most recently updated issues, and asks for each waited issue the list left out. It passes the result to every patrol it runs in that step as `--issues`. When nothing needs it, the tick runs no `gh`.
- **A failed fetch is said, once.** When `gh` is missing, not logged in, or fails, the tick prints that issue checks are not run and why. It says it again only when that state changes, as it already does for quota. Whatever it did read is still passed.
- **`keel --doctor` shows whether issue checks are running.** It reads the tick's last issue state and prints `issue checks` as running, or not running with the reason.

This departs from the quota decision of 2026-10-25 (#456 D4: Keel runs no command to obtain quota). That decision stands for quota. For issues the owner chose on 2026-10-26 to have the tick run `gh` itself.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/tick.js`, `bin/keel.js` (the doctor line), `scripts/validation/shift.py`, `scripts/validation/registry.py`, the README in both languages, `docs/cli-team.md`, the `keel/config.yaml` comment, the published spec, and the changelog.
