## Why

Keel's completion and close gates hard-validate specific *forms* — the Review `Status` vocabulary, the `## Expectation Coverage` section, and the Findings ownership shape — but those required and accepted forms live only in the validators (`src/core/gates.js`, `src/core/context.js`), never in the author-facing surface: the `keel-spec-driven` tasks template and the `keel-task-capsule/v1` tasks instruction. An author who follows the shipped template and instruction is never told what the gate will accept, so a change hits an avoidable hard-stop at task-complete or change-close that is diagnosable only by reading source or deleting text until it passes.

GitHub issue #1 documents these as Cases B, C, and D, all still live on the current HEAD (5.2.0) and all hit during Keel's own dogfooding. They share one root cause: **the gate's hard-validation surface is disconnected from the authorization surface authors read.** One is also an internal-consistency defect: the accepted-`Status` regex `pass|passed|complete|completed|ok` is duplicated verbatim in `gates.js:379` (the gate check) and `context.js:72` (the "already reviewed" probe) — fix one, miss the other, and the context judgment silently diverges from the gate.

Issue #1 Case A (the overlay / `keel --help` / doctor naming `keel-*` skills a real install does not produce) is out of scope here: investigation showed it is a skill-install / delivery defect — `install_to_repo.py:skill_actions` sources the `keel-*` skills from a deliberately retired `dist/` directory, so `keel --init` installs zero of them — not a gate-versus-template mismatch. It moves to the install-family sibling change alongside issues #2 and #3.

## What Changes

Align each hard-validated form with the author-facing surface and remove the duplicated regex. All three cases are keel-owned code plus the `keel-spec-driven` schema assets.

- **Case B — Review.Status vocabulary.** Accept `done` into the accepted set (decided — aligns with OpenSpec's own `done`, lowest author friction). Enumerate the accepted `Status` tokens in the `keel-task-capsule/v1` template and the tasks instruction. Make the `semantic-review` error name the failing field and list the accepted tokens. Extract the accepted-`Status` regex into one shared constant consumed by both `gates.js` and `context.js`.
- **Case C — Expectation Coverage.** Add a `## Expectation Coverage` placeholder to the `keel-spec-driven` tasks template (with the `- None.` default and an `- E<n>: … Covered by: <task ids>` example), require and format it in the tasks instruction, and make the `expectation-coverage` change-close error carry a minimal format sample.
- **Case D — Findings forms.** Enumerate the accepted Findings forms in the template and instruction (`none` | a named OpenSpec/archive owner | `discard: <reason>`), state where a non-blocking note goes (a separate line, not `Findings`), and make the `finding-owner` error show the accepted forms.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: completion and close gate errors become field-named and carry accepted-form / format samples; the Review `Status` accepted set is defined once as a shared constant and now includes `done`.
- `keel-expectation-slice-evidence-gates`: the semantic-Review `Status` vocabulary, the Expectation Coverage requirement, and the Findings ownership forms are written into the task-capsule / tasks authorization surface, not only enforced by the gate.

## Impact

- Code: `src/core/gates.js` (field-named errors; shared Status constant including `done`; change-close and finding-owner format samples), `src/core/context.js` (consume the shared constant).
- Assets: `openspec/schemas/keel-spec-driven/templates/tasks.md` (`## Expectation Coverage` placeholder), the `keel-task-capsule/v1` template and tasks instruction (Status vocabulary including `done`, Findings forms enumerated).
- Validator: `scripts/validate_plugin.py` gains assertions that the template and instruction now surface the accepted forms and that the accepted-`Status` set is single-sourced (and includes `done`).
- Closes GitHub issue #1 Cases B, C, and D. Case A moves to the install-family sibling change.
- Folds into the held, unpublished 5.2.0; no separate version bump.

### Non-goals

- Issue #1 Case A (skill install / delivery) and issues #2 and #3 (openspec runtime / PATH / doctor honesty, guard cleanup on archive, archive↔sync idempotency) — the sibling install-family change.
- Redesigning the gate model or the task-capsule format beyond surfacing the accepted forms.
