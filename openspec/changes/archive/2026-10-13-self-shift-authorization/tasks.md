# Tasks

## 1. self-shift

- [x] 1.1 `self-shift` is a standing-authorization name, and the desktop `ready --wake` reads it
  - Covers:
    - keel-standing-authorization / A session's own shift change on the desktop app is a named authorization / self-shift is accepted and listed
    - keel-standing-authorization / A session's own shift change on the desktop app is a named authorization / A scoped self-shift is refused
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A declared self-shift lets the session take the four steps without asking
    - D1
    - D2
    - D3
    - D4
    - F1
  - Read:
    - src/core/config.js
    - src/core/shift.js
  - Touch:
    - src/core/config.js
    - src/core/shift.js
    - keel/config.yaml
    - README.md
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` passes. In a temporary repository, `authorize:` with `commit` and `self-shift` is read and `keel --doctor` lists `self-shift`; `self-shift:anything` is refused by name. A desktop `keel shift ready --wake` says `Standing-authorized by \`self-shift\`` when it is declared, and names `self-shift` without that sentence when it is not. Both shift-change docs name `self-shift`. Fails with: `self-shift-authorization:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:215603326f65ace562497a2a90faa4cc456163e39bb3accc7e6f3631188390d0
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario self-shift-authorization` reports `self-shift-authorization scenario passed.`
    - M1.red: fail. With the scenario written first and `self-shift` absent from the vocabulary, it reported `self-shift-authorization: self-shift was not read and listed as a standing authorization: …`, carrying the declared signature `self-shift-authorization:`.
    - M1.green: pass. With `self-shift` in `STANDING_AUTHORIZATION_ACTIONS`, the desktop hint reading it, and the README, config comment and docs updated, the scenario passed. It says `Standing-authorized by \`self-shift\`` only when declared, names `self-shift` otherwise, and `self-shift:anything` is refused by name. `shift-restore-authorization`, `shift-desktop-wake`, `standing-authorization-declaration` and `continuation-docs` still pass.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 277 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the real `keel --doctor` and a desktop `keel shift ready --wake` in a temporary repository, once with `self-shift` declared, once without, and once with a scoped form.
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/shift.js`, `keel/config.yaml`, `README.md`, both shift-change docs, `scripts/validate_plugin.py`, and this change's own directory. `ready`'s result also carries `worktree`, which the hint reads.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the specs
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
    - openspec/specs/keel-shift-change/spec.md
    - openspec/specs/keel-standing-authorization/spec.md
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
    - M2: the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`, the ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d4db9d03752a01c5687abec3db1124049b9f2808a895eba20d088ae931ed4727
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.130.0; with the 5.130.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its counterpart in `openspec/specs/keel-shift-change/spec.md`, and the ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the two scenarios check the markers, the changelog, and both promoted specs, and the full suite runs on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, both published specs, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: The accepted-names vocabulary "… push-protected:<branch glob>[@<role>], shift-restore" — `README.md`, the `keel/config.yaml` comment, and `ACCEPTED_AUTHORIZE_NAMES` in `scripts/validate_plugin.py`. Updated by: 1.1
- I2: The desktop recipe's closing line "Keel creates no task. Restoring unattended needs …", which says nothing of the outgoing steps' confirmation — `src/core/shift.js` and both shift-change docs. Updated by: 1.1

## Expectation Coverage

- E1: In a repository that declared `self-shift`, a desktop session takes the four outgoing steps without asking, and nothing beyond them (D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.130.0 tree reports `validation --all passed: baseline plus 277 scenarios, 1 skipped: output-survives-the-pipe.`
