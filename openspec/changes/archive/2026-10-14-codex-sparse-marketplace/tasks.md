# Tasks

## 1. Codex refresh

- [x] 1.1 The Codex marketplace refresh is retried once, a lasting failure names the sparse remedy, and the documented marketplace is sparse
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A failed Codex refresh is retried once
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A lasting Codex refresh failure names the sparse remedy
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A local Codex marketplace is reported, not re-pointed
    - D1
    - D2
    - D3
    - D4
  - Read:
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - README.md
    - README.zh-CN.md
    - docs/updating.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-codex-refresh-retry` runs the real `keel --update` against fake hosts. With the Codex marketplace upgrade failing once, it runs twice, `codex plugin add` runs once, the Codex line says `5.0.0 -> 5.1.0`, and the exit is 0. With it failing every time, it runs twice, `plugin add` does not run, the Codex line reads `failed` and names `sparse_paths`, `.agents/plugins` and `plugins/keel`, and the exit is nonzero. `.agents/plugins/marketplace.json` exists and the plugin source it names lies under `plugins/keel`; both READMEs and `docs/updating.md` name `--sparse .agents/plugins --sparse plugins/keel`. Fails with: `update-codex-refresh-retry: the Codex marketplace upgrade ran 1`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts` passes with its local-marketplace arm requiring `--sparse .agents/plugins --sparse plugins/keel` in the `manual` line. Fails with: `--sparse`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f20bddf244cab6cb5f46b628e8ca3ceada3b80a6a703ffe484470f97c93178f5
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-codex-refresh-retry` reports `update-codex-refresh-retry scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `update-codex-refresh-retry: the Codex marketplace upgrade ran 1 time(s) after one failure, not 2: …`, carrying the declared signature `update-codex-refresh-retry: the Codex marketplace upgrade ran 1`.
    - M1.green: pass. With the retry and the sparse remedy in `updateCodexPlugin`, the scenario next stopped at `README.md does not add the Codex marketplace sparse.`; with both READMEs and `docs/updating.md` updated, it passed.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts` reports `update-covers-installed-hosts scenario passed.`
    - M2.red: fail. With the local-marketplace arm requiring the sparse command, it reported `update-covers-installed-hosts: the manual Codex line does not name the sparse Git marketplace command (--sparse): …`, carrying the declared signature `--sparse`.
    - M2.green: pass. With `CODEX_SPARSE_FLAGS` in the `manual` hint, the scenario passed.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 278 scenarios, 1 skipped: output-survives-the-pipe.` A first run failed `assertion-shape-count` on two compound `if`s in the new scenario; each failure now has its own message.
    - Review:
      - Status: pass
      - Acceptance check: the new scenario runs the real `keel --update` against fake hosts whose Codex marketplace upgrade fails once and then always, and counts the upgrade and add calls, the exit, and the Codex line; it also checks that the Codex catalog's plugin source lies under the sparse path and that the docs use it. The real-machine behavior (sparse upgrade 19–25 s versus a 44 s whole clone) is recorded in #329.
      - Scope check: `git status --short` lists `bin/keel.js`, `README.md`, `README.zh-CN.md`, `docs/updating.md`, `scripts/validate_plugin.py`, and this change's directory.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-native-plugin-package/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ded2a7a6e3876ac63339a8af829c484dd7c5bc23735109558b466216c76a3b8c
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.132.0; with the 5.132.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its counterpart in `openspec/specs/keel-native-plugin-package/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and the promoted spec; the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "then `codex plugin marketplace add TanglmChris/keel --ref main`" — the `manual` hint in `bin/keel.js` and `docs/updating.md`. Updated by: 1.1
- I2: "names the source path and `codex plugin marketplace add TanglmChris/keel --ref main`" — `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1
- I3: "Codex plugin maybe 5.126.0 (`keel --update` hung on `codex plugin list --json`)" — the previous keel-maint shift note. Discard reason: the note was consumed into shift history; this session measured 5.131.0 installed.

## Expectation Coverage

- E1: On a slow link the Codex plugin still updates through `keel --update`, or the owner is told the one-line remedy (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: `codex plugin list --json` hung for minutes once and then returned in 2–3 s; the cause is unidentified and each host call may take 5 minutes. Durable owner: https://github.com/TanglmChris/keel/issues/329

## Change Evidence

- C1: pass. `npm test` on the 5.132.0 tree reports `validation --all passed: baseline plus 278 scenarios, 1 skipped: output-survives-the-pipe.`
