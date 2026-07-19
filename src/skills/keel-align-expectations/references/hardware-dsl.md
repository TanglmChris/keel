# Hardware DSL alignment reference

Domain lens for hardware modeling DSL work. Use during alignment when generated RTL, golden output, or model equivalence assumptions may be implicit.

## Material risk surface

Treat these as deep-path candidates when the change touches them: DSL syntax or semantics, generated RTL, generated tests, regeneration order, golden output, equivalence expectations, lowering rules, scheduling, reset semantics, valid-ready mapping, CSR generation, naming stability, and artifact ownership. Ask only questions that materially affect Acceptance, verification checks, Touch, specs, design decisions, or non-goals; stop when the task contract can be written without guessing.

## Durable placement

- specs for observable DSL behavior and generated artifact expectations.
- design.md for lowering decisions, regeneration policy, equivalence rationale, conflict authority, and baseline policy.
- tasks.md for Covers, verification, Touch, stop/autonomy details, and Coupling when source and generated artifacts must change together.

## Evidence expectations

Prefer reproducible evidence: golden output or snapshot evidence when generated artifacts are deterministic; regeneration commands when source changes must update generated RTL or tests; equivalence or behavioral checks when generated output must preserve model semantics; coupled-task evidence when DSL source, generated artifacts, and baselines must be evaluated as one candidate.

## Execution and review checks

While implementing and reviewing, keep source and generated artifacts moving as one candidate: after any DSL or lowering change, re-run the full regeneration command and commit-or-diff every regenerated artifact — a hand-edited generated file is a defect, not a fix. Prove semantics with equivalence or behavior checks rather than diff-silence alone, and treat golden output updates as decisions needing a recorded rationale. In review, reject changes where generated RTL, generated tests, or baselines moved without their DSL source (or vice versa), and confirm naming and interface stability expectations still hold after regeneration.
