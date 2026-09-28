# Tasks

## 1. Name the reload, not the update

- [x] 1.1 The drift line recognizes an update the host already installed
  - Covers:
    - keel-native-runtime-projection / A drift report names an update the host already installed / An installed update is named as needing only a reload
    - keel-native-runtime-projection / A drift report names an update the host already installed / A PATH copy matching the installed version is not called a shadow
    - keel-native-runtime-projection / A drift report names an update the host already installed / No install record keeps the current report
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F3
  - Read:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `drift-names-a-pending-reload` scenario plants the packaged plugin at `plugins/cache/mkt/keel/5.80.0` under a scratch directory, with an `installed_plugins.json` four levels above it recording `keel@mkt` at `…/keel/5.81.0`, and a repository declaring protocol 5.81.0. On both channels the drift line must name `already installed plugin 5.81.0` and `/reload-plugins`, and must not name `claude plugin update`. Fails with: `named claude plugin update for an update the host already installed`
    - M2: the same run puts a `keel` reporting 5.81.0 on PATH, and requires neither channel to say `shadows` or name `@christang/keel@5.80.0`. Fails with: `called a PATH keel at the installed version a shadow`
    - M3 (regression): the same scenario rewrites the record to name only another plugin (`other@mkt` at `…/cache/mkt/other/9.9.9`) and requires the line to still name `claude plugin update` and not `already installed`, and with the record removed requires the line byte-identical to the one with the other-plugin record. Detects: `the same-plugin parent comparison removed` -> `read another plugin's install as this one's`
    - M4 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the existing `runtime-version-drift` or `plugin-runs-its-own-cli` scenarios need their assertions changed, because D5 says the no-record wording does not move.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c59f1d9bd05e77afaf1b4443837f48c0b3e991cd3d1fe09bf58e367550e0394c
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario drift-names-a-pending-reload` reports the scenario passing. With the record naming `keel@mkt` at `…/keel/5.81.0` and 5.80.0 loaded, both channels read `… applies after \`/reload-plugins\` or at the next session start. The host has already installed plugin 5.81.0, so nothing needs updating.`
    - M1.red: fail, for the declared reason. Before any hook change the scenario reported `drift-names-a-pending-reload M1 additionalContext named claude plugin update for an update the host already installed: "… Updating is \`claude plugin update\`, which Keel names and does not run. …"`, which is the line from #172 reproduced in a scratch cache.
    - M1.green: pass. Same command after `pendingInstall()` was added and `versionReport()` swapped the update sentence for the installed one. The first attempt stayed red: node loads the hook through its real path (`/private/var/…` on macOS) while the record holds the path as written, so both sides are now compared through `fs.realpathSync`.
    - M2: pass. Same run, with a PATH `keel` at 5.81.0: neither channel says `shadows` or names `@christang/keel@5.80.0`.
    - M2.red: fail, for the declared reason. With M1 green and the shadow sentence untouched, the scenario reported `drift-names-a-pending-reload M2 additionalContext called a PATH keel at the installed version a shadow: "… or align it with \`npm i -g @christang/keel@5.80.0\`."`.
    - M2.green: pass. Same command after the shadow sentence judged PATH against `pending || cli`.
    - M3: pass. Same scenario. With the record naming only `other@mkt` at `…/cache/mkt/other/9.9.9`, both channels still name `claude plugin update` and not `already installed`, and removing the record leaves both channels byte-identical to that run. `runtime-version-drift`, `plugin-runs-its-own-cli`, and `native-plugin-session-start` pass unchanged, so the Stop Rule held.
    - M3.detects: the mutation, the same-plugin parent comparison removed (`if (parent !== path.dirname(root)) continue;` replaced by a comment), made the check fail with `drift-names-a-pending-reload M3 additionalContext read another plugin's install as this one's: …`. Carries the declared failure `read another plugin's install as this one's`. Restored from a backup afterwards and the scenario passes again. The first mutation run passed, because the fixture never created the other plugin's directory and the realpath step dropped the entry before the comparison ran. The fixture now creates it, as the host would.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 189 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1's red is the #172 line itself, so the fix is proven against what actually happened. M2 closes the second half of the report, the downgrade advice. M3 pins that the new read cannot spread: another plugin's record and no record at all both leave the 5.78.0 wording, and the three existing drift scenarios pass with no assertion changed.
      - Scope check: `git status --short` shows `plugins/keel/scripts/session-start.js` and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: Resolved here: M1 and M3 — the review checklist found each check guarding two distinct failures with one condition, so an absent `already installed` sentence would have been reported as naming `claude plugin update`. Each is now split into its own message. The scenario and `npm test` pass after the split.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
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
    - Reason: this task's effect is version markers, a changelog entry, and a promoted spec. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: the delta is promoted, `node node_modules/.bin/openspec validate drift-names-a-pending-reload --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e83c63975472ec5607e6549bdc9bf79c738444e9eb74a57c1f78aa0c765d4c3e
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.78.0 to 5.79.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.79.0 section written into the stub. The Stop Rule held.
    - M2: pass. The ADDED requirement is promoted into `keel-native-runtime-projection`. `node node_modules/.bin/openspec validate drift-names-a-pending-reload --strict` reports the change valid, `openspec validate --specs --strict` reports `26 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 189 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: E1 holds on both halves: 1.1's M1 and M2 prove the reload-only wording and the PATH judgement, and this task carries them to a released version with the requirement promoted where the next reader of the spec will find it.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the promoted spec, this task's Touch, plus the files 1.1 declared complete and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Updating is `claude plugin update`, which Keel names and does not run." — `versionReport()` in
  `plugins/keel/scripts/session-start.js`, printed even when the host already installed the update.
  Updated by: 1.1
- I2: "or align it with `npm i -g @christang/keel@<loaded plugin version>`" — the same function's
  shadow sentence, which names a downgrade when the installed plugin already matches PATH.
  Updated by: 1.1

## Expectation Coverage

- E1: A session whose plugin update is already installed is told only to reload, and is never told
  to update the plugin or downgrade the global CLI (D3, D4, D5). Covered by: 1.1, 2.1
