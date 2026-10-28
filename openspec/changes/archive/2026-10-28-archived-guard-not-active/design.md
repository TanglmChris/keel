## Facts

- F1 — `guardStatus` (`src/core/guard.js`) returns `archived` when the manifest's change directory is gone and the lexically last `openspec/changes/archive/<date>-<change>/tasks.md` shows its task checked (#491 D1). `plugins/keel/scripts/pretooluse-guard.js` makes the same test and then allows every write.
- F2 — Under `completed` (task checked, change live) the hook still denies product writes; under `drifted` and `invalid` it fails closed. Those manifests still need `keel guard clear` or a reauthorization.
- F3 — Measured 2026-10-28 with keel 5.214.0 (`/opt/homebrew/bin/keel`) on a fixture whose `keel/guard.json` guards `demo#1.1`, checked in `openspec/changes/archive/2026-10-28-demo/tasks.md`: `keel guard status` reads `Status: archived`; `keel shift check` exits 1 with `task-in-progress: keel/guard.json: a task's write guard is still active`; `keel context` with `AGENTS.md` stamped 5.100.0 prints `deferred while a task's write guard is active`, and `ask before running it` once the manifest is moved away.
- F4 — The three readers are `check` in `src/core/shift.js`, `protocolRefresh`'s `deferred` in `src/core/context.js`, and the adopt loop in `bin/keel.js`, each testing `fs.existsSync(.../keel/guard.json)`.

## Decisions

- D1 — `guard.js` exports `guardHolds(repo)`: false when `guardStatus(repo).status` is `absent` or `archived`, true otherwise. The three readers in F4 use it in place of the existence test.
- D2 — `keel shift check`, when `keel/guard.json` exists and does not hold, adds the note "keel/guard.json guards <change>#<task>, which is checked and archived, so it enforces nothing; `keel guard clear` removes it", and no item.
- D3 — Not changed: the `task-in-progress` wording for a manifest that holds, the `completed` and `drifted` handling, and `keel guard status` itself.
