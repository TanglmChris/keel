# Tasks

## 1. Give the between-task approval a durable home

- [x] 1.1 `continuation` joins `STANDING_AUTHORIZATION_ACTIONS` as the fifth name — declared, it reports authorized and inherits into capsules naming `keel/config.yaml` as source; undeclared, it reports not authorized; and the declaration stays inert to every gate result and to selection
  - Covers:
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary
    - keel-standing-authorization / A continuation authorization covers one approved between-task boundary
    - D1
    - D3
    - D6
    - F1
    - F2
  - Read:
    - src/core/config.js
    - scripts/validate_plugin.py
    - openspec/changes/authorize-continuation-between-tasks/design.md
  - Touch:
    - src/core/config.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `continuation-authorization` scenario in `scripts/validate_plugin.py` runs the real CLI: a repo declaring `authorize:` listing only `continuation` gets `keel --doctor` reporting `continuation: authorized` and each of `commit`, `push`, `release`, `archive` as `not authorized`; a gate fixture task authoring no `Autonomy boundary:` in that repo compiles a capsule whose autonomy names the inherited `continuation` with `keel/config.yaml` as its source while undeclared actions keep the hard-stop default; and against an otherwise identical silent repo, `task-start` and `task-complete` gate results and `keel context` status and next action are equal, with a positive control proving the declaration actually reached the capsule before asserting it inert.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` passes with `continuation: not authorized` added to the commit+push fixture's undeclared needles and the unknown-entry error naming all five accepted names through the extended tuple.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-never-weakens` passes with its all-declared fixture extended to the five names.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if authorizing `continuation` requires any production edit beyond the one constant in `src/core/config.js` — a second edit means a consumer does not read the constant and D1's basis is wrong.
    - Stop if the inertness comparison finds any gate result or selection changed by the declaration.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:43621629573c85515a9fe24886ff11aa1c1b01440bd1a0e827f87dbfe4cd782a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-authorization` reports `continuation-authorization scenario passed.` — a continuation-only declaration gets `continuation: authorized` with all four repository actions `not authorized`; the four-name fixture reports `continuation: not authorized`; the boundary-less fixture task compiles a capsule whose autonomy carries the inherited `continuation` naming `keel/config.yaml` as source with `Default: hard-stop` kept for undeclared actions; and against the identical silent repo, `task-start`/`task-complete` gate results and `keel context` status/selection/next action are equal, with the capsule check as the positive control.
    - M1.red: fail, for the right reason. Scenario added to `scripts/validate_plugin.py` before touching `src/core/config.js`: `continuation-authorization: a continuation-only declaration was refused.` — the unmodified constant reports `unrecognized action: continuation; accepted names are commit, push, release, archive` and the doctor exits non-zero.
    - M1.green: pass. Same command after `continuation` joined `STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js` — the only production edit: `continuation-authorization scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` reports `standing-authorization-declaration scenario passed.` with `continuation: not authorized` added to the commit+push fixture's undeclared needles and the unknown-entry (`deploy`) error checked against all five accepted names through the extended tuple.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-never-weakens` reports `standing-authorization-never-weakens scenario passed.` with its all-declared fixture extended to the five names.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 146 scenarios.` (up from 145; the one new scenario this task added is the only change, no other scenario affected.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declared `continuation` reports authorized and inherits into capsules naming `keel/config.yaml` as its source, an undeclared one reports not authorized, and the declaration stays inert to every gate result and to selection — proven by M1 through the real CLI against declared, undeclared, inheriting, and paired inert fixtures, with M1.red/M1.green showing the unmodified vocabulary refused the word and the one-constant edit accepts it. Neither Stop Rule fired: the only production edit is the constant in `src/core/config.js`, and the inertness comparisons found no gate result or selection changed.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/config.js`, `scripts/validate_plugin.py`) plus this change's own directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Every text an agent reads at the between-task boundary names the standing `continuation` authorization and its exact bounds — the goal skill's stop rule (both copies), `README.md`'s standing-authorization section, `keel/config.yaml`'s comment vocabulary, and `AGENTS.md`'s `## Execution boundary` section
  - Covers:
    - keel-single-task-goal-execution / Goal execution stops at the selected task boundary
    - keel-standing-authorization / A continuation authorization covers one approved between-task boundary
    - D2
    - D4
    - D5
    - F1
  - Read:
    - src/skills/keel-run-single-task-goal/SKILL.md
    - README.md
    - keel/config.yaml
    - AGENTS.md
    - openspec/changes/authorize-continuation-between-tasks/design.md
  - Touch:
    - src/skills/keel-run-single-task-goal/SKILL.md
    - plugins/keel/skills/keel-run-single-task-goal/SKILL.md
    - README.md
    - keel/config.yaml
    - AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: a new `continuation-docs` scenario in `scripts/validate_plugin.py` asserts through the shipped files: step 7 of `plugins/keel/skills/keel-run-single-task-goal/SKILL.md` names a standing `continuation` authorization as the durable form of the user instruction it requires, keeping the stop and the new-start-fingerprint requirement; the `src/skills/` and `plugins/keel/skills/` copies are byte-identical; `README.md`'s standing-authorization section lists all five accepted names and states that `continuation` covers only the next unchecked task of an owner-approved change and removes no gate, evidence, or Review; `keel/config.yaml`'s comment names the five-name vocabulary; and `AGENTS.md`'s `## Execution boundary` section names `continuation` with the same bounds.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-goal-claude` and `--scenario native-goal-codex` pass — both read the shipped skill text this task edits.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if stating the semantics requires changing any lifecycle step other than step 7's continuation clause.
    - Stop if any check would need this repository's own `authorize:` list to gain a `continuation` entry — declaring it here is a separate owner decision this change does not make.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dd16fbdc3f93ee064b565e4d578cd9a6f0dc5f2138c485de8e00e78930793128
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-docs` reports `continuation-docs scenario passed.` — the two skill copies are byte-identical; step 7 still opens `7. Stop.` and names the standing `continuation` authorization in `keel/config.yaml` as the durable form of the instruction, the next unchecked task of the same change, its own recorded fingerprint, and no hidden scheduler; `README.md` carries the five-name accepted-names line, the between-task bounds, and `The five names above are the whole vocabulary.`; `keel/config.yaml`'s comment names the five-name vocabulary; `AGENTS.md`'s `## Execution boundary` section names the same bounds.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-goal-claude` and `--scenario native-goal-codex` both report passed — the shipped skill text this task edited still carries the fallback guidance both scenarios read.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 147 scenarios.` (up from 146; the one new scenario this task added is the only change, no other scenario affected.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that every text an agent reads at the between-task boundary names the standing `continuation` authorization and its exact bounds — proven by M1 reading the shipped files themselves: the stop rule keeps the stop and the new-fingerprint requirement while naming the durable form, the README and config comment teach the five-name vocabulary and what the fifth covers, and the resident protocol carries the same bounds for the agent enforcing the boundary. Neither Stop Rule fired: no lifecycle step other than step 7 changed, and this repository's own `authorize:` list still declares four names.
      - Scope check: `git status --short` shows exactly this task's six Touch paths plus `src/core/config.js` and `scripts/validate_plugin.py`'s scenario addition from task 1.1, already declared complete and dirty before this task started, plus this change's own directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a repository can durably authorize between-task continuation, inert to every proof
    - E2 — every text an agent reads at the between-task boundary names the authorization and its bounds
    - I3 — the published closed-set wording this task updates
    - I4 — the published stop-boundary wording this task updates
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
    - openspec/specs/keel-standing-authorization/spec.md
    - openspec/specs/keel-single-task-goal-execution/spec.md
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
    - M2: `keel/CHANGELOG.md` carries an entry naming the `continuation` vocabulary word and its exact bounds, closing issue #94
    - M3: both spec deltas are promoted into `openspec/specs/`, `node node_modules/.bin/openspec validate authorize-continuation-between-tasks --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9184f08639e62903eebdc09de7c14f165f99c4b3b293a92db00b74d515ef52d9
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.40.0 to 5.41.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.41.0 - authorize continuation between tasks`, naming the fifth vocabulary word, its exact bounds (one between-task boundary of an owner-approved change, every gate and proof unchanged, no repository action rides along, fail-closed on an older Keel), the one-constant production edit, the four text surfaces, and the C-class settlement row issue #94 found missing from issue #34 — closing issue #94.
    - M3: pass. Both deltas are promoted — `openspec/specs/keel-standing-authorization/spec.md` carries the five-name closed set and the new `A continuation authorization covers one approved between-task boundary` requirement, and `openspec/specs/keel-single-task-goal-execution/spec.md` carries the stop-boundary requirement naming the standing form with its new scenario. `node node_modules/.bin/openspec validate authorize-continuation-between-tasks --strict` reports `Change 'authorize-continuation-between-tasks' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the promoted store.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 147 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the files back. M2 is the one prose check, and what it asserts is what a diff alone would not show: the release gives an owner-approved between-task continuation a durable, fail-closed home because the owner decided the conversational grant was the wrong channel, and it names the issue #34 settlement the word closes.
      - Scope check: `git status --short` shows exactly the Touch entries this task wrote — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, both promoted spec files, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus the writes of tasks 1.1 and 1.2 (`src/core/config.js`, `README.md`, `keel/config.yaml`, both goal-skill copies, `scripts/validate_plugin.py`'s scenarios), already declared complete and dirty before this task started, plus this change's own untracked directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "accepted names: commit, push, release, archive" — `README.md`'s `authorize:` example comment,
  and "The accepted names are the whole vocabulary — commit, push, release, archive" —
  `keel/config.yaml`'s comment; both enumerate a four-name vocabulary that is now five. Updated by: 1.2
- I2: "Continuing to another task requires a new explicit user instruction" — step 7 of
  `src/skills/keel-run-single-task-goal/SKILL.md` and its byte-identical `plugins/keel/skills/`
  copy; a standing `continuation` authorization is now a durable form of that instruction.
  Updated by: 1.2
- I3: "The accepted action names MUST be a closed set — `commit`, `push`, `release`, `archive`" —
  the published `openspec/specs/keel-standing-authorization/spec.md`. Updated by: 2.1
- I4: "MUST require new explicit user authorization before projecting or starting another task" —
  the published `openspec/specs/keel-single-task-goal-execution/spec.md` stop-boundary requirement,
  which does not name the standing form. Updated by: 2.1
- I5: `("commit", "push", "release", "archive")` — the `STANDING_AUTHORIZATION_ACTIONS` tuple
  `scripts/validate_plugin.py` mirrors from `src/core/config.js`. Updated by: 1.1
- I6: issue #34's closing settlement table lists L0–L3 and no C-class row — the row this decision
  settles ("C 类＝任务边界停顿") lives on GitHub, not in this tree. Durable owner:
  https://github.com/TanglmChris/keel/issues/34

## Expectation Coverage

- E1: A repository can durably authorize between-task continuation with the same nature as the four existing names — git-tracked, diffable, revocable, and inert to every proof. Covered by: 1.1, 2.1
- E2: Every text an agent reads at the between-task boundary names the standing authorization and its exact bounds. Covered by: 1.2, 2.1
