# Tasks

## 1. The stamp is the default

- [x] 1.1 Stamp `post` and `dm` by default; `--no-stamp` opts out
  - Covers:
    - keel-cross-host-mailbox / Keel stamps the time and answers --help / The stamp is the default
    - D1
    - D2
    - D3
  - Read:
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/chat/cli.js
    - src/core/chat/store.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-stamp-default` runs the real `keel chat` in a two-role group: a plain post, a `--reply-to` reply and a `dm`, none with `--stamp`, each store `[MM-DD HH:MM] <text>` matching the record's own created time; `--no-stamp` stores the text as given; a text opening with `[10-19 11:00]` is stored unchanged; `--stamp --no-stamp` is refused; a reply to a todo opening with `✅` still closes it, and a post opening with `# Plan` keeps the heading on its own line. Fails with: `without --stamp stored 'plain post'`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:904406f0dfbaf8ab058a59c36e1e874deb4541f4c561c3d482560f6c4b6ff0b6 (keel 5.149.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-stamp-default` reports `chat-stamp-default scenario passed.`
    - M1.red: fail. With the scenario written first and `cli.js` unchanged: `chat-stamp-default: post soc plain post without --stamp stored 'plain post', not '[10-19 11:09] plain post'`, carrying the declared signature. After the reauthorization, with the default stamp in place and D3 not yet: `a post opening with a heading was not stamped on its own line: '[10-19 11:15] # Plan\n- one\n- two'` and `a stamped ✅ reply did not close its todo`.
    - M1.green: pass. With `stamped()` stamping unless `--no-stamp`, leaving a text that opens with a stamp alone, refusing both flags, and putting the stamp on its own line above a Markdown block, and `DONE_REPLY` accepting a leading stamp, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 294 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. `chat-core` compares posted text with a leading stamp removed, since the stamp is not the author's text.
    - Review:
      - Status: pass
      - Acceptance check: the real `keel chat` stamps a plain post, a `--reply-to` reply and a `dm` with the record's own created minute; `--no-stamp` and a pre-stamped text are stored as given; `--stamp --no-stamp` is refused; a stamped `✅` reply closes its todo; a post opening with `# Plan` keeps the heading on its own line.
      - Scope check: `git diff --stat HEAD~1` lists `src/core/chat/cli.js`, `src/core/chat/store.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Resolved here: M1 — a `✅` reply written with `--stamp` before this change never closed its todo either, since `DONE_REPLY` required `done`/✅ at the start; the stamp-aware pattern fixes both.
    - Blocker: none
    - Reauthorizations: 2026-10-19 — before any Evidence: `npm test` showed the default stamp breaking two behaviors (a `✅` reply no longer closed its todo, a leading Markdown heading no longer converted for Slack); D3 added, `src/core/chat/store.js` added to Touch, M1 extended to both; anchor re-recorded. The first M1 red was run before the re-record, under M1's earlier text.

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
    - Contract: keel-task-capsule/v1 sha256:bf44a74dbc33539ec1e4ae1629e4694c1f492ca17618113a2519d8b6e56c46b4 (keel 5.149.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.150.0 → 5.151.0; with the "Chat posts carry Keel's time by default" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-cross-host-mailbox`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel chat post` and `keel chat dm` with `--stamp` MUST prefix the text" — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1
- I2: "[--stamp]" in the `post` and `dm` usage lines — `src/core/chat/cli.js`. Updated by: 1.1

## Expectation Coverage

- E1: Every human-written `post` and `dm` carries Keel's time unless its author opts out (#349, D1, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
