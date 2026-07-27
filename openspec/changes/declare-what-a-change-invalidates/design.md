## Context

`## Expectation Coverage` is the existing precedent and the model for this
change: a required tasks.md section, parsed by `expectationProblems` in
`src/core/gates.js`, closing each entry as covered by tasks, deferred to a
durable owner, or discarded with a reason. The new section reuses that shape
rather than inventing a second vocabulary, and differs in two ways: it is
checked at `task-start` rather than `change-close`, and each entry must carry a
searchable phrase.

## Goals / Non-Goals

**Goals:**

- Ask what a change invalidates while the answer is cheap to act on.
- Make the answer executable as a search, not a memo.
- Keep the check structural and the judgment with the agent.

**Non-Goals:**

- Judging whether the declared phrase is the right one, or whether the located
  text was updated correctly. Both are semantic and belong to review.
- Reaching outside the repository. Native agent memory shows the same rot and
  is how this was found, but Keel's protocol holds that memory is never
  authority and this change does not extend Keel's reach to it.
- Editing the consumer bootstrap, which is byte-wedged.

## Decisions

F1 — Nothing in Keel currently asks. `keel-review-checklist/SKILL.md` and
`keel-expectation-slice-evidence-gates/spec.md` contain no occurrence of
invalidation, obsolescence, or staleness; the three matches in
`keel-core-gates` concern execution-evidence drift, a different subject. Basis:
searched 2026-07-27, recorded in issue 16.

F2 — The cost of late discovery is recorded in the repository, not inferred.
`openspec/changes/archive/2026-07-27-honest-surfaces-and-owners/tasks.md` notes
a re-record when `AGENTS.md` entered Touch, and
`.../2026-07-27-touch-layering-and-repo-action/tasks.md` notes two. Basis: the
archived tasks files.

F3 — `taskStart` already loads the whole tasks.md as `selection.content`, which
`expectationProblems` consumes at `change-close`. The new check needs no new
parsing infrastructure and no capsule change. Basis: `src/core/gates.js`,
`taskStart` and `changeClose`.

F4 — The tasks template exists in two synchronized copies,
`openspec/schemas/keel-spec-driven/templates/tasks.md` and the
`assets/openspec/...` copy. Both must gain the section or a scaffolded change
fails its own first `task-start`. Basis: repository layout; the validator
asserts the copies agree.

D1 — The gate runs at `task-start`, not at `change-close`. Basis: accepted by
the user against the cheaper close-time alternative. The whole value is that
affected paths enter Touch before implementation; a close-time check finds the
same facts after the reauthorization it was meant to prevent. F2 is the
evidence that late discovery is the expensive case.

D2 — An entry must carry a searchable symptom phrase, not only a location.
Basis: accepted by the user. Issue 16's asymmetry is decisive — every miss was
a file that merely mentioned the behavior, and a location list can only ever
contain files the author already recalled, so a location-only entry reproduces
the failure it is meant to prevent.

D3 — Closure at `task-start` validates form, not completion. An entry reading
`Updated by: 2.1` is a plan at that moment, and the gate checks that the entry
is well-formed and closed in intent. Basis: completion cannot be asserted
before the task runs. The work is then structurally implied: when task 2.1
completes with those paths in its Touch, the update happened inside a gated
task. This is the accepted consequence of D1 without the second checkpoint.

D4 — `- None.` is legitimate and cheap. Basis: a required section an author
cannot honestly answer degrades into ritual, and most small changes invalidate
nothing; the same escape exists for `## Expectation Coverage`.

D5 — The section lives outside every task body, beside
`## Expectation Coverage`. Basis: the compact-v4 parser slices a task body to
the next task or EOF, so a trailing section is absorbed into the last task's
final field unless it is a `##` heading; keeping it a sibling heading also
keeps it out of the capsule fingerprint.

## Hidden Knowledge / Assumptions

A1 — Authors will write a phrase that actually matches the stale text rather
than a paraphrase. Basis: the phrase is most useful to the author's own later
search, so the incentive is aligned; but nothing structural enforces a match.
Resolve by: observing whether the declared phrases in the next few changes
locate their targets. Durable owner: the review step, which is where semantic
judgment already lives per this change's own spec.

## Coupled Iteration Contract

Not applicable. No task declares `Coupling: required`.

## Risks / Trade-offs

- A required section becomes ritual if authors cannot answer it. Mitigated by
  D4 and by asking at authoring time, when the answer is known.
- Checking only at `task-start` means nothing re-verifies at close that a
  declared update happened. Accepted under D3; the structural implication is
  the mitigation, and review remains the semantic backstop.
- Every existing change in flight gains a new failing gate. There are none in
  this repository at the moment, and the template change means new scaffolds
  are born compliant.

## Open Questions

None.
