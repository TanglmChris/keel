## Why

Issue #160. A tasks file has two readers of "where does this end", and they disagree about one line.
`parseTasks()` ends a task body at `/^\s*##\s/`, so an indented `  ## …` line inside a task ends the
task and every field after it is dropped. `sectionBody()` ends a change-level section at `/^##\s+/`, so
the same line inside `## Invalidates` is read as text and the entries after it are still judged.

5.26.0 kept the section's strict test on purpose — the tolerant one silently drops section entries —
but that decision lived only in prose. No fixture plants an indented `##` in a section, so a later
"tidy-up" to one pattern would pass the suite. And the task side still has the tolerant test: a dropped
required field surfaces as a refusal, but a dropped field with a documented default (the autonomy
boundary, the stop conditions) is replaced by that default without a word.

The owner decided on 2026-09-27 to make both strict, in the direction that drops nothing.

## What Changes

- **One heading test, column zero only**, shared by `parseTasks()` and `sectionBody()`. An indented
  `##` line is text in both: inside a task it joins the field that is open, inside a section it is not an
  entry and does not end the section.
- **The section half is asserted**: `section-boundary` plants an indented `##` in a tail-position
  `## Invalidates` and `## Expectation Coverage`, each followed by an unclosed entry, and requires the
  entry to be refused.
- **The task half is asserted**: a task whose body carries an indented `##` line before later fields
  compiles with those fields.

## Capabilities

### Modified Capabilities

- `keel-task-capsule`: a heading is a `##` line at column zero, for task bodies and change-level
  sections alike.

## Impact

- `src/core/task-contract.js`, `src/core/gates.js`, `scripts/validate_plugin.py`.
- A task in a live change whose body contains an indented `##` line compiles to a different capsule
  after upgrading, so its recorded fingerprint no longer matches and the next gate stops for
  reauthorization. No `tasks.md` in this repository, archived or live, contains such a line.
