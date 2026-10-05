## Context

Feedback rtl_ppa_flow gathered from rtl_ppa_prj sessions on 2026-10-05, in three batches.

## Facts

- F1 — `OWNER_RULE` in `src/core/chat/notice.js` says when to write `@owner`, but not what to do with a message that mixes status and risk.
- F2 — `renderProtocol` in `src/core/context.js` says "leave the diff for the owner to commit". AGENTS.md says "leave the diff uncommitted, because committing it is a separate action".
- F3 — The coverage report in `src/core/gates.js` compares only entries whose claim cites `F/D/A/Q<n>` (`CRITICAL_ID`), and its message does not say so.
- F4 — `Fails with:` takes one literal, by design: it is a prediction recorded before the run.

## Decisions

- D1 — A risk or decision is sent as its own message with `@owner`. Status stays unmentioned, so a notification always means something to act on.
- D2 — The protocol line follows AGENTS.md's wording: the authorization covers running the refresh, and committing it is a separate action.
- D3 — The coverage report names `D<n>`, `F<n>`, `A<n>`, or `Q<n>` and gives a cited example. Whether `E<n>` should count stays with #239.
- D4 — `Fails with:` stays one literal (owner's choice on 2026-10-05). The skill advises a literal every red of the check shares.
- D5 — Catalog pitfalls carry the date and source they were observed with, like the existing ones.
