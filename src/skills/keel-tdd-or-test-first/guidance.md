# keel-tdd-or-test-first — guidance

How to pick a strategy and which evidence form fits it. Every criterion is in `SKILL.md`; nothing here
decides whether a task may start, pass, or complete.

## Choosing from the Acceptance

Read the resolved Acceptance and ask what observation would make it false. The answer names the
strategy:

| The Acceptance says… | Strategy | What the first check shows |
|---|---|---|
| a defect someone observed is gone | `regression-first` | the defect, reproduced through the public interface before the fix |
| a new behavior exists that a check can call | `vertical-tdd` | one behavior absent, then present; the next check starts once this one is green |
| a generated or deterministic output stays as it is | `characterization` | the current output captured, then compared byte for byte |
| a large or structured output stays as it is | `snapshot-characterization` | a stored snapshot, compared on every run |
| a measured result does not move — a refactor, a move, a flow upgrade | `equivalence` | the A/B against `Base:` on the declared `Fields:` |
| an interactive surface behaves | `rendered-behavior` | the real rendered interface, driven the way a user drives it |
| a document, configuration, or diagnosis exists and says something checkable | `evidence-first` | the artifact or finding itself, named precisely enough to be wrong |

Right choices:

- "`keel lock release` frees a lease even when its notice cannot be posted" — a release failed in
  front of someone, so `regression-first`, and M1 replays that release.
- "`keel triage` admits an issue whose number is listed under `issues:`" — new behavior, so
  `vertical-tdd`.
- "the README names the new flag" — `evidence-first`, with a check that searches the README for the
  flag; there is no earlier state of it that a red would teach anything about.
- "the moved constraint file gives the same WNS, TNS, and cell count" — `equivalence` against the
  commit before the move.

Wrong choices, and why:

- `evidence-first` for a new CLI option because a red is slow to run. The option is new behavior; a
  slow red is a cost, and the strategy is about what can fail, not what it costs.
- `equivalence` for a change that also adds a scenario. New behavior is not unchanged behavior: the
  added part goes in a sibling red-green task, and `equivalence` covers what is meant to stay put.
- A lighter strategy because the change looks low-risk. Risk sets how many checks are worth writing,
  not whether the ones written can fail.
- A lighter strategy because a strong model is running the task. A strong executor produces
  confident work; a check that can contradict it is worth more there, not less.

## When a red adds information

A red tells you two things a green cannot: the check reaches the behavior at all, and the failure
it showed is the one the task exists to remove. Both matter most when the code and the check come
from the same reading of the requirement — a misreading shared by both passes green every time.

A red adds nothing when there is no honest one to show: a guard over behavior that is already
green, a version marker, an output fixed before the task. Those have their own forms below; a red
staged by breaking the code on purpose and then restoring it records the staging, not the check.

## Which evidence form pays

- `Fails with:` — when the red's text is predictable. Declare a literal every red of the check
  shares, such as the scenario label it prints.
- `Detects:` `mutation` -> `failure` — when a plausible wrong implementation exists that the check
  might not notice: an off-by-one at a boundary, a swapped condition, a guard that reads the wrong
  field. Apply the mutation by hand, run the check, record the failure as `M<n>.detects`, and revert.
  It is the one form a `(regression)` check can use to show it is not vacuous.
- `Measured:` — when Evidence quotes a number someone will rely on: a count, a size, a timing, a
  slack. The literal ties the number to the output it came from.
- `(regression)` with `deferred to C<n>` — when several tasks would each rerun the same full suite.
  Declare it once under `## Change Verify` and record it once under `## Change Evidence`.
- `artifact <path> sha256:<digest>` — when the output is too long to retell. Keep the file inside
  the change directory; the claim it supports is still written in the Evidence.

## A hardware example

A synchronous FIFO gains simultaneous read and write at full and at empty. That is new behavior, so
`vertical-tdd`; the boundary check carries `Detects:` with the mutation "full is computed before the
read pointer advances" and the failure "the full-and-read case drops a word". A later rename of the
same FIFO's signals and a move of its pipeline register, keeping cycle behavior, is `equivalence`
against the commit before it, with the testbench transaction log as `Fields:`.

Neither proves timing closure, CDC, reset, or security properties. Those are separate evidence, and
a matching lens under `keel/lenses/` names them.
