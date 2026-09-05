# Tasks

## 1. The summary agrees with the file under it

- [x] 1.1 `openspec/specs/keel-openspec-surface-overlay/spec.md` names the managed set in its `## Purpose` and in the requirement that states which actions carry an overlay, its per-target and install scenarios name the same set, and a new check reads `OPENSPEC_OVERLAY_ACTIONS` from `bin/keel.js` and fails when either of those two locations names a proper subset
  - Covers:
    - keel-openspec-surface-overlay / Keel overlays every action in the managed set
    - keel-openspec-surface-overlay / Every overlay summary names the managed action set / The capability's own Purpose names the managed set
    - keel-openspec-surface-overlay / Every overlay summary names the managed action set / The requirement that states the set names all of it
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
  - Read:
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/changes/the-spec-names-the-managed-set/design.md
  - Touch:
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-spec-names-the-managed-set` scenario in `scripts/validate_plugin.py` parses `OPENSPEC_OVERLAY_ACTIONS` out of `bin/keel.js` and asserts that the published spec's `## Purpose` line and the requirement stating which actions carry an overlay each name every action in it. It fails, naming the location, when a copy of the spec has either location reduced to a proper subset, and fails rather than passing when the requirement heading it looks for is absent. The three correct subset spellings named in F2 are asserted to remain accepted, so the check is the two locations and not a scan.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario openspec-surface-overlay` passes unchanged, so rewording the spec did not change what is installed.
    - M3 (regression): `node node_modules/.bin/openspec validate the-spec-names-the-managed-set --strict` passes and `published-specs-validate-strictly` passes, so the delta and the promoted store agree after this task's edit.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making the spec agree with the code requires changing `OPENSPEC_OVERLAY_ACTIONS`, any overlay content, or any installed file; this task reads the code and edits prose.
    - Stop if the check cannot distinguish the three correct subset spellings from the drifted ones without judgment, because a check that refuses correct statements costs more than the drift.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:937a36ff71fbe97610056fc576a8f557d399338097c6e814ae3a578bcd53dbdf
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-spec-names-the-managed-set` reports `the-spec-names-the-managed-set scenario passed.` It parses `OPENSPEC_OVERLAY_ACTIONS` out of `bin/keel.js` and finds all four actions named in both the `## Purpose` line and the requirement `Keel overlays every action in the managed set`. It then fails, as required, on a copy whose requirement heading is reverted to the old name — reporting that the location is missing rather than that an action is — and on four further copies, each with one action deleted from the Purpose line, reporting that action by name. The three correct subset spellings are asserted present and untouched: `apply/archive/sync overlay markers` and `it names sync alongside apply and archive` in the diagnostics spec, and `sync/archive decisions` in this one.
    - M1.red: fail, for the right reason. The check was written and registered before the spec was edited, and reported that `keel-openspec-surface-overlay has no ... Requirement: Keel overlays every action in the managed set heading, so this check found nothing to compare against the managed set` — the pre-change file states the set as two of four under the old heading.
    - M1.green: pass. Same command after the Purpose was corrected directly and the three `MODIFIED` requirements were promoted from this change's delta: `the-spec-names-the-managed-set scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario openspec-surface-overlay` reports `openspec-surface-overlay scenario passed.` unchanged, so rewording the specification did not change which files receive an overlay or what it contains.
    - M3: pass. `node node_modules/.bin/openspec validate the-spec-names-the-managed-set --strict` reports `Change 'the-spec-names-the-managed-set' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store this task promoted into.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 149 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 148 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the two locations name the managed set and that a check reads the set from the code and fails when either stops. M1 proves the first by comparison against `bin/keel.js` rather than against a literal, and proves the second by constructing five drifted copies and requiring each to be reported — including the copy where the requirement is simply gone, which is the case a check like this fails silently on if nobody asserts it. M2 is what makes the change a documentation correction rather than a behavior change: the surfaces the overlay is written to are unchanged.
      - Scope check: `git status --short` shows exactly the two Touch paths (`openspec/specs/keel-openspec-surface-overlay/spec.md`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. This task performs the delta promotion that a release task usually performs, as design.md D4 records: the check it adds reads the published file, so a task that fixed only the Purpose could not pass its own check — the split that `an-owner-outlives-the-change` had to merge one release earlier. `keel gate task-start` reports the fingerprint unchanged from the anchor recorded before implementation.
      - Findings: two. First, still open: the `## Invalidates` quoted-phrase check refuses a quotation that wraps across lines, because its pattern is `"[^"\n]{3,}"`. Five entries across this session's three changes were reported as `names where to look but not what to look for` when they named exactly that and had merely been wrapped, and shortening the quote to one line fixed each — a pure notation round trip, the cost issue #49 measured. The same file already reads Review `Findings` as wrapping across lines by design. Durable owner: https://github.com/TanglmChris/keel/issues/108. Second, repaired in this task: the check's first draft reported a missing requirement heading through the same message it uses for a subset, producing `the requirement or the Purpose line is absent of keel-openspec-surface-overlay does not name propose, apply, archive, sync` — one condition guarding two distinct failures, which `keel-review-checklist` names specifically. Split into two branches, so an absent location says the location is absent and says nothing about the action names, and the reverted-heading copy asserts that branch on its own. Resolved here: M1
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the overlay spec's summary names the managed set the code maintains
    - E2 — that agreement is checked against the code rather than reread
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
    - M2: `keel/CHANGELOG.md` carries an entry naming the 9 drifted statements, the 3 correct subset spellings the check must not refuse, and the structural reason the Purpose line survived issue #79 — that OpenSpec's delta operations are Requirement-scoped — closing issue #86
    - M3: `node node_modules/.bin/openspec validate the-spec-names-the-managed-set --strict` passes and `published-specs-validate-strictly` passes against the store task 1.1 promoted, so no delta is left unpromoted at the close
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:17a3fc2c4e15a18076ab68aeb811f34e16f14f9ea694476df39b103a5eddff1d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.43.0 to 5.44.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.44.0 - the spec names the managed set`, naming the 9 drifted statements and where they are, the 3 correct subset spellings the check must not refuse and why each is correct, and the structural reason the Purpose line survived issue #79 — OpenSpec's delta operations are Requirement-scoped, so no change could have carried that edit. It records that no production code changed and that the managed set stays derived from `bin/keel.js`, and closes issue #86.
    - M3: pass. `node node_modules/.bin/openspec validate the-spec-names-the-managed-set --strict` reports `Change 'the-spec-names-the-managed-set' is valid` and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0`. Task 1.1 performed the promotion, as design.md D4 records, so this check confirms nothing is left unpromoted rather than performing it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 149 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — no failing scenario, no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts through the two tools that consume the published store rather than by reading files back, and its meaning differs from the previous two releases: promotion happened in 1.1, so what M3 proves here is that the close leaves no delta unpromoted. M2 is the one prose check, and what it asserts is what a diff would not show — that the entry names the three correct-looking statements this change deliberately did not touch, so the next reader does not repair them.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `openspec/specs/keel-openspec-surface-overlay/spec.md` from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer. This task's Touch deliberately omits the published spec, which 1.1 owns end to end.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Define Keel's managed overlay for OpenSpec-generated apply/archive target surfaces" — the `## Purpose`
  line of `openspec/specs/keel-openspec-surface-overlay/spec.md`. It names two of the four actions the
  overlay covers, and no OpenSpec delta operation reaches a Purpose line, so nothing was going to correct
  it. Updated by: 1.1
- I2: "Keel overlays apply and archive surfaces" — the opening requirement's name in that same file, with
  its body "a managed overlay on OpenSpec-generated apply/archive skills and command entries" and its three
  scenario names "Claude apply and archive surfaces receive the overlay", "Codex apply and archive surfaces
  receive the overlay", and "OpenCode apply and archive surfaces receive the overlay". Updated by: 1.1
- I3: "an apply/archive/sync OpenSpec file with an outdated Keel overlay block" — the install-refresh
  scenario in that file, together with "before OpenSpec has generated apply/archive/sync files" and "does
  not create placeholder OpenSpec apply/archive/sync files" in the scenario below it. Install and refresh
  cover the `propose` surface too, so these three name three of four. Updated by: 1.1
- I4: "it names sync alongside apply and archive" — a scenario in
  `openspec/specs/keel-target-surface-diagnostics/spec.md`, closing a sentence about the label being
  derived from the managed action list. Discard reason: this
  one is correct and stays. It describes `overlayActionLabel()`, which excludes the authoring action on
  purpose, and the reworded requirement in this change now says so explicitly rather than leaving the
  exclusion to be inferred.

## Expectation Coverage

- E1: The overlay spec's `## Purpose` and the requirement stating which actions carry an overlay name every action in `OPENSPEC_OVERLAY_ACTIONS`, and so do the per-target and install scenarios under them. Covered by: 1.1, 2.1
- E2: A verification check reads the managed set from `bin/keel.js` and fails, naming the location, when either of those two locations names a proper subset — and fails rather than passing when it cannot find the requirement at all. Covered by: 1.1, 2.1
- E3: The three published statements that name a proper subset correctly — the doctor's command-surface label, the archive requirement's `sync/archive decisions`, and the `authoring/apply/archive/sync` spelling — keep passing. Covered by: 1.1
- E4: Every other capability's Purpose is checked the same way. Discard reason: the invariant is specific to this capability, whose subject is the managed set; there is no general rule that a Purpose enumerates a code constant, and inventing one would refuse correct prose elsewhere.
