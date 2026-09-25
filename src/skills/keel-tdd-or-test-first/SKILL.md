---
name: keel-tdd-or-test-first
description: Drive Keel agent test-first or evidence-first execution for a selected OpenSpec task. Use when a task needs software tests, hardware testbench, assertions, lint, new behavior proof, regression coverage, or red/green evidence before implementation.
---

# keel-tdd-or-test-first
## Purpose

Use this skill when Keel execution should start with evidence: software tests first, or hardware testbench, assertion, lint, or equivalent static evidence first. This skill owns the Verify strategy taxonomy, the evidence contract, and their binding to the task capsule; generic test-writing mechanics (how to loop red-green, what to mock) belong to the host runtime and are not restated here.

## Context to read

Read the selected task's compiled capsule: resolved Acceptance, Verify strategy and M<n> checks, Mode, Read, and Touch. `keel gate task-start` returns that capsule and its fingerprint; the fingerprint belongs in the task's Evidence `Contract` line before implementation. Inspect the public interface under test and keep new tests inside the authorized Touch scope.

## Strategy selection

`Verify` names one supported strategy chosen at authoring time as the least-cost proof of the resolved Acceptance:

- `vertical-tdd`: new independently testable deterministic behavior; one check red then green at a time.
- `regression-first`: an observable defect; reproduce it through the public interface first, then prove the fix with the same check.
- `characterization` / `snapshot-characterization`: deterministic or generated outputs kept stable by byte or snapshot comparison; not downgraded to build success.
- `rendered-behavior`: interactive surfaces exercised through the real rendered interface; strict red-green optional by cost.
- `equivalence`: work whose criterion is that a measured result does not change — a refactor, a move, a flow upgrade claiming the numbers hold. It declares `Base:` (a resolvable git ref) and `Fields:` (the compared field set) beside `Strategy:` and owes no red; the A/B command is an ordinary `M<n>` check. `keel gate task-start` refuses a missing `Base:` or `Fields:`, an empty field set, an unresolvable ref, and a `Base:` that is HEAD, because an A/B against itself always agrees. A task covering a scenario its own change *adds* is refused unless a sibling task covers that same entry under a red-green strategy: behavior that is new is not behavior that is unchanged.
- `evidence-first`: docs, configuration, or diagnosis work whose checks state the observable artifact or evidence instead of a red-green loop. It is scoped by an absence — nothing here can fail first — which is why it is not the home for `equivalence` work, whose criterion is stronger than red-green rather than missing.

Red-green strategies (`vertical-tdd`, `regression-first`) must record concrete per-label `.red` and `.green` Evidence entries for the same check; `keel gate task-complete` rejects absent or pending entries.

A check's Evidence may read `artifact <path> sha256:<digest>` instead of retelling the output. `keel gate task-complete` checks the file exists and the digest matches, and refuses a path outside the change's own directory — archiving moves that directory, so a pointer outside it breaks. Keel hashes the bytes and reads nothing inside them: the claim the artifact supports stays yours.

## Domain lenses

When the change's proposal/design/specs or the task's Touch extensions signal a domain, consult the matching lens's `Execution and review checks` section from `keel/lenses/` — the lens whose `Applies when:` header matches — before finalizing the strategy and the first check, and load only that one. When no lens matches, load nothing.

## Coupled-task preflight

When the selected task declares `Coupling: required`, also read design.md's
Coupled Iteration Contract plus the task's Candidate Boundary, Stop Rules, and
Evidence. Before modifying files, run the task's preflight evidence command or
inspect the explicitly named evidence. If the contract is incomplete or task
and design disagree, stop and report the gap; do not infer the missing decision.

## TASK boundary

Align every test or check with the selected OpenSpec task's acceptance criteria or verification evidence. Prove behavior through the public interface: evidence that only shows build success or internal shape does not satisfy a behavioral Acceptance, and mocking your own modules invalidates the proof — mock only at true system boundaries.

## Standalone use

When used alone, name the public interface under test, the behavior being checked, the command used, and the red/green evidence.
