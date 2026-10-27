# Tasks

## 1. Unbinding keeps merged branches reachable

- [x] 1.1 Refuse an unset that would strand merged branches, and let `--leave-branches` unbind anyway
  - Covers:
    - keel-cross-host-mailbox / A parked role's gone session is not reported, and a binding can be removed / Unset refuses to strand merged branches unless told to leave them
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/unset-keeps-branches-reachable/design.md
    - src/core/chat/cli.js
    - src/core/branches.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/chat/cli.js
    - src/core/branches.js
    - scripts/validation/chat.py
    - scripts/validation/registry.py
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-unset-keeps-branches-reachable`: in the `branches_scratch` fixture, where verify's worktree alone checked out `done-a` and `done-b`, both merged and pushed, the real `keel chat role --unset` in verify's worktree exits 2 with stderr naming `done-a`, `keel branches prune`, and `--leave-branches`, and `keel chat role` there still prints `verify`; then `keel chat role --unset --leave-branches` exits 0 printing `Unbound verify` and `done-a`, and `keel chat role` there prints `has no chat role`. Fails with: `chat-role-unset-keeps-branches-reachable:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-park-and-unset` passes, and so do `--scenario branches-lists-merged`, `--scenario branches-prune-under-authorization`, `--scenario readme-zh-matches-english`, `--scenario surfaces-agree-with-code`, and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:09e193c87925124bff3b93ff475b52b92745a5744518e3b934850d6cc71b798e (keel 5.208.0)
    - M1: pass. `chat-role-unset-keeps-branches-reachable scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `chat-role-unset-keeps-branches-reachable: keel chat role --unset exited 0, not 2, with merged branches only verify's worktree reaches: 'Unbound verify from /private/var/folders/…/keel-unset-483-biouokq9/verify.\n' ''` (exit 1).
    - M1.green: pass. `branches.merged` takes `{ without }`, which `owned` skips when reading bindings, and `branches.stranded(where, role, worktree)` returns what `merged` lists now and not without that worktree (D1). `keel chat role --unset` computes it before writing `roles.json`; with stranded branches and no `--leave-branches` it throws `ChatError` (exit 2), naming each branch with `origin/` on the remote side, `keel branches prune`, and `--leave-branches`, and leaves the binding (D2). `--unset --leave-branches` unbinds and names them; `--json` carries `left`; `--leave-branches` alone is refused (D3). The usage line names the flag (I3) and both READMEs say so (I2). In the fixture the refusal named `done-a`, `done-b`, `origin/done-a`, `origin/done-b`, and `keel chat role` still printed verify; `--leave-branches` printed `Unbound verify` and the four branches.
    - M2: pass. Run one at a time, each exit 0: `chat-role-park-and-unset scenario passed.`, `branches-lists-merged scenario passed.`, `branches-prune-under-authorization scenario passed.`, `readme-zh-matches-english scenario passed.`, `surfaces-agree-with-code scenario passed.`, `assertion-shape-count scenario passed: 74 sites`.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel chat role --unset` in a worktree that alone checked out merged, pushed branches, the unset was refused with exit 2 naming `done-a`, `keel branches prune`, and `--leave-branches`, and the binding stayed; `--unset --leave-branches` then unbound it and named `done-a`. The existing scenario shows an unset that strands nothing still unbinds.
      - Scope check: `git status --short` lists `src/core/chat/cli.js`, `src/core/branches.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, both READMEs, and this change's directory, all in Touch; `.DS_Store` was untracked before the task.
      - Findings: Resolved here: M1 — two assertions in the new scenario each guarded two distinct failures with one message; they were split so each message names its own cause, and M1 passed again after the split.
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
    - Contract:
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

- I1: "`keel chat role --unset` MUST remove the binding of the worktree it runs in" — the requirement "A parked role's gone session is not reported, and a binding can be removed" in `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1.
- I2: "`keel chat role --unset` drops the calling worktree's binding while the worktree remains (#476)" — `README.md` and its counterpart in `README.zh-CN.md`. Updated by: 1.1.
- I3: "--unset: drop this worktree's" — the `keel chat role` usage line in `src/core/chat/cli.js`. Updated by: 1.1.

## Expectation Coverage

- E1: Unbinding a worktree does not silently strand its role's merged task branches; it refuses and points at `keel branches prune`, unless `--leave-branches` says to leave them (D1–D3) (#483). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
