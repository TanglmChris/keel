## Context

`keel-domain-profiles` currently requires the three domain references to live inside `keel-align-expectations`, be byte-identical across shipped copies, and load on demand during alignment, execution, and review. This change keeps that on-demand mechanism but relocates authorship of the content to the user's repo.

## Verified facts

- **F1** Domain content lives at `src/skills/keel-align-expectations/references/{web,hardware,hardware-dsl}.md` and is byte-copied into the plugin distribution.
- **F2** Four skills consume it: `keel-align-expectations` (owns the files and its own routing); `keel-tdd-or-test-first`, `keel-debug-failure`, and `keel-review-checklist` cross-reference its `Execution and review checks` section.
- **F3** `bin/keel.js` `ALIGNMENT_REFERENCES` (line 59) is dead code — defined once, never consumed.
- **F4** `scripts/validate_plugin.py` binds the references in at least six places: the required-file blocks (lines ~191-193, 227-249), the `domain-profiles` scenario (~1747-1755), the `expectation-alignment-skill` scenario (~5403-5415), the `authoring-continuity` snippet list (~1609), the `Execution and review checks` README needle, and the `domain-execution-references` scenario.
- **F5** `keel/` is already the target repo's project-local Keel directory (it holds `keel/HANDOFF.md`), so `keel/lenses/` is a consistent home for user-authored lenses.

## Decisions

- **A1** The three built-in references become opt-in templates under `assets/lenses/` and are not loaded by default. `keel lenses add <name>` scaffolds a template into `keel/lenses/`; `keel lenses list` shows available templates plus installed lenses. Rationale: keep the good content usable without making the core ship active domain opinion.
- **A2** This change is executed through the OpenSpec Full flow (dogfooding Keel's own discipline).
- **A3** Lenses are self-describing: each `keel/lenses/*.md` declares an `Applies when:` header naming its domain signals (keywords and/or Touch extensions). The skills read `keel/lenses/`, match by that header, and load only the matching lens. Rationale: the core stays domain-agnostic — it knows the mechanism, not the domains.
- **A4** User lenses live at `keel/lenses/*.md`. Rationale: consistent with F5.
- **A5** Single-source / byte-identical authority continues to apply to the shipped `assets/lenses/` templates (canonical source, validated), but **not** to user lenses in `keel/lenses/`, which are user-owned data the validator does not police.
- **A6** Validator strategy: replace the "references bundled in the skill" assertions with assertions on the new mechanism — templates exist and self-describe under `assets/lenses/`; the four skills route to `keel/lenses/` and no longer reference `references/`; `keel lenses add/list` behave correctly; and the `Execution and review checks` needle is preserved by the templates. This keeps the suite meaningful rather than merely deleting checks.

## Open questions

- **Q1 (non-blocking, naming debt)** The capability id stays `keel-domain-profiles` and the validator scenario names (`domain-profiles`, `domain-execution-references`) are unchanged to limit churn, even though "profiles/references" now reads as "lenses." A later cosmetic rename can reconcile the vocabulary; it is out of scope here.

## Risks

- **R1** Existing installs lose the bundled references after `keel --install`/`--update`. Mitigated by the `keel lenses add` migration path and a CHANGELOG note.
- **R2** Weakening the validator while relocating content could silently drop coverage. Mitigated by A6: each removed assertion is replaced by a mechanism assertion, and `npm test` must stay green at every task boundary.

## Hidden Knowledge / Assumptions

- Domain *signal detection* (reading change artifacts / Touch extensions to decide a domain applies) is unchanged; only the *source* of the loaded lens moves. No new detection heuristic is introduced.
- The `Applies when:` header is prose the agent interprets; it is not a machine-parsed schema, so no core parser is added.
