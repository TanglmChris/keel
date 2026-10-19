# Tasks

## 1. A host-run tick runs the patrol when due

- [x] 1.1 Add `keel tick`, `keel tick task` and `runner: tick`
  - Covers:
    - keel-coordinator-patrol / A host-run tick runs the patrol when due / The patrol runs only when due
    - keel-coordinator-patrol / A host-run tick runs the patrol when due / The launchd job is printed, not installed
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/patrol.js
    - src/core/config.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/tick.js
    - bin/keel.js
    - src/core/config.js
    - src/core/context.js
    - src/core/shift.js
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-runs-due-patrol` declares `patrol: role rtl, runner: tick, cadence: adaptive` in a two-role repository with a real bare remote and runs the real `keel tick --repo <rtl>` from `verify`: the first call runs the patrol (one run-log line) and records `next_at`; the second says `not due` and runs none; one after `next_at` is moved into the past runs it again; `keel tick task` prints a plist with `StartInterval` 300, `tick` and rtl's worktree, `launchctl bootstrap` and `Keel creates nothing`; `keel context --json` in rtl carries `patrol.runner` `tick`, and its SessionStart projection names `keel tick` and not `re-create it with the host`. Fails with: `the first tick exited 2`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3ec0115d8530584796645e29b73aa259c2b86b82189131c39eae83fbfb63f750 (keel 5.152.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-runs-due-patrol` reports `tick-runs-due-patrol scenario passed.` The rendered plist, written to a file, passes `plutil -lint` (`OK`).
    - M1.red: fail. With the scenario written first and no `tick` command: `tick-runs-due-patrol: the first tick exited 2: '' 'keel: repo path was provided more than once…'`, carrying the declared signature.
    - M1.green: pass. With `src/core/tick.js` (state in `<chat store>/tick/state.json`, fetch then `keel patrol --since-last --notify --json` in the bound worktree when `next_at` has passed, `keel tick task` printing the launchd plist and its install commands), `runner: tick` in `readPatrolDeclaration`, and the reminder carried through `context.js`, `shift.js` and the SessionStart projection, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 298 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. The first run failed `the-tarball-is-the-repository` only because `src/core/tick.js` was not yet in Git; it passed once staged.
    - Review:
      - Status: pass
      - Acceptance check: the real `keel tick` runs the patrol once and records `next_at`, skips with `not due` on the next call, and runs again once `next_at` is past; `keel tick task` prints a plist (`StartInterval` 300, `tick`, the bound worktree) with `launchctl bootstrap` and `Keel creates nothing`, writing nothing; with `runner: tick` the context carries it and the projection names `keel tick` instead of re-creating a session schedule.
      - Scope check: `git status --short` lists `src/core/tick.js`, `bin/keel.js`, `src/core/config.js`, `src/core/context.js`, `src/core/shift.js`, `plugins/keel/scripts/session-start.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/348 — waking a role whose CLI session has exited is the next change of the owner's CLI waker.
        - Durable owner: https://github.com/TanglmChris/keel/issues/357 — the CLI self-shift through the waker's queue follows it.
        - Discard reason: the launchd job was linted, not loaded, on the owner's machine; installing it is the owner's step, which the printed commands perform.
    - Blocker: none
    - Reauthorizations: 2026-10-19 — before any Evidence: the patrol reminder is rendered in `src/core/context.js` (JSON), `src/core/shift.js` (resume) and `plugins/keel/scripts/session-start.js` (projection), not only `src/core/config.js`; those were added to Touch, I2 declared, and M1 now checks the JSON and the projection; anchor re-recorded.

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

- I1: "re-create it with the host if this session has none" as the only reminder without `host_task:` — `src/core/config.js`. Updated by: 1.1
- I2: "a session's schedule ends with the session, so re-create it with the host" in the projection — `plugins/keel/scripts/session-start.js`. Updated by: 1.1

## Expectation Coverage

- E1: On the CLI, the patrol keeps running on its recommended cadence without a session schedule or a model, from one host job the CLI can render (owner, 2026-10-19; D1, D2, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
