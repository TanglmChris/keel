# Tasks

## 1. Drift names its cause

- [x] 1.1 Version in the anchor; Git-tied drift diagnosis; compiler-only re-record; authorization change at close
  - Covers:
    - keel-core-gates / Drift names its cause when Git ties the anchor to a commit / A compiler change is named as one
    - keel-core-gates / Drift names its cause when Git ties the anchor to a commit / An edit is named by the field it changed
    - keel-core-gates / Drift names its cause when Git ties the anchor to a commit / An anchor no commit explains claims nothing
    - keel-core-gates / A re-record may carry what the author declares survived it / A compiler-only re-record keeps the evidence, verified
    - keel-core-gates / change-close compares the anchor of every checked task / A standing-authorization change does not drift a completed task
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
  - Read:
    - src/core/gates.js
    - src/core/context.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/drift.js
    - src/core/gates.js
    - src/core/context.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario contract-drift-diagnosis` runs the real CLI in a real Git repository whose change it commits after each step: `task-start --record` writes `(keel <running version>)` in the anchor; an anchor rewritten to another digest with `(keel 5.0.0)` and committed makes `task-complete` fail with `contract-drift` naming a compiler change, the recording commit, `5.0.0`, the running version and that no `--keep-evidence` is needed, and a following `task-start --record` warns that the evidence stands, names the commit, and names no check as stale; the same rewritten digest naming the running version yields a drift message with no cause; a re-recorded and committed task whose Touch is then edited fails naming `touch` and the commit; a checked task inheriting `push:main` whose `keel/config.yaml` then changes to `push-protected:main` passes `change-close --action archive` with a warning naming the task, while `task-complete` on an unchecked task inheriting it still fails with `contract-drift`; `keel context` names the cause for the selected drifted task. Fails with: `does not name a compiler change`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario contract-anchor-is-compared`, `--scenario drift-names-where-to-look`, `--scenario a-staleness-report-names-its-exception`, and `--scenario evidence-survives-what-did-not-change` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d0e38b55ddf5fc4094835882ab0f524b8f4f3f9a40faf4c785c5b2cd779b2344
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario contract-drift-diagnosis` reports `contract-drift-diagnosis scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `contract-drift-diagnosis: the drift message does not name a compiler change: "The Evidence `Contract` anchor records sha256:aaaa…, but this task now compiles to sha256:d4bbc893… under keel-task-capsule/v1. The contract changed after the anchor was recorded, …"`, carrying the declared signature `does not name a compiler change`.
    - M1.green: pass. With `src/core/drift.js` (recording commit by `git log -S`, the commit's change/specs/config compiled by the running compiler with Git answered by the real repository, linked / compiler / unavailable as D3, fields diffed as D4), the versioned anchor in `--record`, the cause in `task-complete`, `change-close` and `keel context`, the compiler-only re-record warning, and the checked-task authorization warning at the close, the scenario passed.
    - M2: pass. `--scenario contract-anchor-is-compared`, `--scenario drift-names-where-to-look`, `--scenario a-staleness-report-names-its-exception`, and `--scenario evidence-survives-what-did-not-change` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 285 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0). The first run failed `core-gates` and `record-derives-skeleton`, which compared the recorded anchor line exactly and now expect `(keel {PACKAGE_VERSION})`, and `the-tarball-is-the-repository` until `src/core/drift.js` was added to the index.
    - Review:
      - Status: pass
      - Acceptance check: the scenario commits real gate output in a real repository and asks the real CLI: a compiler change is named with commit and both versions and its re-record keeps the evidence; an unexplained anchor gets no cause; a Touch edit is named as `touch` by `task-complete` and `keel context`; a checked task survives a `push:main` → `push-protected:main` edit at `change-close --action archive` with a warning while an unchecked one still drifts. On a local clone of rtl_ppa_prj at `aee9fa7d`, `change-close` on `fast-check-waivers`, `io-comb-loops`, and `handshake-depth-contracts` diagnosed all eight drifted tasks as standing-authorization-only, each naming its recording commit (e.g. `7859598bb89a`), matching the 2026-10-13 measurement.
      - Scope check: `git status --short` lists `README.md`, `scripts/validate_plugin.py`, `src/core/context.js`, `src/core/drift.js`, `src/core/gates.js`, `src/core/task-contract.js`, and this change's directory — all in Touch or the record layer.
      - Findings:
        - Discard reason: anchors recorded before this release carry no version, so a compiler-only drift on them (the 2026-10-03 `add-iecc-cbbs` case) still gets no cause; the version cannot be recovered from Git, and claiming one would be the unverifiable claim #342 is about.
        - Discard reason: an anchor recorded, then its contract edited before the commit, then compiled after a Keel upgrade, would be named a compiler change. The message states its basis (the commit and both versions), task-complete normally compares before that commit, and the re-record D5 still requires is a person's check.
        - Discard reason: a re-record that lands the same digest refreshes the version in the anchor line and reports `unchanged`; unchanged is true of the fingerprint, which is what the status describes.
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
    - openspec/specs/keel-core-gates/spec.md
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
    - M2: the ADDED requirement joins `keel-core-gates` and both MODIFIED ones replace their counterparts, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:32a85ca743f2f85613aba2f2264b760e7cd33302811d362ccad919c846a6c37a
    - M1: `node scripts/bump_version.js minor` moved every marker 5.139.0 → 5.140.0; with the "Contract drift names its cause" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the ADDED requirement joined `keel-core-gates` after the change-close requirement, and the three MODIFIED ones replaced their counterparts; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Keel MUST NOT name which checks are unaffected, because it retains only the previous fingerprint and cannot know." — `openspec/specs/keel-core-gates/spec.md`. Updated by: 2.1
- I2: "`change-close` MUST compare each checked task's recorded anchor against its recompiled fingerprint, and MUST fail on a difference." with no exception — `openspec/specs/keel-core-gates/spec.md`. Updated by: 2.1
- I7: "and MUST state that execution evidence produced under the previous contract is stale." with no exception for a compiler change — `openspec/specs/keel-core-gates/spec.md`. Updated by: 2.1
- I3: "**Keel does not verify the claim** — it keeps only the previous fingerprint, not the capsule behind it" — `README.md`. Updated by: 1.1
- I4: "Two hashes and nothing to search … only the previous fingerprint is retained, not the capsule behind it, so this names where to look and never what changed." — the `driftSearchSet` comment in `src/core/context.js`. Updated by: 1.1
- I5: "The gate keeps only the previous fingerprint and cannot know which checks are unaffected" — a failure message in `scripts/validate_plugin.py`; still true for the blanket report it guards, which this change leaves as it is. Discard reason: the sentence describes the no-diagnosis case, which remains.
- I6: "It names where to look and never what changed." and "Reconstructing one from Git would answer for the last commit" — `keel/CHANGELOG.md` 5.83-era entry. Discard reason: a changelog entry records what was true of its release; the new entry says what changed.

## Expectation Coverage

- E1: After a Keel upgrade or a standing-authorization edit, the author is told what moved a fingerprint, is not asked to vouch for a compiler change, and can archive a completed change without re-recording for an authorization change (#342, D3, D5, D6). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
