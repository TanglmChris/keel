# Tasks

## 1. The last statement

- [x] 1.1 `bin/keel.js` sets `process.exitCode` instead of calling `process.exit()` at the top level, so a payload larger than the receiving pipe's buffer still arrives whole, with every exit code unchanged and the process still terminating
  - Covers:
    - keel-cli-output-contract / Output written for a program arrives complete
    - D1
    - D2
    - D3
    - A2
    - F1
    - F2
    - F3
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/changes/output-survives-the-pipe/design.md
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `output-survives-the-pipe` scenario in `scripts/validate_plugin.py` forces the condition rather than waiting for it. It creates a pipe, shrinks it to 4096 bytes with `fcntl(F_SETPIPE_SZ)`, starts `keel project goal --target codex --json` against a fixture whose capsule exceeds that, begins reading only after the child has exited, and asserts the bytes received equal the bytes the same invocation writes to a file and that they parse as JSON. On a platform without `F_SETPIPE_SZ` the scenario reports the suite's skip contract with exit `3` and names what it could not do, rather than passing.
    - M2 (regression): the same scenario asserts the exit codes did not move — a successful command returns 0, a refused `keel gate task-start` returns 1, and an invalid argument returns 2 — and that each process terminates rather than staying alive, which is the assumption A2 records and the way a lingering handle would surface.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-goal-projection` passes, the scenario whose intermittent failure under parallel load was this defect firing.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the truncation cannot be reproduced on demand, because D2 records that a test which merely runs the command passes on an idle machine whether or not the defect is present, and a green with no red behind it proves nothing here.
    - Stop if removing `process.exit()` leaves the CLI running after `main()` returns, because that trades a silent truncation for a hang and A2 is the assumption that would have been wrong.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1b4e691c770214208010db8a31d5dc7a11b8d0b684a0ed5f9a85e3fabc806700
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario output-survives-the-pipe` reports `output-survives-the-pipe scenario passed.` The scenario shrinks a pipe to 4096 bytes with `fcntl(F_SETPIPE_SZ)`, runs `keel project goal --target codex --json` against a fixture whose projection is 11,915 bytes, pauses so the buffer fills and the rest of the write is left pending, then reads to EOF and compares byte for byte against the same invocation captured normally. It asserts the payload parses as JSON, and it refuses to run vacuously: a fixture projection of 4096 bytes or fewer fails the scenario rather than passing it, because the condition it exists to force would not have arisen.
    - M1.red: fail, for the right reason. With `process.exit(main());` still the last statement, the scenario reported `output-survives-the-pipe: 4096 of 11915 bytes survived a 4096-byte pipe.` — exactly the buffer size, which is the signature of a write discarded at exit rather than a short read. The first draft of the scenario waited on the child before reading; that ordering would have hung against the fixed CLI, which blocks on a full pipe until someone reads, so the read now comes first and the wait after. The red was re-taken with that final ordering in place.
    - M1.green: pass. Same command after the last statement became `process.exitCode = main();`: `output-survives-the-pipe scenario passed.` — 11,915 of 11,915 bytes through the same 4096-byte pipe.
    - M2: pass. Asserted inside the same scenario: `keel --version` returns 0, `keel gate task-start --change no-such-change` returns 1, `keel --not-a-flag` returns 2, and each process terminates — `child.wait(timeout=60)` returns rather than timing out, which is where A2's assumption that nothing keeps the event loop alive would have failed loudly instead of quietly.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-goal-projection` reports `native-goal-projection scenario passed.` This is the scenario whose intermittent failure was this defect firing; it parses the projection this task just stopped truncating.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 156 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 155 by the one scenario this task added, with no other scenario affected.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a payload larger than its channel arrives whole and that no exit code moved. M1 proves the first against a channel small enough that the defect must fire, rather than against an idle machine where it never does — which is the whole difference between this check and one that would have passed before the fix. Byte equality against the same invocation captured normally is the assertion, not a length threshold, so a payload that arrives complete but altered would also fail. M2 proves the second for all three codes the CLI returns, and the termination assertion is what distinguishes this fix from trading a silent truncation for a hang.
      - Scope check: `git status --short` shows exactly the two Touch paths (`bin/keel.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from task-start. `fail()` at `bin/keel.js:166` still calls `process.exit`, deliberately and as `## Expectation Coverage` E3 records.
      - Findings: one, still open, and it is about how this was found rather than about the fix. The defect surfaced first as an intermittent failure of `native-goal-projection` during a parallel `npm test`, while an unrelated change was in the working tree, and it read as a regression from that change — I recorded it as one before isolating it. The general shape is that a load-dependent defect in shared infrastructure is attributed to whatever was being edited when it fired, and the suite offers no way to tell the two apart: a scenario that fails under `--all` and passes alone looks like flakiness rather than like a diagnosis. Durable owner: https://github.com/TanglmChris/keel/issues/119 — the correction and the deterministic reproduction are recorded there, including the measurements that could not be reproduced on demand and why.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded once after this task's checks had passed, because `keel gate task-complete` refused M2 for having no `.red`/`.green` Evidence and it was right to: M2 asserts that three exit codes this change does not touch still hold, which is a check with no honest red. It is now tagged `(regression)`, which is what it always was. `sha256:ed317eee02…` → `sha256:1b4e691c77…`. Nothing about Covers, Touch, Acceptance, or the boundaries changed, and no check text changed. Every check above was re-run under the new contract and reports the same result.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a payload larger than the channel arrives whole
    - E2 — the exit codes and the termination behavior are unchanged
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
    - openspec/specs/keel-cli-output-contract/spec.md
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
    - M2: `keel/CHANGELOG.md` carries an entry stating that the loss was silent, that it fires under load rather than at any particular payload size, and that a suite failure was misread as a regression because of it
    - M3: the spec delta is promoted into `openspec/specs/keel-cli-output-contract/spec.md`, `node node_modules/.bin/openspec validate output-survives-the-pipe --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:29f6cd72c14768dcec10c0a1b743b49db79db371ad1796ace4300d10e341b685
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.48.0 to 5.49.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.49.0 - output survives the pipe`. It states that the loss was silent — no error, no exit-code change, no diagnostic — that it fires under memory pressure rather than at any particular payload size, and that the defect was first recorded as a regression from an unrelated change because a scenario failing under `--all` and passing alone reads as flakiness. It names the consumer that would have been hit (`session-start.js` parsing `keel context --json`, routing a throw to `fallback()`), the measured payload sizes, and what is deliberately not fixed.
    - M3: pass. The delta is promoted — `openspec/specs/keel-cli-output-contract/spec.md` now exists as a published capability with the `Output written for a program arrives complete` requirement and both scenarios. `node node_modules/.bin/openspec validate output-survives-the-pipe --strict` reports `Change 'output-survives-the-pipe' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.` — up from 22 by this new capability, which is the count `## Invalidates` I1 declared would move.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 156 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M3 asserts the promotion through both tools that consume the published store, including the spec count this change was declared to move. M2 is the one prose check, and what it has to carry is the part a reader cannot reconstruct from the diff: the fix is one statement, so an entry describing only the statement would leave the next person with no way to recognize this failure mode when it appears somewhere else. The entry is therefore about how it hides — under load, in shared infrastructure, attributed to whatever was being edited.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-cli-output-contract/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `bin/keel.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "keel-validation-runner" — the published capability list this repository maintains. This change
  adds `keel-cli-output-contract`, and the count of published specs asserted by
  `published-specs-validate-strictly` moves with it.
  Updated by: 2.1
- I2: "process.exit(main());" — the last statement of `bin/keel.js`. It is the defect itself, quoted so
  that a reader searching for the old form finds where it went.
  Updated by: 1.1

## Expectation Coverage

- E1: A payload larger than the receiving pipe's buffer arrives whole, proven against a buffer small enough to force the condition. Covered by: 1.1, 2.1
- E2: Every exit code the CLI returns is unchanged, and the process still terminates. Covered by: 1.1
- E3: `fail()` keeps its `process.exit` call. Discard reason: A1 records that it runs only for usage errors, before any command output, and writes two short lines that fit any pipe buffer — so the race exists there in principle and can lose nothing in practice; https://github.com/TanglmChris/keel/issues/119 owns it if a caller ever writes something large through it.
