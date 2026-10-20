# Tasks

## 1. Long role names and lock notices

- [x] 1.1 Accept a direct group name made of two valid role names, whatever its length
  - Covers:
    - keel-cross-host-mailbox / Groups have maintained membership, direct groups, and archive / Two long role names share a direct group
    - D1
  - Read:
    - src/core/chat/store.js
    - openspec/changes/lock-long-dm-names/design.md
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/config.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-dm-long-role-names`: `kaiwu-design-iecc` runs `keel chat dm kaiwu-pm-iecc …` and it exits 0; the message is unread for `kaiwu-pm-iecc`; `keel chat dm-kaiwu-design-iecc--kaiwu-pm-iecc --peek` prints it; `group list --json` lists the group as direct; a `chat-reply:dm-kaiwu-design-iecc--kaiwu-pm-iecc` authorization is read without a problem; and a group name that is neither form is still refused. Fails with: `a direct message between long role names failed`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario resource-lock` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5db9883540d46fb1d3450f0837c21622920f37eb01cdaad09fef350c995eaee3 (keel 5.169.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-dm-long-role-names` reports `chat-dm-long-role-names scenario passed.`: `keel chat dm kaiwu-pm-iecc` from `kaiwu-design-iecc` exited 0, the message was unread for `kaiwu-pm-iecc` and printed by `--peek`, `group list --json` listed the group as direct, doctor read `chat-reply:dm-kaiwu-design-iecc--kaiwu-pm-iecc` as authorized, and `dm-kaiwu-pm-iecc--kaiwu-design-iecc`, `Not_A_Group` and a 33-character name were refused as not valid names.
    - M1.red: fail. With 5.169.0's group check: `chat-dm-long-role-names: a direct message between long role names failed: 'keel chat: Group "dm-kaiwu-design-iecc--kaiwu-pm-iecc" is not a valid name: use ^[a-z0-9][a-z0-9-]{0,31}$.'`
    - M1.green: pass. With `validGroup`/`checkGroup` in `src/core/chat/store.js` replacing the group checks in `createGroup`, `post`, `wait`, `view`, `listGroupNames` and `keel chat summary --group`, and the `chat-reply` scope pattern accepting the direct form, the scenario passed; `chat-reply-authorization` passes too.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario resource-lock` reports `resource-lock scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel chat` CLI, two long role names share a direct group that can be posted, read, listed and authorized, and malformed or unsorted names are still refused.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `src/core/chat/cli.js`, `src/core/config.js`, `scripts/validate_plugin.py` and this change's directory, all in Touch or the record layer.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Free a lease before telling anyone, and print a notice that cannot be posted as a warning
  - Covers:
    - keel-resource-lock / A lease ends at release or at its noticed expiry, and waiters are told / A notice that cannot be posted does not keep the lease
    - keel-resource-lock / A lease ends at release or at its noticed expiry, and waiters are told / Long role names are told on release
    - D2
  - Read:
    - src/core/lock.js
    - openspec/changes/lock-long-dm-names/design.md
  - Touch:
    - src/core/lock.js
    - scripts/validate_plugin.py
    - docs/resource-lock.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario lock-notice-best-effort`: with the holder–waiter direct group archived, `keel lock release` exits 0, the lease is gone from `keel lock list`, and stderr warns naming the waiter; the same holds for an expired lease freed by `keel lock list`; with `kaiwu-design-iecc` holding and `kaiwu-pm-iecc` waiting, release exits 0 with no warning and the direct group holds the release message. Fails with: `a notice that could not be posted kept the lease`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b96a9d45d86c0425d7f21e47ee04729794c6fd9787c9d194ebaccb16247fa383 (keel 5.169.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario lock-notice-best-effort` reports `lock-notice-best-effort scenario passed.`: with `dm-integ--sweep` archived, `keel lock release main-checkout` exited 0, removed the lease and warned naming `sweep`; an expired lease was freed by `keel lock list` with the same warning; `kaiwu-design-iecc` released `cpu-heavy` with `kaiwu-pm-iecc` waiting, exit 0 and no warning, and `dm-kaiwu-design-iecc--kaiwu-pm-iecc` holds one release message.
    - M1.red: fail. With 5.169.0's `lock.js` (and task 1.1's group check): `lock-notice-best-effort: a notice that could not be posted kept the lease: exit 1, 'keel lock: Group dm-integ--sweep is archived: it keeps its history and takes no new records.'`
    - M1.green: pass. With `release` and `reap` removing the lease file before `notify`, and `notify` catching a `ChatError` per role and returning it as a warning that `runLock` prints to stderr as `keel lock: warning: …`, the scenario passed; `resource-lock` passes too.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 309 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. The first run failed `assertion-shape-count` on five combined conditions in the two new scenarios; they were split before this run.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel lock` CLI, a lease is freed on release and on expiry even when its notice cannot be posted, the failure is a warning naming the waiter, and a release between long role names reaches the waiter with no warning.
      - Scope check: `git status --short` lists task 1.1's files plus `src/core/lock.js` and `docs/resource-lock.md`; `scripts/validate_plugin.py` is in both tasks' Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

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
    - openspec/specs/keel-resource-lock/spec.md
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
    - M2: the delta requirements are promoted into `keel-cross-host-mailbox` and `keel-resource-lock`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9fcb5ac0aafb5892ab48dbb3039eb8d89392f6829fd3166b7526f732b17519c0 (keel 5.169.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.169.0 → 5.170.0; with the "Long role names share direct groups, and a lease is freed even when its notice fails" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: both MODIFIED requirements replaced their published text in place in `keel-cross-host-mailbox` and `keel-resource-lock`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E3 — version markers, the changelog section and both published specs carry the change; both validator scenarios pass.
      - Scope check: changed files beyond tasks 1.1 and 1.2 are the version markers, `keel/CHANGELOG.md` and the two published specs, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Release sends each waiter with a role a direct chat message." — `docs/resource-lock.md` does not say that a message which cannot be posted only warns. Updated by: 1.2.
- I2: "`keel chat dm <role> <text>` MUST post to the direct group `dm-<a>--<b>`" and "A lease ends at release or at its noticed expiry" — the published `keel-cross-host-mailbox` and `keel-resource-lock` specs. Updated by: 2.1.

## Expectation Coverage

- E1: Two roles with long names can message each other directly, and a lease held between them can be released (#403; D1). Covered by: 1.1
- E2: Releasing or expiring a lease never fails because a notice cannot be delivered (#403; D2). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
