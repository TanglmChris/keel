## Context

Issue #307 and the owner's decision of 2026-10-12 recorded on it. Parts 2 (quota thresholds) and 3 (risk-only escalation) follow in their own changes. Not chosen: host `send_message` by session id; a separate `ready --self` marker.

## Facts

- F1 — rtl_ppa_prj's hand-written patrol nudges idle sessions over addressed unread (> 30 min, once per 2 h), context ≥ 50 % (once per 6 h), and self-shift notes; its first version counted all group unread and nudged over week-old chatter (#307).
- F2 — A direct message from a sender other than the role wakes the role's Claude session through its signal file (`wakes` in `src/core/chat/store.js`); `keel-patrol` (5.115.0) and `keel-shift` (5.114.0) already write such records.
- F3 — Keel cannot observe a session's context share; the host can (`get_usage` in the Claude desktop app).
- F4 — A note filed by `ready --wake` is the shift a role started itself; a note filed without it may be a coordinator parking a role on purpose (#293, #307).

## Decisions

- D1 — `keel patrol --nudge [--context <role>=<percent>]... [--shift-at <percent>]` (default 50) considers every role in `roles.json` except the patrolling role. A role is idle when its presence `last_active` is missing or older than `--idle`.
- D2 — Waiting records are the role's waking unread records whose sender is not `keel-patrol`, `keel-shift`, or `keel`. Unread nudge: an idle role with waiting records, the oldest older than `--idle`, not nudged for unread in the last two hours: `<role>: <n> record(s) addressed to you have waited since <created>; read them with \`keel chat unread\`.`
- D3 — Shift nudge: an idle role with no waiting records and no waiting note, whose `--context` figure is at least `--shift-at`, not shift-nudged in the last six hours: `<role>: your context is at <p>%. Change your own shift: \`keel shift check\`, then \`keel shift ready --wake "<note>"\`, then clear this session. A session serving Remote Control cannot be cleared: turn it off, clear, then turn it back on.`
- D4 — `ready --wake` writes `Self-initiated: this shift armed \`keel shift ready --wake\`.` into the note's header. Resume nudge: a waiting note carrying that line, older than `--idle`, with no `keel-shift` record for the role since it was written, not yet nudged for this note: `<role>: your previous shift left a note at <time>; run \`keel context\`, then \`keel shift resume\`.`
- D5 — Each nudge is a direct message from `keel-patrol` with ref `keel-patrol-nudge`; the state lives in `<chat root>/patrol/nudges.json` (`{ <role>: { unread, shift, resume } }`). Output lines read `nudged <role>: unread|shift|resume`, `--json` adds `nudges`, and a run that nudged exits 2.
- D6 — `keel shift check` does not count unread records from `keel-patrol` or `keel-shift` as loose ends: found when the scenario's `lint`, nudged to change its shift, was refused by `check` over that nudge.
