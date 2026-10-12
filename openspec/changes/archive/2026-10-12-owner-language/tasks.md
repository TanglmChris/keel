# Tasks

## 1. Owner language

- [x] 1.1 `owner_language:` is read, carried by context, stated at session start, and restated on every prompt; the protocol makes it binding
  - Covers:
    - keel-owner-language / A declared owner language is restated where replies are written / Every prompt restates the owner's language
    - keel-owner-language / A declared owner language is restated where replies are written / A malformed language is reported
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
  - Read:
    - src/core/config.js
    - src/core/chat/notice.js
    - plugins/keel/scripts/session-start.js
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - src/core/chat/notice.js
    - plugins/keel/scripts/session-start.js
    - plugins/keel/scripts/mail-hook.js
    - keel/config.yaml
    - AGENTS.md
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario owner-language` declares `owner_language: zh` in a repository with an unbound worktree and requires: `keel chat hook user-prompt-submit` there printing `additionalContext` containing `中文` and `structured-choice`; `keel context --json` carrying `ownerLanguage` `zh`; the session-start note containing `中文`; the same hook for a bound role with an unread mention carrying both the rule and the notice; and, with `owner_language: Chinese!`, a context warning naming `owner_language`, no `ownerLanguage`, and no language line from the hook; and `AGENTS.md` containing `declares \`owner_language:\``. Fails with: `owner-language:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:798a37d40209ea4d0b95074e804033f20da19629f7b7af77c38cc1bceec40ac8
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario owner-language` reports `owner-language scenario passed.`
    - M1.red: fail. Before the change the scenario reported `owner-language: AGENTS.md does not make a declared owner_language binding.`, carrying the declared signature `owner-language:`.
    - M1.green: pass. With `readOwnerLanguage`/`ownerLanguageRule`, the context fields, the projection line, the prompt hook output for any worktree, and the protocol line: the unbound `loose` worktree's prompt hook carries `中文` and `structured-choice`; `keel context --json` carries `ownerLanguage` `zh`; the session-start note carries `中文`; `rtl`, bound and with an unread mention, gets the rule and the notice together; `owner_language: Chinese!` is warned about by name, not carried, and adds no `Owner language` line. In this repository, `keel context --json` now prints the rule ending `对负责人说话一律用中文。`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 270 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel chat hook user-prompt-submit`, `keel context --json`, and the plugin's SessionStart hook in bound and unbound worktrees, and reads `AGENTS.md`.
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/context.js`, `src/core/chat/notice.js`, `plugins/keel/scripts/session-start.js`, `plugins/keel/scripts/mail-hook.js`, `keel/config.yaml`, `AGENTS.md`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a reminder cannot force the reply's language; it puts the rule beside every reply, which is what the owner chose, and whether drift stops is observed in use rather than tested here.
    - Blocker: none
    - Reauthorizations: none
## 2. Release

- [x] 2.1 Release and publish the new spec
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
    - openspec/specs/keel-owner-language/spec.md
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
    - M2: `openspec/specs/keel-owner-language/spec.md` is created from the change's spec with a Purpose, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8b9cd1c39aaf832460a34070c8543dd939c585ebded026c3e82e676a04fcb5d3
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.120.0; with the 5.120.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. `openspec/specs/keel-owner-language/spec.md` is created with a Purpose and the ADDED requirement; `published-specs-validate-strictly` reports `35 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the new spec are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the new spec, and the files 1.1 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Match the user's language where practical" — `AGENTS.md` User-facing communication, which becomes binding where `owner_language:` is declared. Updated by: 1.1
- I2: "a worktree with no chat role gets no output" — the header comment of `plugins/keel/scripts/mail-hook.js`. Updated by: 1.1

## Expectation Coverage

- E1: With a declared owner language, the rule sits next to every reply the agent writes, in every worktree, and the protocol makes it binding (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.120.0 tree reports `validation --all passed: baseline plus 270 scenarios, 1 skipped: output-survives-the-pipe.`
