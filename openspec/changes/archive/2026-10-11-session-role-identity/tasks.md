# Tasks

## 1. The role is the identity

- [x] 1.1 `keel context` and the session projection name the bound chat role, and remind an unbound worktree among bound ones
  - Covers:
    - keel-native-runtime-projection / The projection names the chat role a session speaks as / A bound role is named
    - keel-native-runtime-projection / The projection names the chat role a session speaks as / An unbound worktree among bound ones is reminded
    - keel-native-runtime-projection / The projection names the chat role a session speaks as / A repository without chat roles is unchanged
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/context.js
    - plugins/keel/scripts/session-start.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario session-role-identity` builds a repository with worktrees `rtl` (bound) and `loose` (unbound) and a separate repository with no roles, and requires: `keel context --json` in `rtl` to carry `role` `rtl` and the real SessionStart hook to name `rtl`; in `loose`, `role` null, a warning naming `keel chat role --set`, and the hook carrying it; in the role-less repository, `role` null, no such warning, and no `chat role:` line. Fails with: `session-role-identity:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7a17e055bc23ef4995ebb253706ff7246f535c87f8986d1fccf22b1b7e44e97b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario session-role-identity` reports `session-role-identity scenario passed.`
    - M1.red: fail. Before the change the scenario reported `session-role-identity: rtl's context carries role None, not 'rtl'.`, carrying the declared signature `session-role-identity:`.
    - M1.green: pass. With `role` set in `resolveContext`, the reminder when other worktrees are bound, and the hook's `chat role:` line, rtl's context and projection name `rtl`, `loose` is reminded in both, and the role-less repository carries `role: null` with neither.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 251 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario binds a real role in one of two worktrees and reads `keel context --json` and the shipped SessionStart hook's output in each, plus a repository with no roles.
      - Scope check: `git status --short` lists `src/core/context.js`, the session-start hook, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Resolved here: M1. The first green attempt saw an empty projection because the fixture had no `openspec/` directory, where the hook deliberately projects nothing; the fixture now commits one, and the red recorded above predates that and still names the missing role.
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
    - openspec/specs/keel-native-runtime-projection/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-native-runtime-projection/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d8d7b3243a79d511ed9de1ea915c3b236dd40faf39cd62dd4a305eafb4c621b5
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.107.0 on top of `main` at 5.106.0 (#279). With the 5.107.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-native-runtime-projection/spec.md`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the requirement with its three scenarios, and the changelog names the issue and the decision.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.107.0 reports `validation --all passed: baseline plus 251 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A session sees the role others address it by, and an unbound one among bound ones is told to bind (D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
