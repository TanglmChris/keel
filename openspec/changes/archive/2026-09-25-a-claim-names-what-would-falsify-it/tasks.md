# Tasks

## 1. A claim names what would falsify it

- [x] 1.1 Declaration clauses are parsed as a trailing sequence so any may follow another, and `Detects:` declares a mutation and the failure it must produce; a malformed clause is refused by name, a `(regression)` check may declare one, and `task-complete` requires the declared failure in a `.detects` Evidence entry for the same check
  - Covers:
    - keel-task-capsule / A check may declare the defect it detects / A declared injection requires its failure in evidence
    - keel-task-capsule / A check may declare the defect it detects / A regression check may declare an injection
    - keel-task-capsule / A check may declare the defect it detects / A malformed injection clause is refused by name
    - keel-task-capsule / Declaration clauses chain on one check / Two clauses on one check both parse
    - keel-task-capsule / Declaration clauses chain on one check / An existing single-clause check is unaffected
    - F1
    - F2
    - D1
    - D2
    - D5
    - A1
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - openspec/changes/a-claim-names-what-would-falsify-it/design.md
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-claim-names-what-would-falsify-it` scenario drives the real `keel gate task-start` and `task-complete` against fixtures. A check closing `Fails with: \`x\` Detects: \`mutate\` -> \`boom\`` has both clauses reported by task-start, and `task-complete` fails naming the check while `M1.detects` is absent or lacks `boom`, then passes once it carries it. Fails with: `Detects: is not parsed`
    - M2: a `(regression)`-tagged check declaring `Detects:` is accepted, its injection enforced, and it stays exempt from `.red`/`.green` — the case D5 narrows the report on, asserted rather than argued. Fails with: `regression check may not declare`
    - M3: a check carrying `Detects:` with one literal, or with a `->` and no second literal, is refused by task-start naming the check; and the clause inside inline code is quoted material, not a declaration, which is what lets this repository's own tasks write about it. Fails with: `was silently ignored`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` passes unchanged, so what `Fails with:` accepts, refuses, and requires is untouched when it stands alone.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making the clauses chain changes how a check with a single trailing `Fails with:` parses, because D1's whole warrant is that every existing task is unaffected and M4 is the check that would catch otherwise.
    - Stop if enforcing the injection requires Keel to run the mutation, because the Non-Goals record that Keel records the claim and the author runs it.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f221f081ca2005b9358b8c99768e8b4061bbebf4ddaa54c7e0a2230afc9894f3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-claim-names-what-would-falsify-it` reports `a-claim-names-what-would-falsify-it scenario passed.` A check closing `Fails with: \`boom\` Detects: \`sed …\` -> \`assert 5e-16 == 5e-13\`` compiles with **both** clauses carried as their own fields, and the failure signature is asserted to survive a clause following it — which is the half that was impossible before. Editing the declared injection moves the contract fingerprint, asserted by compiling the two variants and comparing, so an injection changed after the run reports as drift rather than passing as a transcription. Completion is driven through the real `keel gate task-start --record` then `task-complete` on three fixtures: no `.detects` fails `missing-injection-evidence`; a `.detects` recording something else fails `injection-missing-declared-failure`; one carrying the declared failure passes.
    - M1.red: fail, for the declared reason. `a-claim-names-what-would-falsify-it: Detects: is not parsed — a check carrying a failure signature followed by an injection clause was refused; got 'fail' 'M1 carries a \`Fails with:\` marker that does not close the check with a literal.'` The cause is exactly what F2 predicted: the signature was end-anchored on the check, so a clause after it made the signature itself unparseable. Carries the declared signature `Detects: is not parsed`. The completion half was red separately and after the parser was green — `Detects: is not enforced — a declared injection with no \`.detects\` Evidence completed cleanly.` — so the parse and the enforcement each have their own failure rather than one standing for both.
    - M1.green: pass. Same command after the trailing-clause parser and the `.detects` requirement were written.
    - M2: pass. A `(regression)`-tagged check declaring `Detects:` is accepted, its injection compiled and enforced, and it stays exempt from `.red`/`.green`. This is D5 asserted rather than argued.
    - M2.red: fail, for the declared reason, and taken by **implementing the report's own suggestion** rather than by reverting to an earlier state: a refusal reading `M2 is tagged (regression) and declares an injection, but a regression check has no red for one to describe.` The scenario reports `regression check may not declare an injection`. That is the design this change narrows, made real for long enough to watch it remove the clause from the one place it is worth most — a check with no honest red, where an injection is the only mechanism that can show it is not vacuous. Carries the declared signature `regression check may not declare`. Reverted.
    - M2.green: pass. Same command with no such refusal in the parser.
    - M3: pass. Both malformed shapes are named rather than ignored — one literal with no arrow, and an arrow with nothing after it — each refused by `malformed-injection` with the check named, asserted on the diagnostic code rather than on the message text. A clause named inside inline code stays quoted material: a check whose prose contains `` `Detects:` `` and closes with a real failure signature compiles clean, which is what lets this repository's own tasks write about the marker.
    - M3.red: fail, for the declared reason, from the state where the clause parses and a malformed one falls through: `a malformed injection clause (one-literal) was silently ignored, which leaves the author believing an injection is enforced when none was parsed.` Carries the declared signature `was silently ignored`.
    - M3.green: pass. Same command after the marker survived into the malformed report.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` reports `a-red-declares-what-it-proves scenario passed.` unchanged, so what `Fails with:` accepts, refuses, and requires is untouched when it stands alone — which is every task in the archive. `npm test` reports `validation --all passed: baseline plus 176 scenarios, 1 skipped`.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a check can declare an injection, that the declaration is enforced, and that existing checks are unaffected. All of it is driven through the real gates against fixtures — task-start for the parse and the fingerprint, task-start plus task-complete for the enforcement — never by calling the parser. The reds are staged so no check is carried by another: M1's parse red is the starting state, M1's enforcement red is taken after the parser is green, M2's red is the rejected design implemented on purpose, and M3's is the permissive parser. M2's red deserves the emphasis: the cheap way to "prove" D5 would have been to assert the acceptance and argue the rest in prose, and instead the refusal was built and observed removing the clause from its best use. A1 is unchanged and unclaimed — Keel does not run the mutation, so a `.detects` entry is the author's claim exactly as every other `M<n>` result is.
      - Scope check: `git status --short` shows `src/core/task-contract.js`, `src/core/gates.js`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. Both Stop Rules held: `a-red-declares-what-it-proves` is green unchanged, so a single trailing signature parses as it did; and nothing executes the mutation. Two defects in this task's own work were caught by the suite rather than by me and fixed here: an assertion of mine guarded two distinct failures behind one message, which `assertion-shape-count` refused and which is split; and the `## Invalidates` entry I2 quoted README's example verbatim, whose text contains a `--scenario` reference that `authored-scenario-names-are-registered` then read as a scenario needing registration — the entry now describes the example instead of reproducing it, and says why.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `Measured:` binds a literal to the check's own recorded output, enforced against that check's bare `M<n>` Evidence, and nothing requires an undeclared number to appear anywhere
  - Covers:
    - keel-task-capsule / A check may bind a number to the measurement behind it / A declared measurement must appear in the check's own output
    - keel-task-capsule / A check may bind a number to the measurement behind it / A number with no declaration is not checked
    - F3
    - F4
    - D3
    - D4
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: in the same scenario, a check closing `Measured: \`1799.9\`` fails `task-complete` while its `M1` Evidence records an output without that literal, naming the check and the literal, and passes once the output carries it. Fails with: `Measured: is not enforced`
    - M2 (regression): a fixture whose Evidence states numbers in inline code with no `Measured:` clause completes cleanly, so D4's opt-in boundary holds and the 847 spans F4 measured in this repository's own archive are not a new class of refusal.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if satisfying `Measured:` requires reading any Evidence entry other than the check's own `M<n>`, because D3 records that entry as the one holding the command and its output.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:21771ba8c5dfbbcede922483875f10efe3503bc35da015bfa3aaa956b633e9f0
    - M1: pass. In the same scenario, a check closing `Measured: \`1799.9\`` whose `M1` Evidence records `a fanout load of 1200 fF` fails `task-complete` with `measurement-missing-from-evidence`, naming the check and the literal; the same fixture with `1799.9` in the output passes. Driven through the real `task-start --record` then `task-complete`, and asserted on the diagnostic code rather than the message text. The fixture is the reporting session's own case: an estimate of 1200 against a measured 1799.9.
    - M1.red: fail, for the declared reason. `a-claim-names-what-would-falsify-it: Measured: is not enforced — a declared literal absent from the check's own recorded output completed cleanly, which is an estimate presented as a measurement.` Carries the declared signature `Measured: is not enforced`.
    - M1.green: pass. Same command after the clause was parsed and held against the check's bare `M<n>` Evidence.
    - M2: pass. A fixture whose `M1` Evidence states `\`1200\` fF across \`2433\` fanout pins` with no `Measured:` clause completes cleanly, so nothing requires an undeclared number to appear anywhere. That is D4's boundary asserted rather than assumed, and it is what keeps the 847 inline-code spans F4 measured in this repository's archive out of scope. Correctly tagged regression: undeclared numbers were required nowhere before this task either.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declared literal must appear in the check's own recorded output and that an undeclared number is required nowhere. Both are driven through the real gates. The pair matters more than either half: the enforcing case alone would be satisfied by a rule that checked every number, which is precisely the design declined on measurement, so the opt-in boundary is asserted beside it. The weakness stays stated rather than hidden — an author who invents a number will not volunteer to bind it — and what answers it is F3: `Fails with:` is opt-in too and still caused a third of the reporting repository's re-records, because the cost lands after the author has declared.
      - Scope check: `git status --short` shows `src/core/task-contract.js`, `src/core/gates.js`, and `scripts/validate_plugin.py` — exactly this task's Touch, all three already dirty from 1.1 — plus this change's own untracked directory. `npm test` reports `validation --all passed: baseline plus 176 scenarios, 1 skipped`. The Stop Rule held: the requirement reads `evidenceValue(task, entry.label)` and no other entry.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 The two clauses are documented where `Fails with:` is documented — the protocol's verification-discipline statement and the README section that teaches the marker — including that Keel judges neither and runs neither
  - Covers:
    - keel-task-capsule / A check may bind a number to the measurement behind it / A number with no declaration is not checked
    - I1
    - I2
    - A1
  - Read:
    - README.md
    - AGENTS.md
  - Touch:
    - README.md
    - AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the same scenario asserts both surfaces name `Detects:` and `Measured:`, state that Keel records the claim rather than verifying it, and state that the clauses are optional; and that `README.md`'s worked example shows two clauses on one check, so a reader learns the chaining from the example rather than from prose about it. Fails with: `README does not name Detects:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` and the baseline pass, so the wording those surfaces already carry about `Fails with:` is extended rather than replaced.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if documenting the clauses requires the resident block, because that block's budget was raised once already in 5.63.0 and these clauses are capsule vocabulary rather than a rule an agent needs before deciding anything.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:408746fb9d2723c0c7d62192ae9ccf6f8d8108494d6517951bc915e1824bdf5b
    - M1: pass. The scenario asserts both surfaces name `Detects:` and `Measured:`; that `README.md` states Keel `records the claim` and `does not run` the mutation, matched against the whitespace-flattened text so the sentences can be rewrapped; and that the README carries a **worked example with both clauses on one check**, matched as `Fails with: \`…\` Detects: \`…\` -> \`…\`` rather than by looking for prose about chaining. That last assertion is the one that matters: a reader copies the example, and an example showing one clause teaches that one clause is all there is.
    - M1.red: fail, for the declared reason. `a-claim-names-what-would-falsify-it: README does not name Detects: — the injection clause must be named, and a clause an author cannot find is a clause nobody declares.` Carries the declared signature `README does not name Detects:`.
    - M1.green: pass. Same command after both surfaces were written. `README.md` gained two subsections — the honest-red-immune case with the measured 1000× unit error, and the number-claiming-to-be-a-measurement case with the 847-span reason the universal rule was declined — and `AGENTS.md`'s verification-discipline statement gained both clauses, the chaining, and one sentence stating that Keel runs no mutation and judges no declaration.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-red-declares-what-it-proves` and the baseline both pass, and `npm test` reports `validation --all passed: baseline plus 176 scenarios, 1 skipped`. The `Fails with:` wording those surfaces already carried is extended rather than replaced: its own subsection, its example, and its optional/refusal paragraph are byte-identical, with the new material following them.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that both clauses are documented where the first one is, including what Keel does not do. The non-enforcement sentences are asserted by content rather than trusted, because they are the part a later editor would trim as boilerplate and they are the only thing standing between a reader and the belief that a declared injection was verified. The chaining is asserted through the example for the reason stated above. What no check here covers is whether a reader then declares anything — documentation's reach ends at being findable.
      - Scope check: `git status --short` shows `README.md`, `AGENTS.md`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus `src/core/task-contract.js` and `src/core/gates.js` from 1.1 and 1.2, both complete and untouched here, plus this change's own untracked directory. The Stop Rule held: `assets/bootstrap/AGENTS.md` is byte-unchanged, so the resident block whose budget was raised in 5.63.0 pays nothing for capsule vocabulary.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a check may declare the defect it detects, and the declaration is enforced
    - E2 — a check may bind a number to the output that produced it
    - E3 — the clauses chain and existing tasks are unaffected
    - I3
  - Read:
    - keel/CHANGELOG.md
    - openspec/specs/keel-task-capsule/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted spec text. The behavior was proven red-green in 1.1 to 1.3, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry stating the measured case an honest red cannot reach — a check whose red, signature, and green were all real while a 1000× unit error left it green — and recording both declined designs with their measurements: the universal numeric rule against the 847 spans it would reach here, and the report's suggested refusal of `Detects:` on regression checks against the reason a regression check is where it is worth most
    - M3: the delta is promoted into `openspec/specs/keel-task-capsule/spec.md`, `node node_modules/.bin/openspec validate a-claim-names-what-would-falsify-it --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:65f54a16998e3e032e5e69e87b15fcdd5a9b395ce97273c04a7eb5ec934cc75c
    - M1: pass. `version-alignment` passes; every marker moved 5.63.0 to 5.64.0 via `node scripts/bump_version.js minor`. The Stop Rule held: no marker turned up that the scenario does not check.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.64.0 - a claim names what would falsify it`. It states the measured case an honest red cannot reach — real red, correct signature, real green, and a 1000× unit error leaving the check green — and records **both** declined designs with their measurements: the universal numeric rule against the 847 inline-code spans it would reach here (with the 247-of-256 `Contract:`-line split that shows the archive has almost no author-supplied digests to check), and the report's suggested refusal of `Detects:` on regression checks against the reason a regression check is where it is worth most. It also states that Keel runs no mutation and judges no declaration.
    - M3: pass. The delta is promoted into `openspec/specs/keel-task-capsule/spec.md` with all three requirements. `node node_modules/.bin/openspec validate a-claim-names-what-would-falsify-it --strict` reports valid, and `published-specs-validate-strictly` reports `24 published specs validate strictly against openspec 1.6.0.` — unchanged at 24, this change modifying an existing capability rather than adding one.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 176 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads the markers through the scenario that checks them all rather than the bump script's own report. M3 asserts the promotion through both consuming tools, strict in both, and the count staying at 24 is the check that an existing capability was extended rather than a new file published by mistake. M2's job is the part a later reader most needs: not what was added, but what was refused and on what measurement — both declines are in the entry, with their numbers, rather than left in the change directory for someone to find.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, the promoted spec, and the paths 1.1 to 1.3 declared complete, plus this change's own untracked directory. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "A check owing a red MAY close with `Fails with:` and one inline-code literal, declaring the
  failure its red must show" — the `## verification discipline` statement in `AGENTS.md`. It
  enumerates the one clause a check may close with, so two more make it an incomplete list rather
  than a wrong sentence, which is the shape a reader who is not counting never notices.
  Updated by: 1.3, 2.1
- I2: "`Fails with:` marker that names no literal. To *write about* the marker in a check without
  declaring one" and the worked `M1:` example beneath it — `README.md`'s section teaching the marker.
  The example shows one clause closing a check, which after this change is one of three and no
  longer shows what a check carrying two looks like. Quoted by description rather than verbatim
  here: the example's own text contains a `--scenario` reference, and `authored-scenario-names-are-registered`
  reads one of those in a live change's `tasks.md` as a scenario that must be registered.
  Updated by: 1.3, 2.1
- I3: "A check owing a red MAY close with `Fails with:` and one inline-code literal" and the
  end-anchoring rationale beneath it — `openspec/specs/keel-task-capsule/spec.md`'s
  `A check may declare the failure its red must show`. The clause keeps its meaning and stops being
  the only one, so the requirement stands and the capability gains three beside it.
  Updated by: 2.1
- I4: "the clause closes the check" — the comment above `FAILURE_SIGNATURE` in
  `src/core/task-contract.js:157`. After this change a failure signature closes the *clause
  sequence* rather than the check, and the comment is the thing a later reader would trust over the
  code.
  Updated by: 1.1

## Expectation Coverage

- E1: A check may declare a mutation and the failure it must produce, completion requires that failure in a `.detects` entry, and the declaration is in the fingerprint (D2, F1). Covered by: 1.1
- E2: A check may bind a literal to its own recorded output, and an undeclared number is required nowhere (D3, D4, F3, F4). Covered by: 1.2
- E3: The clauses chain, and a check with a single trailing failure signature parses exactly as before (D1, F2). Covered by: 1.1
- E4: A `(regression)` check may declare an injection, which is where it is worth most (D5). Covered by: 1.1
- E5: Both surfaces that teach the vocabulary name the new clauses and state that Keel judges and runs neither (A1, I1, I2). Covered by: 1.3
- E6: Whether a declared injection was actually run, rather than written plausibly (A1). Discard reason: deliberately not done rather than deferred. Keel does not execute an `M<n>` check either; every result in Evidence is the author's claim, and a `.detects` entry has exactly that standing. Building verification for this one clause would mean Keel running a mutation against the worktree — a far larger claim than this change makes, and one nothing else in the capsule does. What catches a fabricated injection is Review, and the surfaces say so rather than implying a check.
