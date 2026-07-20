<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. <!-- Task Group Name -->

- [ ] 1.1 <!-- Task description -->
  - Covers:
    - <source expectation: spec scenario as `capability / requirement or scenario heading`, hidden-knowledge assumption, domain lens requirement, or critical D<n>/F<n>/A<n>/Q<n>; an unresolved Q<n> requires an authorized fallback>
  - Touch:
    - <path>
  - Verify:
    <!-- verification discipline: Strategy is one of vertical-tdd,
         regression-first, characterization, snapshot-characterization,
         rendered-behavior, or evidence-first. Each M<n> check must prove the
         resolved Acceptance through the public interface, not build-only or
         shape-only evidence. Red-green strategies record per-label `.red` and
         `.green` Evidence entries for the same check before completion. -->
    - Strategy: <strategy>
    - M1: <public behavior check>
  - Evidence:
    - Contract: pending task-start capsule and fingerprint
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, a durable OpenSpec/archive owner, or an explicit discard rationale -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

<!-- Exceptional boundaries are declared only when they differ from defaults:
     - Mode: diagnose-only (with `Touch: none`) or plan-first
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
    - Contract: pending task-start capsule and fingerprint
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
