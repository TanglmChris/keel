# Tasks

## 1. Explain a session whose directory is gone

- [x] 1.1 Wake now names a vanished directory and prints the fork command; tick skips it; patrol and shift status list it
  - Covers:
    - keel-cross-host-mailbox / A session whose directory is gone is explained, not resumed / A session from a renamed workspace prints the fork command
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/wake-moved-worktree/design.md
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/tick.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/chat/cli.js
    - src/core/tick.js
    - src/core/patrol.js
    - src/core/shift.js
    - scripts/validation/chat.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-moved-worktree`: with a stand-in claude whose `agents` row and verify's presence both record a directory that does not exist, the real `keel chat wake now verify` runs no `claude --bg`, exits nonzero, names the directory, and prints `cd <verify's worktree> && claude --bg --fork-session --resume sess-verify-1`; `keel tick` after a new dm to verify runs no `claude --bg`; `keel patrol` from rtl reports a risk naming verify and `keel chat wake now verify`; and `keel shift status` lists verify under `Sessions that cannot be resumed:`. Fails with: `chat-wake-moved-worktree: wake now does not print the fork command`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-now-cli --scenario chat-wake-skips-removed-session --scenario shift-cli-self-shift --scenario assertion-shape-count` passes, and so do `--group chat --jobs 4` and `--group shift --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:23125d4a1504f2436090b01081bee96e207b64582c49f40e8a5c62fec61db799 (keel 5.200.0)
    - M1: pass. `chat-wake-moved-worktree scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `chat-wake-moved-worktree: wake now does not print the fork command for verify's worktree: "Could not resume verify's CLI session sess-verify-1 in …/renamed-away/verify.\nclaude was not found; put it on PATH or name it with KEEL_CLAUDE\n"` (exit 1). The missing `cwd` made `spawnSync` fail with `ENOENT`, which was misreported as a missing `claude`.
    - M1.green: pass.
      - `resumeCli(entry, where)` takes the directory from the host row's `cwd`, or from presence. When that directory is missing, it returns `moved`, starts nothing, and prints `forkCommand`: `cd <bound worktree> && claude --bg --fork-session --resume <id> -n "<role> · <time>" --permission-mode <declared> "<wake prompt>"` (D1).
      - `wake now` raises it, and so exits nonzero. `wakeEnded` marks the record woken on `moved` (D2).
      - `movedSessionRisks` feeds the patrol's risks, and `keel shift status` adds a `Sessions that cannot be resumed:` section (D4).
      - The first green run failed only on the path's spelling: `roles.json` holds the realpath `/private/var/…`, so the check now accepts either spelling.
    - M2: pass.
      - `chat-wake-now-cli`, `chat-wake-skips-removed-session`, and `shift-cli-self-shift` passed.
      - `assertion-shape-count` first counted 75 against 74 recorded. The new status check combined "no section" and "verify not listed" under one message, and is now split, giving `74 sites`.
      - `validation --group chat passed: 49 scenarios.` and `validation --group shift passed: 59 scenarios.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel chat wake now`, `keel tick`, `keel patrol`, and `keel shift status` with a stand-in claude whose row and presence both name a vanished directory: no `claude --bg` runs, `wake now` exits nonzero naming the directory and printing the fork command for verify's worktree, the tick leaves the session alone, the patrol names verify with `keel chat wake now verify`, and status lists verify.
      - Scope check: `git status --short` lists `src/core/chat/notice.js`, `src/core/chat/cli.js`, `src/core/tick.js`, `src/core/patrol.js`, `src/core/shift.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, and this change's directory, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations:
      - 2026-10-25: M1's `Fails with:` changed from `wake now resumed a session whose directory is gone` to `wake now does not print the fork command`. The first red showed that no `claude --bg` ran at all: `spawnSync` with a missing `cwd` fails with `ENOENT`, which `resumeCli` reported as `claude was not found; put it on PATH or name it with KEEL_CLAUDE`. The predicted red was wrong about the mechanism, and the check's assertions are unchanged. task-start was re-run for the new fingerprint, and no execution evidence had been recorded.

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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - M2: the delta is promoted into `keel-cross-host-mailbox`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b648df7a2e7a45589c5ef0ca6d3d7eefa918bd119de27a5ea8d43e820d4d0930 (keel 5.200.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.200.0 → 5.201.0. With the section "Wake now explains a session whose directory is gone" written, `version-alignment scenario passed.` (exit 0).
    - M2: the added requirement "A session whose directory is gone is explained, not resumed" is promoted into `keel-cross-host-mailbox`. `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` on commit 7b2a2daf (clean tree), started 21:03 at load 3.22: `validation --all passed: baseline plus 338 scenarios, 2 skipped: output-survives-the-pipe, docx-converts-markdown-with-svg.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2. The markers, the 5.201.0 section, and the published spec carry the change, and the full suite passes on the committed tree.
      - Scope check: beyond task 1.1, the files are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Only `--bg --resume <id>` and the prompt: any other flag starts a copy with a new session id." — the `resumeCli` comment in `src/core/chat/notice.js`, which now also names the vanished-directory case that resumes nothing. Updated by: 1.1.

## Expectation Coverage

- E1: A session whose directory is gone is explained with a command to copy, not resumed into a host error, and the roles it affects are listed (#465; D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
