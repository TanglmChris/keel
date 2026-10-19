# Tasks

## 1. Launchd jobs name a stable node

- [x] 1.1 Share one stable-node and clean-PATH helper, use it in the three LaunchAgents, and report a gone node in doctor
  - Covers:
    - keel-coordinator-patrol / Keel's launchd jobs name a node that outlives an upgrade / The printed job names the symlink, not its target
    - keel-coordinator-patrol / Keel's launchd jobs name a node that outlives an upgrade / The chat waker's LaunchAgent does the same
    - keel-coordinator-patrol / Keel's launchd jobs name a node that outlives an upgrade / Doctor reports a job whose node is gone
    - D1
    - D2
    - D3
  - Read:
    - src/core/tick.js
    - src/core/chat/wake.js
    - src/core/chat/lifecycle.js
    - bin/keel.js
  - Touch:
    - src/core/launchd.js
    - src/core/tick.js
    - src/core/chat/wake.js
    - src/core/chat/lifecycle.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario launchd-stable-node` runs the real `keel tick task` and `keel chat wake add` under a node reached through a symlink in a scratch `bin/` whose target lies in a versioned directory, with a plugin cache directory first on `PATH`: both plists' first program argument is the scratch `bin/node` and their `PATH` has no plugin cache directory; then the real `keel --doctor` with a `dev.keel.tick.x.plist` naming a missing node prints a `launchd` problem naming the file, the path and `keel tick task`, and prints `launchd: ok` once the path exists. Fails with: `the tick job names the versioned node`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8bc7b472e4da12eed2b3e86e1271e060bfe81541401dfabd17cc85e1145efba8 (keel 5.161.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario launchd-stable-node` reports `launchd-stable-node scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `launchd-stable-node: the tick job names the versioned node: '/opt/homebrew/Cellar/node/26.0.0/bin/node', not '<scratch>/bin/node'`, carrying the declared signature.
    - M1.green: pass. With `src/core/launchd.js` (`stableNode`, `launchdPath`, `inspectJobs`) used by `keel tick task`, `keel chat wake add` and the chat bridge, and a `launchd` line in `keel --doctor`, the scenario passed: the tick plist and the chat waker's LaunchAgent name the scratch `bin/node` symlink and carry no plugin cache directory in `PATH`, doctor names `dev.keel.tick.x.plist`, the missing path and `keel tick task`, and prints `launchd: ok` once the path exists.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 304 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick task`, `keel chat wake add` and `keel --doctor` under a node reached through a symlink to a versioned directory, the jobs name the symlink and a gone node is reported with the command that re-creates the job.
      - Scope check: `git status --short` lists `src/core/launchd.js`, `src/core/tick.js`, `src/core/chat/wake.js`, `src/core/chat/lifecycle.js`, `bin/keel.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the chat bridge's LaunchAgent changes with the same helper but has no scenario of its own; it shares `stableNode` and `launchdPath` with the two that do, and `chat bridge install` needs a real launchd to exercise.
        - Durable owner: https://github.com/TanglmChris/keel/issues/387 — the LaunchAgent already installed on this machine (`dev.keel.tick.keel`) still names the Cellar node until its owner re-runs `keel tick task` and re-bootstraps it.
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
    - Contract: keel-task-capsule/v1 sha256:be3e9c4d5cc9000c38fb783ddeaadb2c29722d59c648e749b504ae4a0a4aed2f (keel 5.161.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.162.0 → 5.163.0; with the "Keel's launchd jobs name a node that outlives an upgrade" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-coordinator-patrol`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A launchd job Keel prints or writes keeps working after the node it was rendered under is upgraded, and a job whose node is gone is reported (#387; D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
