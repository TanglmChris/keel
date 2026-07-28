# the-gate-reads-what-it-promises

## Why

Two open defects share a shape: a structure is read differently from how it is documented, and the gap is invisible until it misfires.

- **#29** — `parseTasks` gives a task every line up to the next task or end of file, and a `##` heading does not stop it. So `## Invalidates` and `## Expectation Coverage` are appended to the last task's open `Evidence` field. An unfilled-slot token quoted in either section makes that Evidence non-concrete, and the gate then reports a task whose Evidence is fine. Worse, `invalidation-phrase` requires the searchable wording in double quotes while the concreteness test rejects an angle-bracket token outside inline code — so an entry quoting wording that contains one can satisfy neither arrangement. #16 made this common by requiring Invalidates to quote exactly the kind of prose that carries such tokens.
- **#30** — `task-complete` passes a task whose Evidence `Contract` anchor is still `pending`, reporting nothing. `anchoredFingerprint` returns null for a non-digest value and the comparison is simply skipped, so the drift guarantee the protocol states unconditionally holds only for tasks that recorded an anchor. A task can be implemented against one contract, have its Touch or Verify rewritten mid-flight, and complete clean, purely by never running `task-start --record`.

5.3.7 closed #30's inference path, but an explicitly named unrecorded task still passes.

## What Changes

- A task body ends at the next task **or the next `##` heading**, so a change-level section is never read as the last task's field. The `--record` anchor search uses the same extent.
- `task-complete` refuses a task whose `Contract` anchor holds no compiled fingerprint, naming `task-start --record`. Recording the anchor becomes a precondition of completion rather than an optional convenience, which is what the protocol prose already claims.

## Impact

- `src/core/task-contract.js`, `src/core/gates.js`
- `scripts/validate_plugin.py`
- Specs: `keel-task-capsule`, `keel-core-gates`
- `AGENTS.md`, `assets/bootstrap/AGENTS.md` and the shipped schema where they state the affected rules

## Non-goals

- No change to what `## Invalidates` or `## Expectation Coverage` must contain. #29 is that they are read in the wrong place, not that they ask for the wrong thing.
- No change to `task-start`, which may legitimately run before any anchor exists.
