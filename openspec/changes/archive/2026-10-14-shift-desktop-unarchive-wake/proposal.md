## Why

Issue #326. 5.131.0 added a step to the desktop self-shift recipe: before the clear, dismiss every PR bound to the session with `unbind_pr` until `get_status` reports none, so the app's auto-archive leaves the cleared, idle session for its wake. The long-gap test on 2026-10-14 showed that the step does not do that. After one `unbind_pr` (#330), `get_status` read `bound: false`; 3 min after the clear the AutoArchiveEngine archived the session anyway, "PR merged", listing all 20 PRs the session ever had. The step's stop condition cannot see the set the engine archives on, so it reports success while doing nothing. The archive also came right after the session was focused and the app refreshed its PR checks, not on a sweep tick, so the exposure is not "until the next sweep" either.

What did work is the fallback: the wake unarchived the session, the app rebound the same worktree on its branch, and the send was delivered. The owner chose on 2026-10-14 to fix the recipe first.

## What Changes

- The desktop `ready --wake` recipe drops the dismiss step and goes back to four steps: Remote Control off, the one-shot wake task, the rename, the clear.
- The wake prompt makes the unarchive its main path rather than a fallback: it first calls `get_session` on the session, and when that reports it archived, calls `unarchive_session` before `send_message`; a send still refused as archived unarchives and sends once more. It says which path it took. The recipe says why: the app's auto-archive can archive the cleared session before the wake (#326), and an unarchive brings back the same worktree.
- The unattended line names `mcp__ccd_session_mgmt__get_session` and `mcp__ccd_session_mgmt__unarchive_session` beside `set_remote_control`, and no longer `mcp__ccd_pr__unbind_pr`.
- `self-shift` covers the four steps again.
- The docs, the README vocabulary, and the `keel/config.yaml` comment follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop recipe loses the dismiss step; the wake unarchives first.
- `keel-standing-authorization`: `self-shift` covers four steps.

## Impact

`src/core/shift.js`, `keel/config.yaml`, `README.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, both published specs, and the changelog.
