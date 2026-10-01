## Context

Issue #177 reports a contract-drift bypass for multi-line critical statements and unlinked multi-reference Covers entries. An anonymous CLI fixture reproduced both on Keel 5.80.0: editing a nested detail left the SHA-256 value unchanged, and `D1、D2` passed as a `legacy-task-reference`. The current compiler takes only a one-line regex match, and its Covers expansion recognizes ASCII commas only.

## Goals / Non-Goals

**Goals:** Bind all owned decision text to the fingerprint; fail visibly on combined critical references that are not supported syntax; retain deliberate supporting mentions and actionable colon diagnostics.

**Non-Goals:** Parse all CommonMark constructs, interpret the semantic correctness of a decision, automatically preserve old evidence, or change the established `Q<n>` subject-versus-supporting-detail rule.

## Decisions

- F1 — The public `keel gate task-start --json` currently returns the same fingerprint after changing only an indented D1 detail, and its authority text contains only the opening sentence. Basis: 2026-09-30 anonymous temporary CLI fixture against this checkout.
- F2 — `D1、D2` currently passes `task-start` as one `legacy-task-reference` instead of two linked critical statements. Basis: the same 2026-09-30 CLI fixture.
- F3 — A colon-shaped `design.md` opener already yields an `Unparsed Covers critical statement` diagnostic when cited bare; the current spec explicitly leaves colon syntax unaccepted. Basis: `src/core/task-contract.js`, `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`, and existing CLI scenario `unparsed-covers-critical-statement`.
- D1 — Resolve the accepted opener first, then collect only its structurally owned subsequent lines before normalizing text; an equal-or-shallower peer, heading, or blank-line-separated equal-level paragraph ends ownership. Basis: issue #177's desired boundary and the need to avoid unrelated drift.
- D2 — Keep one opening critical reference per Covers entry, plus existing ASCII-comma splitting; diagnose unsupported multi-reference syntax and prose-wrapped critical citations rather than treating them as legacy text. Basis: issue #177's false-authority failure and the existing annotation/Q-supporting-detail rules.
- D3 — Preserve the existing colon diagnostic and accepted dash opener set; do not choose a new colon syntax. Basis: F3 and the issue's explicit either-accept-or-diagnose outcome.
- D4 — Treat moved fingerprints as a deliberate compatibility change: require explicit reauthorization and review of old evidence, with release guidance naming that path. Basis: the contract drift gate's purpose and issue #177's migration request.

## Hidden Knowledge / Assumptions

None. The owner-facing issue and existing specifications establish the acceptance boundary; no private consuming-project details are needed for implementation or proof.

## Risks / Trade-offs

- Stricter Covers diagnostics can reject historical free-text entries containing critical identifiers. Limit the check to critical citation patterns, retain existing single-reference annotations and the question-supporting-detail case, and exercise both positive and negative CLI scenarios.
- Structural line collection is intentionally narrower than a full Markdown parser. Tests must cover nested bullet, continuation, peer bullet, same-level paragraph, heading, and normalization boundaries.
- Existing active anchors can drift after upgrade. Do not bypass the gate; document re-recording and evidence revalidation.

## Open Questions

None.
