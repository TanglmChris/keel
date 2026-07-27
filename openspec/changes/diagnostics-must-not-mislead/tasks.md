<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Stop the silent compact-to-v3 downgrade

- [x] 1.1 Report a non-concrete Verify as its own diagnostic instead of switching required-field sets
  - Covers:
    - D1 a non-concrete Verify produces its own diagnostic and does not silently select the v3 field set
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler / Non-concrete Verify is reported, not silently downgraded
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md
  - Verify:
    - Strategy: regression-first
    - M1: a compact v4 task whose Verify carries an unfilled template token reports one diagnostic naming that token and stating that compact detection needs a concrete Verify, and no longer reports the expanded v3 fields Candidate Boundary, Report, Owner, Mode, Commands, Acceptance, or Stop Rules as missing; a new validator scenario locks both the presence of the naming diagnostic and the absence of the v3 field list
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2821a5738b02891abc97c18e7a10ccc169573dff67c0eceab05868807d7e584c
    - M1: requiredFieldProblems now returns a single non-concrete-verify diagnostic when Verify is declared but carries an unfilled token, naming the matched token and stating that the expanded v3 fields are not required. unfilledToken was extracted alongside isConcrete over a shared normalizeFieldText and UNFILLED_TOKEN, so the concreteness rule has one definition. A task with no Verify at all still receives the expanded v3 required-field diagnostics, verified by the second half of the new scenario
    - M1.red: with src/core/task-contract.js stashed, the reported case (Verify prose containing an angle-bracket filename pattern) produced 10 problems — 8 missing-field entries for Owner, Mode, Read, Commands, Acceptance, Candidate Boundary, Stop Rules, Report, plus missing-boundary and missing-command-check — and named the offending token nowhere. The new non-concrete-verify-diagnostic scenario exited 1 with "an unfilled token in Verify did not produce the non-concrete-verify diagnostic"
    - M1.green: the same case now produces 2 problems, the first quoting the matched angle-bracket date token back to the author and stating that compact v4 detection requires a concrete Verify; the scenario exited 0 and npm test reported "validation --all passed: baseline plus 59 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the author is told which token caused the failure and is no longer handed a field list from the other schema, satisfying D1
      - Scope check: pass — only src/core/task-contract.js and scripts/validate_plugin.py changed, both within Touch
      - Findings: the defect is wider than issue #7 reported. the token pattern also matches three bare keywords case-insensitively, so prose describing them trips it. This change hit that three times while being authored: task 1.1's own Verify, a Covers reference whose target scenario name used one keyword, and this Evidence block itself, which cannot quote the tokens it describes. Recorded as F6 in this change's design.md; task 1.2 narrows the angle-bracket case, and whether the bare keywords should also be narrowed is deferred. Durable owner: keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md
    - Blocker: none

- [ ] 1.2 Treat angle brackets inside inline code spans as concrete prose
  - Covers:
    - D2 angle brackets inside inline code spans are concrete prose
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler / Documented patterns in inline code are concrete
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: a field whose angle brackets appear only inside inline code spans compiles as concrete, a bare angle-bracket token outside inline code is still judged unfilled, and the existing fingerprint-stability scenarios still pass unchanged; a new validator scenario locks the positive and the negative case together
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 2. Make Covers and authority diagnostics name their cause

- [ ] 2.1 Name a separator collision in the unresolved-covers diagnostic
  - Covers:
    - keel-task-capsule / Covers resolves durable authority and Acceptance / Separator collision is named
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: when a Covers reference fails to resolve and the target capability holds a requirement or scenario whose own name contains the hierarchy separator, the diagnostic states that the name contains the separator and cannot be referenced; an ordinary unresolved reference keeps its existing wording; a new validator scenario locks both
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

- [ ] 2.2 State the exact field and line prefix in the unresolved-authority diagnostic
  - Covers:
    - keel-task-capsule / Task modes and conditional fields are executable / Authority diagnostic names the field to add
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: a task whose Covers references an unresolved Q reference without an authorized fallback reports a diagnostic naming the Autonomy boundary field and the Pre-authorized fallback line prefix, and no longer describes the requirement only as documented design authority; a new validator scenario locks the diagnostic text
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Separate Keel's own repository from a consuming project

- [ ] 3.1 Add the Keel-source-repository predicate and scope the dev-only doctor check to it
  - Covers:
    - D3 one exported predicate answers whether this is Keel's own repository
    - D4 a consumer repository omits the native plugin source line
    - keel-target-surface-diagnostics / Native plugin diagnostics are behavior-probed / Development-only source check is scoped to Keel's own repository
  - Touch:
    - src/core/capabilities.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: doctor run in a temporary consumer repository prints no native plugin source line and no remediation directing the author to install an already-installed plugin, while doctor run in this repository still prints the line as ok; a new validator scenario asserts both directions
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

- [ ] 3.2 Skip the AGENTS.md bootstrap write inside Keel's own repository
  - Covers:
    - D5 install and init skip the bootstrap write in Keel's own repository and report the skip
    - keel-target-surface-diagnostics / Keel install does not damage its own source repository / Install skips the bootstrap write in Keel's own repository
    - keel-target-surface-diagnostics / Keel install does not damage its own source repository / Install still writes the bootstrap in a consuming project
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel --install --target claude run in this repository leaves the AGENTS.md managed block byte-identical and prints a skip line naming the reason, while the same command in a temporary consumer repository still writes the bootstrap block from the asset; a new validator scenario locks both directions, and the full suite passes, proving the four scenarios that assert on managed-block protocol text stay green
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: an author writing a first compact v4 tasks.md is never handed a v3 field list they did not ask for Covered by: 1.1, 1.2
- E2: a diagnostic that requires the author to add a field names that field and its exact prefix Covered by: 2.2
- E3: a diagnostic that cannot resolve a reference names the reason when the reason is structural Covered by: 2.1
- E4: a consuming project is never shown a check it cannot satisfy or a remediation it has already done Covered by: 3.1
- E5: running keel --install inside Keel's own repository does not turn the repository red Covered by: 3.2
- E6: no existing valid task changes its compiled fingerprint Covered by: 1.2
