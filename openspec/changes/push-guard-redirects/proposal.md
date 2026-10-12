## Why

Issue #286 (rtl_ppa_prj flow session, 2026-10-12): with `push:flow-*` declared, `git push --dry-run origin HEAD:refs/heads/flow-guard-probe 2>&1 | tail -1` was refused as pushing to `2>`. The push guard's word splitter stops at `&` and `|` but does not know redirections, so `2>` became a refspec. Sessions habitually append `2>&1 | tail`, so in-scope pushes were refused — a false stop.

## What Changes

- The guard's shell reader drops redirections — `>`, `>>`, `<`, `2>`, `2>&1`, `&>`, `>&2`, `2>/dev/null` and the like — together with their target before reading `git push` arguments.
- A redirection that names its target by shell expansion still marks nothing, since the target is dropped, not read.

## Capabilities

### Modified Capabilities
- `keel-touch-write-guard`: a redirection is never read as a push target.

## Impact

`plugins/keel/scripts/pretooluse-guard.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
