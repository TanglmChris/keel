# Tasks

## 1. Distinguish missing from unparsed critical statements

- [x] 1.1 `criticalAuthority()`'s zero-match branch reports `Unparsed` (naming the required line shape) when the referenced `D<n>`/`F<n>`/`A<n>`/`Q<n>` identifier is textually present in `design.md` but not in the exact resolvable shape, and keeps `Missing` only when the identifier is textually absent
  - Covers:
    - keel-expectation-slice-evidence-gates / Unresolved critical-statement Covers references distinguish missing from unparsed
    - D1 — add a whole-word loose check inside the existing zero-match branch; state the required shape in the new message
    - D2 — do not widen accepted shapes or touch the scenario-matching branch (`specAuthority`)
    - F1 — `Missing Covers critical statement: D2.` reproduces today for a present-but-mis-shaped `D2` line
  - Read:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/unparsed-is-not-missing/design.md
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `unparsed-covers-critical-statement` scenario in `scripts/validate_plugin.py` runs `keel gate task-start` through the real CLI against two fixtures — one where `design.md` has no `D2` line at all (still reports `Missing Covers critical statement: D2.`), one where `design.md` has `- **D2** — Keep one shared parser.` (present, wrong shape; must report `Unparsed Covers critical statement: D2.` and name the required `D2 — one-line statement` shape) — and a third fixture where `design.md` has a correctly-shaped `D2 — Keep one shared parser.` line, which must still resolve as authority.
    - M2 (regression): the existing `expectation-slice-gates` scenario still passes unchanged — correctly-shaped D1/A1 resolution, ambiguous-covers duplication, and missing-scenario rejection are unaffected.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if satisfying M1 requires widening what shape `criticalAuthority()` accepts as resolved authority — the owner's proposal was diagnostic wording only, not a parser change.
    - Stop if it requires touching `specAuthority()` or any diagnostic outside `criticalAuthority()`'s zero-match branch.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ef8198b981e1f105df91a909f5b45fa2ef87685d4ee9b41ab5c208aeffc33eed
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unparsed-covers-critical-statement` reports `unparsed-covers-critical-statement scenario passed.` — all three fixtures (absent, present-but-mis-shaped, correctly-shaped) behave as required through the real CLI.
    - M1.red: fail, for the right reason. New scenario added to `scripts/validate_plugin.py` before touching `task-contract.js`: `unparsed-covers-critical-statement: a present-but-mis-shaped D2 must report Unparsed, got: 'Missing Covers critical statement: D2.'` — the unmodified `criticalAuthority()` collapses the present-but-mis-shaped case into `Missing`.
    - M1.green: pass. Same command after `criticalAuthority()`'s zero-match branch gained the whole-word loose check: `unparsed-covers-critical-statement scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` reports `expectation-slice-gates scenario passed.` — correctly-shaped D1/A1 resolution, ambiguous-covers duplication, and missing-scenario rejection are unaffected.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 142 scenarios.` (up from 141; the one new scenario this task added is the only change, no other scenario affected.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a present-but-mis-shaped critical-statement identifier is reported as Unparsed naming the required shape, while a genuinely absent one still reports Missing and a correctly-shaped one still resolves — proven by M1 through the real CLI against all three fixtures, M1.red/M1.green showing the new scenario fails against the unmodified code for the stated reason and passes after the fix, and M2 showing the pre-existing critical-statement/duplicate/scenario resolution paths are unaffected.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/task-contract.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a Covers reference to a present-but-mis-shaped critical statement is reported as `Unparsed`, naming the required shape, instead of `Missing`
    - I1 — the version markers this task moves
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
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming this diagnostic fix and closing issue #49 item 1
    - M3: the spec delta is promoted into `openspec/specs/`, `node node_modules/.bin/openspec validate unparsed-is-not-missing --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c640fdb45f93be63182b703d26e37484edebf9ce1b38ed000e61850e785f041e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.37.0 to 5.38.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.38.0 - unparsed is not missing`, naming the diagnostic fix (closes issue #49 item 1), the exact reproduction and the new message shape, and noting issue #49's other two sub-issues were confirmed already fixed and are untouched by this release.
    - M3: pass. The delta is promoted — the new Requirement `Unresolved critical-statement Covers references distinguish missing from unparsed` and its three Scenarios now sit in `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` beside the eighteen pre-existing Requirements, unmodified. `node node_modules/.bin/openspec validate unparsed-is-not-missing --strict` reports `Change 'unparsed-is-not-missing' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 142 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: this release fixes the Missing/Unparsed conflation for critical-statement Covers references and explicitly leaves #49's other two sub-issues out because they were already fixed, not because they were ignored.
      - Scope check: `git status --short` shows exactly the Touch entries this task wrote — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/task-contract.js` and `scripts/validate_plugin.py`'s scenario addition from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Missing Covers critical statement: D2." as the universal zero-match message for critical-statement
  Covers references — openspec/changes/unparsed-is-not-missing/design.md's Context section quotes it as
  today's behavior, and issue #49's description of the same defect. Updated by: 1.1

## Expectation Coverage

- E1: A Covers reference to a present-but-mis-shaped critical statement is reported as `Unparsed`, naming
  the required shape, instead of `Missing`. Covered by: 1.1, 2.1
