# Tasks

## 1. The digest

- [x] 1.1 `keel chat summary --since` lists per group and sender what changed, folds superseded records, and names waiting acknowledgements
  - Covers:
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / A coordinator's digest
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / Nothing since the time
    - keel-cross-host-mailbox / A structural digest summarizes what changed since a time / A summary without a time or a role is refused
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - src/core/chat/view.js
  - Touch:
    - src/core/chat/store.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-summary` builds the coordinator's-digest fixture with roles `rtl` and `verify` and requires `keel chat summary --since <before> --json` to report it as the scenario describes, every read cursor file to be byte-identical before and after, a `--since` after the last record to say nothing changed with exit 0, and a missing `--since`, an unreadable one, and a worktree with no role each to exit non-zero naming the fix. Fails with: `chat-summary:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:02ae3830652197a832e56cf73b9bacbe4ee65de11e928d7d59e277d1128b0ba8
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-summary` reports `chat-summary scenario passed.`, three runs in a row.
    - M1.red: fail. Before the change the scenario reported `chat-summary: keel chat summary failed:  keel chat: No group summary.`, carrying the declared signature `chat-summary:`: the word was read as a group name to view.
    - M1.green: pass. With `store.summary` and the `summary` command, the scenario passes: per-sender counts with the superseded rule folded, todos with `open`/`done`, the closed todo under its closer, the superseding record naming its target, the waiting acknowledgement naming `verify`, every cursor file byte-identical, `nothing changed` with exit 0, and the three refusals.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 245 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real CLI with two roles, reads the `--json` digest field by field, compares every cursor file's bytes before and after, and reads the text form for the superseding line.
      - Scope check: `git status --short` lists `src/core/chat/store.js`, `src/core/chat/cli.js`, `scripts/validate_plugin.py`, `README.md`, and this change's own directory.
      - Findings: Resolved here: M1 and M2. The first full run failed `assertion-shape-count` on two combined guards in the new scenario, and a `--since` with sub-second precision could miss records stamped to the second; both were fixed and re-run.
        Discard reason: a todo closed is listed under the role that closed it, which D2 leaves open; per-sender is the digest's unit, so the closer is the sender.
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:af8fd697749b0770068bc26f8b3b04b1340cf37d0a0c713fe729536d0c31fbd8
    - M1: pass. After merging `main` (5.103.0, #273), `node scripts/bump_version.js minor` moved every marker to 5.104.0. With the 5.104.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-cross-host-mailbox/spec.md`; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries the digest requirement with its three scenarios, and the changelog names the issue and the command.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.104.0 reports `validation --all passed: baseline plus 245 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- None.

## Expectation Coverage

- E1: A coordinator reads what changed since a time from one deterministic command, with superseded records folded and waiting acknowledgements named (D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
