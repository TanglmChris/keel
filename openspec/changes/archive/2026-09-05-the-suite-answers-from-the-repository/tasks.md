# Tasks

## 1. The suite answers from the repository

- [x] 1.1 `run_openspec()` resolves `node_modules/.bin/openspec` before `PATH`, and `compact-task-authoring` splits its two failures so an unresolvable CLI reports the skip contract while naming where it looked, and a CLI that ran and refused fails with what it said
  - Covers:
    - keel-validation-runner / The full run is parallel, deterministic, and fail-loud
    - D1
    - D2
    - D3
    - F1
    - F2
  - Read:
    - scripts/validate_plugin.py
    - package.json
    - openspec/changes/the-suite-answers-from-the-repository/design.md
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-declared-dependency-is-resolved` scenario in `scripts/validate_plugin.py` asserts the behavior rather than the constant: with `PATH` emptied of any `openspec`, `run_openspec(ROOT, "--version")` still returns a completed process whose output names a version, because the package's own `node_modules/.bin/openspec` is found; and with both that path and `PATH` unavailable it returns `None` rather than raising. The scenario also asserts that `compact-task-authoring`'s unresolvable branch and its refusal branch carry different messages, and that the unresolvable branch returns the skip code `3`.
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --all` passes with `PATH` carrying no `openspec`, which is the reproduction from issue #105 — before this task it reports `validation --all failed for: compact-task-authoring`.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario compact-task-authoring` passes, so resolving the CLI differently did not change what that scenario verifies.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if resolving the local dependency requires changing how scenarios invoke `run_openspec`, rather than what it resolves.
    - Stop if the skip path cannot name the locations it searched, because a skip nobody can explain is worse than the failure it replaces.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cb75aa7f10d083db85fbdc8891d993a8040517512320907dced46099e9643ff4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-declared-dependency-is-resolved` reports `a-declared-dependency-is-resolved scenario passed.` It builds a PATH with every directory holding an `openspec` executable removed — and asserts it actually built one — then calls `run_openspec(ROOT, "--version", env=...)` and requires a completed process reporting a version. It then asserts `compact-task-authoring`'s branch says the tool `could not be found`, names where it `searched`, returns the skip code `3`, and no longer carries `if which is None or which.returncode`.
    - M1.red: fail, for the right reason, and only after a false pass was removed. The first draft emptied `PATH` outright and got `exit=127` — the openspec shim needs `node`, so it was asserting that a shell with no interpreter fails. Narrowed to removing only the directories that hold an `openspec`, it then *passed* wrongly, because `run_openspec` resolved through the scenario process's own PATH rather than the env it was about to run under. With resolution following the env, the honest red arrived: `with no openspec on PATH the runner resolved nothing, but this package declares it as a dependency and installs it at node_modules/.bin`.
    - M1.green: pass. Same command after `resolve_openspec()` was added, trying the package's own `node_modules/.bin/openspec` before `PATH`, and after `compact-task-authoring`'s condition was split: `a-declared-dependency-is-resolved scenario passed.`
    - M2: pass. With `PATH=/usr/bin:/bin:$HOME/.nvm/versions/node/v24.20.0/bin` — `which openspec` reports nothing — `node scripts/run_python.js scripts/validate_plugin.py --all` reports `validation --all passed: baseline plus 152 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` This is issue #105's reproduction exactly; against 5.45.0 the same command reports `validation --all failed for: compact-task-authoring`.
    - M2.red: fail, for the right reason, observed directly at 5.45.0 rather than inferred. `scripts/validate_plugin.py` was reverted to `HEAD` and the same command run on the same PATH: `validation --all failed for: authored-scenario-names-are-registered, compact-task-authoring`, and the scenario alone printed `compact-task-authoring could not resolve the schema through OpenSpec.` — while `node_modules/.bin/openspec schema which keel-spec-driven --json` resolves that schema with `"source": "project"`. The second failing name is an artifact of reverting one file while this change's `tasks.md` names scenarios that file no longer holds; it is the registry check doing its job and is not part of the reproduction.
    - M2.green: pass. Working copy restored, same command, same PATH: `validation --all passed: baseline plus 152 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.`
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario compact-task-authoring` reports `compact-task-authoring scenario passed.` run with no openspec on `PATH`, so it verifies the same schema resolution it always did and now reaches it.
    - M4: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a checkout which installed its dependencies runs these scenarios, and that a probe which cannot find its CLI reports that distinctly. M2 is the proof of the first and is the issue's own command rather than a proxy for it — the suite run end to end on a PATH with no openspec. M1 is the proof of the second, and it asserts the emitted branch text rather than the constant, because what the issue is about is what the reader is told. The false pass recorded in M1.red is the part worth keeping: a scenario that resolves through the developer's own PATH would have passed on this machine and failed on CI, which is the failure mode this change exists to remove.
      - Scope check: `git status --short` shows exactly the one Touch path (`scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `## Invalidates` I2 declared the two skip messages naming `PATH` as the only place looked, in the `openspec-surface` and `spec-template-validates` scenarios; both now name the search order, which is a message change with no verdict change.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `package.json`'s `files` gains negated entries that keep build residue out of the published package — written there because a root ignore file is not consulted once `files` is declared — and a new check asserts every file `npm pack` would ship is tracked by Git
  - Covers:
    - keel-release-artifact / The published package is determined by the repository, not by the machine
    - D4
    - D5
    - F3
    - F4
  - Read:
    - package.json
    - .gitignore
    - scripts/validate_plugin.py
    - openspec/changes/the-suite-answers-from-the-repository/design.md
  - Touch:
    - package.json
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-tarball-is-the-repository` scenario in `scripts/validate_plugin.py` runs `npm pack --dry-run --json` in the repository root and asserts every path it reports is tracked by Git, naming any that is not. It creates `scripts/__pycache__/` residue first, so the assertion runs against the state that reproduces issue #110, and removes only what it created.
    - M2: `npm pack --dry-run --json` reports the same file count with and without `scripts/__pycache__/` present — 41 either way, where before this task it is 41 and 42, and where a root `.npmignore` carrying the same patterns still reports 42.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the exclusion would remove a file the package needs; the packed set must not shrink below the clean-checkout set of 41.
    - Stop if the check cannot name an untracked file it found, because the repair belongs to the packaging rules and not to the check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a1d429339a2bf3ff581b40c3237042260cb293a5cf83b4dcfa86f99a90032cd2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-tarball-is-the-repository` reports `the-tarball-is-the-repository scenario passed: 41 packed files, all tracked.` The scenario creates `scripts/__pycache__/keel-pack-probe.pyc` before it asserts anything, so it runs against the state that reproduces the issue rather than one that happens to be clean, then runs `npm pack --dry-run --json` and checks every reported path against `git ls-files -z`. It removes only what it created, in a `finally`, and it refuses an empty file list so a pack that reported nothing cannot pass as "nothing untracked".
    - M1.red: fail, for the right reason. The scenario was written and registered before `package.json` was touched, and reported `the-tarball-is-the-repository: 1 packed file(s) are not tracked by Git, so what ships depends on the machine that packs it rather than on the repository: scripts/__pycache__/keel-pack-probe.pyc`.
    - M1.green: pass. Same command after `files` gained `!**/__pycache__` and `!**/*.pyc`.
    - M2: pass. `npm pack --dry-run --json` reports `41` on a clean tree and `41` with `scripts/__pycache__/probe.pyc` present. Before this task the same pair is 41 and 42, and with a root `.npmignore` carrying `__pycache__/` and `*.pyc` it is still 41 and 42 — F4's measurement, which is why the exclusion is in `files`.
    - M2.red: fail, for the right reason. Before `files` was touched, `npm pack --dry-run --json` reported `41` on a clean tree and `42` with `scripts/__pycache__/probe.pyc` present — the extra file being that residue, which is the whole of issue #110. The same measurement with a root `.npmignore` carrying `__pycache__/` and `*.pyc` in place also reported `42`, which is how the arrangement the issue proposed was found not to run.
    - M2.green: pass. After `files` gained `!**/__pycache__` and `!**/*.pyc`: `41` on a clean tree and `41` with the same residue present.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the packed set is a function of the repository. M1 asserts that directly — every packed path tracked by Git — rather than comparing against a recomputed expected list, which would have to reimplement npm's inclusion order and would drift from it. It also reproduces the defect before asserting, so a machine that happens to be clean cannot make it pass. M2 is the count from the issue, measured on both trees.
      - Scope check: `git status --short` shows exactly the two Touch paths (`package.json`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. The `.npmignore` created while testing F4's three arrangements was removed before this task's contract was re-recorded; `git status` confirms no such file remains.
      - Findings: one, resolved here. The task was authored to add an `.npmignore`, following issue #110's own suggested repair, and design.md D4 argued for it over narrowing `files`. Measured false: with a `files` array declared, a **root** `.npmignore` is not consulted for an included directory at all — it packs 42, the unfixed count — so the arrangement that reads as correct does nothing. A `.npmignore` inside `scripts/` works but guards only that directory. Implementation stopped and returned to authoring: F4 records all three measurements, D4 now decides for negated `files` entries and says why, and the proposal, the new capability's requirement, this task's title, Touch, M2, and Stop Rule, and `## Invalidates` I4 were all corrected. Resolved here: M2, which measures the arrangement that was rejected alongside the one that shipped.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded twice, both before implementation and both authoring corrections rather than scope: once when `.gitignore` was added to Read alongside `package.json`, and once for the F4 correction recorded in Findings, which moved Touch from `.npmignore` to `package.json`. `sha256:4c8927c251…` → `sha256:42e3e33dc5…` → `sha256:a1d429339a…`. Every check above was run under the final contract.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the suite resolves its own declared dependency and says so when it cannot
    - E2 — the packed file set is decided by the repository
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
    - openspec/specs/keel-validation-runner/spec.md
    - openspec/specs/keel-release-artifact/spec.md
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
    - M2: `keel/CHANGELOG.md` carries an entry naming the PATH reproduction from a clean checkout, the two failures that shared one message, and the 41-versus-43 packing measurement, closing issues #105 and #110
    - M3: both spec artifacts are promoted — the modified `keel-validation-runner` requirement and the new `keel-release-artifact` capability — `node node_modules/.bin/openspec validate the-suite-answers-from-the-repository --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0c55c8c605f601099ff63b0ea303243c2cc8d3b9cf48890268e9cfdfabe94163
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.45.0 to 5.46.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`. The `files` negations task 1.2 added to `package.json` survive the bump.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.46.0 - the suite answers from the repository`, naming the clean-checkout reproduction and its verification with no `openspec` on `PATH`, the two failures that shared one message and why `assertion-shape-count` could not have caught that one, and the 41-versus-42 packing measurement. It states plainly that issue #110's own suggested repair was measured and does not work, which is the part a reader coming from that issue most needs and the part a diff would not show. Closes issues #105 and #110.
    - M3: pass. Both artifacts are promoted — `openspec/specs/keel-validation-runner/spec.md` carries the reworded fail-loud requirement with its two new scenarios, and `openspec/specs/keel-release-artifact/spec.md` is a new published capability. `node node_modules/.bin/openspec validate the-suite-answers-from-the-repository --strict` reports `Change 'the-suite-answers-from-the-repository' is valid`, and `published-specs-validate-strictly` reports `22 published specs validate strictly against openspec 1.6.0` — up from 21 by the new capability.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 153 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 151 by the two scenarios this change added.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking, and this release needed that more than the last three: the bump rewrites `package.json`, which is also where task 1.2's exclusion lives. M3 asserts the promotion through the two tools that consume the published store, and its count moving 21 to 22 is what shows the new capability actually landed there rather than only in the change. M2 is the one prose check, and what it asserts is the correction: a reader arriving from issue #110 would otherwise apply the repair that issue proposes and find their package unchanged.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-validation-runner/spec.md` and the new `openspec/specs/keel-release-artifact/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus this change's own untracked directory, the record-write layer. `package.json` and `scripts/validate_plugin.py` also carry tasks 1.1 and 1.2's completed writes; both are declared in this task's Touch as well, and this task wrote only the version markers in them.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes once for the whole change with `node_modules/.bin` on `PATH`, reporting no failing scenario and no exception, with both new scenarios registered and every pre-existing scenario green.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 153 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` Run once for the whole change with `node_modules/.bin` on `PATH`: no failing scenario, no exception, both new scenarios registered and green, and every pre-existing scenario green.

## Invalidates

- I1: "only because an external runtime it probes is absent" — the "The full run is parallel,
  deterministic, and fail-loud" requirement in `openspec/specs/keel-validation-runner/spec.md`. It is the
  whole rule for when a scenario may skip, and it does not distinguish a runtime the host provides from a
  CLI this package declares as its own dependency and installs. Updated by: 2.1
- I2: "the openspec CLI is not on PATH" — the skip messages in `scripts/validate_plugin.py`, which name
  `PATH` as the only place the CLI could have been. After this change `PATH` is the fallback and the
  package's own `node_modules/.bin` is the first place looked. Updated by: 1.1
- I3: "compact-task-authoring could not resolve the schema through OpenSpec." — the message in
  `scripts/validate_plugin.py` reached by one condition covering both an unresolvable CLI and a CLI that
  ran and refused. Updated by: 1.1
- I4: "最直接的是新建 `.npmignore` 写 `__pycache__/` 与 `*.pyc`" — the suggested repair in issue #110.
  Measured false: a root `.npmignore` is not consulted once `files` is declared, and packs 42 rather than
  41. Discard reason: the issue is the record of what was found and is closed by this change rather than
  rewritten; the changelog entry and the closing comment carry the corrected account.

## Expectation Coverage

- E1: The suite resolves `openspec` from the package's own installed dependencies before `PATH`, so a checkout that ran `npm install` runs every scenario probing it; and a probe that cannot resolve its CLI reports that distinctly from a CLI that ran and refused. Covered by: 1.1, 2.1
- E2: `npm pack` ships only files tracked by Git, whatever the packer's working tree holds, and a check asserts it and names any file that breaks it. Covered by: 1.2, 2.1
- E3: The skip contract still covers a genuinely absent external runtime, and the Codex and OpenCode probes keep it. Covered by: 1.1
