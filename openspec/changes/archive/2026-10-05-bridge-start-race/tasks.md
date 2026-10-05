# Tasks

## 1. Lifecycle

- [x] 1.1 Start, stop, install, and status follow launchd's actual state
  - Covers:
    - keel-chat-slack-bridge / The bridge runs unattended but stays visible and controllable / Start after stop waits for the unload
    - keel-chat-slack-bridge / The bridge runs unattended but stays visible and controllable / A bootstrap that never succeeds is reported
    - keel-chat-slack-bridge / The bridge runs unattended but stays visible and controllable / A stale status file is not reported as running
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/lifecycle.js
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/lifecycle.js
    - src/core/chat/bridge.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-start-race` drives `keel chat bridge install`, `stop`, and `start` against a stateful launchctl double that fails the first two bootstraps after each bootout with `Bootstrap failed: 5: Input/output error` and answers `print` with `state = running`/`pid = 4242` when loaded or `Could not find service` (exit 113) when not, and requires `start` to exit 0 with three bootstraps logged and the double loaded; then sets the double to fail every bootstrap and requires `start` (with `KEEL_CHAT_LAUNCHCTL_WAIT_MS=1500`) to exit non-zero naming `5: Input/output error`; then writes a status file with `launchd: true`, `connected: true`, and a live pid, and requires `keel chat bridge status --json` to report `running: false` both when the double is unloaded and when it reports pid 4242, and `running: true` for the same file without `launchd`. Fails with: `chat-bridge-start-race:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-lifecycle` passes.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:020181d1f2c7cea8934ee005b11778a61300df0ae6e0e24b1b11697e2357dcc4
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-start-race` reports `chat-bridge-start-race scenario passed.`
    - M1.red: fail. With `src/core/chat` set aside in a stash, the scenario reported `chat-bridge-start-race: install failed although the unload finishes: keel chat: launchctl could not load …/dev.keel.chat-bridge.plist: Bootstrap failed: 5: Input/output error`, carrying the declared signature `chat-bridge-start-race:`.
    - M1.green: pass. With `loadedState`, the waiting `bootout`, the retrying `bootstrap` used by `install` and `start`, `start` returning early for a loaded agent, the bridge recording `launchd` in its status, and `readStatus` consulting launchd for such a status, the same scenario passes.
    - M2: pass. `chat-bridge-lifecycle` reports `chat-bridge-lifecycle scenario passed.`; its echo double gives `print` no state, so the unknown branch keeps the old behavior.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real CLI against a double that reproduces the observed race (F1): start after stop succeeds only after the retries with the agent loaded, a bootstrap that never succeeds fails naming `5: Input/output error`, and a launchd-written status file with a live pid reads as not running when launchd has unloaded the agent or runs another pid, while a hand-run status file still reads as running.
      - Scope check: `git status --short` lists `src/core/chat/lifecycle.js`, `src/core/chat/bridge.js`, `src/core/chat/cli.js`, and `scripts/validate_plugin.py`, all in Touch, plus this change's own directory.
      - Findings: Discard reason: `XPC_SERVICE_NAME` being the agent's label under launchd is not exercised by the scenario, because no double can stand in for launchd's environment; it is checked against the real agent on this machine when the release is installed, as the owner's ordinary `bridge stop`/`start`.

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E1
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
    - openspec/specs/keel-chat-slack-bridge/spec.md
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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.95.2, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.95.2 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b05d9a628fbba54bc926dcd23edf8c310002bdfb706b4e6f5f531b9cbf86f371
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.95.2. With the 5.95.2 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy in `openspec/specs/keel-chat-slack-bridge/spec.md`, keeping the three existing scenarios and adding the three new ones; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted requirement carries the start, stop, install, and status clauses with their scenarios, and the changelog names both halves of #226.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 233 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: `keel chat bridge start` succeeds only when the bridge is actually loaded, and `status` does not report a stopped bridge as running. Covered by: 1.1, 2.1
