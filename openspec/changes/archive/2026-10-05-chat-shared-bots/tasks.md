# Tasks

## 1. Shared bots

- [x] 1.1 A registered bot serves a role in each project that maps it
  - Covers:
    - keel-chat-slack-bridge / A role may post as its own Slack app / A verified role posts under its own app
    - keel-chat-slack-bridge / A role may post as its own Slack app / A token for another bot is not used
    - keel-chat-slack-bridge / A role may post as its own Slack app / A channel the role's bot is not in falls back
    - keel-chat-slack-bridge / A role may post as its own Slack app / A mention of a role's bot wakes the role
    - keel-chat-slack-bridge / A role may post as its own Slack app / One bot is a different role in each project
    - keel-chat-slack-bridge / A role's app takes direct messages / The owner messages a session privately
    - keel-chat-slack-bridge / A role's app takes direct messages / The session answers privately
    - keel-chat-slack-bridge / A role's app takes direct messages / A stranger's direct message is ignored
    - keel-chat-slack-bridge / A role's app takes direct messages / A bot serving two roles takes no direct messages
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/bridge.js
    - src/core/chat/cli.js
  - Touch:
    - src/core/chat/bridge.js
    - src/core/chat/cli.js
    - src/core/chat/lifecycle.js
    - src/core/chat/store.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-shared-bots` lists one bot `pm` with `keel chat bot add pm`, maps its id to `a-pm` in project `a` (group `ops` on `CA`) and to `b-pm` in project `b` (group `ops` on `CB`), and requires: `keel chat bot list` to show `pm` with its Keychain entries present and no token text; both roles' posts to carry the bot's token, to `CA` and `CB`; the owner's `<@UBOTPM>` in `CA` to land in `a` as a mention of `a-pm` and nowhere in `b`; no Socket Mode connection with the bot's app token; and status to list bot `pm` serving `a/a-pm` and `b/b-pm` with direct messages off for 2 roles. Fails with: `chat-shared-bots:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps` and `chat-role-direct`, updated to register their bot with `keel chat bot add` and to read status by bot, each pass.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each pass.
    - M4 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d7e017eccb436c91be36ee64f7266d16e165506c1505a198dcb1b34cdfc2205d
    - Blocker: none
    - Reauthorizations: Touch gained `src/core/chat/store.js` before any implementation: the first red showed `keel chat bot add` read as a group named `bot`, so `bot` must join the reserved group names that store.js owns.
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-shared-bots` reports `chat-shared-bots scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-shared-bots: keel chat bot add pm failed: keel chat: No group bot. Create it with \`keel chat group create bot\`.`, carrying the declared signature `chat-shared-bots:`.
    - M1.green: pass. With the machine bot list and `keel chat bot add|remove|list`, `bot:<name>` / `app:<name>` Keychain lookup, per-project role assignment from each bot's `auth.test` user id, direct messages only for a bot serving one role, status listing bots, and `bot` reserved as a group name, the same scenario passes: one `pm` bot posts for `a/a-pm` to `CA` and `b/b-pm` to `CB`, a mention in `CA` reaches only `a`, and no direct-message connection opens.
    - M2: pass. `chat-role-apps` and `chat-role-direct` each report `scenario passed.`
    - M2.red: fail. Updated to register their bot and read status by bot, before the change they reported `chat-role-apps: status does not list bot rtl serving rtl/rtl: {}` and `chat-role-direct: status does not report rtl's direct-message connection: {}`.
    - M2.green: pass. After the change both pass unchanged from their updated form.
    - M3: pass. `chat-bridge-outbound`, `chat-bridge-inbound`, and `chat-bridge-lifecycle` each report `scenario passed.`
    - M4: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the new scenario runs two projects against one bot through the real CLI and a running bridge and reads the token, channel, store, sockets, and status each produced, covering the shared-bot scenario and the two-role direct-message rule; the updated 5.93 scenarios still prove posting, fallback, mention resolution, echo suppression, and direct messages under the bot list.
      - Scope check: `git status --short` lists `scripts/validate_plugin.py` and `src/core/chat/{bridge,cli,lifecycle,store}.js`, all in Touch after the recorded reauthorization, plus this change's own directory. `assertion-shape-count` stays at 80.
      - Findings: none

## 2. Setup guide

- [x] 2.1 The setup guides describe shared bots
  - Covers:
    - D1
    - D2
    - D4
    - D6
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps-are-documented` requires both setup guides to name `keel chat bot add`, the Keychain accounts `bot:<name>` and `app:<name>`, that one bot can serve a role in each of several projects, and that a bot serving more than one role takes no direct messages, and refuses `bot:<role>` in either guide; and requires both READMEs to say one bot can serve several projects. Fails with: `chat-role-apps-are-documented:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:304f1d00df22bea1189de6e307fc44574f5a40a268e31a29588bc2bf7c02f77d
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-apps-are-documented` reports `chat-role-apps-are-documented scenario passed.`
    - M1.red: fail. Updated for shared bots, before the edits the scenario reported `chat-role-apps-are-documented: docs/chat-slack-setup.md does not carry 'keel chat bot add'.`, carrying the declared signature `chat-role-apps-are-documented:`.
    - M1.green: pass. With the role-app section of both guides rewritten as "bots that speak for roles" (generic names, `keel chat bot add`, `bot:<name>` / `app:<name>`, the per-project `bots` mapping, one bot per role per project, no direct messages for a bot serving several roles) and one sentence in each README, the same scenario passes.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads the shipped guides and READMEs for each element and refuses the stale `bot:<role>` form, which updates I1 and I2.
      - Scope check: `git status --short` lists both guides, both READMEs, and `scripts/validate_plugin.py`, all in Touch, plus this change's own directory.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.94.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.94.0 section written.
    - M2: the MODIFIED requirements replace their published text in `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a545dad245bc8665e82af01a3a7cfa6c3663daed631ecadf4c0bfe7b893f68f6
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.94.0. With the 5.94.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both MODIFIED requirements and the token requirement replace their published text in `openspec/specs/keel-chat-slack-bridge/spec.md`, which updates I3; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted spec carries the bot list, per-project assignment, and the one-role direct-message rule, and the changelog names the change and the 5.93.0 compatibility.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 231 scenarios, 1 skipped: output-survives-the-pipe.`, with `chat-shared-bots`, the updated `chat-role-apps`, `chat-role-direct`, and `chat-role-apps-are-documented` passing.

## Invalidates

- I1: "security add-generic-password -s keel-chat-slack -a bot:<role> -w" and "give a role its own app" / "给某个角色单独建一个 App" — `docs/chat-slack-setup.md` and `docs/chat-slack-setup.zh-CN.md`, which tie an app to one role. Updated by: 2.1
- I2: "A role may also have its own Slack app" and "某个角色也可以有自己的 Slack App" — `README.md` and `README.zh-CN.md`. Updated by: 2.1
- I3: "each declared role's `bot:<role>` token" and "accounts `bot:<role>` and `app:<role>`" — `openspec/specs/keel-chat-slack-bridge/spec.md`. Updated by: 3.1

## Expectation Coverage

- E1: The owner registers each bot once per machine, and each project assigns it to that project's role, so one PM bot is the PM in every project's channel while direct messages stay unambiguous. Covered by: 1.1, 2.1, 3.1
