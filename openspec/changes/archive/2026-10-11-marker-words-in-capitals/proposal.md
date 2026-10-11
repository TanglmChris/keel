## Why

Issue #271, seen on 2026-10-11 while completing `chat-ack#1.1`: `keel gate task-complete` refused an `M1.green` Evidence line that read "With `--ack` on post and todo, …", reporting the unfilled slot `todo`. The word was the name of a `keel chat` record kind, and the line was otherwise concrete. The unfilled-slot test matches its marker words in any case, so ordinary lowercase prose — "a todo", "the placeholder text" — reads as a slot. Attended, it costs one edit; in an unattended run it is a false stop that ends the cycle.

## What Changes

- The marker words `TODO`, `TBD`, and `PLACEHOLDER` read as unfilled only when written in capitals. The same words in lowercase or mixed case are prose.
- Angle-bracket slots, `<…>`, stay unfilled whatever their content, and inline code still exempts every form.
- The `non-concrete-verify` diagnostic states the capitals rule instead of saying "the word placeholder".

## Capabilities

### New Capabilities

### Modified Capabilities
- `keel-task-capsule`: the unfilled-slot token set is stated, with marker words in capitals only.
- `keel-core-gates`: the Reauthorizations shape rule refers to that set instead of listing a lowercase `placeholder`.

## Impact

`src/core/task-contract.js`, `scripts/validate_plugin.py`, two published specs, and the changelog. A task whose field carried a lowercase marker word and was refused before now passes; nothing that passed before is refused.
