# Tasks

## 1. The remedy of what lags

- [x] 1.1 The drift line names the protocol refresh when the protocol lags, and the plugin update only when the plugin or CLI lags
  - Covers:
    - keel-native-runtime-projection / The session projection reports runtime version alignment / A lagging protocol names the protocol refresh
    - keel-native-runtime-projection / The session projection reports runtime version alignment / A stale runtime is reported on both channels
    - D1
    - D2
    - F1
    - F2
  - Read:
    - plugins/keel/scripts/session-start.js
    - src/core/context.js
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario runtime-version-drift` runs the shipped SessionStart hook with plugin and CLI at one version and a `CLAUDE.md` managed block stamped older, and requires the drift line to name `keel --install --target claude` and not `claude plugin update`; the existing case, plugin and CLI behind the protocol, still names the plugin update. Fails with: `runtime-version-drift`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:18472a187a7454d0825146c4b5010033b3d1fa1ae7a27a31f6e23c69aaec390f
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario runtime-version-drift` reports `runtime-version-drift scenario passed.`
    - M1.red: fail. Before the change the scenario reported `runtime-version-drift a protocol behind the plugin and CLI does not name the protocol refresh: …`, carrying the declared signature `runtime-version-drift`; the preceding assertion, that plugin and CLI behind the protocol still name `claude plugin update`, already passed.
    - M1.green: pass. With the remedy chosen per lagging item, the protocol refresh named with `keel context`'s target rule, the scenario passes; `runtime-versions-are-checked` and `assertion-shape-count` still pass.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the shipped hook with a planted manifest and a fake CLI against two repositories and reads the model payload for the named remedy.
      - Scope check: `git status --short` lists `plugins/keel/scripts/session-start.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: the target rule is copied from `src/core/context.js` `installedTarget` rather than shared, because the hook runs from the plugin directory and loads no module from `src/`; the comment beside the copy names its origin.

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
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-runtime-projection/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js patch` moves every marker to the next patch version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-native-runtime-projection/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ed2bd809d78693d4f638ab709061b8bc77b933e50d902821b0a6c74f5e63bc83
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.99.6. With the 5.99.6 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding one; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirement says which remedy each lagging item gets with its scenario, and the changelog names the issue.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.99.6 reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A session told its runtime disagrees is given the remedy that fixes the item that lags (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
