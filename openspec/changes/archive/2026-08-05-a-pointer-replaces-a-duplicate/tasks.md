# Tasks

## 1. Point the skill at the protocol instead of repeating it

- [x] 1.1 Replace the skill's duplicated Unattended-runs prose with a pointer; update the two
      validators that pinned the duplicate
  - Covers:
    - keel-unattended-triage / A repository declares which work may start without asking / A secondary surface points instead of repeating
    - keel-unattended-triage / An unattended run may open a pull request and may not merge / A secondary surface points instead of repeating
    - keel-unattended-triage / An unattended run may open a pull request and may not merge / The boundary is stated where a run can read it
    - D1 — the section heading stays; only the body changes
    - D2 — "states no separate copy" is the shared pointer phrase both validators check for
    - D3 — both validators keep requiring the full phrase sets against AGENTS.md unchanged
    - D4 — no change to keel-skill-sourcing-and-portability's "one portable authority" requirement
    - D5 — the pointer relies on the AGENTS.md bootstrap Keel already guarantees and diagnoses
    - F1 — the skill's section is the fuller restatement (1,581 vs. 1,457 characters), not a summary
    - F2 — exactly two validator functions read content from this section
    - F3 — `keel --doctor` already diagnoses a missing/broken AGENTS.md bootstrap independent of this skill
  - Read:
    - src/skills/keel-align-expectations/SKILL.md
    - plugins/keel/skills/keel-align-expectations/SKILL.md
    - AGENTS.md
    - scripts/validate_plugin.py
    - openspec/changes/a-pointer-replaces-a-duplicate/design.md
    - openspec/changes/a-pointer-replaces-a-duplicate/proposal.md
  - Touch:
    - src/skills/keel-align-expectations/SKILL.md
    - plugins/keel/skills/keel-align-expectations/SKILL.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario unattended-boundary` and `--scenario triage-admits-from-the-repository` both pass, proving the updated validators accept the pointer in the skill files while still holding `AGENTS.md` to the full phrase sets.
    - M2: the two skill files each contain the pointer phrase `states no separate copy` exactly once, are byte-identical to each other, and no longer contain the five boundary phrases or the sentence `Work enters an unattended run only by the repository's declared triage policy`; `AGENTS.md` is byte-identical to its pre-task content.
    - M3 (regression): `npm test` passes with no failing scenario and reports the same 138-scenario count (no scenario added or removed).
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making this work requires changing `AGENTS.md`'s own `## Unattended runs` content — that surface is the pointer's target and is out of scope.
    - Stop if the canonical and plugin-distributed skill copies cannot stay byte-identical after the edit.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a84874b900391390773d76aeb816f865230b0910c65e95d6491acb029e179477
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unattended-boundary` reports `unattended-boundary scenario passed.`; `--scenario triage-admits-from-the-repository` reports `triage-admits-from-the-repository scenario passed.`
    - M2: pass. `grep -c "states no separate copy"` reports 1 for both `src/skills/keel-align-expectations/SKILL.md` and `plugins/keel/skills/keel-align-expectations/SKILL.md`; `diff` between the two reports no difference; `grep -c "Work enters an unattended run only by the repository's declared triage policy"` reports 0 for both; `grep -c "open a pull request"` against the canonical skill reports 0; `git diff --stat -- AGENTS.md` reports no change, and `grep -c` for the four boundary phrases against `AGENTS.md` reports 4 (one each), unchanged from before this task.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — the same count as the pre-task baseline, no failing scenario.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the skill's duplicated section becomes a pointer while `AGENTS.md` and the byte-identical canonical/distributed invariant are unchanged. M1 proves the two updated validators pass under the new content, not just that the file changed. M2 proves both directions directly — the old duplicated sentence and phrase are gone from the skill, the new pointer phrase is present exactly once in each copy, the copies stay byte-identical, and `AGENTS.md` itself is untouched (`git diff --stat` empty) rather than merely "probably fine". M3 proves no other scenario in the suite depended on the removed text.
      - Scope check: `git status --short` shows exactly this task's Touch — `plugins/keel/skills/keel-align-expectations/SKILL.md`, `scripts/validate_plugin.py`, `src/skills/keel-align-expectations/SKILL.md` — plus this change's own untracked directory (the record-write layer) and `keel/guard.json`, which the guard itself manages. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start, so no contract edit occurred. No file outside Touch or the change's own directory appears in `git status`.
      - Findings: none
    - Blocker: none

## 2. Close

- [x] 2.1 Sync, archive, and release 5.32.0
  - Covers:
    - E1 — a reader of the skill learns the unattended-run boundary is defined once, in `AGENTS.md`, and where to find it
    - E2 — a reader of the release notes learns what was measured, what changed, and why the two validators were relaxed only for the skill copies
    - I1 — the skill's duplicated Unattended-runs prose this task promotes past
  - Read:
    - keel/CHANGELOG.md
    - openspec/changes/a-pointer-replaces-a-duplicate/specs/keel-unattended-triage/spec.md
  - Touch:
    - openspec/specs/keel-unattended-triage/spec.md
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
  - Verify:
    - Strategy: evidence-first
    - M1: after the two new scenarios are agent-applied into `openspec/specs/keel-unattended-triage/spec.md`, `node bin/keel.js openspec validate a-pointer-replaces-a-duplicate --strict` passes (pre-archive).
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.32.0.
    - M3: `keel/CHANGELOG.md` carries a 5.32.0 entry naming the duplication measurement, the pointer replacement, and the two validators updated.
    - M4: `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes against the promoted store.
    - M5 (regression): `npm test` passes with no failing scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
    - Stop if sync produces a published-spec diff beyond the two new scenarios.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:766a399b654b17cbe1a2fe848dda2d86e8c6782e217a6e0faaa7e541dc54d226
    - M1: pass. After hand-applying the two `MODIFIED Requirements` scenarios into `openspec/specs/keel-unattended-triage/spec.md`, `node bin/keel.js openspec validate a-pointer-replaces-a-duplicate --strict` reports `Change 'a-pointer-replaces-a-duplicate' is valid`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` after `node scripts/bump_version.js 5.32.0` moved every marker: package/lockfile, both plugin manifests, `AGENTS.md`/`CLAUDE.md`/`assets/bootstrap/AGENTS.md`, the four `opsx/*.md` overlay markers, the eight `.claude/skills/openspec-*` and `.codex/skills/openspec-*` overlay markers, and `PACKAGE_VERSION`/`PROTOCOL_VERSION` in `scripts/validate_plugin.py`.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.32.0 - a pointer replaces a duplicate`, naming the 1,581-vs-1,457-character measurement, the pointer replacement (8,364 to 7,152 characters, byte-identical copies), and the two validator functions updated with what they now require of each surface.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` reports `published-specs-validate-strictly scenario passed: 21 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, none added or removed.
    - Review:
      - Status: pass
      - Acceptance check: M1 is the scenario that reads the promoted store directly rather than trusting the hand-edit by eye, confirming both new scenarios resolve against the published capability with every pre-existing scenario intact (the delta tool refuses a MODIFIED block that drops an existing scenario, so this also proves none were accidentally reworded away). M2 and M4 assert the release through the two tools that consume it (`version-alignment` and `published-specs-validate-strictly`), not by reading files back. M3 is the one prose check, asserting what a diff alone would not tell a reader: why the duplication mattered and what changed as a result.
      - Scope check: `git status --short` shows exactly the union of this task's Touch and task 1.1's Touch (the release step legitimately rewrites files task 1.1 already declared, e.g. `scripts/validate_plugin.py`'s version markers) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one re-recorded at this task's task-start (after Touch was corrected to include the eight `.claude/skills/openspec-*`/`.codex/skills/openspec-*` markers `bump_version.js` also writes), so no further contract edit occurred since. No file outside Touch or the change's own directory appears in `git status`.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "Work enters an unattended run only by the repository's declared triage policy" — the opening
  sentence of the `## Unattended runs` section body in `src/skills/keel-align-expectations/SKILL.md`
  and `plugins/keel/skills/keel-align-expectations/SKILL.md`. Updated by: 1.1

## Expectation Coverage

- E1: A reader of `src/skills/keel-align-expectations/SKILL.md` learns the unattended-run boundary
  (admission, what it authorizes, the open-PR/no-merge line) is defined once, in `AGENTS.md`'s own
  `## Unattended runs` section, and is pointed there rather than reading a second, independently
  maintained copy. Covered by: 1.1
- E2: A reader of the release notes learns the duplication measurement (1,581 vs. 1,457
  characters), that the section was replaced with a pointer, and that
  `validate_unattended_boundary_scenario` and `validate_triage_admits_from_the_repository_scenario`
  were updated to check the skill files for the pointer instead of the full phrase sets, while
  `AGENTS.md` keeps the full requirement unchanged. Covered by: 2.1
