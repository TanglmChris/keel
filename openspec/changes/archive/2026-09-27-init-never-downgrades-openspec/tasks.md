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

- [x] 1.2 Doctor's protocol remedy names `keel --install`, not the `keel --init` that caused #168
  - Covers:
    - keel-target-surface-diagnostics / Doctor's protocol remedy does not rewrite OpenSpec surfaces / A repository behind its install is sent to install
    - D5
    - F1
    - F5
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `marker-version-is-read` requires the behind-repository `protocol` warning to name `keel --install` and not `keel --init`. Fails with: `was told to run keel --init`
    - M2 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if another surface also names `keel --init` as the refresh for a behind protocol, because that belongs in the same Touch.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:066e7861cd15954660bd085b123f69feb5cbab0036b1050a5fbc77116a50e9d2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-marker-version-is-read` reports the scenario passing. The behind-repository line reads `protocol: warning - repo declares 5.14.0, this CLI is 5.77.0 — the repository is behind its install; run keel --install --target claude to bring the protocol forward; it leaves OpenSpec's surfaces as they are (#168)`.
    - M1.red: fail, for the declared reason. `the-marker-version-is-read scenario: a repository behind its install was told to run keel --init; got 'protocol: warning - … run keel --init --target claude to bring the protocol forward'.` Carries the declared signature `was told to run keel --init`. The first draft checked the `keel --install` needle before this check and failed on that instead, so the order was swapped to make the red name the defect.
    - M1.green: pass. Same command after `printProtocolVersionDrift()` named `keel --install --target <t>`. A first wording that explained itself by mentioning `keel --init` failed the same check, and was reworded. The duplicate `compareVersions()` 1.1 had added was removed: the earlier definition, which is the one in effect, has the same sign semantics.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 188 scenarios, 1 skipped: output-survives-the-pipe.`, run after 2.1 filled the 5.77.0 changelog stub. Before that, `version-alignment` refused the unfilled stub, and `validation-runner` failed as a knock-on of it. The Stop Rule held: `grep` found no other surface in `plugins/`, `src/core/`, or `AGENTS.md` naming `keel --init` as the refresh for a behind protocol. The not-comparable branch keeps `keel --init` for a repository that was never set up (D5).
    - Review:
      - Status: pass
      - Acceptance check: this defect was found by 2.1's read-only doctor run in the affected repository. The remedy doctor printed there was the command that caused #168, so this repair is what makes E2 true for it. The check forbids `keel --init` on the line outright, which is why even an explanatory mention was refused.
      - Scope check: `git status --short` shows `bin/keel.js` and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory and the version markers and changelog 2.1 had written.
      - Findings: none
    - Blocker: none
    - Reauthorizations: 2026-09-27 — D5 added to Covers. `change-close` refused the change because E2 cites D5, the decision this task implements, and no task's Covers named it. The checks are unchanged, so M1 and M2 evidence is kept with `--keep-evidence`.

## 2. Close

- [x] 2.1 Release, and show what doctor now tells the affected repository
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
    - Contract: keel-task-capsule/v1 sha256:cf0d7050e7f1edb0cad391c9972f11eb0017da75b4196abbf87083050155e17a
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.76.0 to 5.77.0. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.77.0 section written into the stub. The Stop Rule held.
    - M2: pass. Running `node bin/keel.js --doctor` from inside `rtl_ppa_prj` printed three warnings, each with its remedy:
      - `OpenSpec surfaces: warning - written by OpenSpec 1.13.2, newer than the OpenSpec Keel runs (1.6.0); keel --init leaves them unrewritten rather than downgrading them, and keel --install --target claude refreshes the protocol without touching them`;
      - `protocol: warning - … run keel --install --target claude to bring the protocol forward; it leaves OpenSpec's surfaces as they are (#168)`;
      - `plugin auto-update: warning - … Git does not track the file, so only this checkout declares it; commit it with \`git add .claude/settings.json\``.

      A `shasum` of `git -C rtl_ppa_prj status --porcelain` taken before and after is identical. The `protocol` line's 5.77.0 is this working tree's, and becomes true once 5.77.0 is released.
    - M3: pass. Four ADDED requirements are promoted: one into `keel-openspec-surface-overlay` and three into `keel-target-surface-diagnostics`. `node node_modules/.bin/openspec validate init-never-downgrades-openspec --strict` reports the change valid, `openspec validate --specs --strict` reports `26 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 188 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the owner's two constraints both hold. Nothing in `rtl_ppa_prj` changed, which the identical status hash shows, and every problem it has is now named by its own `keel --doctor` together with the command that fixes it. M2's first run is also what found 1.2's defect, a remedy that would have repeated #168, so the verification did its job before release rather than after.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and both promoted specs, this task's Touch, plus the files 1.2 declared complete and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/169 — Keel still runs OpenSpec 1.6.0, so the `OpenSpec surfaces` warning will persist in the affected repository until Keel moves to 1.13.x.
    - Blocker: none
    - Reauthorizations: 2026-09-27 — Re-recorded after task 1.2 was added mid-release. 2.1's own M2 found doctor sending the affected repository to `keel --init`, and adding 1.2 changed E2's wording (`D5`, `Covered by: 1.1, 1.2, 2.1`), which 2.1 covers. No 2.1 evidence had been recorded.

## Invalidates

- I1: "Update the shrinkwrap to the newest 1.x … and keep it moving with releases" — the proposed fix
  in issue #168's body, of which this change does only the second half.
  Durable owner: https://github.com/TanglmChris/keel/issues/169
- I3: "the repository is behind its install; run keel --init --target ${target} to bring the protocol
  forward" — `printProtocolVersionDrift()` in `bin/keel.js`, doctor's remedy for a behind protocol,
  which sends the reader to the command that rewrote OpenSpec surfaces in #168.
  Updated by: 1.2
- I2: "plugin auto-update: ok - .claude/settings.json declares keel-marketplace autoUpdate: true" —
  doctor's line for a declaration in an untracked file, as 5.75.0 printed it.
  Updated by: 1.1

## Expectation Coverage

- E1: A repository whose OpenSpec surfaces are newer than Keel's keeps them through `keel --init`
  (D1, D2). Covered by: 1.1
- E2: `keel --doctor` run in the affected repository names each of its problems with the command
  that fixes it, so that repository is repaired from its own session (D3, D4, D5). Covered by: 1.1, 1.2, 2.1
