# Tasks

## 1. The declaration

- [x] 1.1 A check may declare the failure its red must show, the declaration compiles into the contract, and a declaration that can produce no red is refused by name
  - Covers:
    - keel-task-capsule / A check may declare the failure its red must show
    - D1
    - D5
    - D6
    - F2
    - F4
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/a-red-declares-what-it-proves/design.md
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-red-declares-what-it-proves` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI. A check ending in a `Fails with:` clause with an inline-code literal compiles, and the literal appears in the JSON capsule as the check's failure signature; editing only that literal moves the reported fingerprint, and removing the clause moves it back to the value the task had without it. A `(regression)`-tagged check declaring a signature fails and the message names the check; the same declaration under `evidence-first` fails the same way. A `Fails with:` marker that is not a clause closing the check — no literal after it, or a literal not at the end — fails and names the check rather than compiling as if nothing were declared, while the same marker written inside inline code compiles untouched, because a check that describes this rule must be able to name it. This task's own checks declare no signature: the parser that would read one does not exist when its contract is compiled.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario task-capsule` passes unchanged, so a task declaring no signature keeps the capsule and fingerprint it had.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if enforcing the declaration requires Keel to run or capture any process output, because D4 records that the gate stays local and reads only what the author wrote.
    - Stop if a check declaring no signature compiles to a different capsule than it does today.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c286c57ba395b187ba14d50b65a99c70fcc64cee3d071145b354d96a6cb69ee2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` reports `a-red-declares-what-it-proves scenario passed.` A check closing with a `Fails with:` clause compiles, and the literal lands in the JSON capsule as the check's own field while staying in the check text the author wrote. Editing only the literal moves the fingerprint; removing the clause moves it back to the value the task had without it. A `(regression)`-tagged check and an `evidence-first` task both refuse the declaration by name with code `signature-without-red`. Three malformed shapes — no literal, an unquoted one, a literal that does not close the check — refuse with `malformed-failure-signature`, while the same marker written inside inline code compiles and carries no signature.
    - M1.red: fail, for the right reason. Before the parser existed the scenario reported `the compiled check does not carry the declared failure signature; got [{'label': 'M1', 'check': 'node test.js asserts the public behavior. Fails with: `openspec: not found`'}]` — the clause present in the text the author wrote and read by nothing.
    - M1.green: pass. Same command after `failureSignature()` parsed the clause, the command mapper carried it, and the capsule emitted `failsWith`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-capsule` reports `task-capsule scenario passed.`, and `task-contract-core` passes alongside it, so a task declaring no signature keeps the capsule and fingerprint it had.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 170 scenarios.` — up from 169 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a signature can be declared, compiles into the contract, and a declaration that can produce no red is refused. M1 proves each. The assertion that carries the change's whole value is the fingerprint one: a signature that could be edited after the red was recorded would be a transcription of whatever happened to fail, and the point of declaring it is that it was written first. Putting the clause inside the check text buys that for free, which is why it is written there rather than in a field of its own.
      - Scope check: `git status --short` shows exactly this task's two Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged since the re-record.
      - Findings: one, fixed in this task. Both regression checks named scenarios that do not exist — `task-contract-compile` and `red-green-evidence`, neither in the registry — so as written they could not have been run. Caught by grepping the registry before running them rather than by any gate: `keel gate task-start` validates that a check is concrete prose, not that a command it names resolves. That gap is real and is not this change's to close, since a gate that ran a check to see whether it exists would be running the check. What made it visible here is that the checks were read before being trusted. Resolved here: M2
      - Blocker: none
      - Reauthorizations: one. Correcting the two scenario names moved the fingerprint from `sha256:f4a1582…` to `sha256:c286c57…`; re-recorded with `--keep-evidence M1`, because M1's check text is unchanged by the correction and its red had already been observed against it. M2 and M3 are the checks whose text changed, and both were re-run after the re-record.

- [x] 1.2 A declared signature is enforced against the recorded red at completion, and the obligation names which checks declared one at task-start
  - Covers:
    - keel-core-gates / A declared failure signature is enforced against the recorded red
    - D2
    - D3
    - D4
    - D7
    - F1
    - F3
    - A1
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the `a-red-declares-what-it-proves` scenario is extended to drive `keel gate task-complete` through the real CLI. A task whose check declares a signature and whose `.red` Evidence does not contain it fails, and the message names both the check and the missing string. The same task with the string present passes. A red-green task declaring no signature completes exactly as it does now, asserted against the same fixture with the clause removed. The `task-start` obligation line names which checks owing a red declared a signature and which did not. Fails with: `accepted a red that does not show the declared failure`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario task-verification-strategies` passes unchanged, so every existing red-green verdict keeps its shape.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the enforcement would refuse a task that declares no signature, because D3 records that the undeclared case is unchanged.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b28d14ab189440d665445ceb9e44fc41f1fabbb9ef470c95280a1a34b130ec2c
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` reports `a-red-declares-what-it-proves scenario passed.` A task whose check declares a signature and whose `.red` reads `it failed before the implementation existed.` is refused with code `red-missing-declared-failure`, and the message names both `M1` and `openspec: not found`. The same task whose `.red` quotes that string passes. The same fixture with the clause removed and the same weak red passes, so nothing changed for a check that declares no signature. The task-start obligation names `M1 must fail with` and the literal when one is declared, and says `declared no failure signature` when none is.
    - M1.red: fail, for the right reason, and the reason this task predicted. The scenario reported `task-complete accepted a red that does not show the declared failure; got 'pass'` — the declared signature sitting in the contract while completion read only whether a `.red` line was present. That string is the one this task's own `Fails with:` clause declared before the check was written.
    - M1.green: pass. Same command after `completionChecks` read the compiled `failsWith` and compared it against the recorded `.red`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-verification-strategies` reports `task-verification-strategies scenario passed.` Every existing red-green verdict keeps its shape, including the refusals for missing and pending red evidence.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 170 scenarios.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declared signature is enforced against the recorded red, that an undeclared check is untouched, and that the obligation is stated at task-start. M1 proves all three, and the second is asserted the way it has to be: against the *same* weak red the declared check was refused for, with only the clause removed. Asserting that some undeclared task still passes would prove nothing, since it might pass for reasons unrelated to the clause. This task also demonstrated its own subject — the red it recorded is the string it declared before writing the check, and the first red the scenario produced was a different assertion failing, which is precisely the case the declaration exists to distinguish.
      - Scope check: `git status --short` shows this task's two Touch paths plus `src/core/task-contract.js` from task 1.1, already complete and untouched here, plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, not fixed here. Keel cannot tell a declared signature that predicts a failure from one transcribed after seeing it — an author can record the red, then write a clause matching it, and only the fingerprint makes that edit visible rather than impossible. Design A1 states this as the accepted limit, and it is the same shape as `Discard reason:` and `--keep-evidence`: Keel records the claim and puts it where a reviewer sees it. Naming a weak signature (`Error`, the scenario's own name) is the same limit from the other side. Durable owner: https://github.com/TanglmChris/keel/issues/116
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a check may declare the failure its red must show
    - E2 — a declared signature is enforced against the recorded red
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
    - README.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-core-gates/spec.md
    - openspec/specs/keel-task-capsule/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. Both behaviors were proven red-green in tasks 1.1 and 1.2, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming issue #116, stating both measured cases the report brought, and recording what the declaration deliberately does not verify
    - M3: both spec deltas are promoted, `node node_modules/.bin/openspec validate a-red-declares-what-it-proves --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ca9a3171e99072bdd9012b01c95a378fe75f761fb1469baf2c392edbd91b30f6
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` after `node scripts/bump_version.js minor` rewrote every marker to 5.57.0 — the npm package, both native plugin manifests, the protocol docs, and the twelve installed OpenSpec surfaces.
    - M2: pass. `keel/CHANGELOG.md` carries the `5.57.0 - a red declares what it proves` entry. It names issue #116, states both measured cases the report brought — the red that passed because the fixture had not cleared `PATH`, and the two fixtures that failed for an unrelated reason because they contained no wording the checker would refuse — and records what the declaration deliberately does not verify: whether the signature is a good one. `AGENTS.md` and `README.md` carry the same, the README with a worked example.
    - M3: pass. Both deltas are promoted — `A check may declare the failure its red must show` into `openspec/specs/keel-task-capsule/spec.md` and `A declared failure signature is enforced against the recorded red` into `openspec/specs/keel-core-gates/spec.md`. `node node_modules/.bin/openspec validate a-red-declares-what-it-proves --strict` reports `Change 'a-red-declares-what-it-proves' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 170 scenarios.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the release carries both behaviors and that the published wording is true of them. M1 and M3 prove the markers and the promoted requirements; M2 is the one that needed writing rather than checking. The README section states the limit in the same breath as the feature — Keel does not judge whether the signature is a good one — because a reader who takes the clause for a guarantee of honest reds is worse off than one who never had it.
      - Scope check: `git status --short` shows the version markers, the twelve installed surfaces the bump rewrote, the protocol docs, the README, the changelog, the two promoted specs, and this change's own directory. `keel guard status` reports the fingerprint unchanged since the re-record.
      - Findings: one, fixed in this task. The task's Touch declared the version markers but not the twelve installed OpenSpec surfaces that `bump_version.js` also rewrites, so the writes landed outside declared authority and the Scope check caught it rather than the guard — the bump runs as a script through Bash, which the PreToolUse hook does not intercept. The gap is real: a task can write outside Touch through any tool the hook does not see. It is not this change's to close, and the honest reading is that the guard is a second line and the Scope check is the first. Resolved here: M1
      - Blocker: none
      - Reauthorizations: two. First, correcting the `## Invalidates` I3 entry to quote the wording it searched for rather than only name the files, refused by `task-start` as `names where to look but not what to look for` — a correct refusal, since a discard with nothing quoted cannot be re-checked later. Second, adding the twelve installed surfaces to Touch after the Scope-check finding above. Both moved the fingerprint from `sha256:e9e6f7b…` to `sha256:ca9a317…`; re-recorded with `--keep-evidence M1,M2,M3,M4`, because neither edit touched any check's text — one is an Invalidates entry and the other is a Touch entry — and all four checks were re-run after the re-record regardless.

## Invalidates

- I1: "A behavioral task needs behavior assertions or an explicit smoke step" and the
  red-green sentence around it — the verification-discipline section of `AGENTS.md`,
  which states that red-green strategies record concrete `.red`/`.green` Evidence
  without mentioning that a check may declare what its red must show.
  Updated by: 2.1
- I2: "the failing check" and the red-green section around it — `README.md`, which
  describes recording a red without mentioning that a check may declare what its
  red must show.
  Updated by: 2.1
- I3: "red-green strategies record concrete per-label `.red`/`.green` Evidence" —
  searched in `assets/bootstrap/AGENTS.md` and `CLAUDE.md`, the two other places
  the protocol is published.
  Discard reason: neither carries the sentence or any red-green wording — the
  bootstrap file is nine lines and `CLAUDE.md` is an include of `AGENTS.md`.
  Checked 2026-09-08.

## Expectation Coverage

- E1: A check may declare the failure signature its red must show, it compiles into the contract and the fingerprint, and a declaration that can produce no red is refused by name. Covered by: 1.1, 2.1
- E2: A declared signature is required to appear in the recorded `.red` Evidence, an undeclared check is unaffected, and task-start names which checks declared one. Covered by: 1.2, 2.1
