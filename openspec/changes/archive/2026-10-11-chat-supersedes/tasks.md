# Tasks

## 1. Supersedes

- [x] 1.1 `post --supersedes`, superseded records leave unread, views mark both, unread and the notice list newest first
  - Covers:
    - keel-cross-host-mailbox / A record can supersede an earlier one, and unread shows only the current version, newest first / A rule change supersedes the old rule
    - keel-cross-host-mailbox / A record can supersede an earlier one, and unread shows only the current version, newest first / Superseding is refused when it would not be the author's current version
    - keel-cross-host-mailbox / A record can supersede an earlier one, and unread shows only the current version, newest first / Unread lists newest first
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
  - Read:
    - src/core/chat/store.js
    - src/core/chat/view.js
    - src/core/chat/cli.js
    - src/core/chat/notice.js
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/view.js
    - src/core/chat/cli.js
    - src/core/chat/notice.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-supersedes` runs, in a two-role chat fixture, a `pm` post superseded by a second `pm` post and requires `verify`'s `keel chat unread --json` to hold only the second, `keel chat notice --check` for `verify` to still report one addressed record, and `keel chat team` to mark both; requires each refused supersede (another author's record, an already superseded record naming its successor, a retracted record, a record in another group) to exit non-zero naming why; and requires three posts mentioning `verify` to be listed newest first by `keel chat unread` and by the notice text. Fails with: `chat-supersedes:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f8e1f262c24f2061cdc860cce7a35ab838f7f5af99f945e5f8a92228cd91afbd
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-supersedes` reports `chat-supersedes scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-supersedes: the posts did not return ids:  keel chat: Unknown option for keel chat: --supersedes`, carrying the declared signature `chat-supersedes:`.
    - M1.green: pass. With `--supersedes` checked and recorded by `post`, superseded records dropped from `store.unread`, views marking both records, and `keel chat unread` and the notice reversed, the scenario passes; `chat-records`, `chat-mail-migration`, and `assertion-shape-count` still pass.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI with two roles: unread JSON, the notice text, and the group view are read for the superseded and superseding records; each refusal's exit code and message are read; and three posts are checked for newest-first order in unread and the notice.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `view.js`, `cli.js`, `notice.js`, `scripts/validate_plugin.py`, `README.md`, and this change's own directory.
      - Findings: Resolved here: M1 — the first version of the notice-order check joined "not listed" and "out of order" behind one message, which `assertion-shape-count` caught (81 against 80); they are now two checks.

- [x] 1.2 The bridge marks a superseded record's Slack copy
  - Covers:
    - keel-chat-slack-bridge / A superseded record's Slack copy says so / The superseded Slack message is updated
    - D5
    - F3
  - Read:
    - src/core/chat/bridge.js
  - Touch:
    - src/core/chat/bridge.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound` adds a record superseding one the bridge already posted, and requires a `chat.update` on that earlier message's `ts` whose text opens `(superseded by <id>)`. Fails with: `chat-bridge-outbound:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:853eab62215fec8dfc82de65ebfa1ae842b607b687a3081384ab7b3b6966f603
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-bridge-outbound` reports `chat-bridge-outbound scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-bridge-outbound: the superseded record's Slack message was never updated.`, carrying the declared signature `chat-bridge-outbound:`.
    - M1.green: pass. With `markSuperseded` updating the earlier message after the successor posts, on both the shared-app and direct paths, the scenario passes; `chat-role-apps`, `chat-shared-bots`, `chat-bridge-lifecycle`, and `assertion-shape-count` still pass.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the bridge once against the fake Slack server and reads the `chat.update` call on the superseded message's `ts` and its text.
      - Scope check: `git status --short` lists `src/core/chat/bridge.js` and `scripts/validate_plugin.py` beyond 1.1's paths, and this change's own directory.
      - Findings: Discard reason: the marked copy carries the superseded record's original text, not an edit made to it before it was superseded; superseding an edited record is rare, and the successor itself carries the current text.

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirements are appended to `openspec/specs/keel-cross-host-mailbox/spec.md` and `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:693da58d1ac57a7d899f683dc07f64a980d44fb2e82f91978acd54193ab03d77
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.100.0, #268; the one conflict was both changes registering a scenario at the same line, and both were kept), `node scripts/bump_version.js minor` moved every marker to 5.101.0. With the 5.101.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements were appended to `openspec/specs/keel-cross-host-mailbox/spec.md` and `openspec/specs/keel-chat-slack-bridge/spec.md`; `published-specs-validate-strictly` reports `32 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, both published specs carry their new requirement with scenarios, and the changelog names the issue and each behavior.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and both specs, all in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.101.0 reports `validation --all passed: baseline plus 241 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A session acts on the current version of a record, not a superseded one, and sees the newest unread first (D1–D4). Covered by: 1.1
- E2: The Slack copy of a superseded record says so (D5). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
