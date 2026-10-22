# Tasks

## 1. Session ids in notes

- [x] 1.1 Skip UUID-shaped and recorded session ids in the note's commit check, and drop empty header slots
  - Covers:
    - keel-shift-change / A shift note's session ids are not read as commits / Session ids in a note are not listed as commits
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/note-commit-session-ids/design.md
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-resume-skips-session-ids`: a `keel shift ready` run as CLI session `<uuid1>` (`CLAUDE_CODE_ENTRYPOINT=cli`), whose note names a landed commit, `deadbee1`, and the first eight digits of `<uuid2>`, a session recorded by a SessionStart hook in rtl's worktree, is followed by a `keel shift resume` that lists the landed commit as `already in origin/<default>` and `deadbee1` as `not found`, lists neither `<uuid1>[:8]` nor `<uuid2>[:8]`, and prints a note whose header holds no `\n\n\n`. Fails with: `shift-resume-skips-session-ids:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes, `shift-resume-checks-commits` among them, and so does `--scenario assertion-shape-count`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:728c05d200135d4945fcdfebb3b5c624ca02e75e474d36408543fe9e5c390b93 (keel 5.193.0)
    - M1: pass. `shift-resume-skips-session-ids scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `shift-resume-skips-session-ids: the header's CLI session id b5a55cf2 is listed as a commit: '- b5a55cf2: not found'` (exit 1). This is the line this shift's own resume printed.
    - M1.green: pass. Three changes in `src/core/shift.js`:
      - `NOTE_SHA` no longer matches a token followed by `-` and four hex digits (D1).
      - `noteCommits` skips a token that begins an id `knownSessionIds` reads from `sessions/` and `shift/transcripts/` (D2).
      - The header drops empty slots (D3).
    - M2: pass. `validation --group shift passed: 54 scenarios.` (exit 0), `shift-resume-checks-commits` among them. `assertion-shape-count` passed at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift ready` and `keel shift resume` with a CLI session's environment, neither session id is listed. The landed commit and the unknown `deadbee1` keep their marks. The header holds no blank slot. `shift-resume-checks-commits` shows the #347 behaviour unchanged.
      - Scope check: `git status --short` lists `src/core/shift.js`, the two validation files, and this change's directory.
      - Findings: none.
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
    - openspec/specs/keel-shift-change/spec.md
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
    - M2: the delta is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:385d3311df8938e4daaefa9811b22d1a3ba89846fd9f8d8b02c814315e940055 (keel 5.193.0)
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a commit id being 7 to 40 hex digits after `@`, or elsewhere holding at least one letter and one digit or resolving to a commit" — `openspec/specs/keel-shift-change/spec.md`. Discard reason: the sentence stays true; the added requirement narrows it for session ids, and the old one is not edited.
- I2: "A bare token needs a letter and a digit, or, when it is all digits, to resolve to a commit, so a date does not count." — the `noteCommits` comment in `src/core/shift.js`. Updated by: 1.1.

## Expectation Coverage

- E1: A resumed note lists no session id as a commit while a real or unknown commit is still listed, and the header has no blank slots (#445; D1–D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
