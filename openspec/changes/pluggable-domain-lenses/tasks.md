<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Omitted fields inherit versioned defaults: Owner is the current Keel agent,
     Mode is implementation, Read is this change's proposal/design/specs/tasks
     plus discovered repository context, Acceptance derives from Covers, autonomy
     defaults to hard-stop, and commit/push/sync/archive stay unauthorized. -->

## 1. Pluggable lens mechanism

- [x] 1.1 Relocate domain content to self-describing templates and route skills to `keel/lenses/`
  - Covers:
    - keel-domain-profiles / Keel supports pluggable domain lenses
    - keel-domain-profiles / Domain lenses serve execution and review phases
    - keel-domain-profiles / Shipped lens templates stay single-source
  - Touch:
    - assets/lenses/web.md
    - assets/lenses/hardware.md
    - assets/lenses/hardware-dsl.md
    - src/skills/keel-align-expectations/references/
    - src/skills/keel-align-expectations/SKILL.md
    - src/skills/keel-tdd-or-test-first/SKILL.md
    - src/skills/keel-debug-failure/SKILL.md
    - src/skills/keel-review-checklist/SKILL.md
    - plugins/keel/skills/keel-align-expectations/
    - plugins/keel/skills/keel-tdd-or-test-first/SKILL.md
    - plugins/keel/skills/keel-debug-failure/SKILL.md
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: characterization
    - M1: the three templates exist under `assets/lenses/`, each carries an `Applies when:` header and an `Execution and review checks` section, and no `references/` dir remains under any shipped skill
    - M2: the four skills instruct consulting `keel/lenses/` and contain no bundled `references/` domain path; `ALIGNMENT_REFERENCES` is gone from `bin/keel.js`
    - M3: `npm test` passes with the validator's domain assertions rewritten to the pluggable mechanism (no assertion merely deleted)
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a0ada7c96be20e472bb9b972a9f775954ba6f376fed7595f7e66353cfd22c672
    - M1: assets/lenses/{web,hardware,hardware-dsl}.md exist, each with an `Applies when:` header and an `## Execution and review checks` section; no `references/` dir remains under any src or plugin skill.
    - M2: keel-align-expectations, keel-tdd-or-test-first, keel-debug-failure, and keel-review-checklist all consult `keel/lenses/` with no bundled `references/` path; `ALIGNMENT_REFERENCES` removed from `bin/keel.js`.
    - M3: `npm test` → "validation --all passed: baseline plus 48 scenarios"; the six domain assertions were rewritten to the pluggable mechanism, not deleted.
    - Review:
      - Status: pass
      - Acceptance check: pass — lenses are user-authored and self-describing (keel/lenses/), execution and review consult the matching lens, and templates stay single-source in assets/lenses/.
      - Scope check: pass — changes limited to Touch (assets/lenses, the four skills in src and plugin, bin/keel.js, scripts/validate_plugin.py) plus this change's own tasks.md.
      - Findings: none
    - Blocker: none

## 2. keel lenses CLI

- [ ] 2.1 Add `keel lenses list|add` scaffolding
  - Covers:
    - keel-domain-profiles / Keel scaffolds domain lenses
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: rendered-behavior
    - M1: `keel lenses list` reports the three shipped templates and any lenses in `keel/lenses/`
    - M2: `keel lenses add web` in a temp repo creates `keel/lenses/web.md` with its `Applies when:` header, and a second `add web` refuses without a force flag
    - M3: `npm test` passes with a scenario covering list/add/no-clobber
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Documentation

- [ ] 3.1 Describe pluggable lenses in the docs and protocol
  - Covers:
    - keel-domain-profiles / Keel supports pluggable domain lenses
    - keel-domain-profiles / Keel scaffolds domain lenses
  - Touch:
    - README.md
    - README.zh-CN.md
    - AGENTS.md
  - Verify:
    - Strategy: evidence-first
    - M1: both READMEs describe user-authored `keel/lenses/`, `keel lenses add`, and self-describing lenses; `AGENTS.md` refers to lenses rather than bundled references
    - M2: `npm test` passes with the `Execution and review checks` needle preserved via the templates and the skill-policy needles intact
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

## 4. Release alignment

- [ ] 4.1 Bump to 5.2.0 and record the change
  - Covers:
    - keel-domain-profiles / Keel supports pluggable domain lenses
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/bump_version.js minor` aligns every version pin to 5.2.0 and the CHANGELOG entry describes pluggable lenses
    - M2: `npm test` passes
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
