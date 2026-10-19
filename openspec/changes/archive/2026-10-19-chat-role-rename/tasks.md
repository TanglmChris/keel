# Tasks

## 1. A role can be renamed

- [x] 1.1 Add `keel chat role --rename`; read the log through the renames; move per-role state
  - Covers:
    - keel-cross-host-mailbox / A role can be renamed / A renamed role keeps its groups, todos, state and mentions
    - keel-cross-host-mailbox / A role can be renamed / A rename onto a role that already exists keeps the new role's state
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
  - Read:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/notice.js
    - src/core/shift.js
    - src/core/patrol.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/rename.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-rename` sets up `verify` (in `soc` and `dm-rtl--verify`, an open todo, a read record, a shift note, `patrol: role: verify` in `keel/config.yaml`), runs the real `keel chat role --rename verify check`, then through the real commands: `group list` shows `check` in both groups; `todos --mine` lists the todo; `unread --json` does not list the record read before; `shift status` names `check`'s note; a new `@verify` post from `rtl` lists `check` in its mentions and the record wakes `check`; `role --set verify` is refused naming `check`; the rename's output lists the `patrol:` line. A second repository where `check` was bound first and holds a later cursor: the rename passes, the later cursor stays, and `--alias verify` is refused naming `check`. Refusals: unknown `<old>`, `<old>` equal to `<new>`, and both bound to worktrees. Fails with: `keel chat role --rename was refused`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b6baecf3b5e9135da44d8d258f101c8b5ce6e94af0a1bb396efb78b1c5e9289e (keel 5.157.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-role-rename` reports `chat-role-rename scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `chat-role-rename: keel chat role --rename was refused: '' 'keel chat: Unknown option for keel chat: --rename\n'`, carrying the declared signature.
    - M1.green: pass. With `renames.json` and `canonicalRole`, `readLog` and `findRecord` mapping each role field and a direct group's members through it, `aliasMap` holding former names, `setRole` refusing them, and `src/core/chat/rename.js` moving bindings and per-role state, the scenario passed. Three mutations each turned it red with their own message: skipping the cursor move (`a record verify had read is unread again`), `readLog` without the mapping (`check is not a member of soc`), and `aliasMap` without former names (`@verify does not mention check`).
    - M2: pass. `npm test`: `validation --all passed: baseline plus 302 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through the real commands, after `keel chat role --rename verify check`, `check` is a member of `soc` and `dm-rtl--verify`, holds verify's open todo, keeps what verify had read, has its shift note, is mentioned and woken by `@verify`, cannot be re-bound as `verify`, and the rename lists `keel/config.yaml`'s `role: verify`. A rename onto an existing `check` keeps its later cursor, and `--alias verify` is refused naming `check`. An unknown role, a rename onto itself and onto a bound role are refused, each for its reason.
      - Scope check: `git status --short` lists `README.md`, `scripts/validate_plugin.py`, `src/core/chat/cli.js`, `src/core/chat/rename.js`, `src/core/chat/store.js`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Discard reason: `renames.json` stays on this machine like the rest of the store's state, so another machine sharing the groups through the archive branch or Slack still reads the old name; every team that uses roles today runs on one machine, and a second machine can run the same rename.
        - Discard reason: `keel shift request|start <old>`, `keel chat wake now <old>` and `keel chat role --park <old>` do not map a former name: park and wake now refuse it by name, and a shift request reaches the new role through the mapped log, only under a direct group spelled with the old name. Mapping every role argument would widen this change past the store and the chat CLI.
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
    - Contract: keel-task-capsule/v1 sha256:ad1d21fc586027314b6ee1b8e12a11935337be36e3cf064845c1d40c0682d275 (keel 5.158.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.158.0 → 5.159.0; with the "a chat role can be renamed" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-cross-host-mailbox`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel chat role --set <role> [--alias <a>]`" — README.md, the command list, which gains `--rename`. Updated by: 1.1

## Expectation Coverage

- E1: A renamed role keeps its groups, open todos, read state, shift and patrol state, and mentions of its old name reach it (#376; D1, D2, D3, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
