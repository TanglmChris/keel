# Tasks

## 1. The Claude refresh is retried and a failure names the host's error

- [x] 1.1 Retry `claude plugin marketplace update` once; a failed step names its last stderr line
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A failed Claude refresh is retried once
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A lasting Claude refresh failure says so with the host's error
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A failed host step names the host's error
    - D1
    - D2
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - docs/updating.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-claude-refresh-retry` runs the real `keel --update` against fake `npm`, `claude` and `codex` whose failing calls write two stderr lines: a marketplace update that fails once runs twice, then `claude plugin update` once, and the line reports `5.0.0 -> 5.1.0` with exit 0; one that keeps failing runs twice, runs no `claude plugin update`, exits nonzero, and its line reads `failed`, `failed twice` and the last stderr line only; a failing `claude plugin update` runs once and its line names `exited 1` and its last stderr line. Fails with: `ran 1 time(s) after one failure, not 2`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-codex-refresh-retry`, `--scenario update-host-query-timeout` and `--scenario update-covers-installed-hosts` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:28a4e17e47106f9f5110c34eb64001516d9c14eee4829989f47cf061b62802d3 (keel 5.143.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-claude-refresh-retry` reports `update-claude-refresh-retry scenario passed.`
    - M1.red: fail. With the scenario and the fake's stderr lines written first and `bin/keel.js` unchanged: `update-claude-refresh-retry: the Claude marketplace update ran 1 time(s) after one failure, not 2: [...]`, carrying the declared signature `ran 1 time(s) after one failure, not 2`. The red was run before this change directory was authored; the fingerprint above was recorded before the evidence and the final assertion split.
    - M1.green: pass. With `hostFailure` (spawn error, or `exited <status>: <last stderr line>`) used by `runHostSteps`, and `updateClaudePlugin` running the marketplace update at most twice before `claude plugin update`, the scenario passed.
    - M2: pass. `--scenario update-codex-refresh-retry`, `--scenario update-host-query-timeout` and `--scenario update-covers-installed-hosts` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 288 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. An earlier run failed `assertion-shape-count` (81 OR-guarded sites, 80 recorded) on a combined version/exit check in the new scenario; it was split into two messages.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel --update` against fake hosts: one refresh failure runs the refresh twice, `claude plugin update` once, reports `5.0.0 -> 5.1.0` and exits 0; a lasting failure runs it twice, never runs `claude plugin update`, exits nonzero, and reads `failed twice` with only the last stderr line; a failing `claude plugin update` runs once and names `exited 1` and its last stderr line.
      - Scope check: `git status --short` lists `bin/keel.js`, `docs/updating.md`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the cause of the owner's two 2026-10-18 failures is still unknown, since the stderr was not captured then; this retries past it and makes the next one visible rather than preventing it.
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
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a3a7d913bb61874e415eeefb19d394d930cc19ae612f5582d92b0546ac5c3e40 (keel 5.143.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.143.0 → 5.144.0; with the "The Claude marketplace refresh is retried once" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its counterpart in `keel-native-plugin-package`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`failed`: the command that failed, which also makes `keel --update` exit nonzero." with no mention of the host's error, and the Claude refresh's lack of a retry beside "`keel --update` retries the refresh once" for Codex — `docs/updating.md`. Updated by: 1.1
- I2: "The Codex marketplace refresh MUST be retried once when it fails" with no rule for the Claude refresh — `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A Claude marketplace refresh that fails once no longer leaves the plugin a version behind, and a failure that lasts shows the host's own error (#359, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
