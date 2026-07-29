<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, Coupling defaults to none, and
     helpers stay read-only/evidence-only. Autonomy defaults to hard-stop, and
     commit, push, sync, archive, and cross-task continuation stay unauthorized,
     EXCEPT where `keel/config.yaml` standing-authorizes an action: a task that
     authors no `Autonomy boundary:` inherits that declaration, and the capsule
     names the declaration as the entry's source. A standing authorization
     removes the confirmation, never the gate, evidence, or Review.
     Declare a field only when it differs from these defaults. -->

## 1. <!-- Task Group Name -->

- [ ] 1.1 <!-- Task description -->
  - Covers:
    - <source expectation: spec scenario as `capability / requirement or scenario heading`, hidden-knowledge assumption, domain lens requirement, or critical D<n>/F<n>/A<n>/Q<n>; a Q<n> that OPENS an entry is an open question and requires an authorized fallback, while one named inside an entry about a fact is a citation and does not>
  - Touch:
    - <path>
  - Verify:
    <!-- verification discipline: Strategy is one of vertical-tdd,
         regression-first, characterization, snapshot-characterization,
         rendered-behavior, or evidence-first. Each M<n> check must prove the
         resolved Acceptance through the public interface, not build-only or
         shape-only evidence. Red-green strategies record per-label `.red` and
         `.green` Evidence entries IN ADDITION TO the bare `M<n>` entry, which
         is always required; all three must be concrete before completion.
         An M<n> check may carry an optional comma-separated tag set after its
         label, drawn from fast, full, and regression (e.g. `M1 (fast): …`,
         `M2 (regression): …`, `M3 (fast, regression): …`). fast/full marks
         which checks the fast inner-loop pre-push runs; an untagged check is
         full. regression marks a check that asserts something already green
         stays green: it has no honest red, so it is exempt from `.red`/`.green`
         but still needs its bare `M<n>` Evidence, and a red-green strategy must
         keep at least one check untagged. change-close still needs every
         M<n>'s Evidence. -->
    - Strategy: <strategy>
    - M1: <public behavior check>
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, an absolute https://… reference, or any repo-relative path that exists (keel/archive/…, an openspec/changes/… artifact, or the repository's own ledger) named after "Durable owner:"; not keel/HANDOFF.md, which is a pointer override -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

<!-- Exceptional boundaries are declared only when they differ from defaults:
     - Mode: diagnose-only or repo-action (both with `Touch: none`), or plan-first.
       repo-action is for a task whose whole effect is an authorized
       repository-level action — a commit, a tag — and which writes no worktree
       file; it is the one mode that may commit, and it still may not push,
       sync, archive, or mark tasks complete
     - Read: additional required starting context beyond the base set
     - Acceptance: a task-specific observable delta the Covers authority does not express
     - Execution recommendation / Rationale: advisory notes for the current agent
     - Autonomy boundary: a pre-authorized fallback with its exact reversible bound and required evidence
     - Coupling: required, with the design.md Coupled Iteration Contract, one
       complete candidate, Candidate Boundary, completion-gate final assertions,
       and candidate-level Stop Rules
     - Stop if: extra hard limits beyond the standard prohibitions
     Requires modifying files outside Touch. always remains a stop condition. -->

## 2. <!-- Task Group Name -->

- [ ] 2.1 <!-- Diagnose-only example: exceptional Mode and no-write scope are declared -->
  - Mode: diagnose-only
  - Covers:
    - <source expectation or critical D/F/A statement being diagnosed>
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - M1: <reproduction or diagnosis check with its observable evidence>
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. <!-- Task Group Name -->

- [ ] 3.1 <!-- Red-green example: a vertical-tdd task and the Evidence it must record -->
  - Covers:
    - <source expectation whose observable behavior this slice proves>
  - Touch:
    - <path>
  - Verify:
    <!-- The untagged check below is load-bearing: a red-green strategy whose
         every check is tagged (regression) is refused as regression-only,
         because a regression check has no honest red to record. -->
    - Strategy: vertical-tdd
    - M1: <public behavior check for the new behavior>
    - M2 (regression): <check asserting behavior that is already green stays green>
  - Evidence:
    <!-- M1 is red-green, so it records THREE entries: the bare M1 plus M1.red
         and M1.green. M2 is tagged regression, so it records only its bare
         entry — it is exempt from .red/.green, not from Evidence. -->
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

<!-- task-start requires this section before any task of this change runs, so
     the statements this change makes stale can be named while their paths can
     still be declared in Touch instead of forcing a reauthorization later.
     Each entry quotes the wording a reader would SEARCH for — not just the
     files you already remembered, because the text that goes stale is the text
     you were not thinking about — then says where it lives, then closes:
     `Updated by: 1.1` (tasks of this change), `Durable owner: <url or path>`
     — an absolute https:// reference, or any repo-relative path that exists;
     keel/HANDOFF.md is refused — or `Discard reason: why it stands`. Use `- None.` when this change makes
     no existing statement wrong.

     - I1: "the exact wording that is now wrong" — where that wording lives. Updated by: 1.1
     -->
- None.

## Expectation Coverage

<!-- change-close requires this section. One line per critical expectation:
     `- E1: the expectation Covered by: 1.1` (task ids that own it), or a
     `Durable owner: <url or any repo-relative path that exists>` /
     `Discard reason: why` closure. Use `- None.` only when the change has no critical expectations. -->
- None.
