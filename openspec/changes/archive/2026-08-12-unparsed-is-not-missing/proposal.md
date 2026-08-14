## Why

`criticalAuthority()` in `src/core/task-contract.js` reports a Covers reference to a `D<n>`/`F<n>`/`A<n>`/`Q<n>` critical statement as `Missing` whenever its zero-match branch is reached, whether the identifier never appears in `design.md` at all, or it appears but not in the one exact line shape the regex accepts (`D2 — text`, no leading `-`/`**` decoration). Reproduced directly against the current tree (2026-08-12, 5.37.0): a `design.md` containing `- **D2** — Keep one shared parser.` and a `tasks.md` Covers entry of `D2` fails `keel gate task-start` with `Missing Covers critical statement: D2.`, even though D2 is present. The message sends the author to write a statement that already exists instead of to the one-line shape fix that would resolve it. `Invalidates` and `Expectation Coverage` diagnostics already distinguish "absent" from "present but wrong shape" and name the required shape in the message (issue #49, items already fixed); this is the one diagnostic in the same family that still collapses both into `Missing`.

## What Changes

- `criticalAuthority()`'s zero-match branch checks whether the reference token appears anywhere in `design.md` as a whole word. If it does not, the message stays `Missing Covers critical statement: <ref>.` If it does, the message changes to a new `Unparsed Covers critical statement: <ref>.` wording that states the required line shape (`<ref> — one-line statement`, at the start of the line, no other decoration).
- No change to what shape is accepted, to the scenario-matching branch (`specAuthority`), or to any other diagnostic.

## Capabilities

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the "Critical statements carry minimal provenance" area gains a requirement that an unresolved critical-statement Covers reference is reported as missing or unparsed according to whether the identifier is textually present in `design.md`.

## Impact

- Affected code: `src/core/task-contract.js` (`criticalAuthority`).
- Affected tests: `scripts/validate_plugin.py` (new regression scenario for the unparsed case; existing missing/duplicate/resolved scenarios must keep passing).
- No protocol, schema, security, or acceptance-shape change. No new dependency. Diagnostic text only.
