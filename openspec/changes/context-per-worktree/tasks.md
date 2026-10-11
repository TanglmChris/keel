# Tasks

## 1. Per-worktree context

- [x] 1.1 Inference counts only the changes that belong to this worktree and lists the rest as context
  - Covers:
    - keel-stateless-continuity / A change that belongs to another worktree does not set this session's status / Another worktree's blocked change is context, not a block
    - keel-stateless-continuity / A change that belongs to another worktree does not set this session's status / A declared owner role decides
    - keel-stateless-continuity / A change that belongs to another worktree does not set this session's status / Explicit selection reaches a change that belongs elsewhere
    - keel-stateless-continuity / Keel resolves continuity conservatively / Multiple candidates are not guessed
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
    - F5
  - Read:
    - src/core/context.js
    - src/core/chat/store.js
  - Touch:
    - src/core/context.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario context-per-worktree` builds a repository with worktrees `rtl`, `verify`, and `review` and requires: `keel context --json` in `review` to report `idle` with an `elsewhere` entry naming the blocked change committed on `rtl`'s branch and worktree `rtl`, while in `rtl` it reports `blocked`; a change declaring `owner: verify` present in both `rtl` and `verify` to be selected in `verify` and listed as belonging to `verify` in `rtl`; and `keel context --change` in `review` naming the `rtl` change to select it. Fails with: `context-per-worktree:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario stateless-continuity` and every scenario whose name starts with `context-` or contains `pause` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ed04863da9eb9a82efbe94e6625407ffc1e57c836fa5e91a2e03f8f59afc5a68
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario context-per-worktree` reports `context-per-worktree scenario passed.`
    - M1.red: fail. Before the change the scenario reported `context-per-worktree: review is 'ambiguous', not idle`, carrying the declared signature `context-per-worktree:`: the review worktree was told two changes it owns neither of were plausible candidates, the issue's own symptom.
    - M1.green: pass. With ownership decided by `owner:` then committed branch history, review reports `idle` listing `broken` as blocked in worktree `rtl` and `owned` as belonging to `verify`; rtl stays `blocked` by its own change and lists only `owned` elsewhere; verify selects `owned`; and `--change broken` in review still reaches it.
    - M2: pass. `stateless-continuity`, `a-paused-change-is-not-the-next-action`, `context-names-its-keel`, and `context-names-the-protocol-refresh` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario builds three real worktrees with bound chat roles, commits on one branch, and reads `keel context --json` status, selection, and `elsewhere` in each.
      - Scope check: `git status --short` lists `src/core/context.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: sessions sharing one checkout, as several rtl_ppa_prj design sessions do, cannot be told apart by worktree; an `owner:` role still separates them only when each binds a different role, which one checkout cannot, and per-session state would break stateless continuity.
    - Blocker: none
    - Reauthorizations: none

- [ ] 1.2 A role listed in `read_only_roles:` reports one idle line, and the session note stops asking for an owner
  - Covers:
    - keel-stateless-continuity / A read-only role infers nothing / A review session is quiet
    - keel-stateless-continuity / A read-only role infers nothing / Explicit selection still works in a read-only session
    - D4
    - D5
    - F3
    - F4
  - Read:
    - src/core/context.js
    - src/core/config.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/context.js
    - src/core/config.js
    - plugins/keel/scripts/session-start.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario read-only-role` declares `read_only_roles:` with `review` and a malformed entry in a repository with two active changes, binds the worktree to `review`, and requires `keel context --json` to report `idle`, one reason naming `review`, `readOnly` naming `review`, and a warning naming the malformed entry; the real session-start hook's output to contain `read-only session (role review)` and not `select an owner`; and `keel context --change` to select the named change. Fails with: `read-only-role:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:97d992a7d3356186bd165cb6a06e38430556bbe1e4aa7aac5ab2df17dad994c7
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED and ADDED requirements are promoted into `openspec/specs/keel-stateless-continuity/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Nine independent declarations live here" — the header of `keel/config.yaml`, which gains `read_only_roles`. Updated by: 1.2
- I2: "next: run `keel context` and select an owner explicitly" — `plugins/keel/scripts/session-start.js`, no longer said to a read-only session. Updated by: 1.2
- I3: "unique actionable OpenSpec inference, then a non-ready status" — `openspec/specs/keel-stateless-continuity/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A session is not reported blocked or ambiguous by a change that belongs to another worktree, which it sees as context instead (D1, D2, D3). Covered by: 1.1
- E2: A read-only session reports one quiet idle line and is not asked to select an owner (D4, D5). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
