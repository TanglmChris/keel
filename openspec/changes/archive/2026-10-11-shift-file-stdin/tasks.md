# Tasks

## 1. The note from --file

- [x] 1.1 `ready` reads `--file -` from stdin and refuses an unreadable `--file` by name
  - Covers:
    - keel-shift-change / The outgoing shift leaves a note and closes the request / The note comes from --file
    - D1
    - D2
    - F1
    - F2
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` runs `keel shift ready --file <missing path>` and requires exit 1, stderr opening `keel shift:` and naming the path, and no Node stack frame; then runs `keel shift ready --file -` with a note on stdin and requires exit 0 and a stored worktree note holding that text. Fails with: `shift-without-role:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8a520fb655a25ae99326eac3cf2e4837c5d359690a3d0bebfa5786b71ed439e2
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-without-role` reports `shift-without-role scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-without-role: an unreadable --file was not refused by name: exit 1, …/src/core/shift.js:466` followed by `Error: ENOENT: no such file or directory, open '…/missing-note.md'`, the uncaught exception of the issue, carrying the declared signature `shift-without-role:`.
    - M1.green: pass. With `readNoteText` reading fd 0 for `-` and wrapping any other read failure in a `ShiftError`, the scenario passes; `shift-change` still passes.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI, reads its exit code and stderr for the missing path, and pipes a note through `--file -` and reads the stored note file.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Resolved here: M1 — the first version of the check joined four distinct failures of the refusal, and two of the stored note, behind one message each. The first C1 run's `assertion-shape-count` caught it (82 sites against 80 recorded). Each failure now has its own message, and M1 and `assertion-shape-count` pass again.

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
    - openspec/specs/keel-shift-change/spec.md
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
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.99.2, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.99.2 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5b408cbc2b58c1cedc29d51a178ab001697de3a4298bf9b161406e9b17a9f718
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.99.2. With the 5.99.2 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its scenarios and adding one; with `npm ci` run in this worktree, `published-specs-validate-strictly` reports `31 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published requirement carries the `--file -` and unreadable-file clauses with their scenario, and the changelog names the issue and both behaviors.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump, with `npm ci` run in this worktree, reports `validation --all passed: baseline plus 239 scenarios, 1 skipped: output-survives-the-pipe.` The first run, before `npm ci` and before the split of 1.1's assertions, failed four scenarios; the Finding on 1.1 records the one that was this change's.

## Invalidates

- None.

## Expectation Coverage

- E1: `--file -` reads stdin, and an unreadable `--file` is a named refusal rather than a stack trace (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
