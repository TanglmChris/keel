# Tasks

## 1. Two live sessions on one role are reported

- [x] 1.1 Record sessions per role; warn on context, post and read when two are live
  - Covers:
    - keel-cross-host-mailbox / Two live sessions on one role are reported / A second live session on a role is reported, and the report ends with it
    - D1
    - D2
    - D3
  - Read:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario two-live-sessions-on-one-role` runs the real chat hooks in verify's worktree as CLI session `sess-a` (this process) and `sess-b` (a live `sleep`), then the real `keel context --json`, `keel chat post` and `keel chat unread --json`: one session gives no warning; two give a context warning naming `verify`, `sess-a`, `sess-b` and `read cursor`, and stderr warnings on post and unread with parseable JSON on stdout; after `sess-b`'s process is killed the context warning is gone. Fails with: `keel context's warning does not name 'verify'`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b4690dc7f483a210876c70d28e10651a43f90fa7cf697b9fe06f46356dde477b (keel 5.156.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario two-live-sessions-on-one-role` reports `two-live-sessions-on-one-role scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `two-live-sessions-on-one-role: keel context's warning does not name 'verify': ['Working tree has uncommitted paths …']`, carrying the declared signature.
    - M1.green: pass. With `touchPresence` recording each session under `presence/<role>.sessions.json` and pruning ended ones, `twinWarning` for two or more live sessions, the context warning, and the stderr warning on `post`, `dm`, `todo`, `unread` and `read`, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 300 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through the real hooks and commands, one CLI session on `verify` is quiet; with a second live one, `keel context` warns naming `verify`, both session ids and the read cursor, and `post` and `unread --json` warn on stderr while stdout stays valid JSON; killing the second process clears the warning.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/context.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: the read cursor stays per role, as #369 offered a warning as the alternative; keying it per session would change what every existing store counts as read.
        - Durable owner: https://github.com/TanglmChris/keel/issues/369 — its CLI team documentation, the last point, follows once the CLI hand-off has merged.
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
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - M2: the delta requirements are promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract:
    - M1:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Two sessions running as one role are told so before one hides the other's records (#369 point 4; D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
