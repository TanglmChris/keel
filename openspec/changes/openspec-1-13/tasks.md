# Tasks

## 1. OpenSpec 1.13

- [x] 1.1 Pin OpenSpec 1.13.2, and Codex overlays, doctor, and uninstall follow the layout the repository carries
  - Covers:
    - keel-openspec-surface-overlay / Codex overlays follow the OpenSpec layout the repository carries / A new Codex repository gets the 1.13 layout
    - keel-openspec-surface-overlay / Codex overlays follow the OpenSpec layout the repository carries / A 1.6-era Codex repository keeps its layout
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - bin/keel.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Touch:
    - npm-shrinkwrap.json
    - bin/keel.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: with the pin at 1.13.2, `openspec-surface-overlay` requires the Codex overlay on `.agents/skills/openspec-*/SKILL.md`. Fails with: `missing overlay target`
    - M2: `target-surface` requires the Codex doctor to report the full OpenSpec surface under `.agents/skills`. Fails with: `Codex doctor did not report full surface`
    - M3: `sync-surface-overlay` requires the Codex sync surface at `.agents/skills/openspec-sync-specs/SKILL.md`. Fails with: `has no sync surface`
    - M4: `uninstall-removes-the-overlay` requires the Codex surfaces carrying the overlay after init to be the `.agents/skills` ones, and requires uninstall to remove each overlay. Fails with: `are not the ones this scenario expects`
    - M5: `authoring-alignment-overlay` requires exactly one alignment overlay on `.agents/skills/openspec-propose/SKILL.md` after init and after refresh. Fails with: `propose surface lacks exactly one alignment overlay`
    - M6 (regression): a new cell in `openspec-surface-overlay` plants 1.6-layout Codex skills under `.codex/skills` and prompts in `CODEX_HOME`, runs `keel --install --target codex`, and requires the overlay on both. Detects: `the layout is always agents` -> `1.6-layout Codex surfaces lost their overlay`
    - M7 (regression): `npm test` reports no failing scenario other than `published-specs-validate-strictly`, which 1.2 owns
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a failing scenario under 1.13.2 is not one of the six F3 names, because that is an incompatibility this change did not account for.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:26071c994608d3787cd64f36e78feff63286f3a5944a0f148d6878b16c65abfd
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario openspec-surface-overlay` reports the scenario passing. `keel --init --target codex` under OpenSpec 1.13.2 puts the Keel overlay on `.agents/skills/openspec-{apply-change,archive-change}/SKILL.md`, doctor reports `Keel apply/archive/sync overlay: ok`, and a stale overlay is refreshed idempotently.
    - M1.red: fail, for the declared reason. With only the pin moved to 1.13.2, it reported `openspec-surface-overlay scenario Codex overlay failed: missing overlay target: …/codex/.codex/skills/openspec-apply-change/SKILL.md`. Carries the declared signature `missing overlay target`.
    - M1.green: pass. Same command after `codexOpenSpecLayout()` was added to `bin/keel.js` and `openspecSkillRootForTarget()` / `commandPathForAction()` follow it. In the agents layout the command surface is empty and its `null` paths are filtered.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario target-surface` reports the scenario passing. The Codex doctor reports `OpenSpec action skills: ok - 5/5 under .agents/skills` and `OpenSpec commands: ok - none; OpenSpec 1.13 surfaces Codex's workflows as the skills under .agents/skills`. A removed skill gives `OpenSpec action skills: missing`.
    - M2.red: fail, for the declared reason. With only the pin moved, it reported `target-surface scenario Codex doctor did not report full surface.`. Carries the declared signature `Codex doctor did not report full surface`.
    - M2.green: pass. Same command after doctor used the repository's layout for the skill root and printed the skills-only commands line.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario sync-surface-overlay` reports the scenario passing, with the Codex sync surface at `.agents/skills/openspec-sync-specs/SKILL.md`.
    - M3.red: fail, for the declared reason. With only the pin moved, it reported `sync-surface-overlay M1 codex has no sync surface at .codex/skills/openspec-sync-specs/SKILL.md, so the projection has nothing to cover.`. Carries the declared signature `has no sync surface`.
    - M3.green: pass. Same command after the layout change.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario uninstall-removes-the-overlay` reports the scenario passing: after init the Codex overlays sit on the four `.agents/skills` surfaces, and uninstall removes each of them.
    - M4.red: fail, for the declared reason. With only the pin moved, it reported `uninstall-removes-the-overlay M1 the codex surfaces carrying the overlay after init are not the ones this scenario expects, …`, with `only installed: []`. Carries the declared signature `are not the ones this scenario expects`.
    - M4.green: pass. Same command after the layout change, which `removeOpenSpecSurfaceOverlay()` reads through `openspecOverlaySurfacesForTarget()`.
    - M5: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario authoring-alignment-overlay` reports the scenario passing, with exactly one alignment overlay on `.agents/skills/openspec-propose/SKILL.md` after init and after refresh.
    - M5.red: fail, for the declared reason. The pin alone made this scenario crash with `FileNotFoundError`, which is not a red. So the red was taken with the test updated to `.agents/skills` and `bin/keel.js` taken from `HEAD`: `authoring-alignment-overlay Codex propose surface lacks exactly one alignment overlay: …/codex/.agents/skills/openspec-propose/SKILL.md`. Carries the declared signature `propose surface lacks exactly one alignment overlay`.
    - M5.green: pass. Same command with the working tree's `bin/keel.js`.
    - M6: pass. Same scenario as M1. A new cell plants 1.6-layout Codex skills under `.codex/skills` and prompts in `CODEX_HOME`, runs `keel --install --target codex`, and finds exactly one overlay on each.
    - M6.detects: the mutation, `codexOpenSpecLayout()` returning `"agents"` unconditionally, made the scenario fail with `openspec-surface-overlay scenario 1.6-layout Codex surfaces lost their overlay: ['…/codex-legacy/.codex/skills/openspec-propose/SKILL.md', …]`. Carries the declared failure `1.6-layout Codex surfaces lost their overlay`. Restored from a copy afterwards.
    - M7: pass. `npm test` reports `validation --all failed for: published-specs-validate-strictly`, the one failure 1.2 owns, and nothing else. The Stop Rule held: no failing scenario outside F3's six.
    - Review:
      - Status: pass
      - Acceptance check: each red was the scenario failing because the pinned OpenSpec moved Codex's surfaces, and each green is Keel following them. M6 pins the other side: a 1.6-era repository keeps both its skills and its prompts. This repository's own tracked `.codex/skills` are that legacy case, and `bump_version.js` keeps sweeping them. `package.json`'s range stays `^1.4.1`; only the shrinkwrap moved.
      - Scope check: `git status --short` shows `npm-shrinkwrap.json`, `bin/keel.js`, `src/core/context.js`, and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [ ] 1.2 Six specs get a real Purpose, and the protocol says where 1.13 puts Codex's workflows
  - Covers:
    - D5
    - D6
    - F3
  - Read:
    - openspec/specs/keel-native-plugin-package/spec.md
    - openspec/specs/keel-single-task-goal-execution/spec.md
    - openspec/specs/keel-skill-sourcing-and-portability/spec.md
    - openspec/specs/keel-surface-evolution-policy/spec.md
    - openspec/specs/keel-touch-write-guard/spec.md
    - openspec/specs/keel-validation-runner/spec.md
    - AGENTS.md
  - Touch:
    - openspec/specs/keel-native-plugin-package/spec.md
    - openspec/specs/keel-single-task-goal-execution/spec.md
    - openspec/specs/keel-skill-sourcing-and-portability/spec.md
    - openspec/specs/keel-surface-evolution-policy/spec.md
    - openspec/specs/keel-touch-write-guard/spec.md
    - openspec/specs/keel-validation-runner/spec.md
    - AGENTS.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `published-specs-validate-strictly` runs the pinned OpenSpec 1.13.2 over every published spec and requires none to fail. Fails with: `published spec(s) fail strict validation`
    - M2 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a spec still fails for a reason other than its Purpose, because that is a requirement change rather than a missing sentence.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - M2: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [ ] 2.1 Release
  - Covers:
    - E1
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's effect is version markers, a changelog entry, a promoted spec, and a read-only doctor run. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: `node bin/keel.js --doctor` run with `rtl_ppa_prj` as its working directory prints `OpenSpec surfaces: ok`, and `git -C rtl_ppa_prj status --porcelain` is the same before and after
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate openspec-1-13 --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Codex OpenSpec commands are global prompts under `CODEX_HOME/prompts/opsx-*.md`" — `AGENTS.md`,
  `## Completion gates`. True only of a repository set up under OpenSpec 1.6.
  Updated by: 1.2
- I2: "its OpenSpec commands are global prompts under CODEX_HOME" — the comment on `installedTarget()`
  in `src/core/context.js`. Under 1.13 a Codex install writes `.agents/skills`, and the inference still
  holds because it keys on the Claude and OpenCode surfaces.
  Updated by: 1.1
- I3: "TBD - created by archiving change …" — the `## Purpose` of six published specs.
  Updated by: 1.2
- I4: "Keel itself still runs OpenSpec 1.6.0." — the 5.77.0 entry in `keel/CHANGELOG.md`. History, left
  as written; the new entry records the move.
  Updated by: 2.1

## Expectation Coverage

- E1: Keel ships the current OpenSpec, and every target's surfaces, a 1.6-era Codex repository's
  included, keep their Keel overlays (D1, D2, D3, D4). Covered by: 1.1, 2.1
