# Tasks

## 1. A timed-out host query is retried once

- [x] 1.1 Retry a `plugin list --json` that timed out once
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A query that times out once is retried
    - D1
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - docs/updating.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-retry` runs the real `keel --update` against fake hosts with `KEEL_UPDATE_QUERY_TIMEOUT_MS=4000` and a `codex plugin list --json` that holds 15 s on its first N calls: with N=1 the Codex line reports `5.0.0 -> 5.1.0` and the run exits 0; with N=9 the query runs twice, the line reads `failed`, names `codex plugin list --json`, `timed out twice` and `4 s`, and the run ends within 25 s. Fails with: `did not go on to update the Codex plugin`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-timeout`, `--scenario update-codex-refresh-retry` and `--scenario update-claude-refresh-retry` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b8df95ce996a5da658a905ad21c5e3f6d29093b4aed614182dcf4ac3fd21e1d2 (keel 5.146.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-retry` reports `update-host-query-retry scenario passed.`
    - M1.red: fail. Under the re-recorded contract, with `bin/keel.js` reverted to HEAD: `update-host-query-retry: a query that timed out once did not go on to update the Codex plugin: 'keel update: codex plugin: failed - \`codex plugin list --json\` timed out after 4 s'`, carrying the declared signature `did not go on to update the Codex plugin`.
    - M1.green: pass. With `hostQuery` running a timed-out query once more and reporting `timed out twice, after <n> s each`, the scenario passed.
    - M2: pass. `--scenario update-host-query-timeout`, `--scenario update-codex-refresh-retry` and `--scenario update-claude-refresh-retry` each report `scenario passed.` The #354 scenario's needle `timed out after 1.5 s` became `1.5 s`, since the message now reads `timed out twice, after 1.5 s each`; the new scenario asserts `timed out twice`.
    - M3: pass. `npm test`: `validation --all passed: baseline plus 291 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. The previous run failed this scenario at 1.5 s under parallel load; see Reauthorizations.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel --update` against fake hosts: one 15 s hold under a 4 s limit is retried and the Codex plugin updates with exit 0; a lasting hold runs the query twice, reads `failed … timed out twice, after 4 s each`, and ends within 25 s.
      - Scope check: `git status --short` lists `bin/keel.js`, `docs/updating.md`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: a lasting hang now costs twice the limit (60 s by default) before the component reads `failed`; accepted in D1 as the bound, against a longer single limit that every hang would pay.
    - Blocker: none
    - Reauthorizations: 2026-10-18 — M1's limits were widened from 1.5 s / 10 s / 12 s to 4 s / 15 s / 25 s after `npm test` showed the unheld retry exceeding 1.5 s under the suite's parallel load; anchor re-recorded and red and green re-run under the new text.

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - Contract:
    - M1:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a query that times out, exits nonzero, or prints no JSON MUST report that component `failed`" with no retry — `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1
- I2: "allowed 30 s where the update commands get five minutes, that times out, exits nonzero, or prints no JSON is reported `failed` instead" — `docs/updating.md`. Updated by: 1.1

## Expectation Coverage

- E1: One slow `plugin list --json` no longer leaves a plugin a release behind, and a lasting hang stays bounded (#365, D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
