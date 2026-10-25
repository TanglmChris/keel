# Tasks

## 1. What the tick passes the patrol

- [x] 1.1 Measure free disk in `keel tick` and pass it, with a declared `disk_min_gb:`
  - Covers:
    - keel-coordinator-patrol / The tick passes free disk and a declared quota to the patrol / Low disk reaches the owning coordinator once
    - D1
    - D2
  - Read:
    - openspec/changes/tick-disk-quota/design.md
    - src/core/tick.js
    - src/core/config.js
  - Touch:
    - src/core/tick.js
    - src/core/config.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-passes-free-disk`: with `patrol:` listing scoped pm-a and pm-b, both `runner: tick`, and `disk_min_gb: 1000000` on pm-a, two due runs of the real `keel tick` (pm-a's and pm-b's `next_at` moved into the past between them) leave pm-a exactly one `keel-patrol` message containing `free disk is` and `below 1000000 GB`, and pm-b none. Fails with: `tick-passes-free-disk:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes, `tick-runs-due-patrol` and `tick-runs-each-patrol` among them, and so do `--scenario surfaces-agree-with-code`, `--scenario config-documents-in-declaration-order`, `--scenario delegation-resident-text`, and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b7b82b186360305a5c1eb9cf67911ce294524fa1a13bb51de78ace9e6a6a0301 (keel 5.196.1)
    - M1: pass. `tick-passes-free-disk scenario passed.` (exit 0).
    - M1.red: fail. With the corrected fixture and the committed `src/core/tick.js`: `tick-passes-free-disk: the disk risk reached {'pm-a': 0, 'pm-b': 0}, not pm-a once` (exit 1).
      - The first fixture kept the floor at 1000000 from the start. That made the baseline `low`, and patrol reports only disk *turning* low (F1), so it stayed red even with the change.
      - The fixture now runs at a floor of 1, then raises it twice. It was fixed before this red was taken.
    - M1.green: pass. `freeDiskGb` measures each patrol worktree's filesystem with `fs.statfsSync`, as `floor(bavail*bsize/2^30)`. The tick passes `--disk-free-gb`, plus `--disk-min-gb` from the first item declaring `disk_min_gb:` (D1, D2). `patrolItem` reads `disk_min_gb:` and `quota_file:`.
    - M2: pass. `validation --group shift passed: 57 scenarios.` (exit 0). `surfaces-agree-with-code`, `config-documents-in-declaration-order`, and `delegation-resident-text` each passed on its own, and `assertion-shape-count` passed at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick` with the real disk measurement, the disk turning low reaches pm-a, the first listed of two scoped coordinators, exactly once, and reaches pm-b never.
      - Scope check: `git status --short` lists `src/core/tick.js`, `src/core/config.js`, the two validation files, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Read a declared `quota_file:` in `keel tick` and say once when quota is stale or unchecked
  - Covers:
    - keel-coordinator-patrol / The tick passes free disk and a declared quota to the patrol / A quota file drives the quota risk, and its absence is said once
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/tick-disk-quota/design.md
    - src/core/tick.js
  - Touch:
    - src/core/tick.js
    - src/core/config.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
    - README.md
    - README.zh-CN.md
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario tick-reads-quota-file`: with `quota_file:` declared on the first of two scoped `runner: tick` items, due ticks with the file reading `91` and then `96` leave the first coordinator one `keel-patrol` message containing `past 90%` and one containing `past 95%` and the second none; with the file's mtime set 7 hours back the next tick prints a line containing `quota` and `stale`; in a repository declaring no `quota_file:`, the first tick prints a line containing `quota is not checked` and the second tick prints no line containing `quota`. Fails with: `tick-reads-quota-file:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4` passes, and so do `--scenario readme-zh-matches-english`, `--scenario config-documents-in-declaration-order`, `--scenario surfaces-agree-with-code`, and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bf0287f6c0e0fb2f2407f78d90ccc09b3b33cc4df77ae6f23fded7c054d0595c (keel 5.196.1)
    - M1: pass. `tick-reads-quota-file scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `tick-reads-quota-file: the 'past 90%' quota risk reached {'pm-a': 0, 'pm-b': 0}, not pm-a once.` (exit 1).
    - M1.green: pass.
      - `readQuota` resolves `quota_file:` from the first item declaring it, relative to the worktree, with `~` expanded. It passes the file's first number, rounded, as `--quota` when the file is under 6 hours old (D2, D3). It runs no command (D4).
      - The quota state (`read`, `stale`, `unreadable`, `unchecked`) is kept in `tick/state.json` as `quota_state`, and printed only when it changes.
      - A repository declaring no `patrol:` gets no quota line at all.
    - M2: pass. `validation --group shift passed: 58 scenarios.` (exit 0). `readme-zh-matches-english`, `config-documents-in-declaration-order`, and `surfaces-agree-with-code` each passed on its own, and `assertion-shape-count` passed at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick`, quota files reading 91 and then 96.4 reach pm-a, the owning coordinator, as `past 90%` and `past 95%` once each, and reach pm-b never. A file 7 hours old is reported stale. With none declared, the first tick says quota is not checked, and the second says nothing about quota.
      - Scope check: `git status --short` lists `src/core/tick.js`, the two validation files, both READMEs, `keel/config.yaml`, and this change's directory. `src/core/config.js` was already changed by 1.1 and is in Touch.
      - Findings: none.
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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-coordinator-patrol/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Tasks 1.1 and 1.2 prove the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:152839c5134b6f36c2607172578c6e341b1cf17fe27f5ab4ad304f0b0de56012 (keel 5.196.1)
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`keel tick` MUST be one model-free step: … run `keel patrol --since-last --notify` as that role" — `openspec/specs/keel-coordinator-patrol/spec.md`. Discard reason: still true; the added requirement says what the tick now passes, and the step stays model-free.
- I2: "patrol once its recommended next run has passed" — the `patrol` comment in `keel/config.yaml`, and the README patrol sections in both languages, which name no `disk_min_gb:` or `quota_file:`. Updated by: 1.2.

## Expectation Coverage

- E1: A patrol run by `keel tick` reports low disk (D1, D2) and, from a declared quota file, the quota steps (D2, D3, D4) to the coordinator that owns repository-wide risks, and says once when quota is stale or unchecked (#456). Covered by: 1.1, 1.2
- E2: The release carries it. Covered by: 2.1
