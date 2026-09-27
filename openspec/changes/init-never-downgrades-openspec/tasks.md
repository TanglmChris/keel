# Tasks

## 1. Keep newer surfaces, and say so

- [x] 1.1 `keel --init` skips the OpenSpec rewrite for newer surfaces, and doctor reports the surfaces' OpenSpec and an untracked auto-update declaration
  - Covers:
    - keel-openspec-surface-overlay / Project init never downgrades OpenSpec surfaces / Newer surfaces are left alone
    - keel-openspec-surface-overlay / Project init never downgrades OpenSpec surfaces / Older surfaces are still refreshed
    - keel-target-surface-diagnostics / Doctor reports the OpenSpec that wrote the surfaces / Newer surfaces are named with their remedy
    - keel-target-surface-diagnostics / Doctor reports an auto-update declaration only one checkout carries / An untracked declaration is named
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `init-never-downgrades-openspec` scenario installs a Claude-target scratch repository with `keel --init`, restamps its OpenSpec skills `generatedBy: "99.0.0"`, and appends a sentinel line to one. It then runs `keel --init` again, and requires the sentinel kept and the output to name `99.0.0` and the skip. Fails with: `rewrote OpenSpec surfaces written by a newer OpenSpec`
    - M2: the same scenario runs `keel --doctor` on that repository and requires an `OpenSpec surfaces: warning` line naming `99.0.0`, Keel's OpenSpec version, and `keel --install --target claude`. Fails with: `no OpenSpec surfaces warning`
    - M3 (regression): the same scenario restamps the skills `generatedBy: "1.0.0"`, appends a sentinel, runs `keel --init`, and requires the sentinel gone, because older surfaces are still refreshed. Detects: `the guard skips whenever any generatedBy stamp is present` -> `skipped the OpenSpec refresh for surfaces older`
    - M4: the same scenario, in a Git scratch repository after `keel --install`, requires `plugin auto-update: warning` naming `git add .claude/settings.json` while the file is untracked, and `plugin auto-update: ok` once it is committed. Fails with: `did not say .claude/settings.json is untracked`
    - M5 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if verifying against `rtl_ppa_prj` would need anything beyond running `keel --doctor` there, because the owner forbade changing that repository from here.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:367083e08a1a2fa26466cd504fd90f5de9ecd2c2ea1573a4b9eefd8221c58ba4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario init-never-downgrades-openspec` reports the scenario passing. After the skills are restamped `99.0.0` and a sentinel is planted, a second `keel --init` keeps the sentinel and prints `keel: OpenSpec surfaces were written by OpenSpec 99.0.0, newer than the 1.6.0 Keel runs; skipped \`openspec init --force\` and \`openspec update --force\`, which would downgrade them (#168). …`.
    - M1.red: fail, for the declared reason. Calling the check's helper alone before any change reported `M1 keel --init rewrote OpenSpec surfaces written by a newer OpenSpec (99.0.0): the planted sentinel is gone.` That is #168 reproduced in a scratch repository. Carries the declared signature `rewrote OpenSpec surfaces written by a newer OpenSpec`.
    - M1.green: pass. Same helper after `surfaceGeneratorVersion()` and `compareVersions()` were added to `bin/keel.js`. `runProjectInit()` now skips both OpenSpec `--force` runs when the surfaces are newer, and still runs the installer and the overlay refresh.
    - M2: pass. Same scenario. Doctor prints `OpenSpec surfaces: warning - written by OpenSpec 99.0.0, newer than the OpenSpec Keel runs (1.6.0); keel --init leaves them unrewritten rather than downgrading them, and keel --install --target claude refreshes the protocol without touching them`.
    - M2.red: fail, for the declared reason. `M2 doctor printed no OpenSpec surfaces warning for 99.0.0 surfaces: []`. Carries the declared signature `no OpenSpec surfaces warning`.
    - M2.green: pass. Same helper after doctor printed the `OpenSpec surfaces` line after `openspec`. It is printed only when a stamp exists.
    - M3: pass. Same scenario. With the skills restamped `1.0.0`, `keel --init` rewrites the planted file and the sentinel is gone. It was green before any change, as a regression check should be.
    - M3.detects: the mutation, the guard skipping whenever any `generatedBy` stamp is present (`compareVersions(surfaces, resolved) > 0` removed), made the check fail with `M3 keel --init skipped the OpenSpec refresh for surfaces older than the OpenSpec it runs (1.0.0); only newer surfaces are protected.` Carries the declared failure `skipped the OpenSpec refresh for surfaces older`. Restored from a backup afterwards.
    - M4: pass. Same scenario. In a Git scratch repository after `keel --install`, doctor reports `plugin auto-update: warning - … Git does not track the file, so only this checkout declares it; commit it with \`git add .claude/settings.json\``, and `plugin auto-update: ok` once the file is committed.
    - M4.red: fail, for the declared reason. `M4 doctor did not say .claude/settings.json is untracked: 'plugin auto-update: ok - …'`. Carries the declared signature `did not say .claude/settings.json is untracked`.
    - M4.green: pass. Same helper after `pluginAutoUpdateDeclaration()` checks `git rev-parse --is-inside-work-tree` and `git ls-files --error-unmatch .claude/settings.json`.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 188 scenarios, 1 skipped: output-survives-the-pipe.` On this repository, doctor prints `OpenSpec surfaces: ok - written by OpenSpec 1.6.0; Keel runs 1.6.0` and `plugin auto-update: ok`. The Stop Rule held: nothing was run against `rtl_ppa_prj` in this task.
    - Review:
      - Status: pass
      - Acceptance check: M1's red is the reported incident itself, reproduced from a clean install, so the guard is proven against the failure that happened rather than an imagined one. M3 pins the other edge: an older stamp is still refreshed, so the guard cannot quietly become "never refresh". Doctor names a remedy for each of the two problems the affected repository has, and runs nothing.
      - Scope check: `git status --short` shows `bin/keel.js` and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/169 — Keel still runs OpenSpec 1.6.0, so a brand-new repository starts on its templates. This guard only stops the downgrade.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [ ] 2.1 Release, and show what doctor now tells the affected repository
  - Covers:
    - E1
    - E2
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
    - openspec/specs/keel-target-surface-diagnostics/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, promoted specs, and a read-only doctor run. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: `node bin/keel.js --doctor` run with `rtl_ppa_prj` as its working directory prints `OpenSpec surfaces: warning` naming 1.13.2 and 1.6.0, and `plugin auto-update: warning` naming `git add .claude/settings.json`, while `git -C rtl_ppa_prj status --short` is the same before and after
    - M3: both deltas are promoted, `node node_modules/.bin/openspec validate init-never-downgrades-openspec --strict` passes, and `npm test` reports no failing scenario
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

- I1: "Update the shrinkwrap to the newest 1.x … and keep it moving with releases" — the proposed fix
  in issue #168's body, of which this change does only the second half.
  Durable owner: https://github.com/TanglmChris/keel/issues/169
- I2: "plugin auto-update: ok - .claude/settings.json declares keel-marketplace autoUpdate: true" —
  doctor's line for a declaration in an untracked file, as 5.75.0 printed it.
  Updated by: 1.1

## Expectation Coverage

- E1: A repository whose OpenSpec surfaces are newer than Keel's keeps them through `keel --init`
  (D1, D2). Covered by: 1.1
- E2: `keel --doctor` run in the affected repository names each of its problems with the command
  that fixes it, so that repository is repaired from its own session (D3, D4). Covered by: 1.1, 2.1
