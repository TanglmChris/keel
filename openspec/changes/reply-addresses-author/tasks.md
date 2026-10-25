# Tasks

## 1. A reply addresses the role it answers

- [x] 1.1 `--reply-to` mentions the answered record's author
  - Covers:
    - keel-cross-host-mailbox / A reply addresses the role it answers / A reply without @ reaches the author it answers
    - keel-cross-host-mailbox / A reply addresses the role it answers / A reply to one's own record, or no reply at all, addresses no one
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/reply-addresses-author/design.md
    - src/core/chat/store.js
  - Touch:
    - src/core/chat/store.js
    - scripts/validation/chat.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-reply-addresses-author`: through the real CLI, `verify`'s `--reply-to` reply to `rtl`'s record with no `@` mentions `rtl`, `rtl`'s `keel chat notice` names the reply, and `notice --check` in `rtl`'s worktree exits 0. After `rtl` reads `soc`, `verify`'s reply to its own record and its plain message mention no one, and `notice --check` exits 1. A `--reply-to … --ack` with no `@` is accepted. Fails with: `chat-reply-addresses-author: a reply without @ does not mention the role it answers`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group chat --jobs 4` passes, and so does `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dc9a645596e4d0a7f70679201b95429b3f32ad912fa036777bbfd1869b3f0dad (keel 5.202.0)
    - M1: pass. `chat-reply-addresses-author scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `chat-reply-addresses-author: a reply without @ does not mention the role it answers: {'id': '20261025T144905149Z-verify-57086a', 'group': 'soc', 'from': 'verify', 'mentions': [], …}` (exit 1). This is the #468 record shape: `reply_to` set, and no mentions.
    - M1.green: pass. `post()` adds the parent record's author to `mentions` when the author is another member of the group and is not yet mentioned, before the `--ack` check (D1–D3). Every `wakes`-based reader then sees the reply as addressed: the notice, `--check`, signal files, waker, and patrol. Self-replies and plain messages stay unaddressed, and `notice --check` exits 1 for them.
    - M2: pass. `validation --group chat passed: 50 scenarios.` (exit 0, load 4.96). `assertion-shape-count scenario passed: 74 sites`.
    - Review:
      - Status: pass
      - Acceptance check: the issue's three acceptance arms, through the real CLI. A no-`@` reply addresses `rtl` (notice lists it, and `--check` exits 0). A self-reply does not address anyone, and neither does a plain message (`--check` exits 1). A `--reply-to --ack` is accepted.
      - Scope check: the changed paths are `src/core/chat/store.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:536be12426fe68e030f7e1c0ede7b9729b07b2a7b8098089ac0a46871a451327 (keel 5.202.0)
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A reply reaches the role it answers without an `@` (#468; D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
