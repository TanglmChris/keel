## Context

#142 reports a task class whose correct evidence is zero difference, and no `Verify` strategy that fits
it. The reporting repository worked around the gap by re-recording its contract twice — evidence that
the shape, not the criterion, was wrong.

## Facts

- **F1** — `evidence-first` is the only existing strategy without a red-green requirement, and it is
  scoped by an absence: "no meaningful red-green loop applies", stated in a `Reason:`. An A/B
  comparison is the opposite — a specific, stronger criterion — so filing it under `evidence-first`
  records "there was nothing to check" about the one task class with the most checkable criterion.
- **F2** — `Verify` already has exactly one place commands live: the `M<n>` checks. `Strategy:` and
  `Reason:` are the only non-check entries, and `verification()` filters them out by name.
- **F3** — the gates already read Git: `task-complete` compares the worktree against the dirty set
  `task-start` recorded. Resolving a ref is not a new class of dependency for them, and stays local
  and offline.
- **F4** — a task's `Covers` entries name `capability / Requirement / Scenario`, and a change's delta
  specs mark new behavior under `## ADDED Requirements`. The two are comparable without new syntax.

## Decisions

- **D1** — `Base:` and `Fields:` are fields beside `Strategy:`, and the A/B command is an ordinary
  `M<n>` check. #142 proposes a third field, `Command:`; taking it would put commands in two places,
  one of them outside the labelled evidence `task-complete` enforces (F2). What the check cannot say by
  itself is what it is compared against and on which fields, and those are the two fields.
- **D2** — `equivalence` requires no red, and says so in the vocabulary rather than in a `Reason:`.
  Its criterion is that base and head agree on `Fields:`. Unlike `evidence-first` it states what *is*
  proved, so no reason for an absence is owed (F1).
- **D3** — four refusals at `task-start`, each naming the way the shape can pass while testing
  nothing: no `Base:`; no `Fields:`, or a `Fields:` that resolves to an empty set; a `Base:` no git ref
  resolves; and a `Base:` resolving to the same commit as `HEAD`. The last is the one worth having:
  an A/B against yourself always agrees.
- **D4** — the escape-hatch guard is change-level and evaluated at `task-start`. An `equivalence` task
  whose `Covers` names a scenario under `## ADDED Requirements` is refused unless another task of the
  same change declares a red-green strategy and covers that scenario (F4). A task cannot prove both
  that behavior is new and that behavior is unchanged, and without this the strategy is a way to author
  a feature with no red anywhere.
- **D5** — artifact Evidence is `artifact <path> sha256:<digest>`, and the path must be inside the
  change's own directory. That is the inverse of the rule for a `Durable owner:` path, and for the
  opposite reason: a follow-up pointer must outlive the change, while an evidence artifact must travel
  *with* it, and a path outside the directory is one `openspec archive` will leave behind.
- **D6** — Keel checks existence and digest and reads nothing else. It does not parse the artifact, does
  not know what a field is, and does not compare anything: the claim that base and head agree is the
  author's, recorded before Review, exactly as `Fails with:` and `Detects:` are. What the digest buys is
  that the file Review reads is the file the author meant, which a retelling cannot offer.

## Alternatives considered

- **A1** — let `equivalence` satisfy any task, with no guard. Rejected by D4: the strategy's whole
  appeal is that it needs no red, which is exactly what makes it the first thing reached for by a task
  that should have one.
- **A2** — have Keel run the A/B itself. Rejected: it would make the gate non-local (a checkout of
  `base`), non-deterministic (whatever the command does), and slow, and it would put Keel in the
  position of judging a domain field set it cannot understand (D6).
- **A3** — allow an artifact path anywhere in the repo. Rejected by D5: archiving moves the change
  directory, and an evidence pointer that breaks on archive is worse than a retelling, which at least
  survives.

## Open questions

None.
