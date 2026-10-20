## Context

Three read-only audits on 2026-10-20 compared README.md with the CLI and specs, the Chinese README and docs with the English, and the skills and protocol with the code. This change takes the protocol, code, and spec findings. The README and docs findings follow in the next change.

## Facts

- F1 — `src/core/task-contract.js` builds `prohibitions` with "must not continue to another task", "must not mark tasks complete", and "must not transfer Keel ownership", and sets `owner` to `keel-agent` when no `Owner:` is authored. The capsule is hashed whole, so either change moves every fingerprint.
- F2 — `src/core/drift.js` (#342) recognizes a compiler change. It recompiles the task as committed in the anchor's recording commit; if that reproduces today's fingerprint while the anchor names an older Keel version, it says "re-record with `--record`; the evidence stands". `contract-drift-diagnosis` covers this mechanism generically.
- F3 — `STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js` has 13 names, and `SCOPED_AUTHORIZATION_ACTIONS` has 5.
- F4 — `NO_WRITE_MODES` in `task-contract.js` refuses diagnose-only unless its Touch is `none`.
- F5 — No code implements a hook completion gate. `plugins/keel/hooks/hooks.json` declares only SessionStart and PreToolUse, and the chat hooks only post notices.
- F6 — `assets/bootstrap/AGENTS.md` is 1389 bytes against `BOOTSTRAP_BLOCK_BYTE_BUDGET = 1400`, so the authorization sentence has to be paid for inside the block.

## Decisions

- D1 — Remove the three prohibitions, and emit `owner` only when authored. Rely on F2 for the drift: each live task re-records once with `--record`, and its evidence stands.
- D2 — Each surface states what the code does:
  - diagnose-only takes `Touch: none`;
  - `Verify` checks prove Acceptance;
  - commit and push need the task's, the owner's, or `keel/config.yaml`'s authorization;
  - the strategies include `equivalence`;
  - Findings may read `Resolved here:`;
  - coupled tasks have no retry counting;
  - no hook gates completion.
- D3 — `keel --help` lists `keel patrol` and `keel tick`, and `keel chat help` lists `post-tool-use`. The overlays state the `keel openspec` instruction once instead of twice.
- D5 — The bootstrap pays for the longer authorization sentence by shortening its projection sentence, and the budget stays at 1400.
- D4 — A new scenario, `surfaces-agree-with-code`, holds D1–D3. It compiles a task and checks the capsule, reads each surface for the corrected statements, and derives the authorization names from `STANDING_AUTHORIZATION_ACTIONS` to check the published spec.
