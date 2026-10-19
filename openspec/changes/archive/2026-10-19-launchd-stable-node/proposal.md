## Why

Issue #387 (2026-10-19, Keel 5.161.0): `keel tick task` printed a plist whose first `ProgramArguments` entry was `/opt/homebrew/Cellar/node/26.0.0/bin/node`, the `process.execPath` of a Homebrew node, which is the versioned Cellar directory. After `brew upgrade node` that path is gone and launchd runs nothing: every 300 s fails silently, hand-offs and wakes stop, and nothing reports it. The plist's `PATH` also carried a Claude plugin cache directory of one release (`…/keel-marketplace/keel/5.149.0/bin`), stale after the next update. `keel chat wake add` and the chat bridge write their LaunchAgents from the same `process.execPath`.

## What Changes

- The three LaunchAgents Keel prints or writes (`keel tick task`, `keel chat wake add`, the chat bridge) name the `node` found on `PATH` that is the same binary as the running one, so a symlink such as `/opt/homebrew/bin/node` is used instead of its Cellar target; when none matches they keep `process.execPath`.
- Their `PATH` leaves out any directory inside a Claude plugin cache.
- `keel --doctor` reports each `dev.keel.*` LaunchAgent in the LaunchAgents directory whose first program argument does not exist, naming the file and the command that re-creates it.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`: Keel's launchd jobs name a node that outlives an upgrade.

## Impact

`src/core/launchd.js` (new), `src/core/tick.js`, `src/core/chat/wake.js`, `src/core/chat/lifecycle.js`, `bin/keel.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, one published spec, the changelog.
