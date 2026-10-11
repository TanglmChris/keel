## Why

Issue #257 (rtl_ppa_prj via rtl_ppa_flow, from TanglmChris/rtl_ppa_prj#218, 2026-10-06): the owner set three standing authorizations for that repository, and `authorize:` can hold none of them exactly. `push` cannot be limited to branches, so "only the coordinator pushes `main`" lives in a document; closing an issue is not in the vocabulary at all; and cleaning a session's own scratchpad has no name. The owner decided on 2026-10-11 to add all three and to have the write guard enforce the push branch.

## What Changes

- `push:<branch glob>` limits the push authorization to branches matching one of the declared globs; it may be declared more than once. A bare `push` keeps today's meaning, and declaring both forms is refused.
- When any `push:<glob>` is declared, the Claude write guard checks every `git push` a `Bash` call runs, whether or not a task is active, and refuses one whose target branch matches no declared glob, or whose target it cannot determine, naming the explicit form to use.
- `issue-close:<owner>/<repo>` authorizes closing an issue on that repository; declaration only, carried to `--doctor` and the capsule as `issue:` is.
- `cleanup:scratch` authorizes removing temporary worktrees and run output under the session's own scratchpad after checking they are merged and unused, never branches or another session's files; declaration only.

## Capabilities

### Modified Capabilities
- `keel-standing-authorization`: three new forms, and a push scope that is enforced rather than only carried.
- `keel-touch-write-guard`: a `git push` check on `Bash` calls, independent of any task manifest.

## Impact

`src/core/config.js`, `bin/keel.js`, `plugins/keel/scripts/pretooluse-guard.js`, `plugins/keel/hooks/hooks.json`, `scripts/validate_plugin.py`, `README.md`, `keel/config.yaml` (comments only), two published specs, and the changelog. Codex keeps its `manual` guard capability; this adds no Codex enforcement.
