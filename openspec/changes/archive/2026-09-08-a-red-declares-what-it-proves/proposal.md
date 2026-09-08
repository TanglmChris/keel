# A red declares what it proves

## Why

Red-green discipline forces the expensive half — write a check that fails before
the implementation exists — and `keel gate task-complete` enforces it: a missing
`M<n>.red` refuses the task. But nothing checks that the red failed **because of
the thing under test**. A red that fails for an unrelated reason is shape-perfect.

Two measured cases in this repository (issue #116), both caught by eye, neither by
a gate:

- `a-declared-dependency-is-resolved` (5.47.0): the first red **passed**, because
  the fixture had not cleared `PATH` and `run_openspec` found the author's own
  `openspec`. A green red. The author noticed the result looked wrong.
- `a-quoted-span-is-not-a-claim` (5.43.0): the first two fixtures contained no
  wording the checker would refuse. They failed, honestly recorded as `.red`, for
  an entirely different reason. Exposed only when a third fixture errored.

The protocol already says the words — `keel-tdd-or-test-first` reads "fail, for
the right reason" — but that is a sentence written for a person, not a criterion.
The most expensive half of the discipline is fully enforced, and all of its value
rests on a condition nothing examines.

## What Changes

- A check may declare the failure signature its red must show, as a trailing
  `Fails with:` clause naming a literal string in inline code.
- When declared, `task-complete` requires that string to appear in the check's
  `.red` Evidence, so the recorded red carries a line of the failure output
  rather than only a conclusion.
- When not declared, nothing changes: every existing task keeps its behavior.
- `task-start` reports which red-green checks declared a signature and which did
  not, at the moment the author is about to write the failing check rather than
  after the checks have been run.
- A declaration that cannot produce a red — on a `(regression)` check, or under a
  strategy with no red-green requirement — is refused by name rather than ignored.

## Impact

- Affected specs: `keel-core-gates`, `keel-task-capsule`
- Affected code: `src/core/task-contract.js`, `src/core/gates.js`,
  `scripts/validate_plugin.py`
