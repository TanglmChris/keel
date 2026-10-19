# Tasks

## 1. The /keel:shift command

- [x] 1.1 Ship the command, declare it in the Claude manifest, and prove its steps hand a shift over
  - Covers:
    - keel-shift-change / A session changes its own shift with one slash command / The command's own steps hand a shift over
    - keel-native-plugin-package / The Claude plugin is the npm package / One package carries the plugin and its CLI
    - D1
    - D2
    - D3
    - D5
  - Read:
    - plugins/keel/skills/keel-handoff/SKILL.md
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Touch:
    - plugins/keel/commands/shift.md
    - .claude-plugin/plugin.json
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-slash-command` finds the command through the root manifest's `commands`, requires its text to name `caffeinate` and `--force-reason`, then runs its fenced `keel shift` lines in order in a clean fixture worktree bound to `verify` with a `keel` on PATH: `keel shift check` exits 0, `keel shift ready --wake --file -` stores the heredoc's note at `keel-chat/shift/verify.md` and prints that the wake is armed. Fails with: `the root manifest declares no command`
    - M2 (regression): `claude plugin validate .` reports the root plugin valid, the command file included.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4c83c1f3a17a365ef63379f5572ad5e363c66d3088252e32958a9787476eada5 (keel 5.162.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-slash-command` reports `shift-slash-command scenario passed.`
    - M1.red: fail. With the scenario written first and no command: `shift-slash-command: the root manifest declares no command`, carrying the declared signature.
    - M1.green: pass. With `plugins/keel/commands/shift.md` and `"commands": ["./plugins/keel/commands/shift.md"]` in the root manifest, the scenario passed: it found the command through the manifest, read its front matter, required `caffeinate`, `--force-reason`, `self-shift` and `end your turn` in its text, then ran its two fenced `keel shift` blocks in a clean worktree bound to `verify`: `check` exited 0, `ready --wake --file -` stored the heredoc's note at `keel-chat/shift/verify.md` and printed that the wake is armed.
    - M2: pass. `claude plugin validate .` reports `Validation passed with warnings`; the one warning is the existing root `CLAUDE.md` note, none concerns the command.
    - M3: pass. `npm test`: `validation --all passed: baseline plus 305 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the command is declared by the root manifest, valid to `claude plugin validate`, and its own `keel shift` lines run in order against the real CLI and hand a shift over.
      - Scope check: `git status --short` lists `plugins/keel/commands/shift.md`, `.claude-plugin/plugin.json`, `scripts/validate_plugin.py`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/386 — the command's behaviour in a live Claude session (that `/keel:shift` is listed after `/reload-plugins` and that a model follows its steps) is not provable by a script; the owner's next self-shift is that check.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the specs
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
    - openspec/specs/keel-shift-change/spec.md
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - M2: the delta requirements are promoted into `keel-shift-change` and `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dfaf30fee5907d0ee7c316c7ddbb10f840c84d3fdfb9ad2c8c31b1583986e7f6 (keel 5.162.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.163.0 → 5.164.0; with the "/keel:shift changes a session's own shift in one command" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-native-plugin-package`, `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "declares the canonical skills, the Claude agent, and hooks equal to" — the Claude plugin requirement in `openspec/specs/keel-native-plugin-package/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: A session changes its own shift with one command that orders the check, the note and the hand-over, and says a host's keep-awake is not a loose end (#386; D1, D2, D3, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
