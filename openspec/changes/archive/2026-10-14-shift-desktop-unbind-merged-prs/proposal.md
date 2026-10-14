## Why

Issue #326. The first self-shift on 5.130.0 lost its wake. Keel did not archive the session; the desktop app's auto-archive did. The engine archives an idle session whose bound PRs are all merged, and it releases the session's worktree to the pool. On this repository every PR a maintenance session opens is merged by the `land` job, so that is the normal case. The recipe leaves the cleared session idle for about three minutes before the wake, which is exactly the state the engine archives.

The mitigation was tested on 2026-10-13. Before the clear, every merged PR bound to the session was dismissed with `unbind_pr`. Between the clear (22:37:53) and the wake (22:41:35), `~/Library/Logs/Claude/main.log` has no AutoArchiveEngine line for the session, and the wake's `send_message` was delivered on the first try (`isArchived: false`). The owner then asked, on 2026-10-14, to build that step into the recipe.

Step 3 of the recipe also says the rename is "so its archived copy can be told apart". A desktop clear keeps the same session id, so there is no separate archived copy, and the wording invites archiving the session.

## What Changes

- The desktop `ready --wake` recipe gains a step between turning Remote Control off and creating the task: dismiss every PR bound to this session, reading them with `get_status` and dismissing each with `unbind_pr`. The step gives the reason (#326), and says the new shift can bind an open one again with `bind_pr`. The recipe then has five steps.
- The rename step says why it is there without "archived copy".
- The wake prompt gains a fallback: if `send_message` is refused because the session is archived, call `unarchive_session` on it, then send, and say which path was taken.
- The unattended line names `mcp__ccd_pr__unbind_pr` and `mcp__ccd_session_mgmt__unarchive_session` beside `set_remote_control`.
- `self-shift` covers the five steps, including dismissing this session's own bound PRs.
- The docs, the README vocabulary, and the `keel/config.yaml` comment follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop recipe's dismiss step, the rename reason, and the wake fallback.
- `keel-standing-authorization`: `self-shift` covers the dismiss step.

## Impact

`src/core/shift.js`, `keel/config.yaml`, `README.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, both published specs, and the changelog.
