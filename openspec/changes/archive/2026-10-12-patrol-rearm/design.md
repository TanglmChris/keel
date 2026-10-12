## Context

Issue #260 and the owner's decision of 2026-10-12 (remind, do not schedule; a machine-level LaunchAgent was not chosen because it would change the "Keel schedules nothing" protocol line).

## Facts

- F1 — `configMap(repo, key)` in `src/core/config.js` reads a block of `name: value` lines with word keys and one-token values.
- F2 — `keel context` carries `role` (#245), and the SessionStart hook prints the projection from it on startup, resume, and compaction, including after `/clear`.
- F3 — `keel shift resume` prints the previous shift's note and is what a new shift runs first.
- F4 — `parseSince` accepts `90s`, `15m`, `2h`, `3d`.

## Decisions

- D1 — `patrol:` holds `role:` (a chat role name) and `every:` (`<n>s|m|h|d`). Missing or malformed values are reported in `keel context` warnings and remind nobody.
- D2 — When the bound role equals `patrol.role`, `keel context` sets `patrol: { role, every }`; the projection prints `- patrol: role <r> runs \`keel patrol\` every <every>; a session's schedule ends with the session, so re-create it with the host if this session has none, and wake the model only on exit 2.`; `keel shift resume` appends the same sentence to its text and `patrol` to its JSON.
