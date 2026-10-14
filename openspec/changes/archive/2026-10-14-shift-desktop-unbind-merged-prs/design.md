## Context

Issue #326, and the test of 2026-10-13 22:37–22:41 recorded in this session (log lines from `~/Library/Logs/Claude/main.log`, the run of scheduled task `keel-maint-self-shift-326-test`). Not chosen: asking the owner to turn off auto-archive (it is the owner's setting and helps other sessions), and relying on the unarchive fallback alone (the engine releases the worktree when it archives, so an unarchive is not a clean recovery).

## Facts

- F1 — 2026-10-13 22:02:22: `[AutoArchiveEngine] Archiving local_27bd271b-… (PRs #318,#321,#322,#323,#325; worktree remote-control-107a82) (PR merged)`, 3 min after that session's clear. The wake's `send_message` was refused: the session was archived.
- F2 — The engine held sessions only while "a turn is in flight" or "live work … (remote_control)". The recipe turns Remote Control off, and a cleared session has no turn in flight.
- F3 — 2026-10-13: all 20 merged PRs bound to `local_a4222dad-…` were dismissed with `unbind_pr` before its clear (22:37:53). The log has no AutoArchiveEngine line for it up to the wake (22:41:35), and the wake task reported `isArchived: false` and delivered on the first send. One sweep window only; a longer gap is not yet measured.
- F4 — `get_status` reports one bound PR at a time and `unbind_pr` takes its URL; with nothing bound, `get_status` says `bound: false`.
- F5 — A desktop clear keeps the session id (`Clearing session local_a4222dad-…`, then the wake resumed the same id).

## Decisions

- D1 — The desktop hint gains step 2, after Remote Control is off and before the task: call `get_status`, and while it reports a bound PR, dismiss it with `unbind_pr` and call `get_status` again, until it reports none. The step says why (an idle session whose bound PRs are all merged is archived by the app's auto-archive and its worktree released, #326), and that the new shift can bind an open one again with `bind_pr`. Every bound PR is dismissed, not only merged ones, because the `land` job can merge an open one inside the gap.
- D2 — Step 4 (rename) says the title marks the session as between shifts until the woken session renames it back; the words "archived copy" go.
- D3 — The wake prompt adds: if `send_message` is refused because the session is archived, call `unarchive_session` on it, then send, and say which path it took.
- D4 — The unattended line names `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_pr__unbind_pr` and `mcp__ccd_session_mgmt__unarchive_session` under `permissions.allow`, and `shift-restore` under `authorize:`.
- D5 — `self-shift` covers the five steps; the hint says "these five steps". It reaches only this session's own bound PRs.
