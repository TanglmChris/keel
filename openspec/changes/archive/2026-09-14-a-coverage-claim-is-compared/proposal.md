## Why

`## Expectation Coverage` carries the only global assertion in the protocol: **every
expectation has an owner**. It has three closure forms, and until now only two of them
were checked. `Durable owner:` must name a path that exists or a `https://…` reference
(5.51.0, #100). `Discard reason:` must give a reason. `Covered by: <task>` — **80% of
all closures in the repository that measured it** — was checked only for "does that task
exist and is it checked". What the entry *claims* was never compared against anything.

Issue #133 ran the comparison by hand over 24 archived changes: 146 E entries, 117 of
them `Covered by:`. Of the 117, **42 cite expectation identifiers and 6 of those are
wrong**:

```
2026-09-13-count-stages-from-worst-path-only       E3 -> F4   F4 is in no task's Covers
2026-09-13-respect-liberty-lexical-structure       E3 -> F3   F3 is in no task's Covers
2026-09-13-restore-schema-immutability             E3 -> A1   A1 is in no task's Covers
2026-09-13-search-fmax-over-delay-targets          E3 -> F3   F3 is in task 1.1, E3 names 2.1
2026-09-14-fingerprint-the-metric-code             E4 -> A2   A2 is in task 1.1, E4 names 2.1
2026-09-14-model-broadcast-ports-as-ideally-driven E1 -> F2   F2 is in task 2.1, E1 names 1.1
```

Two of the six are the same fact stated twice in opposite directions: one E entry says
`F4` is covered by task 1.1 while another defers `F4` to a tracker issue, and task 1.1's
`Covers:` names neither. The archive records two contradictory beliefs about the same
identifier and passed every gate holding both.

**All six are archived.** They passed `keel gate change-close` and a semantic Review. They
are not findable by reading: the operation that finds them is a set difference between two
lists of identifiers that are already structured, in the same file, which is exactly the
work a person will not do by eye and a gate does for free.

## What Changes

- `keel gate change-close` compares an `## Expectation Coverage` entry's cited
  `F<n>`/`D<n>`/`A<n>`/`Q<n>` identifiers against the `Covers:` of the task its
  `Covered by:` names, and refuses a mismatch. The refusal names the entry, the
  identifier, and **where that identifier actually is covered** — free information,
  already in the same file, and the difference between "your claim is wrong" and "your
  claim is wrong, here is the task you meant".
- The gate reports how much of the section it compared: how many `Covered by:` entries
  cited an identifier and how many cited none. A `pass` that says nothing about its own
  reach is read as "checked", and for the repository that filed this, 58% of the section
  is structurally outside any comparison.
- **Citing identifiers stays optional.** An entry that names none is not refused and is
  not nudged; some expectations are prose ("documentation and skills follow the behavior
  changes above") and numbering them would be a ritual. What changes is that an entry
  which *does* cite is now held to it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-expectation-slice-evidence-gates`: a coverage claim naming identifiers is compared
  against the capsule it names, and the gate reports how much of the section it compared.

## Impact

- `src/core/gates.js` — the comparison and the report inside the existing
  `expectationProblems`.
- `scripts/validate_plugin.py` — one new scenario.
- **Not adopted from the report**: its second suggestion, that an identifier must not
  appear on both a `Covered by:` and a `Durable owner:`/`Discard reason:` entry. Run over
  83 archived changes it produced **one hit, and that hit was a false positive** — an
  entry citing an identifier precisely to say which half of it *was* covered, so that the
  half it owned was unambiguous. The comparison above already catches the report's own
  contradiction case, by the route that does not need to guess why an identifier was
  mentioned. Detail in design.md, D3.
