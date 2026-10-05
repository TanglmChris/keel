# Tasks

## 1. Exit status and the parallel quota

- [x] 1.1 Record the exit status and the parallel-quota pitfall
  - Covers:
    - keel-external-agents / The external agent brief is the delegation brief, checked for egress / The printed command records the exit status
    - keel-external-agents / The external agent brief is the delegation brief, checked for egress / A clean helper brief is written and its command printed
    - D1
    - D2
    - F1
    - F2
    - F3
  - Read:
    - src/core/agents.js
  - Touch:
    - src/core/agents.js
    - scripts/validate_plugin.py
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-exit-status` compiles a helper brief for `codex` and one for `dsh` against stubs that exit with status 3, runs each printed command with `sh -c` from a known directory, and requires the exit file beside the result to hold `3`, the shell's directory afterwards to be the one it started in, the JSON payload and the text output to name the exit file, and `keel agents codex` to print a pitfall about parallel runs sharing one quota. Fails with: `external-agent-exit-status:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-catalog`, `external-agent-brief`, and `external-agents-are-documented` each pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:798c059362628d33dc67f16a02a5a5faa038e7efc3613d38dbbb0154cc24af46
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario external-agent-exit-status` reports `external-agent-exit-status scenario passed.`
    - M1.red: fail. Before the change the scenario reported `external-agent-exit-status: the codex brief names no exit file.`, carrying the declared signature `external-agent-exit-status:`.
    - M1.green: pass. With the printed command wrapped as `( <template> ); echo $? > <result>.exit`, the payload's `exit` field, the `Exit status:` output line, and the codex parallel-quota pitfall, the same scenario passes for both codex and dsh stubs exiting 3, and the shell stays in its starting directory after dsh's `cd`.
    - M2: pass. `external-agent-catalog`, `external-agent-brief`, and `external-agents-are-documented` each report `scenario passed.`
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 227 scenarios, 1 skipped: output-survives-the-pipe.` A first run failed only `assertion-shape-count` at 81 sites, from this task's scenario joining two checks in one condition; it now matches one regex for a single pitfall line, and the count is back at 80.
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the printed command itself with `sh -c` against stubs that exit 3, so the exit file is checked as produced, not as described, and it covers the dsh template whose `cd` is the reason for the subshell.
      - Scope check: `git status --short` lists `src/core/agents.js`, `scripts/validate_plugin.py`, `README.md`, and `README.zh-CN.md`, all in Touch, plus this change's own directory. The dsh entry also gained a dated pitfall found while testing dsh on 2026-10-05 (headless fails with MISSING_CREDENTIAL until a key is stored), inside the same file and the same fact shape.
      - Findings: none

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.92.1, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.92.1 section written.
    - M2: the MODIFIED requirement replaces its published text in `openspec/specs/keel-external-agents/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "MUST print the command line filled from the catalog template," — `openspec/specs/keel-external-agents/spec.md`, which says nothing of the exit status. Updated by: 2.1
- I2: "writes it to a file, and prints the command to run" and "写成文件，再打印要跑的命令" — `README.md` and `README.zh-CN.md`, which do not name the exit file. Updated by: 1.1

## Expectation Coverage

- E1: A session running the command a brief prints finds the agent's exit status in a file beside its result, and a session deciding how many runs to start can read that parallel runs share one quota. Covered by: 1.1, 2.1
