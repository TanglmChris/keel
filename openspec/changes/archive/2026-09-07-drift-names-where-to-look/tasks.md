# Tasks

## 1. What the hard stop says

- [x] 1.1 The fingerprint drift report names the distinct authority sources the capsule resolved text from and states that Evidence, Review, and the checkbox are not covered, while both fingerprints and the blocking behavior stay exactly as they are
  - Covers:
    - keel-stateless-continuity / A reported drift names where the covered authority was read from
    - D1
    - D2
    - D3
    - A1
    - F1
    - F2
    - F3
  - Read:
    - src/core/context.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/drift-names-where-to-look/design.md
  - Touch:
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `drift-names-where-to-look` scenario in `scripts/validate_plugin.py` drives `keel context --json` through the real CLI against a fixture repository. A task whose recorded anchor no longer matches reports `blocked`, and the reason names `openspec/changes/<change>/tasks.md` and the `design.md` a `Covers` entry was resolved from — asserted by citing a `D<n>` so the capsule holds two distinct sources, and by asserting a source the capsule did *not* resolve from is absent, so the list is the authority set and not a directory listing. The reason states that Evidence, Review, and the checkbox are not covered, and it names no field as the one that changed. Both fingerprints still appear.
    - M2 (regression): drift still blocks. The same fixture reports `blocked` with the drift reason and no `next action` that would let work continue, and a task whose anchor matches still reports `ready` with the unchanged reason text, so the report grew only on the path that was failing.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario anchor-reverification-bound` passes unchanged, so when drift is detected is untouched.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if naming the sources requires retaining the previous capsule, because D3 records that only its digest is kept and a message that names a field it inferred is worse than one that names a search set.
    - Stop if the source list cannot be built without reading Git, because D4 records that a diagnostic depending on whether work was committed answers for a different moment than the one that drifted.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dbb560a4c644a8fca501644b6e6a99f17ecf5b16fde47883f22c00d6253507a3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario drift-names-where-to-look` reports `drift-names-where-to-look scenario passed.` Against a fixture whose `Covers` cites both `E1` and a `D1` in `design.md`, `keel context --json` reports `blocked` and the reason reads: `… The fingerprint covers text resolved from: openspec/changes/demo/design.md, openspec/changes/demo/tasks.md. Evidence, Review, and the task checkbox are not covered — editing them does not move it. Reauthorize by re-running \`keel gate task-start\` and recording the new anchor, after confirming the change to the authority above was intended.` Both fingerprints still appear. `proposal.md` is asserted absent, so the list is the authority set rather than the change directory. The reason is asserted not to claim which field moved.
    - M1.red: fail, for the right reason. Before `driftSearchSet()` existed the scenario reported `the drift reason does not name the authority source 'openspec/changes/demo/tasks.md'` and printed the whole message — two hashes and a full stop, which is the message that produced a wrong record in this repository.
    - M1.green: pass. Same command after the drift reason gained the resolved authority sources and the sentence naming what is outside the fingerprint.
    - M2: pass. Asserted in the same scenario: the drifted fixture reports `blocked` with `Next action: none`, and a fixture whose recorded anchor equals the compiled value reports `ready` with no fingerprint wording in its reasons at all — the message grew only on the path that was already failing.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario anchor-reverification-bound` reports `anchor-reverification-bound scenario passed.` When drift is detected is untouched; only what the report says changed.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 160 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 159 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a drift names its authority sources, says what it does not cover, and claims no culprit. M1 proves all three, and the two negative assertions carry the weight: `proposal.md` absent is what makes the list an authority set rather than a directory listing, and the no-culprit assertion is what keeps D3 honest — the previous capsule is not retained, so a message naming a field would be inventing one. M2 proves the hard stop is still a hard stop, from both sides, because a diagnostic change that quietly let work continue would be far worse than the message it replaced.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/context.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from task-start. Nothing about what the fingerprint covers, when drift is detected, or what it blocks was touched.
      - Findings: one, still open, and it is the limit this change accepts rather than solves. The report names *where* the covered authority lives and cannot name *what* moved, because only the previous fingerprint is retained and not the capsule behind it. In the case that motivated this change the search set would have been two files, one of which the author had been writing Evidence into all session — so the message narrows the search without ending it. Retaining enough of the previous capsule to answer precisely is a real option with a real cost, and it is a different decision than this one. Durable owner: https://github.com/TanglmChris/keel/issues/115
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a drift hands the author the files whose text it covers
    - E2 — a drift says what it does not cover
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
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - M2: `keel/CHANGELOG.md` carries an entry stating that a two-hash message produced a wrong record in this repository, what the corrected mechanism is, and that the fix names a search set rather than guessing a field
    - M3: the spec delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`, `node node_modules/.bin/openspec validate drift-names-where-to-look --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4af701b56ed0e5ec7007ad59354666f7c1a1eb4f195a829523cf4c33991fb027
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.51.0 to 5.52.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.52.0 - drift names where to look`. It states what the old message was, that it produced a wrong record in this repository and what the measured mechanism actually is, that the search set was already free in the compiled authority entries, and that the report names where to look and never what changed — with the reason, which is that only the previous fingerprint is retained. It also records that the correction to the archived note was appended rather than rewritten.
    - M3: pass. The delta is promoted — `openspec/specs/keel-stateless-continuity/spec.md` carries `A reported drift names where the covered authority was read from` with its three scenarios. `node node_modules/.bin/openspec validate drift-names-where-to-look --strict` reports `Change 'drift-names-where-to-look' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 160 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M3 asserts the promotion through both tools that consume the published store. M2 is the one prose check, and what it has to carry is the part a diff cannot show: the change is a few sentences of message text, so an entry describing the text would leave a reader unable to recognize why it mattered. The entry is therefore about the wrong record the old message produced, which is the evidence that a hard stop with nothing to search is not a cosmetic problem.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-stateless-continuity/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/context.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory. `AGENTS.md` needed no wording change: the resident protocol says drift hard-stops until reauthorization and says nothing about what the report contains.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Task contract fingerprint drift for" — the drift reason built in `src/core/context.js` and every
  scenario asserting its text. The sentence keeps that opening and gains the authority sources and the
  statement of what is not covered, so a reader searching the old wording finds a longer message.
  Updated by: 1.1
- I2: "an edit inside the Review, which the compiled capsule covers, so the anchor moved" — the
  Reauthorizations note in
  `openspec/changes/archive/2026-09-05-quoted-text-is-not-a-claim/tasks.md`. It is the wrong cause, and
  it is the reason this change exists.
  Discard reason: already corrected in place on 2026-09-07 by an appended note that states the measured
  mechanism and points at issue #115. Archived evidence is corrected by appending rather than rewriting,
  so the wrong sentence stays visible beside its correction and this change adds nothing to it.

## Expectation Coverage

- E1: A reported drift names each distinct authority source the capsule resolved text from, and no source it did not. Covered by: 1.1, 2.1
- E2: A reported drift states that Evidence, Review, and the checkbox are not covered, and names no field as the one that moved. Covered by: 1.1, 2.1
- E3: Drift still blocks, is still detected at the same moment, and a matching anchor still reports ready unchanged. Covered by: 1.1
- E4: Naming the exact statement that moved. Discard reason: D3 records that the previous capsule is not retained, so it cannot be computed, and https://github.com/TanglmChris/keel/issues/115 owns the question of whether retaining enough to answer it is worth its cost.
