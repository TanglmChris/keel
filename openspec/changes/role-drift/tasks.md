# Tasks

## 1. Binding drift

- [x] 1.1 Drift is computed and reported in patrol, doctor, and the unbound session's projection, and `keel chat role --prune` removes removed bindings
  - Covers:
    - keel-cross-host-mailbox / Binding drift is reported and removed bindings can be pruned / Drift is reported, pruned, and named to an unbound session
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/store.js
    - src/core/patrol.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/chat/drift.js
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/patrol.js
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
    - bin/keel.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario role-drift` binds `ghost` to a worktree and removes it, has `verify` run `keel shift ready` with no presence recorded, and requires: `keel patrol` by `rtl` printing a `drift:` line naming `ghost` and that worktree and one naming `verify` and `shift note`; `keel --doctor` printing `chat roles: drift` for both; `keel context --json` in an unbound worktree carrying `unattendedRoles` with `verify` and the session-start note naming `verify`; `keel chat role --prune` printing `Pruned ghost` and leaving `roles.json` without that worktree but with `rtl` and `verify`; and a second prune printing `No binding`. Fails with: `role-drift:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4e128b95ad2fd51baa9722420c5e31edceb22160ff3805b62e57cfac8cd6b2b7
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario role-drift` reports `role-drift scenario passed.`
    - M1.red: fail. Before the change the scenario reported `role-drift: keel patrol does not report ghost's removed worktree: 'keel patrol: nothing new.\nrole ghost: offline (idle), …'`, carrying the declared signature `role-drift:`.
    - M1.green: pass. With `src/core/chat/drift.js` and its wiring: `keel patrol` prints drift lines for `ghost`'s removed worktree and for `verify`'s waiting shift note; `keel --doctor` prints `chat roles: drift` for both; `keel context --json` in the unbound `loose` worktree carries `unattendedRoles` with `verify`, and its session-start note names `verify`; `keel chat role --prune` prints `Pruned ghost` and leaves `rtl` and `verify` bound; a second prune prints `No binding`. Run read-only against rtl_ppa_prj, the same code reported `iecc-design-sub`'s binding to the removed `r007_comp`, `rtl-report`, `iecc-spec`, and `iecc-verify-sub` with waiting notes, and `iecc-design` with 3 unread records since 10-11.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 267 scenarios, 1 skipped: output-survives-the-pipe.` A first run failed `the-tarball-is-the-repository` until the new `src/core/chat/drift.js` was tracked.
    - Review:
      - Status: pass
      - Acceptance check: the scenario removes a real worktree, writes a real shift note, and reads `keel patrol`, `keel --doctor`, `keel context --json`, the plugin's SessionStart hook, and `roles.json` after `--prune`.
      - Scope check: `git status --short` lists `src/core/chat/drift.js`, `src/core/chat/store.js` (unchanged exports), `src/core/chat/cli.js`, `src/core/patrol.js`, `src/core/context.js`, `plugins/keel/scripts/session-start.js`, `bin/keel.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a role parked on purpose (a note waiting for the coordinator's `start`) is reported as unattended like a drifted one; Keel cannot tell them apart, so the line names both readings instead of prescribing a rebind.
    - Blocker: none
    - Reauthorizations: 1. After the real-repository run showed parked roles told to "bind the session where it runs", D2's wording in design.md was changed to `if its session runs in another worktree, bind <role> there`; the contract was re-recorded with `task-start --record` before any Evidence was written, and `role-drift` passed again on the reworded text.
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
    - Contract: pending

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "chat role: none bound here while other worktrees have one; bind one with `keel chat role --set <name>`" — the session-start line in `plugins/keel/scripts/session-start.js` and the warning in `src/core/context.js`, which now also name unattended roles. Updated by: 1.1

## Expectation Coverage

- E1: A role nobody can wake, or a binding to a removed worktree, is visible to the coordinator and the doctor, can be cleaned up explicitly, and is named to the session that may be that role (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
