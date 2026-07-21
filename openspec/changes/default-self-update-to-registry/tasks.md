<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Default the self-update source to the published registry package

- [x] 1.1 Flip DEFAULT_UPDATE_SOURCE to the registry package and lock the default with a scenario
  - Covers:
    - D1 default the update source to the registry package
    - keel-native-plugin-package / Self-update defaults to the published registry package / Default update packs the registry package
    - keel-native-plugin-package / Self-update defaults to the published registry package / Explicit git source is still honored for development
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: with no explicit source, keel --update --dry-run plans a pack of the registry package @christang/keel and never a git-type spec; a new validator scenario locks this through the CLI, and the existing update-pack-install scenario still proves an explicit --source git spec is honored
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:027e163b8bf73c8d4af87617cc4022f6cb7f8861fde4abe3037196f5b8e9ff40
    - M1: the new update-default-registry validator scenario runs keel --update --dry-run with no source and asserts the pack plan names @christang/keel and contains no github: git-type spec; npm test runs the whole suite including the unchanged update-pack-install scenario that packs an explicit --source git spec
    - M1.red: with DEFAULT_UPDATE_SOURCE reverted to the git spec, the update-default-registry scenario failed at exit 1 — the default dry-run plan named github:TanglmChris/keel instead of the registry package
    - M1.green: after DEFAULT_UPDATE_SOURCE became @christang/keel, the scenario passed at exit 0 and npm test reported "validation --all passed: baseline plus 53 scenarios", green including update-pack-install
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pass
      - Acceptance check: pass — the default self-update source is the registry package @christang/keel, provably not a git-type spec, while an explicit --source git spec is still honored
      - Scope check: pass — only bin/keel.js and scripts/validate_plugin.py changed, both within Touch
      - Findings: none
    - Blocker: none

## Expectation Coverage

<!-- change-close requires this section. -->
- E1: keel --update with no explicit source defaults to packing the published registry package @christang/keel and never a git-type spec, so self-update works where git-type fetches are disabled. Covered by: 1.1
- E2: An explicit --source git spec or KEEL_UPDATE_SOURCE still overrides the registry default and packs the git spec for unreleased builds. Covered by: 1.1
