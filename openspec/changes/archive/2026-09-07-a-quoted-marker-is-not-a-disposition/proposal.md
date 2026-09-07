## Why

`Review Findings` is free prose by design — the protocol says so — and in a repository whose subject *is* the protocol, that prose routinely names the markers themselves. A finding that says the resolution-marker grammar is the topic writes that marker in backticks, and the gate reads it as a disposition.

Measured against the real gate, with a fixture whose Findings mentions the marker inside inline code and then records a genuine disposition:

- mention plus a real `Durable owner: https://…` → `task-complete` returns `fail` with `finding-resolution-evidence`
- mention plus a real `Resolved here: M1` → the same failure

The false marker does not merely add noise. `RESOLVED_HERE` matches globally and the loop stops at the first claim it cannot resolve, so one quoted mention **eclipses every real disposition in the block**. A finding correctly owned by a tracker issue is reported as a resolution with unusable evidence — a diagnostic about the wrong disposition entirely.

The repository has already decided this question once. 5.42.0 established that an inline-code span holds quoted material rather than an assertion, and `withoutInlineCode()` in `src/core/task-contract.js` is that rule. It was applied to the `keel --check` tasks.md rules and to the unfilled-slot scan, and never to the finding dispositions.

It cost two refusals in one task while authoring 5.50.0 — the second while writing the finding that reported the first.

## What Changes

- Inline-code spans are blanked before `Review Findings` is scanned for `Resolved here:`, `Durable owner:`, `Discard reason:`, and `Discard rationale:`. Offsets are preserved, so a marker's position and everything the existing rules read after it are unchanged.
- The refusal names the token it actually read, so an author who wrote the marker's words as an ordinary sentence clause sees what the gate took them for instead of being told they wrote nothing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-core-gates`: a disposition marker is recognized where it is written as a marker, not where it is quoted.

## Impact

- `src/core/gates.js` — the Findings scan and one diagnostic.
- `scripts/validate_plugin.py` — one new scenario.
- Deliberately **not** changed: a `Resolved here:` whose evidence does not immediately follow it still fails. Measured across 388 real dispositions in six repositories, the form authors actually write is prose, then the marker, then the evidence — `one thing, fixed in this task. Resolved here: M1` — and that already passes, with or without prose after the evidence. The original report of this issue claimed the narrow capture was itself the defect; the measurement does not support that, and widening it would reintroduce exactly what 5.36.0's narrowness prevents. The improved diagnostic is what that half of the report actually needed.
