## Context

Issue #34 asked for a loop that pulls issues and merges them unattended. Three layers shipped
before this one: host permission declarations (L0), standing authorization for actions (L1/5.5.0),
and a precedent store for decisions already made (L2/5.6.0). This layer is the one that decides
whether an arriving issue becomes work at all.

The owner's own rule blocks the obvious route. `keel-decision-precedent` requires that a precedent
answer a recurrence within a materiality category and never move a decision out of the list that
requires asking. "Should this issue be done" sits squarely in that list. So no amount of recorded
history can make triage automatic — which is the rule working, not a gap in it.

## Goals / Non-Goals

**Goals:**

- A repository declares, once and in a tracked file, which issues may enter the pipeline without
  being asked about.
- Evaluating that declaration is local, offline, deterministic, and model-free, like every gate.
- An unattended run has an explicit boundary: what it may do, where it must stop, and what it may
  never do.
- A repository declaring nothing admits nothing, exactly as at 5.6.0.

**Non-Goals:**

- Scheduling. `/loop`, cron, and CI triggers are host capabilities.
- Merging a pull request.
- Any network access from Keel.
- Deciding which issues *should* carry the admitting label. That is the owner's curation, one issue
  at a time, and is the whole point of using a label.

## Decisions

- **F1** — `keel-decision-precedent` requires a precedent to answer a recurrence within a
  materiality category and forbids moving a decision out of the must-ask list
  (`openspec/specs/keel-decision-precedent/spec.md`, shipped 5.6.0). Basis: read 2026-07-29.
- **F2** — The nine materiality categories are listed at
  `src/skills/keel-align-expectations/SKILL.md:14` and include "irreversible cost" and "a dependency
  or architecture commitment". Basis: read 2026-07-29.
- **F3** — `src/core/config.js` reads `keel/config.yaml` with a hand-rolled line-oriented reader and
  already serves `fast_check`, `authorize:`, and `precedents:`. Basis: shipped 5.5.0 and 5.6.0.
- **F4** — `.claude/settings.json` allowlists `Bash(gh:*)`, so the agent can fetch issue attributes
  without a permission prompt. Basis: written this session; read 2026-07-29.

- **D1 — Triage admission is an owner declaration, never a precedent inference.** Basis: F1 and F2.
  This is the same distinction that let `release` be authorized in 5.5.0 despite being irreversible
  cost: a precedent is a claim about what the owner *would* decide, while a declaration in a tracked
  file *is* the decision. The two mechanisms stay unconnected on purpose.
- **D2 — Admission is a label allowlist, not a heuristic.** The declaration names labels; an issue
  carrying one is admitted. Basis: a label is applied by a human to one specific issue, so the
  policy authorizes a class the owner curates issue by issue. Alternatives considered and rejected:
  author allowlists (authorize a person, not a piece of work), title or body keywords (authorize
  whatever anyone chooses to type), and size or complexity estimates (authorize the agent's guess
  about difficulty, which is exactly the judgement that should not be automated).
- **D3 — `keel triage` takes issue attributes as arguments and performs no I/O beyond reading the
  declaration.** The agent fetches with `gh` (F4) and passes what it found. Basis: a gate that
  reaches the network trades local, offline, deterministic evaluation for convenience (issue #33),
  and offline evaluation is also what makes the command testable without a network or a fixture
  server.
- **D4 — Refusal names the reason and the accepted policy.** An issue that is not admitted reports
  which labels it carried and which the declaration accepts. Basis: the existing convention that a
  rejection names the field and its accepted forms (`keel-core-gates`); a bare refusal sends the
  reader to the source to learn what the policy was.
- **D5 — Admission starts work; it does not finish it.** An admitted issue enters authoring and
  implementation, where every existing gate still applies. Alignment still stops at material
  decisions, `task-start` and `task-complete` still run, and the write guard still binds. Basis:
  triage answers "may this begin", which is a different question from every question that follows.
- **D6 — An unattended run may open a pull request and may not merge it.** Basis: merging is the
  point where an unreviewed decision becomes the project's history. The owner may already authorize
  `push` under 5.5.0, and a PR is the artifact that makes an unattended run reviewable after the
  fact; auto-merge would remove the last place a human can see the whole change at once.
- **D7 — Keel ships no scheduler, and the documentation says so.** Basis: `/loop` and cron belong to
  the host. A Keel command that implied it drove the loop would be claiming a capability it does not
  have, which is the failure mode `keel capabilities` exists to prevent elsewhere.
- **D8 — Stopping at a material decision is the designed end state, not an error.** The run reports
  where it stopped and why. Basis: the honest ceiling of this design is a loop that runs until it
  meets a decision that is genuinely the owner's; presenting that as a failure would create pressure
  to widen the policy until it stops happening.

## Hidden Knowledge / Assumptions

- **A1** — The admitting label is applied by a human. Keel cannot verify this and does not try; if
  automation applies the label, the declaration silently becomes broader than the owner believes.
  Basis: D2's whole value rests on the label being a human act. Owner: the repository's label
  permissions, which are outside Keel. The documentation must state this dependency rather than
  imply Keel enforces it.
- **A2** — An unattended run's output is reviewed before merge, because it cannot merge. Basis: D6.
  Resolve by: the specs state the no-merge boundary as a requirement, so a later change cannot
  quietly relax it without editing a spec.

## Risks / Trade-offs

- **An over-broad policy starts work nobody chose.** Mitigated by D2 (a human labels each issue),
  D5 (every later gate still runs), and D6 (nothing merges). Accepted residual: an issue labelled by
  mistake consumes a run and produces a PR nobody wanted, which is visible and reversible.
- **The label becomes a rubber stamp.** If everything gets labelled, the declaration authorizes
  everything. No mechanism prevents this and none should — it is the owner's curation. Named here
  so the failure is recognisable if it starts happening.
- **Two config surfaces now govern autonomy** (`authorize:` for actions, `triage:` for work).
  Accepted: they answer different questions, and merging them would make one of the two answers
  implicit.

## Open Questions

None.
