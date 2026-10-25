# Tasks

## 1. Report what is installed

- [x] 1.1 Read the CLI's before and after versions from the global prefix, and fail an install that did not take
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / An install that did not take is not reported as updated
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/update-verifies-install/design.md
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - scripts/validation/hosts.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-verifies-installed-cli`: with a stand-in npm whose `root -g` names a temporary prefix holding `@christang/keel` 5.0.0, whose `pack` yields 5.1.0, and whose `install -g` writes the version `FAKE_NPM_INSTALLS` names, the real `keel --update` prints a CLI line containing `failed`, the prefix's `package.json` path and `5.0.9` and exits nonzero when the install writes 5.0.9; and prints `updated 5.0.0 -> 5.1.0` and exits 0 when it writes 5.1.0. Fails with: `update-verifies-installed-cli:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --group hosts --jobs 4` passes, with every `update-*` scenario in it, and so do `--scenario update-restores-overlays` and `--scenario assertion-shape-count`, run one at a time.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2237600c2eb5ec8a67db245d254e313ed5d59cd6db6a5d05c53b1e9bca79b678 (keel 5.197.1)
    - M1: pass. `update-verifies-installed-cli scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `update-verifies-installed-cli: an install that left the prefix at 5.0.9 does not read failed: "keel update: cli: updated 5.197.1 -> 5.1.0 - …"` (exit 1). That is the #459 shape: the "from" version came from the running copy, and the install was assumed to have taken.
    - M1.green: pass.
      - `installedCli` reads `<npm root -g>/@christang/keel/package.json` before packing and again after installing (D1, D2).
      - A prefix holding a version other than the packed one reads `failed … exited 0, but <file> holds <v>` and exits nonzero (D3).
      - An unreadable prefix keeps the old wording and appends `; not verified: <why>` (D4).
      - On the real host, this branch's `node bin/keel.js --update` printed `keel update: cli: current 5.197.1 - the npm registry's latest here is 5.197.1; …`, with no "not verified" suffix. So it read `/opt/homebrew/lib/node_modules/@christang/keel/package.json`.
    - M2: pass. `validation --group hosts passed: 37 scenarios.` (exit 0). `update-restores-overlays` and `assertion-shape-count` (74 sites) passed.
      - The first hosts run, started at a 5-minute load average of 22, failed `update-pack-install` and `update-covers-installed-hosts`. Their asserted npm call sequences did not allow the new read-only `npm root -g` before and after. Both now assert those two reads explicitly, and still assert the calls that change something.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel --update` against a stand-in npm with a real prefix directory, an install that did not take reads `failed` and names the file and version. One that took reads `updated 5.0.0 -> 5.1.0`, with its before version from the prefix rather than the running 5.197.1.
      - Scope check: `git status --short` lists `bin/keel.js`, `scripts/validation/hosts.py`, `scripts/validation/registry.py`, and this change's directory.
      - Findings: the original occurrence's root cause is still unknown (design F2). The fix removes the false `updated` whatever the cause. Discard reason: npm keeps 10 debug logs, so the evidence for the 2026-10-25 run is gone, and there is nothing left to investigate without a new occurrence. A new occurrence will now read `failed` and name the file.
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
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7542ad70303b9cceb08558110eae91176f850ccacdf6c39c9c1c50bcbfb65476 (keel 5.197.1)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.197.1 → 5.198.0. With the section "keel --update reports the CLI the global prefix actually holds" written, `version-alignment scenario passed.` (exit 0).
    - M2: the modified requirement "One owner-run update covers every installed Keel component" is promoted into `keel-native-plugin-package`. `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` on commit 2118780c (clean tree), started at load 4.41: `validation --all passed: baseline plus 335 scenarios, 2 skipped: output-survives-the-pipe, docx-converts-markdown-with-svg.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2. The markers, the 5.198.0 section, and the published spec carry the change, and the full suite passes on the committed tree.
      - Scope check: beyond task 1.1, the files are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "applies to the next command that runs keel" reported after any `npm install -g` that exits 0 — `bin/keel.js` `updateGlobalCli`. Updated by: 1.1.

## Expectation Coverage

- E1: `keel --update` never reports the CLI `updated` to a version the global prefix does not hold, and names its before version from that prefix (#459; D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
