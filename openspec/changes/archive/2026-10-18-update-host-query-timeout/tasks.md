# Tasks

## 1. A host query is bounded and honest

- [x] 1.1 `plugin list --json` gets a 30 s limit; a failed query is `failed`, not `absent`
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A hung host query is a failure, not an absent host
    - D1
    - D2
    - D3
    - D4
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - docs/updating.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-timeout` runs the real `keel --update` against fake `npm`, `claude` and `codex` with `KEEL_UPDATE_QUERY_TIMEOUT_MS=1500`: a `codex plugin list --json` that sleeps 10 s makes the Codex line read `failed` naming `codex plugin list --json` and `timed out after 1.5 s`, never `absent`; no `codex plugin marketplace upgrade` runs; the Claude line still reports `updated`; the run exits nonzero within 9 s; a `claude plugin list --json` that exits 3 reads `failed` naming `exited 3`; a missing `codex` executable still reads `absent`; `--dry-run` with the sleeping query exits 0. Fails with: `was reported absent`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts` and `--scenario update-codex-refresh-retry` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c89c1dbc390dee98a11074c2389ed75176eef44fbc1dcfe874895178ddf264fe (keel 5.141.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-timeout` reports `update-host-query-timeout scenario passed.`
    - M1.red: fail. With the scenario written first: `update-host-query-timeout: a claude plugin list --json that exited 3 was reported absent: 'keel update: claude plugin: absent - Claude Code is not installed here or has no Keel plugin'`, carrying the declared signature `was reported absent`. (An earlier ordering first hit the 10 s hang, which the old five-minute limit let finish as `updated`; the exit-status case was moved first so the red shows the misreport.)
    - M1.green: pass. With `hostQuery` (a `KEEL_UPDATE_QUERY_TIMEOUT_MS` or 30 s limit; `absent` on ENOENT or cmd.exe's not-recognized; otherwise `timed out after <n> s`, `exited <status>` or `printed no JSON`), `claudeKeel`/`codexKeel` returning `{ failed }`, and both updates reporting `failed` for a failed query before or after their steps, the scenario passed.
    - M2: pass. `--scenario update-covers-installed-hosts` and `--scenario update-codex-refresh-retry` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 286 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel --update` against fake hosts: a 10 s `codex plugin list --json` under a 1.5 s limit reads `failed … timed out after 1.5 s`, not `absent`, runs no Codex update command, leaves the Claude line `updated`, exits nonzero, and returns well inside 9 s; a query exiting 3 reads `failed … exited 3`; a missing executable still reads `absent`; a dry run with the hung query exits 0.
      - Scope check: `git status --short` lists `bin/keel.js`, `docs/updating.md`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the Windows rule — cmd.exe's `is not recognized as an internal or external command` read as `absent` — keeps the old outcome there for a missing host but is not exercised by any check here, which runs on macOS; a missing host on Windows that prints something else now reads `failed`, which is at worst more cautious than `absent`.
        - Discard reason: the 2026-10-14 hang itself was not reproduced (1.1–1.4 s on 2026-10-18), so its cause stays unknown; this bounds its cost and names it rather than preventing it.
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
    - Contract: keel-task-capsule/v1 sha256:7238a93a42afc4167f893d3650bd2778a13828ee84c849dbfaa63588fbca4897 (keel 5.141.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.141.0 → 5.142.0; with the "A hung host query is bounded and reported as one" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced its counterpart in `keel-native-plugin-package`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`absent`: the host is not installed or has no Keel plugin;" with no mention of a query that failed — `docs/updating.md`. Updated by: 1.1
- I2: "A host that is absent or has no Keel plugin MUST be reported `absent`" with no rule for a failed query — `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A hung `plugin list --json` stalls `keel --update` for at most 30 s and is reported as the failure it is, not as an absent host (#354, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
