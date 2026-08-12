# Tasks

## Invalidates

- None.

## 1. Change-level Verify/Evidence and deferred regression Evidence

- [x] 1.1 A `(regression)`-tagged `M<n>` check may defer its bare Evidence to a change-level `C<n>` check declared in `## Change Verify`/`## Change Evidence`, resolved structurally at `task-complete` and for completeness at `change-close`
  - Covers:
    - keel-core-gates / A change declares checks that run once for the whole change / A regression check defers to a change-level check
    - keel-core-gates / A change declares checks that run once for the whole change / Only a regression-tagged check may defer
    - keel-core-gates / A change declares checks that run once for the whole change / A deferred check must resolve
    - keel-core-gates / A change declares checks that run once for the whole change / Deferral without a Change Verify section is refused
    - keel-core-gates / A change declares checks that run once for the whole change / A change with no deferred check needs neither section
    - keel-core-gates / A change declares checks that run once for the whole change / Change Verify labels are contiguous and concrete
    - keel-core-gates / A change declares checks that run once for the whole change / A declared change-level check needs its own evidence even when unreferenced
    - D1 — parse `## Change Verify`/`## Change Evidence` the same way `## Invalidates`/`## Expectation Coverage` already are, reusing the existing `sectionBody()` boundary
    - D2 — the sections are required only once some task's Evidence references a `C<n>`, not unconditionally
    - D3 — only a `(regression)`-tagged check may defer; read the tag from the already-compiled contract
    - D4 — two-phase resolution: `task-complete` checks the reference resolves, `change-close` checks it is answered
    - D5 — five diagnostic codes, each naming exactly one missing piece
    - D6 — `deferred to C<n>` is matched at the front of the bare Evidence value, not scanned for anywhere in it
    - F1 — reproduced: `completionChecks()` validates a `(regression)`-tagged check's bare Evidence with nothing but `isConcrete()`, so `deferred to C7` already passes today whether or not `C7` exists
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-regression-the-change-owns/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - AGENTS.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `change-verify-deferred-evidence` scenario in `scripts/validate_plugin.py` runs `keel gate task-complete`/`keel gate change-close` through the real CLI and covers, in one fixture family: (a) a `(regression)`-tagged check deferring to a declared `C1` passes `task-complete` with no `C1` result yet required; (b) an untagged check deferring to `C1` fails `task-complete` with `deferred-evidence-not-regression`; (c) a `(regression)`-tagged check deferring to an undeclared `C9` fails with `deferred-check-unresolved`; (d) `change-close` fails with `change-verify-missing` when a task defers but `## Change Verify` is absent; (e) `change-close` fails with `change-evidence-missing` when `C1` is declared but `## Change Evidence` has no concrete entry for it; (f) `change-close` passes once `## Change Evidence` carries concrete evidence for every declared `C<n>`; (g) a change where no task defers reports nothing about either section whether present or absent; (h) non-contiguous or duplicated `C<n>` labels fail `change-close` with `change-verify-shape`.
    - M2 (regression): the existing `regression-check-tag` scenario still passes unchanged — the `(regression)` tag's own compiled-capsule and fingerprint behavior is untouched.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Coupling: none
  - Candidate Boundary:
    - Not applicable; Coupling is none.
  - Stop Rules:
    - Stop if satisfying M1 requires changing `src/core/task-contract.js`'s compiled capsule or fingerprint shape.
    - Stop if it requires letting a non-`(regression)` check defer, or requiring `## Change Verify`/`## Change Evidence` from a change that never defers.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0ecf800ebcc0158919dadc543eba014f29dedebd20025cb9498ea1ec86134453
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario change-verify-deferred-evidence` reports `change-verify-deferred-evidence scenario passed.` — all eight sub-checks (a-h) behave as required through the real CLI: a regression check deferring to a declared `C1` passes `task-complete`; an untagged check deferring fails with `deferred-evidence-not-regression`; deferring to an undeclared `C9` fails with `deferred-check-unresolved`; the same code fires at `change-close` when `## Change Verify` is entirely absent; a declared-but-unanswered `C1` fails `change-close` with `change-evidence-missing`; a fully resolved deferral passes `change-close`; a change nothing defers in reports nothing about either section, present or absent; non-contiguous `C<n>` labels fail with `change-verify-shape`.
    - M1.red: fail, for the right reason. New scenario added to `scripts/validate_plugin.py` before touching `gates.js`: `change-verify-deferred-evidence let an untagged check defer to a change-level check.` — the unmodified `completionChecks()` has no concept of the deferral at all, so an untagged check's `deferred to C1` passed as ordinary concrete Evidence.
    - M1.green: pass. Same command after `completionChecks()`, `changeVerifyChecks()`, `changeEvidenceValue()`, and `changeVerifyProblems()` were added to `src/core/gates.js` and wired into `taskComplete()`/`changeClose()`: `change-verify-deferred-evidence scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario regression-check-tag` reports `regression-check-tag scenario passed.` — the `(regression)` tag's own compiled-capsule and fingerprint behavior is unchanged.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 143 scenarios.` (up from 142; the one new scenario this task added is the only change). One unrelated pre-existing self-check, `assertion-shape-count`, required raising its recorded `OR_GUARDED_ASSERTION_SITES` constant from 75 to 80 for five new sites in the new scenario that repeat an already-accepted idiom (`regression-check-tag`'s own site is one of the original 75); justified inline at the constant's declaration.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a `(regression)`-tagged check may defer its bare Evidence to a change-level `C<n>` check, resolved structurally at `task-complete` and for completeness at `change-close`, with no effect on a change nothing defers in — proven by M1 through the real CLI across all eight cases, M1.red/M1.green showing the new scenario fails against the unmodified gate for the stated reason and passes after the fix, and M2 showing the pre-existing `(regression)` tag mechanics are untouched.
      - Scope check: `git status --short` shows exactly the three Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`, `AGENTS.md`) plus this change's own untracked directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.
  - Report:
    - Summary

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a `(regression)`-tagged `M<n>` check may defer its bare Evidence to a change-level `C<n>` check, resolved structurally at `task-complete` and for completeness at `change-close`, with no effect on a change that never defers
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming this feature and closing issue #95
    - M3: the spec delta is promoted into `openspec/specs/`, `node node_modules/.bin/openspec validate a-regression-the-change-owns --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Coupling: none
  - Candidate Boundary:
    - Not applicable; Coupling is none.
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ddcc53e184556706e5c0e61fc2985ec6a52cfee81f5c9e3b04f630751db4fbb7
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.38.0 to 5.39.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.39.0 - a regression the change owns`, naming the new `deferred to C<n>` disposition and the `## Change Verify`/`## Change Evidence` sections, closing issue #95, and noting no change to the compiled task capsule.
    - M3: pass. The delta is promoted — the new Requirement `A change declares checks that run once for the whole change` and its seven Scenarios now sit in `openspec/specs/keel-core-gates/spec.md` beside the pre-existing Requirements, unmodified. `node node_modules/.bin/openspec validate a-regression-the-change-owns --strict` reports `Change 'a-regression-the-change-owns' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 143 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: this release closes issue #95 by giving a `(regression)`-tagged check a change-level check to defer to, not by touching anything else.
      - Scope check: `git status --short` shows exactly the Touch entries this task wrote — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, `openspec/specs/keel-core-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/gates.js` and `scripts/validate_plugin.py`'s scenario addition from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.
  - Report:
    - Summary

## Expectation Coverage

- E1: A `(regression)`-tagged `M<n>` check may defer its bare Evidence to a change-level `C<n>` check declared
  in `## Change Verify`, resolved structurally at `task-complete` and for completeness at `change-close`, with
  no effect on a change no task defers in. Covered by: 1.1, 2.1
