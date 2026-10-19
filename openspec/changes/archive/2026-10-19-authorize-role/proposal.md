## Why

Issue #378 (kaiwu-ip, 2026-10-19): the team is organized by capability, one session per capability per IP (`kaiwu-design-iecc`, `kaiwu-review-iecc`, …), and the owner split standing authorization by capability. Only `push-protected` takes a role (`main@kaiwu-pm-iecc`). Every other scoped grant — `push:<glob>`, `issue:`, `issue-close:`, `cleanup:scratch`, `chat-reply:` — applies to every session. So the split can be written only as comments, and Keel cannot tell that a review session should not push a design branch. The owner chose on 2026-10-19 to do #378.

## What Changes

- Every scoped entry may end in `@<role>` or a role glob such as `@kaiwu-design-*`, with the meaning it already has on `push-protected`: only a session bound to a matching chat role gets that grant. An entry without one keeps today's meaning.
- What a session reads as authorized is filtered by its role: the capsule's inherited autonomy line, `keel context`, the chat-reply groups, and `keel --doctor`'s per-action lines.
- The Claude write guard applies `push:<glob>@<role>` to `git push`: a branch counts as allowed only for a session of a matching role. The push limit stays on for every session while any push entry is declared, so a session that no entry names is not left unlimited.
- `keel --doctor` lists, for each role bound in the repository, which scoped entries apply to it.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-standing-authorization`: a scoped authorization may name the roles it applies to.

## Impact

`src/core/config.js`, `plugins/keel/scripts/pretooluse-guard.js`, `bin/keel.js` (doctor), `scripts/validate_plugin.py`, `README.md`, one published spec, the changelog.
