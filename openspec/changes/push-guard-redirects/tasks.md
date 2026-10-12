# Tasks

## 1. Redirections

- [x] 1.1 The push guard drops shell redirections before reading push arguments
  - Covers:
    - keel-touch-write-guard / A redirection is never read as a push target / An in-scope push with redirections passes
    - keel-touch-write-guard / A redirection is never read as a push target / An out-of-scope push with redirections is still refused
    - D1
    - F1
  - Read:
    - plugins/keel/scripts/pretooluse-guard.js
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-guard-redirects` feeds the real hook `Bash` events in a repository declaring `push:flow-*` and requires `git push --dry-run origin HEAD:refs/heads/flow-probe 2>&1 | tail -1`, the same with `2>/dev/null`, with `&> out.log`, and with `>&2` each allowed, and `git push origin HEAD:main 2>&1 | tail -1` denied naming `main`. Fails with: `push-guard-redirects:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a1ec0a30fa5a71bf0a5f18d715edd1efc37349c62b34bd0d109a37d0f744f4fd
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario push-guard-redirects` reports `push-guard-redirects scenario passed.`
    - M1.red: fail. Before the change the scenario reported `push-guard-redirects: 'git push --dry-run origin HEAD:refs/heads/flow-probe 2>&1 | tail -1' was {... 'Keel push guard: this command pushes to `2>` ...'}, not allowed.`, carrying the declared signature `push-guard-redirects:` and the issue's own message.
    - M1.green: pass. With redirections and their targets dropped in `shellSegments`, all four in-scope forms are allowed and `HEAD:main 2>&1 | tail -1` is denied naming `main`; `push-branch-guard` and `push-protected-guard` still pass, and a hand probe allowed a heredoc commit followed by `git push origin claude/x 2>&1 | tail -1`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 258 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the shipped hook the issue's own command and three more redirection forms, reading each decision and the refusal's named branch.
      - Scope check: `git status --short` lists the hook script, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
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
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-touch-write-guard/spec.md
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
    - M1: `node scripts/bump_version.js patch` moves every marker to the next patch version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement is appended to `openspec/specs/keel-touch-write-guard/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- None.

## Expectation Coverage

- E1: An in-scope push written with the usual `2>&1 | tail` passes, and an out-of-scope one is still refused by its real target (D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
