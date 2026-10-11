# Tasks

## 1. Acknowledgements

- [x] 1.1 `--ack`, `keel chat ack`, replies as acknowledgements, and who has acknowledged in `show` and `acks`
  - Covers:
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / A sender sees who has not acknowledged
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / A reply acknowledges
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / Acknowledging is refused where it means nothing
    - keel-cross-host-mailbox / A record can ask for an acknowledgement, and who has given it is listed / An acknowledgement wakes nobody and is marked where it is asked
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/view.js
    - src/core/chat/notice.js
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/view.js
    - src/core/chat/notice.js
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-ack` runs, with roles `rtl`, `verify`, and `spec` in one group, every keel-cross-host-mailbox acknowledgement scenario through the real CLI: `show --json` and `acks --mine --json` lists after `verify` acknowledges and `spec` only reads; `spec`'s reply moving it to acknowledged and the record leaving `acks`; each refusal exiting non-zero naming why; `rtl`'s unread holding nothing from the acknowledgement; and `(ack requested)` in `spec`'s group view and wake notice. Fails with: `chat-ack:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound` adds an acknowledged `--ack` record and requires no Slack call carrying the acknowledgement's id. Fails with: `chat-bridge-outbound:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d3a24e7a185417df548573fb3fb68d257a331230709c03a16e3a4546f8c2149d
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-ack` reports `chat-ack scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-ack: a post with --ack returned no id.`, carrying the declared signature `chat-ack:`.
    - M1.green: pass. With `--ack` on `post` and `todo`, `keel chat ack`, replies counted, `show` and `acks` splitting the addressed roles, and `(ack requested)` in views and the notice, the scenario passes; `chat-supersedes`, `chat-records`, and `assertion-shape-count` still pass.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound` reports `chat-bridge-outbound scenario passed.`
    - M2.red: fail. With the bridge's `ack` skip removed, the scenario reported `chat-bridge-outbound: the acknowledgement … reached Slack: [{'method': 'chat.postMessage', 'params': {'channel': 'CSOC', 'text': '', …`, carrying the declared signature `chat-bridge-outbound:`: an acknowledgement would have gone out as an empty Slack message.
    - M2.green: pass. With the skip restored, the scenario passes.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI with three roles in one group and reads `show --json`, `acks --json`, unread JSON, the group view, and the notice; each refusal's exit code and message are read; the bridge check runs the bridge against the fake Slack server and searches every call for the acknowledgement's id.
      - Scope check: `git status --short` lists the five chat sources, `scripts/validate_plugin.py`, `README.md`, and this change's own directory.
      - Findings: none

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
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2fbd8a6717099c46bd1adac21a98635ade9ed981351561900cd432aaeaa5b3af
    - M1: pass. After merging `main` (5.102.1, #272), `node scripts/bump_version.js minor` moved every marker to 5.103.0. With the 5.103.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the acknowledgement requirement with its four scenarios, and the changelog names the issue and each command.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.103.0 reports `validation --all passed: baseline plus 244 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A sender can ask for and see acknowledgements, so silence no longer has to be read as work in progress (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
