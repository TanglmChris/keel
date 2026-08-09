## Context

`src/skills/keel-align-expectations/SKILL.md`'s `## Unattended runs` section (lines 74-97, 1,581
characters) restates `AGENTS.md`'s own `## Unattended runs` section (lines 55-61, 1,457
characters) almost sentence-for-sentence. `#55` measured this as the largest single piece of the
skill's injection footprint and, in its final machine comment, narrowed the recommendation to
exactly one thing: replace the skill's copy with a pointer, and leave everything else in the
skill (routing, quick/deep path, decision precedents, domain lenses) untouched, because those
sections have no AGENTS.md counterpart to point to.

Two deterministic validators currently make the duplication load-bearing rather than incidental:
`validate_unattended_boundary_scenario` requires five distinguishing phrases ("open a pull
request", "may not merge", "Keel schedules nothing", "designed boundary rather than a failure",
"never from a precedent") in `AGENTS.md`, the canonical skill, and the plugin-distributed skill
copy alike. The M5 block inside `validate_triage_admits_from_the_repository_scenario` separately
requires "issue number" in five surfaces including both skill copies, and forbids the stale phrase
"A label is the unit" in all of them. Both were written when the skill's self-containment was the
goal; implementing the owner's decision means both need to accept a pointer in the skill files
while continuing to hold `AGENTS.md` itself to the full text.

## Goals / Non-Goals

**Goals:**

- Remove the duplicated prose from the skill's `## Unattended runs` section, replacing it with a
  short paragraph that names what is in `AGENTS.md`'s own section and points there.
- Keep `AGENTS.md`'s `## Unattended runs` section exactly as it is today — it is the surface every
  session already loads in full, and nothing about it needs to change for the skill to stop
  duplicating it.
- Keep the canonical skill (`src/skills/...`) and the plugin-distributed copy
  (`plugins/keel/skills/...`) byte-identical, which is an existing invariant this change does not
  relax.
- Update the two validators that pin the duplicated phrases inside the skill files so a pointer
  satisfies them, without weakening what they require of `AGENTS.md`.

**Non-Goals:**

- Touching any other section of the skill (Routing, Quick path, Deep path, Implicit expectations,
  Repository facts, Write-back, Decision precedents, Domain lenses, Boundaries). None of them
  duplicate `AGENTS.md` content; `#55`'s own measurement attributed the growth specifically to
  "Decision precedents" and "Unattended runs", and a separate issue already covers the interaction
  between Decision precedents and the precedent store (out of scope here).
- Revisiting `keel-skill-sourcing-and-portability`'s "one portable authority" requirement. The
  pointer content already fits it (it is projected identically to every target); see D4.
- Restructuring the skill into short-router-plus-`references/` form. That was `#55`'s larger
  suggestion and requires its own trigger-behavior re-validation; the owner's decision scoped this
  change to the one section with a concrete pointer target.

## Decisions

- D1 — The skill's `## Unattended runs` heading stays; only the section body changes. Basis: the
  section's place between "Decision precedents" and "Domain lenses" is unrelated to its content,
  and keeping the heading means no other section's relative position or any heading-count
  assertion is disturbed.

- D2 — The pointer paragraph's distinguishing phrase, checked by both updated validators, is
  "states no separate copy". Basis: this repository's existing phrase-pinning style asserts the
  specific claim being made ("Phrases, not keywords" — `validate_unattended_boundary_scenario`'s
  own docstring) rather than a generic word like "AGENTS.md" alone, which could appear in an
  unrelated cross-reference without asserting non-duplication.

- D3 — Both validators keep requiring the full phrase sets against `AGENTS.md` unchanged, and only
  relax what they require of the two skill copies. Basis: F1/F2 below — `AGENTS.md` is the surface
  that must stand alone (it is what the pointer points to), and nothing about its content or
  loading behavior is changing in this proposal.

- D4 — No change to `keel-skill-sourcing-and-portability`'s "Keel skills have one portable
  authority" requirement or its validators. Basis: that requirement is about the skill's content
  being identical across every declared target projection (Claude/Codex/OpenCode), not about
  whether the skill's content is self-contained versus pointing at a host file. The pointer
  paragraph itself is projected identically to every target (D1/canonical-distributed parity is
  unchanged), so the requirement is satisfied exactly as it was before.

- D5 — The pointer assumes `AGENTS.md` exists at the section it names. Basis: F3 below — every
  target Keel installs into receives an `AGENTS.md` bootstrap merge, and `keel --doctor` already
  reports it as missing/broken when absent, independent of this skill; the pointer does not create
  a new failure mode, it relies on a surface Keel already guarantees and diagnoses.

- F1 — Verified 2026-08-05 by reading `src/skills/keel-align-expectations/SKILL.md:74-97` and
  `AGENTS.md:55-61`: five sentences carrying the section's distinguishing content
  ("may not merge", "Keel schedules nothing", "designed boundary", "Admission answers", "never
  from a precedent" per `#55`'s own grep) appear in both, and the skill's version is the fuller
  restatement (1,581 vs. 1,457 characters) rather than a summary.

- F2 — Verified 2026-08-05 by reading `scripts/validate_plugin.py:16686-16733`
  (`validate_unattended_boundary_scenario`) and `:15564-15591` (the M5 block inside
  `validate_triage_admits_from_the_repository_scenario`): both iterate a `surfaces`-style mapping
  that includes `src/skills/keel-align-expectations/SKILL.md` and
  `plugins/keel/skills/keel-align-expectations/SKILL.md` alongside `AGENTS.md`, and both assert
  canonical/distributed byte-parity. A grep for the five boundary phrases, "issue number", and
  "## Unattended runs" across the rest of `scripts/validate_plugin.py` found no other function
  reading content from this section, so these two are the complete set that needs updating.

- F3 — Verified 2026-08-05 by reading `bin/keel.js:1350` and `:1356-1362`: `keel --doctor` already
  reports `AGENTS.md bootstrap missing` and a missing `@AGENTS.md` import for Claude independent of
  this skill, confirming the file's presence is already a diagnosed Keel invariant rather than an
  assumption this change introduces.

## Hidden Knowledge / Assumptions

- A1 — The five-target read count `#55` reported (skill grown to 8,364 chars while the issue was
  open) is the motivating measurement, not a target this change is scored against; the goal is
  removing the specific duplicated section, and the resulting size is whatever remains.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A host repository whose `AGENTS.md` bootstrap is missing or broken now has a skill section that
  points at content that is not there. This is not a new risk class — `keel --doctor` already
  diagnoses that condition (F3) independent of this skill — but it is a real instance of the
  self-containment the skill is trading away, and is exactly the trade-off the owner's decision
  named ("rather than keeping the skill fully self-contained").
- The two validator changes are, individually, small; reviewing them together against this design
  is what confirms neither one silently drops a requirement on `AGENTS.md` itself, which is the
  failure mode that would make the pointer's target unreliable.

## Open Questions

None — the owner's decision (2026-08-05, `dasauto#18`) settled the one material choice `#55` left
open (pointer vs. full self-containment); everything here is the implementation of that choice.
