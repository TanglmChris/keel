# Tasks

## 1. Resolve where it is

- [x] 1.1 Keel resolves its OpenSpec dependency from any install layout, and doctor stops advising a reinstall for a dependency that is installed
  - Covers:
    - keel-target-surface-diagnostics / The OpenSpec dependency resolves from any install layout
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
    - A1
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/changes/the-dependency-resolves-where-npm-put-it/design.md
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-dependency-resolves-where-npm-put-it` scenario in `scripts/validate_plugin.py` builds the layout npm actually produces — Keel's package unpacked at `node_modules/@christang/keel` with no `node_modules` of its own, and an executable OpenSpec stub at the consumer project's `node_modules/.bin/openspec` — and drives the real CLI against it. `keel openspec --version` runs the stub and reports its version; `keel --doctor` does not report the dependency as missing. With a stub beside Keel and a different one in an ancestor, the nearer is resolved, asserted by the version each prints. With no stub anywhere and none on PATH, doctor reports it missing and advises the reinstall, which is the only case where that advice is correct. Fails with: `openspec is not resolvable`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-openspec-honesty` passes unchanged, so the resolvable-versus-PATH distinction keeps its shape.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the scenario needs network access to build the layout, because D5 records that a suite failing for registry reasons proves nothing about this code.
    - Stop if resolution binds to the dependency's internal bin path rather than the `.bin` entry, because D2 records that path belongs to the dependency.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1ab32098700920f8b5f2129d913930736f58343990560f29f83289891485fdcf
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-dependency-resolves-where-npm-put-it` reports `the-dependency-resolves-where-npm-put-it scenario passed.` The scenario builds the layout npm produces — Keel's published `files` set unpacked at `node_modules/@christang/keel` with no `node_modules` of its own, asserted absent, and an OpenSpec stub at the consumer project's `node_modules/.bin` — and runs the real CLI against it with every `openspec`-carrying entry stripped from `PATH`, so what resolves came from the layout and not from the machine. `keel openspec --version` runs the stub and prints `1.12.0`; `--doctor` does not report the dependency missing. With `9.9.9` in an ancestor and `1.12.0` beside the project, the nearer wins. With no stub anywhere, doctor reports it missing and advises the reinstall. The scenario also asserts more than this check claims: a fourth layout with the OpenSpec package present and no bin entry, where doctor names it installed and says a reinstall will not change this — the spec requirement covers that branch and shipping it unasserted would have left the distinction claimed but untested.
    - M1.red: fail, for the right reason, and the reason this task declared before the scenario was written. `the-dependency-resolves-where-npm-put-it: \`keel openspec\` did not run the hoisted dependency; exit 1, stdout '', stderr 'keel: openspec is not resolvable; reinstall keel so npm installs its OpenSpec dependency'.` That is issue #129 reproduced inside the suite, from the layout the suite had never built.
    - M1.green: pass. Same command after `openspecCandidates()` walked outward from the package root through each ancestor's `node_modules/.bin`, and after `unresolvedOpenSpecAdvice()` split the advice by whether the dependency package is present.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-openspec-honesty` reports `doctor-openspec-honesty scenario passed.` The resolvable-versus-PATH distinction keeps its shape.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 171 scenarios.` — up from 170 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the dependency resolves from any install layout and that doctor's advice matches what is wrong. M1 proves both, and the assertion that carries the change is the fixture rather than any single check: this defect survived 170 scenarios and eleven releases because every scenario ran inside the one layout where the old lookup worked. Testing harder in that layout would have found nothing. Confirmed outside the suite as well, against the real `npm install @christang/keel@5.57.0` that found the defect: `keel openspec --version` now prints `1.12.0` and doctor reports `warning — … is keel-resolvable but bare \`openspec\` is not on PATH — use \`keel openspec\``, which is the true state of that installation.
      - Scope check: `git status --short` shows exactly this task's two Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, fixed in this task. The release ritual verifies the working tree and never the published artifact — `version-alignment` and all 170 scenarios ran green through eleven releases while the package, installed the way a user installs it, could not run its own dependency. The gap is structural: a gate that only exercises the working tree cannot see a defect whose cause is the layout the working tree is not in. The scenario added here closes it for this defect by building the other layout from the published `files` set, offline. Resolved here: M1
      - Blocker: none
      - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the dependency resolves from any install layout and doctor's advice matches what is wrong
    - I1 — the published wording this change makes stale
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-target-surface-diagnostics/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The behavior was proven red-green in task 1.1, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming issue #129, stating that the invocation 5.56.0 wrote into twelve surfaces did not resolve on the common install, and recording why 170 green scenarios did not catch it
    - M3: the spec delta is promoted, `node node_modules/.bin/openspec validate the-dependency-resolves-where-npm-put-it --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7671aa8b707073e752a9d6e2710503a92e7da9e00b50a2aa0adeaaedb4a8f265
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` after `node scripts/bump_version.js minor` rewrote every marker to 5.58.0 — the npm package, both native plugin manifests, the protocol docs, and the twelve installed OpenSpec surfaces.
    - M2: pass. `keel/CHANGELOG.md` carries the `5.58.0 - the dependency resolves where npm put it` entry. It names issue #129, states that `keel openspec` — the invocation 5.56.0 wrote into twelve installed surfaces as the one that resolves — did not resolve on a plain `npm install`, and records why 170 green scenarios and eleven releases missed it: every scenario runs inside a checkout of this repository, which is the single layout where the old lookup worked, so the cause was a layout rather than a behavior and no additional coverage inside that layout could have found it.
    - M3: pass. The delta is promoted — `The OpenSpec dependency resolves from any install layout` into `openspec/specs/keel-target-surface-diagnostics/spec.md`. `node node_modules/.bin/openspec validate the-dependency-resolves-where-npm-put-it --strict` reports `Change 'the-dependency-resolves-where-npm-put-it' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 171 scenarios.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the release carries the fix and that the published wording is true of it. M1 and M3 prove the markers and the promoted requirement; M2 is the one that needed writing. The changelog entry spends most of its length on why the suite missed this rather than on what was fixed, because the fix is four lines and the miss is the part a reader of this project should carry away.
      - Scope check: `git status --short` shows the version markers, the twelve installed surfaces the bump rewrote, the protocol docs, the changelog, the promoted spec, and this change's own directory — 24 paths, all declared in Touch — the twelve installed surfaces were declared from the start this time, which the previous release had to add mid-task after the Scope check caught the bump writing outside authority. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "openspec: missing - reinstall keel so npm installs its OpenSpec dependency" —
  the doctor line in `bin/keel.js` and the proxy's `openspec is not resolvable;
  reinstall keel so npm installs its OpenSpec dependency`. Both name the one
  remedy that cannot help when the dependency is installed and unreachable.
  Updated by: 1.1
- I2: "it points at `keel --doctor` for whether a bare `openspec` resolves" — the
  overlay note shipped in 5.56.0 and the `keel-openspec-surface-overlay` spec
  requirement behind it. The wording stays true once doctor answers correctly;
  what was stale was doctor, not the sentence.
  Discard reason: no wording changes. The sentence was never wrong; the
  diagnostic it pointed at was, and 1.1 fixes that. Checked 2026-09-08.

## Expectation Coverage

- E1: Keel resolves its OpenSpec dependency from the hoisted, nested, and ancestor layouts, the nearest wins, and doctor advises a reinstall only when the dependency is genuinely absent. Covered by: 1.1, 2.1
