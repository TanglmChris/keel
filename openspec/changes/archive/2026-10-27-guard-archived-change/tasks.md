# Tasks

## 1. A finished, archived task stops guarding

- [x] 1.1 Let a manifest over an archived, checked task enforce nothing, on the hook and in `keel guard status`
  - Covers:
    - keel-touch-write-guard / A manifest whose change is gone is refused as stale / A finished task's archived change no longer guards
    - keel-touch-write-guard / A manifest whose change is gone is refused as stale / An archived change's manifest denies by naming the clear
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/guard-archived-change/design.md
    - plugins/keel/scripts/pretooluse-guard.js
    - src/core/guard.js
    - scripts/validation/guard.py
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - src/core/guard.js
    - bin/keel.js
    - scripts/validation/guard.py
    - scripts/validation/registry.py
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario guard-archived-complete-task`: with a manifest started on `demo#1.1`, the task then checked and `openspec/changes/demo` moved to `openspec/changes/archive/2026-10-27-demo`, the real PreToolUse hook gives no decision for an `Edit` of `src/feature.js` or a `Write` of `openspec/changes/next/proposal.md`, and the real `keel guard status --json` exits 0 with status `archived`, a problem coded `task-archived`, and a message naming `openspec/changes/archive/2026-10-27-demo` and `keel guard clear`. Fails with: `guard-archived-complete-task:`
    - M2 (regression): run one at a time, each passes: `--scenario guard-stale-manifest` (an archived change with the task unchecked still denies as stale), `--scenario guard-status-stale-manifest`, `--scenario readme-zh-matches-english`, `--scenario surfaces-agree-with-code`, `--scenario assertion-shape-count`, and `node scripts/run_python.js scripts/validate_plugin.py --group guard --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d98051b9c8ac1cbffb31d6c58840360b87dcf66d8c8045a355d5668cfb0ba09c (keel 5.211.0)
    - M1: pass. `guard-archived-complete-task scenario passed.` (exit 0).
    - M1.red: fail. Before the change, exit 1: ``guard-archived-complete-task: an edit of a product file got a decision from a manifest over an archived, checked task: {… 'permissionDecision': 'deny', 'permissionDecisionReason': 'Keel write guard: this manifest is stale — it guards demo#1.1, but openspec/changes/demo no longer exists, … Run `keel guard clear`, …'}`` — the #491 refusal.
    - M1.green: pass. The hook's stale-manifest branch first looks for the lexically last `openspec/changes/archive/<YYYY-MM-DD>-<change>/` (`archivedChangeDir`) and, when `taskIsChecked` — now taking that directory — finds the guarded task checked there, returns no decision (D1, D2). `keel guard status` makes the same test (`archivedCheckedChange` in `src/core/guard.js`) and returns status `archived` with problem `task-archived` naming the archived directory and `keel guard clear`; `bin/keel.js` exits 0 for `archived`. Neither the product edit nor the next change's `proposal.md` got a decision, and status read `archived`. Both READMEs say so (I2), and the hook comment no longer claims every archive is denied (I3).
    - M2: pass. Run one at a time, each exit 0: `guard-stale-manifest scenario passed.` (its archived-unchecked case still denies as stale, D3), `guard-status-stale-manifest scenario passed.`, `readme-zh-matches-english scenario passed.`, `surfaces-agree-with-code scenario passed.`, `assertion-shape-count scenario passed: 74 sites`, and, started once the load average fell below 10, `validation --group guard passed: 50 scenarios.`.
    - Review:
      - Status: pass
      - Acceptance check: through the real hook and the real `keel guard status --json`, a manifest whose task was checked and whose change was moved under `openspec/changes/archive/` decided neither write and read `archived` with exit 0 (M1), while the archived-unchecked case still fails closed (M2, `guard-stale-manifest`).
      - Scope check: `git status --short` lists `plugins/keel/scripts/pretooluse-guard.js`, `src/core/guard.js`, `bin/keel.js`, `scripts/validation/guard.py`, `scripts/validation/registry.py`, both READMEs, and this change's directory, all in Touch.
      - Findings: Discard reason: if a change name is reused, deleted without archiving, and an older archive of the same name shows the task checked, the guard stands down for the newer manifest. Neither the manifest nor the archive records which run it belongs to, a reused name is rare, and the cost is the pre-#56 behavior for that one manifest, so it is not guarded against.
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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-touch-write-guard/spec.md
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
    - M2: the delta is promoted into `keel-touch-write-guard`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:82f2dab03bc10ea51b46cc0e558f62938ab86dea481f0ae0e7d04c31bffee40c (keel 5.211.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.211.0 → 5.212.0. With the section "A manifest over an archived, finished task enforces nothing" written into the stub, `version-alignment scenario passed.` (exit 0).
    - M2: the modified requirement replaces its published form in `openspec/specs/keel-touch-write-guard/spec.md`, and `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`, started once the load average fell below 10: `validation --all passed: baseline plus 352 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.212.0, the promoted spec validates strictly, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, and this change's directory, all in Touch, beside task 1.1's files, which were dirty when this task started because its WIP commit did not go through.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Keel MUST keep denying the write. Failing closed is what stops archiving a change from silently disabling the guard" — the requirement "A manifest whose change is gone is refused as stale" in `openspec/specs/keel-touch-write-guard/spec.md`. Updated by: 2.1.
- I2: "it fails closed: a manifest Keel cannot read refuses edits rather than allowing them" — the write guard paragraph in `README.md` and `README.zh-CN.md`, which does not say an archived, finished task stops guarding. Updated by: 1.1.
- I3: "Denying here fixes both, and denying rather than allowing is what stops `openspec archive` from quietly disabling the guard." — the comment above the stale-manifest branch in `plugins/keel/scripts/pretooluse-guard.js`. Updated by: 1.1.

## Expectation Coverage

- E1: A manifest over a task that was checked and then archived enforces nothing on the hook and reads `archived` in `keel guard status` (D1, D2); any other vanished change still fails closed (D3); the alternatives are recorded as not taken (D4) (#491). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
