# Tasks

## 1. Role apps

- [x] 1.1 A role posts as its own verified app, and its bot's mention resolves to it
  - Covers:
    - keel-chat-slack-bridge / A role may post as its own Slack app / A verified role posts under its own app
    - keel-chat-slack-bridge / A role may post as its own Slack app / A token for another bot is not used
    - keel-chat-slack-bridge / A role may post as its own Slack app / A channel the role's bot is not in falls back
    - keel-chat-slack-bridge / A role may post as its own Slack app / A mention of a role's bot wakes the role
    - D1
    - D2
    - D3
    - D4
    - D5
    - D8
    - F1
    - F2
    - F5
    - A1
  - Read:
    - src/core/chat/bridge.js
    - src/core/chat/lifecycle.js
    - scripts/fake_slack.py
  - Touch:
    - src/core/chat/bridge.js
    - src/core/chat/config.js
    - src/core/chat/lifecycle.js
    - src/core/chat/cli.js
    - scripts/fake_slack.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps` runs the bridge against the fake server with a Keychain double: with `slack.bots` mapping `UBOTRTL` to `rtl` and `bot:rtl` verified, `rtl`'s post carries `rtl`'s token and no `username` while `verify`'s carries the shared token and `username` `verify`, and the edit of `rtl`'s record uses `rtl`'s token; with `auth.test` returning another user the post falls back to the shared token and status reports `mismatch`; a `not_in_channel` answer posts once through the shared token and status names the role and channel; the owner's `<@UBOTVERIFY>` imports as a mention of `verify` reading `@verify`; and `rtl`'s own post echoed back by its app is not re-imported. Fails with: `chat-role-apps:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each pass, so a project with no `slack.bots` behaves exactly as before.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fdfe9a6f66973260099b2caa3066c8acdb848885cee302ee45bc4bdc43054d9c
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps` reports `chat-role-apps scenario passed.`
    - M1.red: fail. Before the bridge changes the scenario reported `chat-role-apps: rtl's post did not use rtl's own app token: 'Bearer xoxb-test-bot'`, carrying the declared signature `chat-role-apps:`.
    - M1.green: pass. With `slack.bots`, the Keychain `bot:<role>` lookup, the `auth.test` check, per-role posting with the `as` field on the posted map, the `not_in_channel` fallback, bot-mention resolution, and the widened own-bot set, the same scenario passes. Reverting only the `message_changed` own-bot check to the shared bot id makes it fail with `chat-role-apps: the bridge's own edit through rtl's app was imported back as an edit.`, so the echo check detects the D5 change.
    - M2: pass. `chat-bridge-outbound`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each report `scenario passed.`
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI and bridge against the fake server and reads the token each call carried, so the identity used is checked as sent, for both apps, the mismatch, and the fallback; the mention and echo checks go through a running bridge's Socket Mode connection.
      - Scope check: `git status --short` lists `scripts/fake_slack.py`, `scripts/validate_plugin.py`, and `src/core/chat/{bridge,cli,config,lifecycle}.js`, all in Touch, plus this change's own directory. `assertion-shape-count` still reports 80 sites.
      - Findings: none

- [x] 1.2 A role's app takes direct messages
  - Covers:
    - keel-chat-slack-bridge / A role's app takes direct messages / The owner messages a session privately
    - keel-chat-slack-bridge / A role's app takes direct messages / The session answers privately
    - keel-chat-slack-bridge / A role's app takes direct messages / A stranger's direct message is ignored
    - D6
    - D7
    - F3
  - Read:
    - src/core/chat/bridge.js
    - src/core/chat/store.js
  - Touch:
    - src/core/chat/bridge.js
    - src/core/chat/cli.js
    - scripts/fake_slack.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-direct` runs the bridge with `bot:rtl` and `app:rtl` in the Keychain double: the bridge opens a second Socket Mode connection with `rtl`'s app token; a direct message from `UOWNER` pushed on it becomes a record from `owner` in `dm-owner--rtl` and grows `signal/rtl`; `rtl`'s `keel chat dm owner "all green"` is posted once with `rtl`'s token to the channel `conversations.open` returned for `UOWNER` and to no mapped channel; a stranger's direct message writes nothing and grows the ignored count; and a direct message added to history while the bridge was stopped is imported once after it restarts. Fails with: `chat-role-direct:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b693c3258584e69313253cc161be7fdb865f770fc4a21e42306b0e92e2915762
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-direct` reports `chat-role-direct scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-role-direct: the bridge opened no Socket Mode connection with rtl's app token:`, carrying the declared signature `chat-role-direct:`.
    - M1.green: pass. With one queue fed by every connection, a kept-up Socket Mode connection per direct-capable role app, direct-message import into `dm-<person>--<role>`, direct outbound through `conversations.open` with the role's token, and direct catch-up from the last ts, the same scenario passes, including the restart that catches up a message sent while down without re-importing the role's own answer.
    - M2: pass. `chat-role-apps`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each report `scenario passed.`; `chat-bridge-outbound` also still passes after the connection refactor.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario pushes direct messages only on the role app's own connection, reads the token and channel of the answer as sent, and checks the stranger, status, and catch-up through the running bridge, so each requirement clause is observed at the Slack boundary.
      - Scope check: `git status --short` lists `scripts/validate_plugin.py` and `src/core/chat/bridge.js`, both in Touch, plus this change's own directory. `assertion-shape-count` still reports 80 sites.
      - Findings: none

## 2. Setup guide

- [x] 2.1 The setup guides and READMEs describe optional role apps
  - Covers:
    - D1
    - D2
    - D6
    - D7
    - F4
  - Read:
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
  - Touch:
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
    - README.md
    - README.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps-are-documented` requires both setup guides to carry a role-app section naming `slack.bots`, the Keychain accounts `bot:<role>` and `app:<role>`, a manifest with `chat:write.public`, `im:history`, and `im:write`, and that direct messages stay on the role's machine; requires neither guide to say 10 apps means 10 machines; and requires both READMEs to mention that a role may have its own app. Fails with: `chat-role-apps-are-documented:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e66c284411d724f41688f3f265f9195fdb351e5fb79e0fa705cf54870981ae99
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps-are-documented` reports `chat-role-apps-are-documented scenario passed.`
    - M1.red: fail. Before the edits the scenario reported `chat-role-apps-are-documented: docs/chat-slack-setup.md does not carry '"bots"'.`, carrying the declared signature `chat-role-apps-are-documented:`.
    - M1.green: pass. With the optional role-app section in both guides (manifest with `chat:write.public`, `im:history`, `im:write`, and the messages tab; the `bot:<role>` and `app:<role>` Keychain accounts; the `bots` registration; status states; direct messages staying on the role's machine), the corrected app-limit sentence, and one sentence in each README, the same scenario passes.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the shipped files for every element the guide must carry and refuses the stale limit sentence in both languages, which updates I1 and I2.
      - Scope check: `git status --short` lists `README.md`, `README.zh-CN.md`, both setup guides, and `scripts/validate_plugin.py`, all in Touch, plus this change's own directory.
      - Findings: none

## 3. Release

- [x] 3.1 Release and promote the spec
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.93.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.93.0 section written.
    - M2: the ADDED and MODIFIED requirements are promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:972082800796538ecfd0199c739d5f2f23cb6651545eb109cc42362ae094aa5f
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.93.0. With the 5.93.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The two ADDED requirements sit after the inbound requirement and the three MODIFIED requirements replace their published text in `openspec/specs/keel-chat-slack-bridge/spec.md`, which updates I3; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted spec carries the role-app and direct-message requirements and the per-role token accounts, and the changelog names what changed and that the two-machine test stays parked.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario, once every task's scenario is registered.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 230 scenarios, 1 skipped: output-survives-the-pipe.`, with `chat-role-apps`, `chat-role-direct`, and `chat-role-apps-are-documented` registered and passing, and `assertion-shape-count` at 80 sites.

## Invalidates

- I1: "The free plan allows 10 apps, which means 10 machines" and "免费版最多 10 个 App，也就是最多 10 台电脑" — `docs/chat-slack-setup.md` and `docs/chat-slack-setup.zh-CN.md`; role apps count too. Updated by: 2.1
- I2: "With one Slack app and one bridge process per machine" and "每台电脑配一个 Slack App、跑一个桥接程序" — `README.md` and `README.zh-CN.md`, which do not say a role may have its own app. Updated by: 2.1
- I3: "with `username` set to the role" and "accounts `app` and `bot`." — `openspec/specs/keel-chat-slack-bridge/spec.md`. Updated by: 3.1

## Expectation Coverage

- E1: A role the owner gives its own Slack app posts under that app, is mentioned by its bot in Slack and woken by it, and takes private messages, while every other role keeps the shared app unchanged. Covered by: 1.1, 1.2, 2.1, 3.1
