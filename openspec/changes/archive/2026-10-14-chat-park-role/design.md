## Context

Issue #316 offered an explicit park, a shift-note park, or inference from inactivity; the owner chose the explicit command on 2026-10-14. Inference was not chosen because it would also silence a role that is stuck rather than parked, the case #331 just made visible. A shift note filed without `--wake` already stops resume nudges and is left as it is.

## Facts

- F1 — `nudgeRoles` (`src/core/patrol.js`) considers every bound role except the patroller and escalates after two unanswered unread nudges (#307 D2).
- F2 — `roleDrift` (`src/core/chat/drift.js`) reports a bound role with unread records or a waiting note and no presence for two hours (#301), which the patrol's `--since-last` snapshot reports whenever its text changes.
- F3 — Presence is written only by the role's own session (hooks and `keel chat` commands), so a presence time later than the park means a session ran as that role since.

## Decisions

- D1 — A park is `<store>/parked/<role>.json` with `role`, `reason`, `by` (the parking worktree's role, or null), and `at`. `--park` refuses a role no worktree is bound to, so a typo does not park nobody. Any member may park or unpark any role; it grants nothing.
- D2 — A park is in effect while the role's presence `last_active` is absent or not later than `at` (F3). A session that runs as the role ends it without anyone remembering to unpark; the file stays until `--unpark` and is then simply inert.
- D3 — `--unpark <role>` removes the file and prints how many addressed records wait for the role and since when, so the work that accumulated is summarized once.
- D4 — `nudgeRoles` skips a role whose park is in effect: no unread, shift, or resume nudge and no escalation; its saved nudge state is kept. `roleDrift` leaves it out of the unattended list. The patrol's role row carries `parked: true` and its snapshot entry reads `parked, N open todos`.
- D5 — After a post, dm, or todo, each role the record wakes whose park is in effect gets one line: `<role> is parked since <at>[ by <by>][: <reason>]; this waits until it is unparked or its session runs again — route anything urgent through the coordinator.` Such a role is left out of the offline and desktop-wake lines. `--json` adds `parked: [{role, at, by, reason}]`.
