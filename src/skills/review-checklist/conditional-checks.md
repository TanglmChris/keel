# review-checklist: conditional checks

Read the section whose condition holds, as `SKILL.md` lists them. Each states a criterion of the review.

## Coupled execution

Applies when a task declares `Coupling: required`.

- For `Coupling: required`, confirm one complete candidate reached its completion gate and generated artifacts are aligned.

## Domain lenses

When the change's artifacts or Touch extensions signal a domain, consult the matching lens's `Execution and review checks` section from `keel/lenses/` — the lens whose `Applies when:` header matches — before concluding the review. When no lens matches, load nothing.

## Skill change review

For a new or materially expanded dedicated skill, confirm the authoring evidence
identifies authoritative sources, provenance and license implications, realistic
positive and negative trigger cases, and real-task evidence. Confirm detailed
conditional knowledge uses progressive references when it is not needed on
every activation.

The canonical portable `SKILL.md` must agree with every declared target
projection. Target metadata may be additive, but it must not redefine skill
behavior or make Keel the authority for target-native discovery or activation.

## Planning artifact funnel

When the work followed an accepted native plan-mode artifact, confirm its decisions affecting scope, Acceptance, completion, or execution boundaries were recorded in proposal, design, specs, or tasks before implementation. A material decision found only in session state is missing authority and returns to OpenSpec authoring; the session plan file is never execution authority.
