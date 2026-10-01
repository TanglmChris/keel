## Context

Issue #174 records the owner's request (2026-09-28): "在与用户互动时请尽量用带选项的方式，用户可以用直接搬手选". The resident protocol and the alignment skill already require plain-language explanation and a recommended answer; they are silent on presenting answers as selectable options.

## Goals / Non-Goals

**Goals:** state the rule once in the resident protocol and once in the portable alignment skill, host-neutrally, so an agent on a host with a structured-choice surface uses it for enumerable decisions.

**Non-Goals:** naming a specific host tool in portable text, detecting at runtime which hosts offer the surface, or gating whether an agent actually used it.

## Decisions

- F1 — `AGENTS.md` `## User-facing communication` and `keel-align-expectations`' Deep path speak of explaining options and recommending an answer, but not of offering them as a selectable choice; the skill's Purpose says question presentation is "the host runtime's concern". Basis: both files at 5.81.0 and issue #174.
- D1 — The rule applies to decisions whose answers can be enumerated; open questions and hosts with no structured-choice surface keep prose. The recommendation comes first and is marked as recommended. Basis: issue #174's proposed direction.
- D2 — Portable text names no host tool; it says "the host's structured-choice surface". Which hosts offer one is a host fact, capability-probed like the rest of Keel's target automation, not asserted by target name. Basis: `keel-skill-sourcing-and-portability` keeps portable `SKILL.md` authority host-neutral.
- D3 — No gate checks presentation; the validation scenario checks only that both carriers state the rule. Basis: issue #174's out-of-scope note that presentation is unobservable to a gate.

## Hidden Knowledge / Assumptions

None.

## Risks / Trade-offs

- A host's choice surface may cap the number of options; the rule says "where offered" and leaves the shape to the host, so a decision with many answers still falls back to prose without violating it.

## Open Questions

None.
