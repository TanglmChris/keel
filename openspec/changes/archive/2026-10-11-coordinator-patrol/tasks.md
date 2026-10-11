# Tasks

## 1. Waits and patrol

- [x] 1.1 `keel chat wait`/`waits` declare waits, and `keel patrol` marks held conditions met, notifies the waiter once, and reports roles
  - Covers:
    - keel-coordinator-patrol / A role declares what it is waiting for in the chat / A declared wait is listed until met
    - keel-coordinator-patrol / A role declares what it is waiting for in the chat / A malformed wait is refused
    - keel-coordinator-patrol / Patrol notifies the roles whose conditions are met and writes nothing otherwise / A landed commit wakes the waiting role once
    - keel-coordinator-patrol / Patrol notifies the roles whose conditions are met and writes nothing otherwise / Nothing new writes nothing
    - keel-coordinator-patrol / Patrol notifies the roles whose conditions are met and writes nothing otherwise / An issue condition needs the caller's issue data
    - D1
    - D2
    - D3
    - D4
    - D6
    - D7
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/notice.js
    - bin/keel.js
  - Touch:
    - src/core/patrol.js
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - bin/keel.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario coordinator-patrol` uses a repository with a bare `origin` and roles `rtl` and `verify`, and through the real CLI requires: `verify`'s `chat wait soc --commit <sha>` listed by `waits --json` with condition `commit <sha> on origin` and nothing unread for `rtl`; a wait with no condition and one with both refused naming both forms; `keel patrol` by `rtl` before the push exiting 0 with every log file byte-identical and the digest naming `verify`; after the push, exiting 2, the wait gone from `waits`, and `verify` having a direct message naming the commit unread; a second run exiting 0 writing nothing; and an issue wait reported unchecked without `--issues` (exit 0) and met with `--issues` listing it `CLOSED` (exit 2). Fails with: `coordinator-patrol:`
    - M2 (regression): `chat-core`, `chat-records`, `chat-ack`, and `chat-supersedes` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0abd8fdd37cf9fabe37ec0dde4edee2ec772223e9517d75caf71c9f1a4afea77
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario coordinator-patrol` reports `coordinator-patrol scenario passed.`
    - M1.red: fail. Before the change the scenario reported `coordinator-patrol: keel chat wait failed:  keel chat: Unknown option for keel chat: --commit`, carrying the declared signature `coordinator-patrol:`.
    - M1.green: pass. With `wait`/`openWaits`/`markMet` in the store, `wait`/`waits` in the chat CLI, and `src/core/patrol.js` behind `keel patrol`, the wait lists with `commit <sha> on origin`, both malformed waits name both forms, the pre-push patrol exits 0 with every log byte-identical, the post-push patrol exits 2 and leaves `verify` a direct message naming the commit, a rerun exits 0 writing nothing, and the issue wait is unchecked without `--issues` and met with it.
    - M2: pass. `chat-core`, `chat-records`, `chat-ack`, and `chat-supersedes` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario uses a real bare remote and pushes the awaited commit between patrol runs, reading exit codes, the waits list, the waiter's unread messages, and byte snapshots of every chat log.
      - Scope check: `git status --short` lists `src/core/patrol.js`, `src/core/chat/store.js`, `src/core/chat/cli.js`, `bin/keel.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: idleness is reported and never sets the exit status (D6), so a stalled coordinator with no met condition still wakes nobody; the owner's decision kept patrol to notices and left any idle escalation for later.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `issue_roles:` routes each labelled issue update to its role once
  - Covers:
    - keel-coordinator-patrol / Issue labels route issue updates to roles / A labelled issue reaches its role once per update
    - D5
    - D7
    - F4
  - Read:
    - src/core/patrol.js
    - src/core/config.js
  - Touch:
    - src/core/patrol.js
    - src/core/config.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-issue-routing` declares `issue_roles:` mapping `role:verify` to `verify` plus one unreadable line, and requires `keel patrol --issues <file>` by `rtl` with issue 157 carrying that label to exit 2 with `verify` having one direct message naming `#157` unread and the unreadable line reported; the same file again to exit 0 writing nothing; and a later `updatedAt` to send exactly one more. Fails with: `patrol-issue-routing:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bebb5e77a52726f69a393254861612f5133957ca6c8e566cb6c330561ca8ab22
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-issue-routing` reports `patrol-issue-routing scenario passed.`
    - M1.red: fail. Before the change the scenario reported `patrol-issue-routing: the first patrol exited 0, not 2: keel patrol: nothing new.`, carrying the declared signature `patrol-issue-routing:`.
    - M1.green: pass. With `readIssueRoles` in `src/core/config.js` and `routeIssues` in the patrol, the first run exits 2 with one direct message naming `#157` for `verify` and the unreadable line reported, the same `updatedAt` exits 0 with every log byte-identical, and a later `updatedAt` sends exactly one more.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 254 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario writes real `gh`-shaped JSON, runs the real `keel patrol` three times, and counts the waiter's unread notices and byte snapshots of the chat logs.
      - Scope check: `git status --short` adds `src/core/config.js` and `keel/config.yaml` to 1.1's files; `README.md` and `scripts/validate_plugin.py` are in this task's Touch as well.
      - Findings: Resolved here: M2. The first `npm test` failed `the-tarball-is-the-repository` because the new `src/core/patrol.js` was untracked; it is now added to the index. Discard reason: the first patrol over a repository with mapped labels notifies every mapped open issue once (D5); patrol keeps no state but the chat, so there is no earlier run to compare with.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and publish the new spec
  - Covers:
    - E3
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
    - openspec/specs/keel-coordinator-patrol/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: `openspec/specs/keel-coordinator-patrol/spec.md` holds the three requirements with a Purpose, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a8f388b314d1e5b39d6079c28de2c45a9282b2b9209dd042b1dbb09cda42709a
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.109.0 on top of `main` at 5.108.0 (#282). With the 5.109.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. `openspec/specs/keel-coordinator-patrol/spec.md` holds a Purpose and the three requirements; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the new published spec carries all three requirements with their scenarios, and the changelog names both issues, the decisions, and the exit statuses.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the new spec, both in Touch.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/260 — re-arming the coordinator's schedule across shift changes, the step the owner deferred; #260 stays open for it.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.109.0 reports `validation --all passed: baseline plus 254 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "Ten independent declarations live here" — the header of `keel/config.yaml`, which gains `issue_roles`. Updated by: 1.2

## Expectation Coverage

- E1: A role that is waiting is told when its condition holds, by a patrol a host can run cheaply, with nothing written when nothing changed (D1–D4, D6, D7). Covered by: 1.1
- E2: An issue update reaches the role its label names, once per update, without anyone watching the issue (D5). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
