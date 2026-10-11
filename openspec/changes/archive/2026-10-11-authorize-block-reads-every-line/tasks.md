# Tasks

## 1. Read every line

- [x] 1.1 `authorize:` reads every indented line and strips trailing comments, in Keel and in the push guard
  - Covers:
    - keel-standing-authorization / Every line of the authorize block is read / An item with a space is refused, not dropped
    - keel-standing-authorization / Every line of the authorize block is read / A trailing comment does not drop an item
    - D1
    - D2
    - F1
    - F2
    - F3
  - Read:
    - src/core/config.js
    - plugins/keel/scripts/pretooluse-guard.js
  - Touch:
    - src/core/config.js
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-block-reads-every-line` requires `keel --doctor` over `commit`, `push:main branch`, `release` to exit non-zero naming `push:main branch` with no action reported authorized, and over `commit  # …` and `push:claude/*  # …` to report `commit: authorized` and `push` scoped to `claude/*`, and requires the real hook script to deny `git push origin HEAD:main` in that second repository. Fails with: `authorize-block-reads-every-line:`
    - M2 (regression): `standing-authorization-declaration`, `authorize-push-close-cleanup`, `push-branch-guard`, and `chat-reply-authorization` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:58be98e17e6bf928d96eb566ab3d7b8c094911895343f2e818f324646b6a4857
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-block-reads-every-line` reports `authorize-block-reads-every-line scenario passed.`
    - M1.red: fail. Before the change the scenario reported `authorize-block-reads-every-line: an item with a space was not refused`, carrying the declared signature `authorize-block-reads-every-line:`: doctor exited 0 with only `commit` declared.
    - M1.green: pass. With every indented line read as an entry and trailing comments stripped in both readers, the spaced item voids the declaration by name, the commented items are read, and the hook denies `HEAD:main` under a commented glob. This repository's own block, which carries indented comment lines, still reads `commit, push, release, archive, issue:TanglmChris/keel`.
    - M2: pass. `standing-authorization-declaration`, `authorize-push-close-cleanup`, `push-branch-guard`, and `chat-reply-authorization` each report `scenario passed.`; `npm test` reports `validation --all passed: baseline plus 248 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads real `keel --doctor` exit codes and lines over both shapes and feeds the shipped hook a real `Bash` event.
      - Scope check: `git status --short` lists `src/core/config.js`, the hook script, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
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
    - openspec/specs/keel-standing-authorization/spec.md
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
    - M2: the ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:91ee6c1b18de32deb27f3fab20b620af8f1a82ca31ea26f17d743ef839a25252
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.105.1. With the 5.105.1 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-standing-authorization/spec.md`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the requirement with both scenarios, and the changelog names the issue and both readers.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.105.1 reports `validation --all passed: baseline plus 248 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: No line of `authorize:` is dropped silently: an unreadable one voids the declaration by name, and a trailing comment is ignored, in Keel and in the push guard (D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
