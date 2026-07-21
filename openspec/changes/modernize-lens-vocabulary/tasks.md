<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Fix the retired-mechanism misdirection in code and validator

- [ ] 1.1 Rewrite the profile-flag rejection to point at pluggable lenses and repoint the validator needle
  - Covers:
    - D2 fix the reject message and resolve the contradiction
    - keel-domain-profiles / Obsolete profile flags are rejected clearly
  - Touch:
    - bin/keel.js
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel invoked with the profile flag prints a rejection that names keel/lenses and the keel lenses add scaffold, and no longer contains the word bundled or the keel-align-expectations skill name
    - M2: the installer script invoked with the profile flag prints the same corrected rejection, and the domain-profiles validator scenario passes against the new wording anchor
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 2. Sweep stale generic profile vocabulary to lens

- [ ] 2.1 Rename current-concept profile to lens in the remaining specs and templates
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
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Rename the domain capability to keel-domain-lenses

- [ ] 3.1 Move keel-domain-profiles to keel-domain-lenses, modernize its Purpose and reject scenario, and rename the validator scenario
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
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

<!-- change-close requires this section. -->
- E1: The profile-flag rejection points to pluggable lenses, not the retired bundled mechanism. Covered by: 1.1
- E2: Current-concept profile vocabulary is modernized to lens while v3-artifact references stay accurate. Covered by: 2.1, 3.1
- E3: The domain capability is renamed to keel-domain-lenses with a modernized Purpose and reject scenario. Covered by: 3.1
