# Tasks

## 1. The gate

- [x] 1.1 Read `skip_specs` in change-close
  - Covers:
    - keel-core-gates / change-close honors a declared skip of specs / A marked change without specs passes the delta-spec check
    - keel-core-gates / change-close honors a declared skip of specs / A marked change that carries a spec fails by name
    - keel-core-gates / change-close honors a declared skip of specs / An unmarked change still needs a delta spec
    - D1
    - D2
  - Read:
    - openspec/changes/skip-specs-close/design.md
    - src/core/gates.js
  - Touch:
    - src/core/gates.js
    - scripts/validation/skipspecs.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario change-close-skip-specs`: in a scratch repository, `keel gate change-close --change demo --action archive --json` on a change whose `.openspec.yaml` holds `skip_specs: true` and which has no `specs/` directory lists no problem coded `missing-delta-spec` and none coded `skip-specs-with-specs`, and the same with `--action sync`; with `specs/demo/spec.md` added it lists `skip-specs-with-specs` naming `specs/demo/spec.md` and no `missing-delta-spec`; with the marker removed, and with `skip_specs: false`, and with an unreadable `.openspec.yaml` (a directory of that name), it lists `missing-delta-spec`. Fails with: `change-close-skip-specs:`
    - M2 (regression): run one at a time, each passes: `--scenario archive-keeps-tracked-evidence`, `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d258e7477bf223d261079b83f68f5c8de6f4db6eb80d0ba56000e2f42091023c (keel 5.225.0)
    - M1: pass. `change-close-skip-specs scenario passed.` (exit 0). In a scratch repository a change with `skip_specs: true` and no `specs/` lists neither `missing-delta-spec` nor `skip-specs-with-specs` for `--action archive` and `--action sync`; with `specs/demo/spec.md` added the result lists `skip-specs-with-specs` naming the file and no `missing-delta-spec`; with no marker, with `skip_specs: false`, and with `.openspec.yaml` replaced by a directory, it lists `missing-delta-spec`.
    - M1.red: fail. Before the change, exit 1: `change-close-skip-specs: a marked change without specs still gets missing-delta-spec for archive: ['missing-verification-form', …, 'missing-delta-spec', …]`.
    - M1.green: pass. `declaresSkipSpecs` and `firstFileUnderSpecs` in `src/core/gates.js`, and the `change-close` branch that uses them (D1, D2).
    - M2: pass. Run one at a time at load 7.6, each exit 0: `archive-keeps-tracked-evidence scenario passed.` and `assertion-shape-count scenario passed: 74 sites, a bound on a shape and not a count of defects.`
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel gate change-close --json`, a marked change no longer gets `missing-delta-spec`, a marker beside a spec file fails by name, and an unmarked, `false` or unreadable declaration still requires a spec (M1).
      - Scope check: `git status --short` lists `src/core/gates.js`, `scripts/validation/skipspecs.py`, `scripts/validation/registry.py` and this change's directory, all in Touch or the record layer.
      - Findings: Discard reason: the gate does not run OpenSpec to ask whether it honors the marker (D3); a marker OpenSpec rejects is caught by `keel openspec archive`, and no scenario fabricates a malformed marker beyond the unreadable file.
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
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - docs/host-contract.md
    - openspec/specs/keel-core-gates/spec.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that state.
    - M2: the delta is promoted into `keel-core-gates`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bdb6b1cbc8192332425e8e92c66aea2c00464281b111260a6efbe5c6aeca3d59 (keel 5.225.0)
    - M1: pass. `node scripts/bump_version.js minor` moved every marker 5.225.0 → 5.226.0 and the changelog entry replaced the stub. `version-alignment scenario passed.` (exit 0).
    - M2: pass. The requirement and its three scenarios are appended to the published `keel-core-gates`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`, started at load 6.3: `validation --all passed: baseline plus 395 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), the 394 of 5.225.0 plus this change's one.
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.226.0, the promoted spec validates and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, task 1.1's files and this change's directory, all in Touch of 1.1 or 2.1.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "archive requires at least one change delta spec." — the message of `missing-delta-spec` in `src/core/gates.js`, true for every change without the marker and so left as it is. Discard reason: the sentence stays correct for an unmarked change, which M1 of 1.1 pins.

## Expectation Coverage

- E1: A change declaring `skip_specs: true` with no `specs/` can pass `change-close` (#517, expectation 1; D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: A marker beside a `specs/` file is reported by name rather than passed (#517, the "stabler" alternative; D2). Covered by: 1.1
