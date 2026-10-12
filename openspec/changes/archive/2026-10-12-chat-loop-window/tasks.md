# Tasks

## 1. Chat

- [x] 1.1 The ping-pong guard counts only fast runs, lets the poster override once, then calls the owner
  - Covers:
    - keel-cross-host-mailbox / Loop guards stop runaway agent traffic / Ping-pong is broken and the owner is called
    - keel-cross-host-mailbox / Loop guards stop runaway agent traffic / A slow exchange is not a loop
    - D1
    - D2
    - F1
    - F2
    - F3
  - Read:
    - src/core/chat/guards.js
    - src/core/chat/store.js
  - Touch:
    - src/core/chat/guards.js
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-loop-guards` requires: after eight quick alternations in `soc`, `rtl`'s ninth post refused naming the loop guard and `--not-a-loop` with no `system` record; `rtl`'s post with `--not-a-loop "new assignment"` accepted and its record carrying `not_a_loop: new assignment`; after eight more quick alternations, the next post refused with exactly one `system` record mentioning `owner`, a `--not-a-loop` post refused too; after `owner` posts, `rtl` posting again; in a direct group, the escalated refusal not saying "another member"; and, with eight alternations whose `created` times are moved three hours back, the next post accepted. The rate limit part of the scenario still holds. Fails with: `chat-loop-guards:`
    - M2 (regression): `chat-core`, `chat-supersedes`, `chat-records`, and `chat-claude-hooks` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:24b36e981842fcc33b6f20c3a2c120e28919528c63d55a28b6f2cc9383ccce2f
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-loop-guards` reports `chat-loop-guards scenario passed.`
    - M1.red: fail. With the scenario rewritten first, it reported `chat-loop-guards: the first refusal does not name --not-a-loop: keel chat: The loop guard stopped this post: rtl and verify have alternated the last 8 messages in soc. The owner has been called; any other member's post clears it.`, carrying the declared signature `chat-loop-guards:` — the paging #297 describes.
    - M1.green: pass. With the time window, the override, and `escalated`: the ninth quick post in `soc` is refused naming `--not-a-loop` with no `system` record; the override post is accepted with `not_a_loop: new assignment` on its record; eight more quick alternations and the next post is refused with exactly one `system` record mentioning `owner`, and an override is refused; after `owner` posts, `rtl` posts again; in `dm-rtl--verify` the escalated refusal does not say "another member"; in `slow`, with eight alternations moved three hours back by rewriting their `created` lines, the next post is accepted; and the rate-limit part still refuses `lint` over its limit.
    - M2: pass. `chat-core`, `chat-supersedes`, `chat-records`, and `chat-claude-hooks` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario posts through the real `keel chat post` and `keel chat dm` from bound worktrees and as `owner`, and reads stderr and the record files; the slow fixture moves real records' `created` back rather than synthesizing records.
      - Scope check: `git status --short` lists `src/core/chat/guards.js`, `src/core/chat/store.js`, `src/core/chat/cli.js`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Resolved here: README.md — the Invalidates entry named a README loop-guard description that did not exist; the README now describes both guards, the window, and the override.
    - Blocker: none
    - Reauthorizations: none
- [x] 1.2 `--stamp` prefixes Keel's time, and `keel chat --help` prints the usage
  - Covers:
    - keel-cross-host-mailbox / Keel stamps the time and answers --help / A stamped post carries Keel's time
    - keel-cross-host-mailbox / Keel stamps the time and answers --help / Help is not an error
    - D3
    - D4
    - F4
  - Read:
    - src/core/chat/cli.js
  - Touch:
    - src/core/chat/cli.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-stamp-help` requires `keel chat post soc --stamp "R008 done"` storing text that starts with `[MM-DD HH:MM] R008 done` matching the record's own `created` month, day, hour, and minute, `keel chat dm verify --stamp x` likewise, and `keel chat --help` and `keel chat -h` each exiting 0 with `Usage:` on stdout. Fails with: `chat-stamp-help:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f79430aaeb1f5bc4ad5d6e26c77e449aa61219f367eafbd73039eed67a23e7bd
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-stamp-help` reports `chat-stamp-help scenario passed.`
    - M1.red: fail. Before the change the scenario reported `chat-stamp-help: post soc --stamp R008 done failed: keel chat: Unknown option for keel chat: --stamp`, carrying the declared signature `chat-stamp-help:`.
    - M1.green: pass. With `stamped` and the `--stamp`/`--help`/`-h` switches: the `soc` post and the direct message each store text starting with `[MM-DD HH:MM] ` equal to their own record's `created` month, day, hour, and minute, and `keel chat --help` and `-h` each exit 0 printing `Usage:`.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 266 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs the real `keel chat post`, `keel chat dm`, and `keel chat --help`/`-h`, and compares each stored body with its record's own `created`.
      - Scope check: `git status --short` lists `src/core/chat/cli.js`, `README.md`, `scripts/validate_plugin.py`, and the files 1.1 changed.
      - Findings: Discard reason: the stamp and `created` are read from the clock a few milliseconds apart, so a post landing exactly on a minute boundary could differ by one minute; widening `writeRecord` to take the stamp's time is out of proportion to that.
    - Blocker: none
    - Reauthorizations: none
## 2. Release

- [x] 2.1 Release and promote the spec
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the MODIFIED requirement replaces its counterpart and the ADDED requirement is appended in `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3822b2cf49ffaa35ca46cb17b061590f15e84d00cf09fbf0153d725660766efc
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.116.0; with the 5.116.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED "Loop guards stop runaway agent traffic" replaces its counterpart and the ADDED requirement is appended in `openspec/specs/keel-cross-host-mailbox/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and the promoted spec are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the published spec, and the files 1.1 and 1.2 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "the next post there by either MUST be refused and Keel MUST write one `system` record mentioning `owner`; the block MUST clear once any other member posts" — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 2.1
- I2: "The owner has been called; any other member's post clears it." and "the next post by either is refused, and Keel calls the owner" — `src/core/chat/guards.js` refusal and header comment, and the loop-guard description in `README.md`. Updated by: 1.1

## Expectation Coverage

- E1: Ordinary request/reply over hours is never refused, a fast exchange is refused first to the poster with a way to say why, and the owner is paged only on a repeat (D1, D2). Covered by: 1.1
- E2: A time in a message comes from Keel's clock when asked, and help is not an error (D3, D4). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.116.0 tree reports `validation --all passed: baseline plus 266 scenarios, 1 skipped: output-survives-the-pipe.`
