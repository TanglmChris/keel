## Why

One class of task's correct evidence is *zero difference*: a refactor, a move (the reporting
repository moved `(* keep_hierarchy *)` out of RTL into the synthesis flow), or a flow upgrade claiming
the measurements do not change. Red-green has no shape for it (#142).

- That repository's `move-keep-hierarchy-from-rtl-into-the-synthesis-flow` says "this one has no honest
  red" several times in its own `tasks.md`, and re-recorded its contract **twice** to get past the
  shape — tagging checks `(regression)`, editing `Fails with:`. Neither re-record was because a
  criterion was wrong. The criterion was right and had nowhere to live.
- The real criterion is an A/B: the same code path run once at `base` and once at `head`, compared
  field by field. It is **stronger** than red-green, because it catches the thing red-green cannot —
  a change that also, incidentally, moved a result. Keel had no place to express it, so it was prose.

And prose is where it stays: Evidence can only be a retelling. An A/B pairing or a sweep-coverage
summary *is* the machine output of one command, and retelling it into `tasks.md` made a 244-line
`tasks.md` mostly a transcription of test output — a transcription that can be wrong and that nobody
can re-check.

Neither part removes a check. Both take a check already being run and give it a shape that can be
validated.

## What Changes

- **`equivalence` becomes a first-class `Verify` strategy.** It declares `Base:` (a git ref) and
  `Fields:` (the compared field set) beside `Strategy:`, and requires no red. `keel gate task-start`
  refuses a missing or empty `Fields:`, a missing `Base:`, a `Base:` no git ref resolves, and a `Base:`
  that resolves to the same commit as `HEAD` — comparing a thing against itself is the shape of a
  passing check that tested nothing.
- **It is not an escape hatch from red-green.** An `equivalence` task whose `Covers` names a scenario
  from an `## ADDED Requirements` delta is refused unless another task of the same change declares a
  red-green strategy and covers that same scenario. Behavior that is new is not behavior that is
  unchanged, and a task cannot prove both at once.
- **Evidence may reference an artifact instead of retelling it.**
  `M2: artifact <path> sha256:<digest>` — `keel gate task-complete` checks the file exists and the
  digest matches, and Review reads the file. The path must live inside the change's own directory, so
  the artifact travels with the change when it is archived and the pointer cannot break.

## Capabilities

### Modified Capabilities

- `keel-task-capsule`: the `equivalence` strategy, its required declarations, its escape-hatch guard,
  and artifact-referencing Evidence.

## Impact

- `src/core/task-contract.js` — the strategy vocabulary, `Base:`/`Fields:` parsing, artifact Evidence.
- `src/core/gates.js` — the refusals at `task-start` and the digest check at `task-complete`.
- `AGENTS.md`, `README.md`, `src/skills/keel-tdd-or-test-first/SKILL.md` — where an author reads what
  the strategy is for.
- **Not adopted as proposed**: a `Command:` field beside `Strategy:`. `Verify` already has exactly one
  place commands live — the `M<n>` checks — and a second would be a fork: two places to look for what
  was run, one of them outside the labelled evidence the gate enforces. The A/B command is an `M<n>`
  check like any other, and `Base:`/`Fields:` are what the check alone cannot say.
