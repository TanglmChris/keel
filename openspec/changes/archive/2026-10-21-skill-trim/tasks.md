# Tasks

## 1. Load the checklist's conditional checks on demand, tell HANDOFF from the shift note

- [x] 1.1 Split review-checklist's conditional sections out, add the handoff paragraph, and check whole skill directories for parity
  - Covers:
    - keel-native-plugin-package / A skill's plugin copy carries every file of its source / A split-out file missing from the plugin copy is caught
    - keel-native-plugin-package / The review checklist loads its conditional checks on demand / The base checklist names the conditions and not their criteria
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - openspec/changes/skill-trim/design.md
    - src/skills/keel-review-checklist/SKILL.md
    - src/skills/keel-handoff/SKILL.md
  - Touch:
    - src/skills/keel-review-checklist/SKILL.md
    - src/skills/keel-review-checklist/conditional-checks.md
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - plugins/keel/skills/keel-review-checklist/conditional-checks.md
    - src/skills/keel-handoff/SKILL.md
    - plugins/keel/skills/keel-handoff/SKILL.md
    - scripts/validation/common.py
    - scripts/validation/hosts.py
    - scripts/validation/docs.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario review-checklist-conditional-checks`: the review checklist `SKILL.md` names `conditional-checks.md` and its four conditions, holds no `## Skill change review` or `## Planning artifact funnel`, and has fewer than 80 lines; `conditional-checks.md` holds both sections and the coupled and lens checks; and the handoff skill names `keel shift ready` and says the shift note selects no task. Fails with: `review-checklist-conditional-checks:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` passes with the whole-directory parity. `--scenario plan-funnel-guidance`, `--scenario review-checklist-defers-to-gate`, `--scenario findings-resolved-here`, `--scenario assertion-shape-count`, the baseline (skill doc requirements) and `--group docs` also pass. Detects: `deleting plugins/keel/skills/keel-review-checklist/conditional-checks.md` -> `conditional-checks.md`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:651c753a4e9f939030e2f0cf710138fad6152bcf9cd9f909b8023b518600a573 (keel 5.187.0)
    - M1: pass. Output: `review-checklist-conditional-checks scenario passed: the base checklist is 79 lines.`
      - The base `SKILL.md` went from 96 to 79 lines. It names `conditional-checks.md` and the four conditions in a `## Conditional checks` paragraph, and no longer holds the moved headings.
      - `conditional-checks.md` holds the moved text verbatim, under headings for the coupled, lens, skill change and planning funnel conditions.
      - The handoff skill names `keel shift ready` and says the shift note "selects no task".
    - M1.red: `review-checklist-conditional-checks: the review checklist does not name conditional-checks.md.` (5.187.0 skill text, before the split)
    - M1.green: `review-checklist-conditional-checks scenario passed: the base checklist is 79 lines.` The split, the handoff paragraph, and both plugin copies were applied. The first green attempt failed at 84 lines, because the new section was a bulleted list; it was compacted to one paragraph.
    - M2: pass.
      - `native-plugin-manifests` now compares every file of each skill directory.
      - These also pass:
        - `plan-funnel-guidance`, which reads `conditional-checks.md`;
        - `review-checklist-defers-to-gate`;
        - `findings-resolved-here`;
        - `assertion-shape-count` (74);
        - the baseline, where the skill doc requirements carry a new `conditional-checks.md` entry and the handoff gains `keel shift ready`;
        - `--group docs`, 23 scenarios.
    - M2.detects: mutation `deleting plugins/keel/skills/keel-review-checklist/conditional-checks.md` → `native-plugin-manifests plugin copy of keel-review-checklist lacks conditional-checks.md, so a reference to it resolves to nothing` (rc=1). The file was restored from a copy, and the scenario passes again. Before this change the check compared only `SKILL.md` and `guidance.md`, so the same deletion would have passed.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads the shipped skill texts that a session loads, which is the public surface of a skill, and checks that the base list names the conditions and not their criteria. M2's detection shows that the new file cannot drift unseen in the plugin copy.
      - Scope check: the changes are the ten Touch files and this change's record. The moved text is byte-identical to the original sections; only headings were added.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validation/common.py
    - scripts/validation/install.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8c4f57125c44fedf811f5f3e779258dae2b3797864ee50a396684e6c5434936c (keel 5.189.0)
    - M1: pass.
      - The branch merged origin/main at 5.188.0 (d6c14867).
      - `node scripts/bump_version.js minor` moved every marker to 5.189.0.
      - The changelog section "5.189.0 - The review checklist reads its conditional checks only when they apply" replaced the `TODO` stub and kept the stub's Version alignment line.
      - `version-alignment scenario passed.`
    - M2: pass. The two ADDED requirements were promoted into `keel-native-plugin-package`. `published-specs-validate-strictly scenario passed: 33 published specs validate strictly against openspec 1.14.0.`
    - M3: pass, on the second run.
      - First run, on commit 53f72f28: only `domain-execution-references` failed. It pinned the lens step to `SKILL.md`, and the check was widened under the recorded reauthorization.
      - Second run, on commit ad8807a6 (clean tree, started 15:03:28 at load 8, rc=0): `validation --all passed: baseline plus 318 scenarios, 1 skipped: output-survives-the-pipe.` and `evidence: 218 deterministic, 100 against a stand-in host, none on a real host (host measurements: docs/host-contract.md)`.
    - Review:
      - Status: pass
      - Acceptance check: M1 and M2 run the marker and published-spec scenarios on the release as written. M3 runs the whole suite on the release commit.
      - Scope check: the bump touched only the listed Touch files. `scripts/validation/install.py` changed only to read `conditional-checks.md` beside `SKILL.md`, and the reauthorization added it to Touch. This change's record also changed.
      - Findings:
        - 1.1's regression list missed `domain-execution-references`, a further check that pinned moved text to `SKILL.md`. The full gate caught it. The check now reads the conditional file too. Resolved here: M3
    - Blocker: none
    - Reauthorizations: 2026-10-21 15:10, before any Evidence was recorded. The first `npm test` on commit 53f72f28 failed only `domain-execution-references`: "skills/keel-review-checklist lacks the on-demand lens consult step ('Execution and review checks')". That check pins the lens consult step to `SKILL.md`, and 1.1 moved the step to `conditional-checks.md`. Under D4, moved text stays checked where it now lives. `scripts/validation/install.py` joins Touch so that the check reads a skill's `SKILL.md` together with its `conditional-checks.md`.

## Invalidates

- I1: "A referenced `guidance.md` travels with the body that names it". This is the comment beside the parity check in `scripts/validation/hosts.py`, which compares only `SKILL.md` and `guidance.md`. Updated by: 1.1.

## Expectation Coverage

- E1: The review checklist's base list is short and its conditional criteria load on demand, the handoff skill tells HANDOFF from the shift note, and the plugin copies of skills are checked as whole directories (#411 rows 7 and 8; D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
