<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Fix the retired-mechanism misdirection in code and validator

- [x] 1.1 Rewrite the profile-flag rejection to point at pluggable lenses and repoint the validator needle
  - Covers:
    - D2 fix the reject message and resolve the contradiction
    - keel-domain-lenses / Keel removes domain profiles deliberately / Obsolete profile flags are rejected clearly
  - Touch:
    - bin/keel.js
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel invoked with the profile flag prints a rejection that names keel/lenses and the keel lenses add scaffold, and no longer contains the word bundled or the keel-align-expectations skill name
    - M2: the installer script invoked with the profile flag prints the same corrected rejection, and the domain-profiles validator scenario passes against the new wording anchor
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:45275453047c42caa413de26cd5c2d2510c45fa448ced8371d9be7b1cf54c99e
    - M1: keel --install --target codex --profile web now prints a rejection naming keel/lenses and the keel lenses add scaffold, with no bundled or keel-align-expectations text
    - M1.red: pre-fix HEAD printed "guidance is bundled with the keel-align-expectations skill as on-demand references"
    - M1.green: post-fix printed "guidance is now user-authored lenses in keel/lenses/*.md (scaffold with keel lenses add)"
    - M2: the python installer prints the same keel/lenses rejection and the domain-profiles validator scenario passes on the keel/lenses anchor
    - M2.red: with the keel/lenses needle in place, the domain-profiles scenario failed against pre-fix code at exit 1, reporting "still accepts --profile"
    - M2.green: after the fix the domain-profiles scenario passed and install_to_repo.py printed the keel/lenses rejection at exit 1
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pass
      - Acceptance check: pass — both the CLI and installer report that domain guidance is now user-authored lenses in keel/lenses/*.md and the flag is unsupported, and neither creates target-specific profile state
      - Scope check: pass — only bin/keel.js, scripts/install_to_repo.py, and scripts/validate_plugin.py changed, all within Touch
      - Findings: none
    - Blocker: none

## 2. Sweep stale generic profile vocabulary to lens

- [x] 2.1 Rename current-concept profile to lens in the remaining specs and templates
  - Covers:
    - D3 keep and sweep boundary, the SWEEP rows outside the renamed capability
  - Touch:
    - openspec/specs/keel-skill-sourcing-and-portability/spec.md
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
    - openspec/specs/keel-expectation-alignment/spec.md
    - openspec/schemas/keel-spec-driven/templates/design.md
    - assets/openspec/schemas/keel-spec-driven/templates/design.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: characterization
    - M1: the three specs and both design.md template copies no longer use profile for the current domain-guidance concept, while v3-artifact references such as the keel-profile prefix and v3 profile-install state stay intact
    - M2: npm test passes at baseline plus every scenario after the sweep
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:10aec7cd2b88d6bf18c2c8a8fdee563c12471e5f4ad1ed238787d48f099c4cb5
    - M1: a case-insensitive grep for profile over the three specs and both design.md template copies returns zero occurrences after the sweep, and lens/lenses now appears (6 in keel-skill-sourcing-and-portability); v3-artifact references such as the keel-profile prefix and v3 profile-install state live in unswept files and were out of this task's scope
    - M2: npm test reported "validation --all passed: baseline plus 51 scenarios" after the sweep
    - Review:
      - Status: pass
      - Acceptance check: pass — the current domain-guidance concept reads as lens across the swept specs and templates per D3's SWEEP rows, with each requirement's meaning and scenarios preserved
      - Scope check: pass — only the five swept files under Touch changed; scripts/validate_plugin.py needed no needle change because its sole profile match is the v3 legacy fixture, a KEEP
      - Findings: none
    - Blocker: none

## 3. Rename the domain capability to keel-domain-lenses

- [x] 3.1 Move keel-domain-profiles to keel-domain-lenses, modernize its Purpose and reject scenario, and rename the validator scenario
  - Covers:
    - D1 rename the capability keel-domain-profiles to keel-domain-lenses
    - D2 the spec-side reject scenario moves off are bundled
    - F5 direct live-spec edit with skip-specs promotion
  - Touch:
    - openspec/specs/keel-domain-profiles/spec.md
    - openspec/specs/keel-domain-lenses/spec.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: characterization
    - M1: openspec/specs/keel-domain-lenses/spec.md exists with a lens Purpose line and a reject scenario that reports the pluggable-lens mechanism, and the keel-domain-profiles directory no longer exists
    - M2: the renamed domain-lenses validator scenario passes, npm test is green, and openspec validate on the change reports valid
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e50306ea306d3bb9f329fa4c153657d3dc5c8c0a75a1155ea7bd5a1fbfcb1352
    - M1: git mv moved the capability to openspec/specs/keel-domain-lenses/spec.md, whose Purpose now reads "Define Keel's pluggable domain lenses …" and whose reject scenario THEN reports "domain guidance is now user-authored lenses in keel/lenses/*.md"; openspec/specs/keel-domain-profiles no longer exists and no tracked file references the old capability name (only the disposable keel/guard.json does)
    - M2: python scripts/validate_plugin.py --scenario domain-lenses reported "domain-lenses scenario passed", npm test reported "validation --all passed: baseline plus 51 scenarios", and openspec validate modernize-lens-vocabulary reported the change is valid
    - Review:
      - Status: pass
      - Acceptance check: pass — the capability is renamed to keel-domain-lenses with a modernized Purpose and a reject scenario off "are bundled" (D1 and the D2 spec side), promoted by direct live edit per F5
      - Scope check: pass — only openspec/specs/keel-domain-profiles/spec.md (moved), openspec/specs/keel-domain-lenses/spec.md, and scripts/validate_plugin.py changed, all within Touch
      - Findings: none
    - Blocker: none

## Expectation Coverage

<!-- change-close requires this section. -->
- E1: The profile-flag rejection points to pluggable lenses, not the retired bundled mechanism. Covered by: 1.1
- E2: Current-concept profile vocabulary is modernized to lens while v3-artifact references stay accurate. Covered by: 2.1, 3.1
- E3: The domain capability is renamed to keel-domain-lenses with a modernized Purpose and reject scenario. Covered by: 3.1
