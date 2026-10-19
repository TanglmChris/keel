# Tasks

## 1. The exit status says who must act

- [x] 1.1 Exit 2 for a risk or the coordinator's own met wait; exit 3 for what only others need
  - Covers:
    - keel-coordinator-patrol / Patrol notifies the roles whose conditions are met and writes nothing otherwise / Only what the coordinator must handle exits 2
    - keel-coordinator-patrol / Patrol notifies the roles whose conditions are met and writes nothing otherwise / A landed commit wakes the waiting role once
    - keel-coordinator-patrol / Issue labels route issue updates to roles
    - keel-coordinator-patrol / A patrol run reports only what changed since the last one / Only a change is reported, once
    - D1
    - D2
  - Read:
    - src/core/patrol.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/patrol.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-exit-says-who-acts` runs the real `keel patrol` as coordinator `rtl`: after a baseline, a run whose only news is a moved remote tip exits 3; a run after the primary checkout gains an uncommitted file exits 2; a run that meets `verify`'s wait exits 3; one that meets `rtl`'s own wait exits 2; `keel patrol --help` names `3:`. Fails with: `exited 2, not 3`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-since-last`, `--scenario coordinator-patrol`, `--scenario patrol-issue-routing` and `--scenario patrol-nudge` pass with their exit expectations moved from 2 to 3 where the run told only other roles.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:99a79e4feda3ac9dab6ff6d5a652568aad4d775ef6008f57090ba02344073cd8 (keel 5.147.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-exit-says-who-acts` reports `patrol-exit-says-who-acts scenario passed.`
    - M1.red: fail. With the scenario written first and `patrol.js` unchanged: `patrol-exit-says-who-acts: a run whose only news is the remote tip exited 2, not 3: 'changed: remote origin/main: …'`, carrying the declared signature `exited 2, not 3`.
    - M1.green: pass. With `EXIT_ACT` (2) for a risk or a held wait whose `from` is the patrolling role and `EXIT_RECORDED` (3) for any other record, nudge or reported change, the scenario passed.
    - M2: pass. `--scenario patrol-since-last`, `--scenario coordinator-patrol`, `--scenario patrol-issue-routing` and `--scenario patrol-nudge` each report `scenario passed.`
    - M2.red: fail. With their expectations moved to 3 and `patrol.js` unchanged: `patrol-since-last: the run after a change exited 2`, `coordinator-patrol: patrol after the push exited 2, not 3`, `patrol-issue-routing: the first patrol exited 2, not 3`, `patrol-nudge: a run that nudged exited 2, not 3.`
    - M2.green: pass. The same four pass with the new exit codes.
    - M3: pass. `npm test`: `validation --all passed: baseline plus 293 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last edit.
    - Review:
      - Status: pass
      - Acceptance check: the real `keel patrol` exits 3 for a moved remote tip, 2 for a new uncommitted path in the primary checkout, 3 for another role's met wait and 2 for its own, and `--help` names 3; the four existing patrol scenarios assert 3 where the run told only other roles.
      - Scope check: `git show --stat HEAD` lists `src/core/patrol.js`, `scripts/validate_plugin.py`, `README.md`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: a host task rendered before this release names only 0, 1 and 2, so its model may report exit 3 as unexpected; the changelog tells the owner to re-render it with `keel patrol task`, and Keel installs no task itself.
    - Blocker: none
    - Reauthorizations: 2026-10-18 — README.md added to Touch and I3 declared before any Evidence was recorded, after its two exit-code sentences were found; anchor re-recorded. The M1 and M2 reds below were run before the re-record; neither check's text moved.

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
    - openspec/specs/keel-coordinator-patrol/spec.md
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
    - M2: the delta requirements are promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3f3f91fdd53775b40441829b86752de4093e2917bf056bca6cdff6240afacb43 (keel 5.147.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.149.0 → 5.150.0; with the "A patrol's exit status says who must act" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-coordinator-patrol`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "It MUST exit 0 when it wrote nothing, 2 when it wrote at least one record" and "It MUST exit 2 when it reported a change or wrote anything" — `openspec/specs/keel-coordinator-patrol/spec.md`. Updated by: 2.1
- I3: "it exits 0 then, 2 when it sent something" and "exits 2 only when something changed" — `README.md`. Updated by: 1.1
- I2: "Exit 0: wrote nothing. 2: sent a notice or marked a wait met. 1: error." and the host task's "Exit 0: nothing changed. Exit 2: keel has already told" — `src/core/patrol.js`. Updated by: 1.1

## Expectation Coverage

- E1: A patrol run wakes the coordinator's model only when it has something to act on (#350, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
