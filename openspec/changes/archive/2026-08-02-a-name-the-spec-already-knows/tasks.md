# Tasks

## 1. Say which segment failed

- [x] 1.1 Name what the spec holds instead, and stop teaching the shape that fails
  - Covers:
    - keel-task-capsule / An unresolved reference into an existing capability names what failed / A Scenario offered as a Requirement is named as one
    - keel-task-capsule / An unresolved reference into an existing capability names what failed / A name the spec does not declare is reported as read
    - keel-task-capsule / An unresolved reference into an existing capability names what failed / A capability with no spec is distinguished from a name that is absent
    - keel-task-capsule / An unresolved reference into an existing capability names what failed / A Scenario declared under more than one Requirement offers no correction
    - keel-task-capsule / An unresolved reference into an existing capability names what failed / What resolves is unchanged
    - D1 — the terminal return branches on what the candidate specs hold
    - D2 — the Scenario case spells the corrected reference
    - D3 — an ambiguous Scenario name offers no correction
    - D4 — the diagnostic code is unchanged and every case still fails
    - D5 — verification runs through the gate, not through the function
    - D6 — a resolvable reference and the refusal verdict are both asserted
    - F1 — the five reproduced references and what each returns today
    - F2 — the terminal return, and the hierarchy sentence it cannot reach
    - F3 — both candidate specs were tried before the terminal return
    - F4 — the heading parses the new diagnostic needs already exist
    - F5 — the two shipped requirements this one completes
    - A1 — a Scenario outside any Requirement degrades to the generic case
    - A2 — no consumer parses the text of this message
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/templates/tasks.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario unresolved-covers-names-what-failed` passes. The scenario builds repositories holding a spec whose Requirement and Scenario names are known, drives `keel gate task-start`, and asserts through the gate: a two-segment reference whose second segment names a Scenario reports the Requirement that Scenario sits under and the corrected three-segment reference; a name the spec declares nowhere reports that the spec was read and states the hierarchy; a capability with no spec reports that instead; a Scenario appearing under two Requirements names both and offers no single correction; every one of those still returns `fail` with code `unresolved-covers`; and a reference that resolves still compiles to the same authority, source, and Acceptance with no added diagnostic.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario covers-separator-collision` still passes, so the sibling diagnostic this one is modelled on, and its assertion that a non-colliding capability receives no separator hint, are unchanged.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` still passes, so scenario provenance, critical statements, duplication, and the missing-scenario refusal are unchanged.
    - M4 (regression): `npm test` passes with no failing scenario and no exception, which is also where both tasks-template copies are checked for their required snippets.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if naming what the spec holds requires changing which references resolve.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3f4665da41f0f065126a6e17a14964901425cd107f08b7e699decca522b3c9e3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unresolved-covers-names-what-failed` reports `unresolved-covers-names-what-failed scenario passed.` Ten assertions driven through `keel gate task-start` on real repositories: the reported reference is still refused, still carries code `unresolved-covers`, names the Requirement its Scenario belongs to, and spells the corrected reference; a name the spec declares nowhere is still refused and reports the spec as read with the hierarchy; a capability with no spec is still refused and reported as having none; a Scenario name under two Requirements is still refused, names both, and offers no correction; and a reference that resolves still compiles to one `requirement` authority with the same source.
    - M1.red: fail, as required, before any change to `src/core/task-contract.js`. The scenario reported `unresolved-covers-names-what-failed: the diagnostic did not name the Requirement the Scenario belongs to, or did not spell the corrected reference.` beside the gate's actual output, `Covers reference could not be resolved: demo-cap / A published store passes the pinned validator.` — the whole message, produced through the gate rather than quoted from #49, and identical in shape to the reporter's.
    - M1.green: pass. All ten assertions hold. The reported reference now returns ``Covers reference could not be resolved: demo-cap / A published store passes the pinned validator. "A published store passes the pinned validator" is a Scenario of Requirement "The store validates itself", not a Requirement; the hierarchy is capability / requirement, or capability / requirement / scenario. Write it as: demo-cap / The store validates itself / A published store passes the pinned validator.`` The assertion that matters most is the last one: reading more of the spec on the failure path is the only direction in which a refusal could have become a resolution, and a reference that resolves still compiles to the same authority, source, and Acceptance with no problems reported.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario covers-separator-collision` reports `covers-separator-collision scenario passed.` The separator hint still reaches only the capability that has a colliding name, and the over-segmented message is byte-identical — its hierarchy clause is now the shared constant the new branches read, not a second phrasing.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` reports `expectation-slice-gates scenario passed.` Scenario provenance, critical statements, `Covers` deduplication, the missing-scenario refusal, the duplicated-scenario refusal, and the unauthorized-question refusal are unchanged.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 130 scenarios.` — no failing scenario, no exception, none skipped; 129 before this task. Both tasks-template copies pass their required-snippet checks after the wording change. The first run of this check failed on `assertion-shape-count`, which measured 78 or-guarded assertion sites against 75 recorded and named the three lines: the new scenario had three conditions each mixing the refusal verdict with a message-content test behind one report. Split so the verdict carries its own message, per that check's own instruction; it now reports `75 sites`, the recorded bound, rather than being raised.
    - Review:
      - Status: pass
      - Acceptance check: every assertion runs through `keel gate task-start` on a real repository rather than against `specAuthority()` directly. That is D5, and it is the point — #49's recorded cost is what an author reads at the gate, and the red half reproduced that exact message from the unfixed tree before the implementation existed.
      - Scope check: `git status --short` lists exactly `assets/openspec/schemas/keel-spec-driven/templates/tasks.md`, `openspec/schemas/keel-spec-driven/templates/tasks.md`, `scripts/validate_plugin.py`, and `src/core/task-contract.js` — the four Touch entries — plus this change's own untracked directory, which is the record-write layer. No path outside Touch. Every edit went through the file tools the write guard can see; nothing was written by shell redirection.
      - Findings: one. The shipped compact task template taught the reference shape that fails: its `Covers` line offered ``capability / requirement or scenario heading``, a two-segment form whose second segment may be a scenario heading, which `specAuthority()` has never accepted. That is the cause of what #49 reports as a diagnostics defect, and it was found while reproducing rather than named in the issue. Both copies of the template now state the two accepted forms and that a scenario is named in the third segment. Resolved here: assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [x] 2.1 Release 5.21.0
  - Covers:
    - E6 — a reader of the release notes learns which message changed, and that what resolves did not
    - I1, I2, I3 — the wordings this change makes stale
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
    - openspec/specs/keel-task-capsule/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.21.0
    - M2: `keel/CHANGELOG.md` carries a 5.21.0 entry naming the reference shape that now explains itself, stating that what resolves is unchanged, and recording that the design.md critical-statement shape is deliberately untouched and where that decision is left
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-name-the-spec-already-knows --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bb0108fd19b1cebaea5405ac5204e7461aefa3ab985ed35a51f8d7ace00bc812
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Twenty-two markers moved from 5.20.0 to 5.21.0 via `node scripts/bump_version.js 5.21.0` — the package and lockfile, both plugin manifests, the three `keel:start` blocks, the twelve `keel:openspec-surface-overlay` markers, the AGENTS.md title and preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.21.0 - a name the spec already knows`, quoting the reported reference and the sentence it now produces, naming the template wording that taught the failing shape, and stating plainly that what resolves is unchanged and that every case still fails with the same code. It records the design.md critical-statement shape as deliberately not done, with the four-shape measurement, the reason both directions are user-visible, and where the decision is left.
    - M3: pass. The delta is promoted — `An unresolved reference into an existing capability names what failed` and its five scenarios now sit in `openspec/specs/keel-task-capsule/spec.md` immediately after `Over-segmented capability reference does not degrade silently`, the requirement it completes. `node bin/keel.js openspec validate a-name-the-spec-already-knows --strict` reports `Change 'a-name-the-spec-already-knows' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 130 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: each release claim is checked by running the thing it describes rather than by reading it — the marker count by `version-alignment`, the promotion by `openspec validate --strict` and then by `published-specs-validate-strictly` against the store that now holds the new requirement.
      - Scope check: `git status --short` lists 2.1's Touch entries plus this change's own `tasks.md`, which is the record-write layer. No path outside Touch. The version markers were written by `scripts/bump_version.js`, the repository's own release tool; a script's writes are invisible to the PreToolUse guard, so every file it touches was declared in Touch beforehand and the resulting worktree was compared against that list here rather than assumed.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "capability / requirement or scenario heading" — the `Covers` line of the shipped compact task template, in both copies: `assets/openspec/schemas/keel-spec-driven/templates/tasks.md:20` and `openspec/schemas/keel-spec-driven/templates/tasks.md:20`. Read today it offers a two-segment reference whose second segment may be a scenario heading, which is the exact reference this change's diagnostic exists to explain, and which `specAuthority()` has never accepted. Updated by: 1.1
- I2: "A capability with no collision keeps the plain wording." — the comment at `scripts/validate_plugin.py:5127`, above the `plain` case of `covers-separator-collision`. After this change that reference receives the new wording naming what the spec holds; the assertion beneath it stays true because it only checks that no separator hint appears, but the comment describes a message that no longer exists. Updated by: 1.1
- I3: "version=5.20.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.20.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: An author who writes the reference the template taught learns which segment failed, without reading `specAuthority()`. Covered by: 1.1
- E2: When the spec holds the name one level down, the diagnostic says where and spells the correction. Covered by: 1.1
- E3: What resolves is unchanged, and every newly-explained case still fails. Covered by: 1.1
- E4: The template stops teaching a reference shape the parser has never accepted. Covered by: 1.1
- E5: Whether `criticalAuthority()` should accept the design.md shapes this repository writes stays with the owner. Durable owner: https://github.com/TanglmChris/keel/issues/49
- E6: A reader of the release notes learns which message changed and that what resolves did not. Covered by: 2.1
