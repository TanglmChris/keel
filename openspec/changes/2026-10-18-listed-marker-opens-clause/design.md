## Context

#362 offered three remedies: read nested and single-line forms alike, say only single-line is accepted, or name the entry read as prose. The first is the one that matches what the refusal already promises, and `reviewValue` already gathers a sub-list as one Findings value (#49), so only the opening rule is narrower than the format it reads.

## Facts

- F1 — `CLAUSE_OPENING` (`src/core/gates.js`) is `(?<=^|[\n.;:!?—–])[ \t]*`; both `RESOLVED_HERE` and `DISPOSITION_MARKER` use it, so recognition and the "marker present" scan agree (#144).
- F2 — `reviewValue` returns a nested Findings as `\n        - Resolved here: M1`; the `-` between the break and the marker fails the opening rule, and `findingOwnerIsDurable` finds no owner form, so the gate reports `finding-owner` (reproduced by `a-listed-marker-opens-its-clause` before the fix).
- F3 — `findingOwnerIsDurable` reads `Durable owner:` and `Discard reason:` without the opening rule, which is why the reporter's other change, whose nested items were a `Durable owner:` and a prose `Resolved here:`, passed.

## Decisions

- D1 — `CLAUSE_OPENING` accepts one optional list bullet (`-`, `*` or `+` followed by spaces or tabs) after its existing openings. Both scans keep sharing it, so they still agree; a word before the marker on a listed line (`- Not resolved here:`) still makes it prose.
- D2 — The refusal's sentence about openings adds "the bullet of a list item".
