## Context

#319 comment 6146019116 and the owner's decision of 2026-10-13. This is the counterpart of `shift-restore` (5.129.0) on the outgoing side. Not chosen: one name covering both sides. The outgoing steps clear a conversation, while the restore only reopens a view, and an owner may want the second without the first.

## Facts

- F1 — In round 2, the probe asked the owner before the four steps, reasoning that "clear and the scheduled task are outside `shift-restore`" (dm 20261013T125041945Z).
- F2 — After the clear, with `shift-restore` declared, the woken probe restored Remote Control and its title without asking (20:53:45, 20:54:11).

## Decisions

- D1 — `self-shift` joins `STANDING_AUTHORIZATION_ACTIONS` with no scope. A scoped form is refused as `unexpected-scope`.
- D2 — The desktop `--wake` hint ends with one of two lines. Declared: `Standing-authorized by \`self-shift\` in keel/config.yaml: take these four steps now, without asking.` Not declared: `Declaring \`self-shift\` under authorize: in keel/config.yaml lets a session take these four steps without asking.`
- D3 — The authorization does not make the decision to change shift. That stays with the protocol's task-boundary rule and the role's coordinator, as the resident protocol says of every standing authorization.
- D4 — This repository declares `self-shift`, by the owner's decision of 2026-10-13.
