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

- [x] 2.1 Add `keel lenses list|add` scaffolding
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
    - Contract: keel-task-capsule/v1 sha256:0f54c02c4c3a49f86496993e57c59d1adda2ec303854907644b3eca6012c08c0
    - M1: `keel lenses list` prints "Shipped lens templates (assets/lenses/)" with web/hardware/hardware-dsl and an "Installed lenses (keel/lenses/)" section that marks installed templates.
    - M2: `keel lenses add web` in a temp repo writes `keel/lenses/web.md` carrying its `Applies when:` header; a second `add web` exits 3 with "pass --force to overwrite"; `add web --force` exits 0 and overwrites.
    - M3: `npm test` → "validation --all passed: baseline plus 49 scenarios"; new `domain-lens-scaffold` scenario exercises list/add/no-clobber/force, and the baseline CLI-support check now requires the `lenses` token.
    - Review:
      - Status: pass
      - Acceptance check: pass — `keel lenses add web` scaffolds a shipped template into the user's `keel/lenses/`, refuses to clobber without `--force`, and `list` surfaces both shipped templates and installed lenses; the command is not run by `keel --init`.
      - Scope check: pass — changes limited to Touch (bin/keel.js, scripts/validate_plugin.py) plus this change's own tasks.md; base HEAD at task-start.
      - Findings: none
    - Blocker: none

## 3. Documentation

- [x] 3.1 Describe pluggable lenses in the docs and rename the domain vocabulary to lenses
  - Covers:
    - keel-domain-profiles / Keel supports pluggable domain lenses
    - keel-domain-profiles / Keel scaffolds domain lenses
  - Touch:
    - README.md
    - README.zh-CN.md
    - AGENTS.md
    - scripts/validate_plugin.py
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/templates/tasks.md
  - Verify:
    - Strategy: evidence-first
    - M1: both READMEs describe user-authored `keel/lenses/`, `keel lenses add`, and self-describing lenses; `AGENTS.md` refers to domain lenses rather than bundled references
    - M2: the domain vocabulary is renamed from reference/profile to lens across `AGENTS.md`, the keel-spec-driven schema.yaml (source and repo copies), and the tasks.md template (source and repo copies), with the authoring-continuity needles updated to match
    - M3: `npm test` passes with the `Execution and review checks` needle preserved via the templates and the skill-policy needles intact
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:650ef26e52fd51f1e1ecc8ecea1221c28326ddd63aa2628159086fb301f10e0c
    - M1: README.md adds a "Domain lenses" section plus `keel lenses list`/`add` commands describing user-authored `keel/lenses/`, self-describing `Applies when:` lenses, and opt-in `assets/lenses/` templates; README.zh-CN.md rewrites its bullet to "可插拔领域透镜" with the same story and the `keel lenses` commands; AGENTS.md now says "domain lenses (user-authored keel/lenses/*.md)" instead of the bundled-references framing.
    - M2: renamed the domain vocabulary to "lens" in AGENTS.md, both keel-spec-driven schema.yaml copies (two "a domain reference" phrases each → "a domain lens"), and both tasks.md template copies ("domain profile requirement" → "domain lens requirement"); the authoring-continuity needles were updated in lockstep to "domain lenses"/"domain lens" so the scenario asserts the new wording.
    - M3: `npm test` → "validation --all passed: baseline plus 49 scenarios"; the `Execution and review checks` needle stays satisfied through the `assets/lenses/` templates and the skill-policy needles are intact.
    - Review:
      - Status: pass
      - Acceptance check: pass — the docs and protocol now present domain guidance as pluggable, user-authored lenses with a scaffold command, matching the "Keel supports pluggable domain lenses" and "Keel scaffolds domain lenses" requirements.
      - Scope check: pass — working-tree changes are limited to the eight Touch files plus this change's own tasks.md; base HEAD (task 2.1 commit) at task-start.
      - Findings: one, explicitly discarded — scripts/install_to_repo.py still carries a stale "domain references are bundled" help string on the obsolete `--profile` flag. Discard rationale: the string is attached to an already-obsolete flag whose only job is to reject usage, it is outside this change's declared Touch, and correcting deprecated-flag help carries no behavioral value; not worth a durable follow-up.
    - Blocker: none

## 4. Release alignment

- [x] 4.1 Bump to 5.2.0 and record the change
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
    - Contract: keel-task-capsule/v1 sha256:3eaa703618fe9f873f268a12eda2eddcdc68873c16ac859e5d16f55f2d917167
    - M1: `node scripts/bump_version.js minor` reported "Bumping 5.1.2 -> 5.2.0" and rewrote all eight pins (package.json, package-lock.json, both plugin manifests, scripts/validate_plugin.py, AGENTS.md, assets/bootstrap/AGENTS.md, keel/CHANGELOG.md); `keel --version` prints "keel 5.2.0". The CHANGELOG 5.2.0 entry now describes pluggable, user-authored `keel/lenses/`, the `keel lenses list|add` CLI and `assets/lenses/` templates, and the reference/profile→lens rename.
    - M2: `npm test` → "validation --all passed: baseline plus 49 scenarios", confirmed stable across three consecutive runs.
    - Review:
      - Status: pass
      - Acceptance check: pass — the release is aligned to 5.2.0 across every pin and the changelog records the pluggable-lenses change, satisfying "Keel supports pluggable domain lenses" as the shipped release.
      - Scope check: pass — working-tree changes are limited to the eight Touch files (the bump script's exact target set) plus this change's own tasks.md; base HEAD (task 3.1 commit) at task-start.
      - Findings: one, explicitly discarded — one `npm test` invocation flaked on `native-plugin-session-start` (a scenario untouched by this change) and passed on every other run. Discard rationale: transient parallel-runner temp-dir timing, not reproducible and unrelated to the release bump; three consecutive clean full-suite runs confirm stability, so no durable follow-up is warranted.
    - Blocker: none
