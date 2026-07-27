<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Document the fast/full verification split

- [x] 1.1 State the fast inner-loop vs full gate split in the shipped READMEs
  - Covers:
    - D1 one capability owns the layering methodology and its surfaces
    - keel-verification-layering / Keel documents the fast and full verification split / The split is documented for projects
  - Touch:
    - README.md
    - README.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: README.md and README.zh-CN.md each gain a verification-layering section stating the fast inner-loop (local pre-push, seconds) versus full gate (CI or change-close) split and directing the slow or exhaustive suite to the full gate; a new validator scenario asserts the section in both READMEs
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:779db3a1ca798d85c539eeefe40bae1cb8e9d14f2b5bd303332f45643e6dec8f
    - M1: both READMEs carry a verification-layering section naming the fast inner-loop (local pre-push) and full gate (CI / change-close); the new verification-layering-docs validator scenario reads both files and asserts the section present, and npm test reported "validation --all passed: baseline plus 54 scenarios"
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pass
      - Acceptance check: pass — the fast/full split is documented in both shipped READMEs and directs the slow suite to the full gate
      - Scope check: pass — only README.md, README.zh-CN.md, and scripts/validate_plugin.py changed, all within Touch
      - Findings: none
    - Blocker: none

## 2. Scaffold the keel/config.yaml fast-check declaration

- [ ] 2.1 Scaffold a commented keel/config.yaml template on install without clobbering an existing one
  - Covers:
    - D2 fast check lives in keel config yaml, flat-key parsed
    - keel-verification-layering / Keel projects declare a fast inner-loop check / Install scaffolds the config template once
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel --install writes a commented keel/config.yaml template describing fast_check when none exists and leaves an existing keel/config.yaml untouched; a new validator scenario locks both behaviors
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Scaffold an opt-in fast local pre-push

- [ ] 3.1 Generate the pre-push hook and set core.hooksPath behind --with-git-hooks, with symmetric revert
  - Covers:
    - D3 with-git-hooks is an explicit flag; revert is symmetric
    - keel-verification-layering / Keel projects declare a fast inner-loop check / Declared fast check is read
    - keel-verification-layering / keel --install --with-git-hooks scaffolds a fast local pre-push / Flag generates the hook and sets hooksPath
    - keel-verification-layering / keel --install --with-git-hooks scaffolds a fast local pre-push / Plain install never touches git config
    - keel-verification-layering / keel --install --with-git-hooks scaffolds a fast local pre-push / Flag refuses without a declared fast check
    - keel-verification-layering / keel --install --with-git-hooks scaffolds a fast local pre-push / Uninstall reverts only a keel-set hooksPath
  - Touch:
    - bin/keel.js
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel --install --with-git-hooks in a repo declaring fast_check writes a sh pre-push running that command and sets core.hooksPath to .githooks; a plain install touches neither; the flag refuses when fast_check is undeclared; and keel --uninstall unsets core.hooksPath only when it equals .githooks; a new validator scenario locks the whole flow
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 4. Diagnose the fast pre-push surface

- [ ] 4.1 Report fast_check, the pre-push hook, and core.hooksPath in keel --doctor
  - Covers:
    - D5 doctor reports the surface, never mutates it
    - keel-verification-layering / Keel diagnoses the fast pre-push surface / Doctor reports the fast pre-push surface
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel --doctor reports whether fast_check is declared, whether .githooks/pre-push exists, and the current core.hooksPath, and changes nothing; a new validator scenario asserts the reported surface
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 5. Add the fast/full verification-layer tag to the task capsule

- [ ] 5.1 Parse an optional M-check layer tag defaulting to full and lock it with a scenario
  - Covers:
    - D4 Verify gains an optional fast or full layer tag, default full
    - keel-task-capsule / Verification strategy and evidence labels are connected / Checks may declare a verification layer
  - Touch:
    - src/core/task-contract.js
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: task-contract.js parses an optional fast or full tag written after an M-check label into a layer on the compiled check, an untagged check compiles as full, and the tag does not alter the check text or Evidence label mapping; both tasks template copies document the tag; a new validator scenario locks the parsed layer
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

<!-- change-close requires this section. -->
- E1: Keel documents the fast inner-loop (local pre-push, seconds) versus full gate (CI or change-close) verification split in the shipped READMEs. Covered by: 1.1
- E2: keel --install scaffolds a commented keel/config.yaml fast_check template once and never overwrites an existing one. Covered by: 2.1
- E3: keel --install --with-git-hooks reads the declared fast_check, generates a sh pre-push that runs it, sets core.hooksPath to .githooks, refuses without a fast_check, stays inert on a plain install, and reverts core.hooksPath on uninstall only when it equals .githooks. Covered by: 3.1
- E4: keel --doctor reports the fast pre-push surface — fast_check declared state, pre-push hook presence, and core.hooksPath — without mutating it. Covered by: 4.1
- E5: A task capsule Verify M-check may carry an optional fast or full layer tag that compiles into a check layer defaulting to full, without changing check text, Evidence mapping, or completion rules. Covered by: 5.1
