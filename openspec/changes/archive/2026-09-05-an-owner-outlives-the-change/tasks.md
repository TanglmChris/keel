# Tasks

## 1. An owner that survives the archive

- [x] 1.1 `durableOwnerVerdict()` and `resolutionEvidenceVerdict()` refuse a repo-relative path inside the selected change's own directory, with a reason of their own that says the directory moves when the change is archived; a path inside a different live change directory stays accepted; the refusal reaches Review `Findings`, `## Invalidates`, and `## Expectation Coverage` alike; and `DURABLE_OWNER_FORMS`, the sentence all three quote, states what each accepted form is worth
  - Covers:
    - keel-expectation-slice-evidence-gates / A durable owner may be any file the repository keeps, and a refusal names what it accepts
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/an-owner-outlives-the-change/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `an-owner-outlives-the-change` scenario in `scripts/validate_plugin.py` drives the real CLI against a fixture repository. Four refusals with the self-pointer `openspec/changes/demo/design.md`, the file present: closing an `## Invalidates` entry at `task-start`, closing an `## Expectation Coverage` entry at `change-close`, owning a Review finding at `task-complete`, and standing as `Resolved here:` evidence — each refusal naming the archive move rather than a spelling problem. Six acceptances with the identical shapes: the same four with the path moved to a different live change directory that exists, plus an archived path and a tracker reference owning a finding. And three refusals that list the forms — the `## Invalidates`, `## Expectation Coverage`, and `Findings` closures — each saying a path is checked for existence when it is cited and that a gate never fetches a tracker reference.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` passes with its `openspec/changes/demo/proposal.md` accepted-form fixture moved off the selected change's own directory, so the existing owner forms — an existing path, a missing path, `keel/HANDOFF.md`, an archived path, and a tracker reference — keep their verdicts.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the selected change's name cannot reach the verdict without re-deriving it from the path being judged, because a path judged against itself cannot distinguish a self-pointer from a pointer at another change.
    - Stop if refusing the self-pointer requires changing what `declaredPath()` extracts.
    - Stop if the three refusals do not in fact share one constant, because then the change is about making them share it and that is a different task.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:25b4909a0f052e53d9f5117b68fb71436f68a51e272aca430a6373818b2eba14
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-owner-outlives-the-change` reports `an-owner-outlives-the-change scenario passed.` All four self-pointer fixtures are refused and every refusal names the archive move: `## Invalidates` at `task-start`, `## Expectation Coverage` at `change-close`, a Review finding at `task-complete`, and a `Resolved here:` claim. All six acceptances pass with the identical shapes pointed at `openspec/changes/other/design.md`, plus `keel/archive/notes/2026-09-05-example.md` and a tracker reference. All three form-listing refusals say `checked for existence when it is cited` and `never fetches`.
    - M1.red: fail, for the right reason. The scenario was written and registered before `src/core/gates.js` was touched, and reported `an-owner-outlives-the-change: a path inside the selected change's own directory closed an Invalidates entry.` — the pre-change gate accepted the pointer that archiving is about to break.
    - M1.green: pass. Same command after `insideOwnChangeDirectory()` and the `transient` verdict reached all three consumers and `DURABLE_OWNER_FORMS` gained what each form is worth: `an-owner-outlives-the-change scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` reports `durable-owner-vocabulary scenario passed.` with its change-artifact fixture moved from `openspec/changes/demo/proposal.md` to `openspec/changes/other-change/proposal.md`. Every other verdict is unchanged: `openspec/FOLLOWUP.md` accepted, `openspec/NOT-THERE.md` refused as missing, `keel/HANDOFF.md` refused as a pointer override, and the archived path and tracker reference accepted.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a self-pointer is refused in all four places an owner or resolution path is read, that a path into a different live change stays accepted, and that every form-listing refusal says what the forms are worth. M1 proves all three through the real CLI — `keel gate task-start`, `task-complete`, and `change-close` against a fixture repository — and asserts the refusal *text*, not just the verdict, because a refusal that reported a spelling problem would leave the author with no repair. The acceptance half is what stops this from being a blanket ban: the same four shapes pass unchanged against `openspec/changes/other/design.md`.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-start` reports the fingerprint unchanged from the anchor recorded before implementation. Two pre-existing scenarios asserted the removed behavior and were repaired rather than deleted, as `## Invalidates` I5 and I6 declared; each keeps the assertion it existed for and changes only the path it demonstrates with.
      - Findings: one, resolved here. This slice was authored as two tasks — the refusal, then the accepted-forms wording — and `keel gate task-start` warned that both declared the same Touch under a red-green strategy. The warning was right: the refusal has to name what to write instead, so it quotes `DURABLE_OWNER_FORMS`, and the first task's own scenario could not pass until the second task's wording existed. That is the tell the review checklist names — one behavior split in half, with no honest red left for the second. Implementation stopped and returned to authoring: the two were merged into this task, and the proposal and design.md D4 were corrected to say the wording is part of the same slice rather than a second one. Resolved here: M1, which now asserts refusal and wording together in one scenario that passes as a whole.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded three times before implementation, all authoring corrections: naming `durable-owner-vocabulary` as the registry spells it (M2 had cited `expectation-slice-gates`, which holds no owner fixture), correcting I5 from a discard to a real `Updated by:` after verifying that scenario does assert the removed behavior, and the merge recorded in Findings. `sha256:7dc33adc37…` → `sha256:63044f7812…` → `sha256:25b4909a0f…`. I6 was added after the final anchor and did not move it, because `## Invalidates` is change-level and outside the task capsule. Every check above was run under the final contract.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a pointer into the change's own directory is refused before it can become a dead link
    - E2 — every refusal says what the accepted forms are worth
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
    - M2: `keel/CHANGELOG.md` carries an entry naming the self-pointer refusal with the 10-of-10 corpus measurement, the cross-change path that stays accepted and why, and the boundary the accepted-forms sentence now states, closing issue #100
    - M3: the spec delta is promoted into `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`, `node node_modules/.bin/openspec validate an-owner-outlives-the-change --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:28e23b45f4068edb869bb98bca48c7dd1f303d309c2797466157b15f0b4296e2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.42.0 to 5.43.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.43.0 - an owner outlives the change`, naming the self-pointer refusal with the 10-of-10 corpus measurement beside the field report's 35-of-36, the cross-change path that stays accepted and why refusing it would have been an invented defect, the boundary the accepted-forms sentence now states together with why the tracker branch is still unchecked, and the archived pointers this change deliberately does not rewrite. It closes issue #100.
    - M3: pass. The delta is promoted — `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` carries the reworded `A durable owner may be any file the repository keeps, and a refusal names what it accepts` requirement with its three new scenarios. `node node_modules/.bin/openspec validate an-owner-outlives-the-change --strict` reports `Change 'an-owner-outlives-the-change' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the promoted store.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 148 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 147 by the one scenario this change added, no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store rather than by reading the files back. M2 is the one prose check, and what it asserts is what a diff would not show: this release makes a gate stricter, so the entry has to say which declarations stop passing, which deliberately keep passing, and — for the half of the issue this change does not fix — why the tracker branch stays unchecked rather than leaving a reader to assume it was overlooked.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/gates.js` from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: one, resolved here. `AGENTS.md`'s Project Conventions section offered "an `openspec/changes/…` artifact" as a durable-owner form without distinguishing the archived path, which survives, from the live one this change now refuses — `## Invalidates` I4. It sits outside the Keel managed block, so `bump_version.js` does not rewrite it and the stale sentence would have survived the release that made it wrong. Repaired in this task: the form now reads `openspec/changes/archive/…`, states that a path inside the change's own directory is refused even though it exists, and states that a different live change is still accepted. Resolved here: `./AGENTS.md`, whose Project Conventions text is both the file the finding names and the file the repair edits. A second finding, still open: that path has to be written `./AGENTS.md` rather than `AGENTS.md`, because `declaredPath()` requires a path separator and every repo-root file — `AGENTS.md`, `CLAUDE.md`, `README.md`, `package.json` — therefore has none. The refusal reads `it names neither a check nor a path` for a path whose file exists, which sends the reader to check the form rather than the file, and the `./` that gets past it is a notation concession rather than a repair. Durable owner: https://github.com/TanglmChris/keel/issues/107 — filed with the reproduction, the `#60` history that fixed one half of path extraction and fixed this shape in place, and a bound on the fix so `Durable owner: pending` stays refused as unrecognized rather than reported as a missing file.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes once for the whole change with `node_modules/.bin` on `PATH`, reporting no failing scenario and no exception, with the new scenario registered and every pre-existing scenario green.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 148 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` Run once for the whole change with `node_modules/.bin` on `PATH`, after task 2.1's promotion: no failing scenario, no exception, `an-owner-outlives-the-change` registered and green, and every pre-existing scenario green including the two this change repaired.

## Invalidates

- I1: "existence is necessary, not sufficient" followed by a single named exception — the third paragraph of
  the "A durable owner may be any file the repository keeps, and a refusal names what it accepts"
  requirement in `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` names `keel/HANDOFF.md` as
  the only path that exists and is still refused. There are now two. Updated by: 2.1
- I2: "an absolute `https://…` tracker reference, or any repo-relative path that exists" — the
  `DURABLE_OWNER_FORMS` constant in `src/core/gates.js` and every refusal that quotes it, which lists the
  forms without saying what checking each one is worth. Updated by: 1.1
- I3: "a path is the one form it can actually check" — the comment above `durableOwnerVerdict()` in
  `src/core/gates.js`, in a sentence contrasting the unverifiable URL with the checkable path. The clause
  stops being unconditional: for a path inside the change's own directory the check expires one workflow
  step later. Updated by: 1.1
- I4: "an `openspec/changes/…` artifact" — the Project Conventions section of `AGENTS.md`, listing owner
  forms. It offers a change artifact as an owner without distinguishing the archived path, which survives,
  from a path in the live directory this change is about to move. Updated by: 2.1
- I6: "openspec/changes/demo/tasks.md" as `owner_path` — the `review-entry-extent` scenario in
  `scripts/validate_plugin.py`, which asserts that a wrapped Review finding's declared owner is accepted.
  The assertion is about how far a wrapped entry extends and stays right; the path it demonstrates with is
  the selected change's own directory, which this change refuses. Updated by: 1.1
- I5: "Durable owner: openspec/changes/demo/proposal.md" — an accepted-form fixture in the
  `durable-owner-vocabulary` scenario in `scripts/validate_plugin.py`, asserted to close an `## Invalidates`
  entry. `demo` is that fixture's own selected change, so it is exactly the self-pointer this change
  refuses. Updated by: 1.1

## Expectation Coverage

- E1: A `Durable owner:` or `Resolved here:` naming a path inside the selected change's own directory is refused at the gate that reads it, in all three consumers, and a path inside a different live change directory is still accepted. Covered by: 1.1, 2.1
- E2: Every refusal that lists the accepted owner forms says what checking each one is worth — a path checked at citation and not afterwards, a tracker reference never fetched. Covered by: 1.1, 2.1
- E3: Archived pointers already written are not rewritten and not retroactively refused. Discard reason: archived evidence is a record of what was written, and the gates refuse an archived change rather than recompiling one (F3), so there is nothing to implement; `keel --doctor` reporting them is issue #100's direction 2 and a separate change.
