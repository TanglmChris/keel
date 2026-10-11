# Tasks

## 1. The refusal names the checkout it compared against

- [x] 1.1 A helper worktree under `.claude/worktrees/` is accepted, and the own-checkout refusal names the checkout and `--repo`
  - Covers:
    - keel-external-agents / The checkout is an external agent's write boundary / A helper worktree beside the session's worktree is accepted
    - keel-external-agents / The checkout is an external agent's write boundary / The refusal names the checkout it compared against
    - D1
    - F1
    - F2
    - F3
  - Read:
    - src/core/agents.js
  - Touch:
    - src/core/agents.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-brief` adds worktrees `<repo>/.claude/worktrees/review` and `<repo>/.claude/worktrees/dsh_review`, requires a `dsh` helper brief with `--dir` the second, run from the first, to be `ready`, and requires the same brief run from inside the second to be refused with reasons naming that worktree's path, `current directory`, and `--repo`. Fails with: `external-agent-brief:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d114ed52a4fa2915d3f6ee864a874f294af9160a41e6f4315f246df7a388c686
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-brief` reports `external-agent-brief scenario passed.`
    - M1.red: fail. Before the change the scenario reported `external-agent-brief: a helper brief run from inside its own --dir was refused without naming '…/repo/.claude/worktrees/dsh_review': … is this session's own checkout. …`, carrying the declared signature `external-agent-brief:`. The sibling-worktree brief was already `ready`, as F2 measured.
    - M1.green: pass. With the refusal naming the checkout it compared against, whether it came from `--repo` or the current directory, and how to point it elsewhere, the scenario passes.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario creates both worktrees under `<repo>/.claude/worktrees/` with real `git worktree add`, runs the CLI from each, and reads the JSON status and reasons.
      - Scope check: `git status --short` lists `src/core/agents.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Resolved here: M1 — the first version of the added check created the worktrees before the fixture's `keel/config.yaml` was committed, so the sibling brief was refused for an undeclared `external_agents:` and the red named the wrong cause. The fixture now commits it first, as a real project does.

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
    - openspec/specs/keel-external-agents/spec.md
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
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-external-agents/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c3f1dcc78b4d50a4729b1b8b9b5a4da7f973f566e7198cb40e0463ae8e88c22b
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.99.2, #263), `node scripts/bump_version.js patch` moved every marker to 5.99.3. With the 5.99.3 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding two; `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirement says what the current checkout is and what the refusal names, and the changelog names the issue and the corrected cause.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.99.3 reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "is this session's own checkout" — the refusal text in `src/core/agents.js`, which claims a knowledge Keel does not have (F3). Updated by: 1.1

## Expectation Coverage

- E1: A helper worktree under `.claude/worktrees/` is accepted, and the own-checkout refusal names the checkout it compared against and how to point it elsewhere (D1). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
