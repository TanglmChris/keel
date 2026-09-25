# Tasks

## 1. The strategy

- [x] 1.1 `equivalence` joins the strategy vocabulary, declares `Base:` and `Fields:` beside `Strategy:`, owes no red, and `keel gate task-start` refuses each way the shape can pass while comparing nothing
  - Covers:
    - keel-task-capsule / A zero-difference claim names its base and its fields / The strategy is accepted without a red
    - keel-task-capsule / A zero-difference claim names its base and its fields / A base that is head compares nothing
    - keel-task-capsule / A zero-difference claim names its base and its fields / A missing declaration is named
    - D1
    - D2
    - D3
    - F1
    - F2
    - F3
  - Read:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `an-equivalence-claim-names-its-base` scenario asserts a task declaring `Strategy: equivalence` with a resolvable `Base:` and a non-empty `Fields:` passes `keel gate task-start`, and that `task-complete` requires no `.red` or `.green` Evidence for its checks. Fails with: `unsupported verification strategy`
    - M2: the same scenario asserts each of the four refusals by name — no `Base:`, no `Fields:`, an empty `Fields:`, and a `Base:` no git ref resolves — and that each diagnostic names the declaration it is about rather than the strategy. Fails with: `accepted an equivalence task that compares nothing`
    - M3: a `Base:` resolving to the same commit as `HEAD` is refused, the refusal names that commit, and it states that an A/B against itself always agrees — the one refusal that catches a shape which is complete, resolvable, and still tests nothing. Fails with: `accepted a base that is head`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario task-verification-strategies` and `--scenario core-gates` pass, so the existing six strategies and their red-green obligations are unchanged by the seventh
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if resolving `Base:` needs a network call or a second checkout, because F3 admits Git reads and nothing more; a gate that fetched would stop being local and offline, which is the property its verdict rests on.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:527bb3587f84f5ef2614d03e96c822ba99efd283270e1afd7449518e6d3c848b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-equivalence-claim-names-its-base` reports `an-equivalence-claim-names-its-base scenario passed.` A task declaring `Strategy: equivalence` with `Base: HEAD~1` and `Fields: wns, tns, cell_count`, inside a git fixture with two commits, passes `keel gate task-start`. The compiled capsule is asserted to carry the strategy *and* both declarations, because a declaration outside the capsule is outside the fingerprint and could be edited after the run it describes. The task-start warnings are asserted to mention neither `.red` nor `.green`, which is how the absence of a red-green obligation is observed rather than assumed.
    - M1.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: unsupported verification strategy — a complete equivalence task was refused, so the one task class with the strongest criterion still has nowhere to declare it. … Verification strategy is unsupported: equivalence; supported: vertical-tdd, regression-first, characterization, snapshot-characterization, rendered-behavior, evidence-first.` Carries the declared signature `unsupported verification strategy`. The same red also showed `Base:` and `Fields:` being read as malformed command entries, which is what they were: `verification()` filtered only `Strategy:` and `Reason:` out of the check list.
    - M1.green: pass. Same command after `equivalence` joined `SUPPORTED_VERIFICATION_STRATEGIES`, `Base:`/`Fields:` joined `isVerificationField`, and both were emitted into the capsule — conditionally, so every existing task's capsule shape and fingerprint are untouched.
    - M2: pass. All four fixtures are refused with the code that names the declaration rather than the strategy: `missing-equivalence-base`, `missing-equivalence-fields` (for both an absent `Fields:` and one that resolves to an empty set), and `unresolvable-equivalence-base`, whose message quotes the ref it could not resolve. The absent and empty cases are additionally asserted to produce *different* sentences: they are the same state to the comparison and opposite mistakes to the author, and telling someone who wrote the line that they did not write it is the way a correct diagnostic wastes an hour.
    - M2.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: accepted an equivalence task that compares nothing — the no-base fixture passed, so the declaration is optional in practice.` Carries the declared signature `accepted an equivalence task that compares nothing`.
    - M2.green: pass. Same command after `equivalenceProblems` was added and pushed into the task's diagnostics.
    - M3: pass. `Base: HEAD` is refused with `equivalence-base-is-head`, the message names the resolved commit — read back out of the fixture with `git rev-parse HEAD` rather than trusted from the diagnostic — and states that an A/B against itself always agrees. This is the only one of the four refusals where nothing about the task looks wrong: the strategy is supported, both declarations are present, and the ref resolves.
    - M3.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: accepted a base that is head — an A/B against itself always agrees, so the check proves nothing and looks complete doing it.` Carries the declared signature `accepted a base that is head`. Recorded plainly: the branch was written in the same edit as M2's refusals, so the red was taken by removing the `equivalence-base-is-head` branch and restoring it — a red for code that existed, not for code that did not. The alternative was to claim a red I had not produced.
    - M3.green: pass. Same command with the branch restored.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-verification-strategies` and `--scenario core-gates` both pass, so the existing six strategies, their red-green obligations, and the gate's other refusals are unchanged by the seventh. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the strategy exists, owes no red, and is refused in each way its shape can be complete while comparing nothing. Every part is asserted on the gate's own JSON — status, problem codes, and message text — rather than on the reader that produced it. Two choices are worth naming. The declarations are asserted *inside the compiled capsule*, not merely accepted, because the fingerprint is what makes a declaration a prediction rather than a note. And the base-is-head refusal is asserted against a commit read back from the fixture, so the scenario cannot agree with a diagnostic that printed the wrong hash.
      - Scope check: `git status --short` shows `src/core/task-contract.js` and `scripts/validate_plugin.py` — two of this task's three Touch entries; `src/core/gates.js` was declared because the refusals could have landed there and turned out not to need it, since task-start's contract diagnostics are assembled in `task-contract.js`. The Stop Rule held: `resolveCommit` runs `git rev-parse --verify --quiet` against the repository the gate is already reading, with no fetch and no second checkout.
      - Findings: M4 named `strategy-vocabulary`, a scenario that does not exist. `authored-scenario-names-are-registered` refused it, and the real check is `task-verification-strategies`. That is the second time in two changes that a `(regression)` check named a scenario from memory rather than from the registry, and both were caught in one run by the same check — the pattern is worth noting rather than the instance. Resolved here: M4, which now names the registered scenario and passes.
    - Blocker: none
    - Reauthorizations: one. M4 named an unregistered scenario (see Findings), so the check text had to change, moving the fingerprint from `sha256:f5bd62f…` to `sha256:527bb35…`. No other check's assertion moved, but nothing was carried forward with `--keep-evidence`: every check above was re-run under the recorded contract, which costs one suite run and removes the need to trust a claim.

- [x] 1.2 an `equivalence` task covering a scenario from an `## ADDED Requirements` delta is refused unless a sibling task of the same change covers it under a red-green strategy
  - Covers:
    - keel-task-capsule / Equivalence is not an escape from red-green / New behavior needs a red somewhere in the change
    - keel-task-capsule / Equivalence is not an escape from red-green / A sibling red-green task satisfies it
    - D4
    - F4
    - A1
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - openspec/changes/an-equivalence-claim-names-its-base/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the same scenario asserts that an `equivalence` task whose `Covers` names a scenario under `## ADDED Requirements`, with no sibling task covering it, is refused with a diagnostic naming that scenario and stating that behavior which is new is not behavior which is unchanged. Fails with: `accepted new behavior with no red anywhere`
    - M2: adding a sibling task declaring `vertical-tdd` that covers the same scenario makes it pass, and a sibling covering a *different* scenario does not — the guard has to be satisfied by coverage of the entry it objected to, not by the presence of any red-green task in the change. Fails with: `any sibling satisfied the guard`
    - M3 (regression): an `equivalence` task covering only `MODIFIED` or unchanged requirements still passes, so the guard fires on new behavior rather than on the strategy
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if satisfying the guard requires reading a task's Evidence rather than its contract, because the guard runs at `task-start` when no evidence exists yet.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9915208b922e661c52ecc1c40355e11197cfc34ca79b1ce4b5c59ee4c83c50b4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-equivalence-claim-names-its-base` reports the scenario passing. A fixture whose delta spec declares `## ADDED Requirements` with a requirement and two scenarios, and whose `equivalence` task covers one of them with no sibling covering it, is refused with `equivalence-covers-added-behavior`. The diagnostic is asserted to name the covered scenario — not just the task — and to say why the two claims conflict, because "add a red-green task" without naming the entry sends the author to guess which Covers line is the problem.
    - M1.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: accepted new behavior with no red anywhere — an equivalence task covering a scenario the change adds passed, so the strategy is a way to author a feature with no red in the whole change.` Carries the declared signature `accepted new behavior with no red anywhere`.
    - M1.green: pass. Same command after `equivalenceEscapeProblems` joined `taskStart`'s problem list, reading `## ADDED Requirements` from the change's delta specs and the task's spec-shaped `Covers` entries.
    - M2: pass. A sibling declaring `vertical-tdd` and covering the same entry makes the task pass; a sibling declaring `vertical-tdd` and covering a *different real* scenario of the same requirement does not, and is still refused with `equivalence-covers-added-behavior`. The guard is satisfied by coverage of the entry it objected to, which is the difference between a guard and a check that the change contains at least one red-green task — a condition every change with more than one task meets.
    - M2.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: any sibling satisfied the guard — a red-green task covering a different scenario was accepted as proof of this one, which makes the guard a check that a change contains at least one red-green task.` Carries the declared signature `any sibling satisfied the guard`. Taken by relaxing the sibling match to `return true` once the control fixture was fixed; the first attempt at this red is recorded in Findings, because it did not fail for the reason it claimed.
    - M2.green: pass. Same command with the entry comparison restored.
    - M3: pass. An `equivalence` task covering no scenario the change adds — the fixture whose delta spec has an empty `## ADDED Requirements` section — passes. The guard fires on new behavior rather than on the strategy, so the ordinary refactor this strategy exists for is unaffected. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the strategy cannot author new behavior with no red anywhere in the change. What makes the check meaningful is the negative control — a sibling that is red-green and real and still does not satisfy the guard — and that control is the part that was wrong first. Both the refusal and the two sibling cases are asserted on the gate's problem codes and message text. `## MODIFIED` requirements are deliberately outside the guard: behavior that changed is still behavior an `equivalence` task can legitimately claim is measurement-stable.
      - Scope check: `git status --short` shows `src/core/gates.js` and `scripts/validate_plugin.py` — this task's two Touch entries. The Stop Rule held: the guard reads contracts and delta specs only, never Evidence, which is correct for a check that runs before any evidence exists.
      - Findings: the negative control passed for the wrong reason. The mismatched sibling first covered an invented scenario, so the fixture was refused because *that sibling's* Covers resolved to nothing — `unresolved-covers` — and not because the guard rejected a sibling covering a different entry. The assertion was green while testing nothing, and it was caught only by relaxing the matcher to take M2's red and finding the red would not fire. Resolved here: M2, whose fixture now declares a second real scenario so the mismatched sibling compiles cleanly.
        The same investigation found a second defect and it is the more serious one: the guard originally read a sibling's strategy by compiling it, and `compileTaskContract` returns no capsule when a task has any diagnostic. A sibling with an unrelated contract error therefore read as having no strategy and silently stopped satisfying the guard, which would refuse a correctly authored change and point at the wrong task. Resolved here: M2, via `declaredStrategy`, which reads the sibling's own `Verify` text in both the compact and expanded forms and does not depend on the rest of that task being valid.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 a check's Evidence may read `artifact <path> sha256:<digest>`, which `keel gate task-complete` checks for existence, digest match, and a path the archive will carry
  - Covers:
    - keel-task-capsule / Evidence may reference an artifact instead of retelling it / A matching digest is accepted
    - keel-task-capsule / Evidence may reference an artifact instead of retelling it / A stale digest is refused
    - keel-task-capsule / Evidence may reference an artifact instead of retelling it / A path that archiving would leave behind is refused
    - D5
    - D6
    - A3
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the same scenario asserts the form is *verified* rather than tolerated: Evidence reading `artifact <path> sha256:<digest>` is accepted when the file is there and its digest matches, and refused when no file is there — a reference any prose entry would already have passed as concrete. Fails with: `an artifact reference was not verified`
    - M2: mutating the artifact's content by one byte is refused, and the diagnostic names the path, the recorded digest, and the computed one, so a reader can tell a stale record from a wrong path. Fails with: `accepted a stale digest`
    - M3: an artifact path outside the change's own directory is refused, stating that archiving moves the change directory — the inverse of the `Durable owner:` rule and for the opposite reason. Fails with: `accepted a path archiving would leave behind`
    - M4 (regression): `npm test` reports no failing scenario, so prose Evidence, `deferred to C<n>`, and the pending-entry refusal all behave as before
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the digest check has to parse the artifact's contents, because D6 records that Keel checks identity and reads nothing else.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:70423185d16038247c2e37e60fc938d518c478af78923d6177e9cc0f05f964b0
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-equivalence-claim-names-its-base` reports the scenario passing. Evidence reading `artifact openspec/changes/demo/evidence/compare.json sha256:<digest>` is accepted when the file is there and hashes to the recorded digest, and refused with `artifact-missing` when no file is there. The second half is the one that matters: as prose that same sentence already passed `isConcrete`, so without a check the form would buy nothing.
    - M1.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: an artifact reference was not verified — a reference to a file that does not exist was accepted, so the form is tolerated as prose rather than checked. Any sentence would have passed the same way.` Carries the declared signature `an artifact reference was not verified`.
    - M1.green: pass. Same command after `artifactReference` recognized the form and `artifactProblems` checked existence inside the per-label Evidence loop. The first green run also corrected the fixture: it recorded a change-relative path while the implementation resolves repo-relative, which is required for M3 to be expressible at all — a change-relative path is inside the change directory by construction and could never be outside it.
    - M2: pass. A file whose content does not hash to the recorded digest is refused with `artifact-digest-mismatch`, and the message is asserted to name the path *and* the recorded digest, because "the digest does not match" leaves a reader unable to tell a stale record from a pointer at the wrong file. This is the case a bare path cannot see, and the common one: the command gets re-run.
    - M2.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: accepted a stale digest — the artifact's content does not hash to the recorded digest and the reference was accepted, so Review reads whatever the file says now.` Carries the declared signature `accepted a stale digest`.
    - M2.green: pass. Same command after the digest comparison was added.
    - M3: pass. An artifact outside the change's own directory is refused with `artifact-outside-change`, and the message is asserted to say that archiving is what breaks the pointer rather than merely that the path is wrong. This is the inverse of the `Durable owner:` rule and for the opposite reason: a follow-up pointer must outlive the change, an evidence artifact must travel with it.
    - M3.red: fail, for the declared reason. `an-equivalence-claim-names-its-base: accepted a path archiving would leave behind — an artifact at 'evidence/compare.json' was accepted although the archive moves only the change directory.` Carries the declared signature `accepted a path archiving would leave behind`.
    - M3.green: pass. Same command after the containment check was added ahead of the existence check, so a path the archive would abandon is named as that rather than as a missing file.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.` Prose Evidence, `deferred to C<n>`, and the pending-entry refusal are untouched: the artifact check runs only when the entry matches the reference form, and every other entry takes the path it took before.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that Evidence may point at machine output whose identity is checked. Each of the three refusals is asserted on the gate's problem code *and* on what its message names, because the whole value of this form over prose is that a reader can act on it — a refusal that does not distinguish a stale digest from a wrong path returns the reader to guessing, which is the state the form exists to leave. Keel reads the file only to hash it: it does not parse the artifact and compares nothing inside it, so the claim that base and head agree stays the author's, recorded before Review exactly as `Fails with:` and `Detects:` are.
      - Scope check: `git status --short` shows `src/core/gates.js` and `scripts/validate_plugin.py` — this task's two Touch entries. The Stop Rule held: `artifactProblems` hashes the bytes and never looks inside them.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: one. 1.3's M1 as authored said the reference is "accepted as concrete Evidence", which every prose sentence already satisfies — the check would have been green before any implementation existed. It was rewritten before implementation to assert that the form is *verified* rather than tolerated, pairing the accepted case with a refused one, and the task was re-recorded. The same pass removed the word `placeholder` from the check, which `unfilledToken` reads as an unfilled slot even inside prose. No evidence existed under the previous contract.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - E3
    - E4
    - I1
    - I2
  - Read:
    - keel/CHANGELOG.md
    - README.md
    - src/skills/keel-tdd-or-test-first/SKILL.md
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
    - src/skills/keel-tdd-or-test-first/SKILL.md
    - plugins/keel/skills/keel-tdd-or-test-first/SKILL.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, documentation, and a promoted spec. The behavior was proven red-green in 1.1 through 1.3, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes
    - M2: `keel/CHANGELOG.md` records that the reporting repository re-recorded its contract twice to get past a shape rather than a criterion, that the A/B criterion is stronger than red-green rather than weaker, and why `Command:` was declined
    - M3: `README.md` and `src/skills/keel-tdd-or-test-first/SKILL.md` document `equivalence`, its two declarations, and the guard that stops it being an escape hatch
    - M4: the delta is promoted, `node node_modules/.bin/openspec validate an-equivalence-claim-names-its-base --strict` passes, and `published-specs-validate-strictly` passes
    - M5: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4c2eaaa940d3500d0e7a9b7e910a2eedd81b8c22330930e0a7ee4c9c93ea7cc9
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.67.0 to 5.68.0 via `node scripts/bump_version.js minor`. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.68.0 - an equivalence claim names its base`. It records that the reporting repository re-recorded its contract twice to get past the shape rather than the criterion and names the task; that the A/B criterion is stronger than red-green rather than weaker, with the reason — it catches the change that incidentally moved a result; why `Command:` was declined; that the guard is satisfied by coverage of the entry it objected to and not by a red-green task existing; that the artifact rule is the inverse of the `Durable owner:` rule and why; and both defects the reds exposed, including the vacuous negative control.
    - M3: pass. `README.md` gains "When the right answer is \"nothing changed\"" with the declaration shown as a `Verify` block, the four refusals, the escape-hatch guard, and the artifact form. `src/skills/keel-tdd-or-test-first/SKILL.md` lists `equivalence` in the strategy taxonomy with its two declarations and the guard, states the artifact-evidence rule beside the red-green evidence rule, and now says of `evidence-first` that it is scoped by an absence — which is why it is not the home for `equivalence` work. `AGENTS.md`'s verification-discipline section carries both rules. The skill's plugin copy was mirrored, so `native-plugin-manifests` passes.
    - M4: pass. The delta is promoted into `openspec/specs/keel-task-capsule/spec.md`. `node node_modules/.bin/openspec validate an-equivalence-claim-names-its-base --strict` reports valid, and `published-specs-validate-strictly` passes inside `npm test`.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M4 asserts the promotion through both consuming tools. M2 and M3 are about what a reader learns without running anything, and the bar for both was that the documentation says why rather than only what — particularly that `equivalence` is stronger than red-green, because an author who reads it as the weaker option will use it where a red belongs, which is exactly what the guard in 1.2 exists to catch. The `evidence-first` line was extended for the same reason: it was the only listed strategy with no red, so a reader had no way to tell that it was scoped by an absence rather than being the general home for work without one.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `README.md`, both copies of `keel-tdd-or-test-first/SKILL.md`, and the promoted spec, plus the files 1.1 through 1.3 declared complete and this change's own directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`Verify` names one supported strategy (vertical-tdd, regression-first, characterization,
  snapshot-characterization, rendered-behavior, evidence-first)" — the enumeration in `AGENTS.md`'s
  verification-discipline section, repeated in `README.md` and in
  `src/skills/keel-tdd-or-test-first/SKILL.md`'s strategy list. A seventh is added, so every copy of
  the six is now wrong.
  Updated by: 2.1
- I2: "`evidence-first`: docs, configuration, or diagnosis work whose checks state the observable
  artifact or evidence instead of a red-green loop" — in `src/skills/keel-tdd-or-test-first/SKILL.md`.
  It stays correct and stops being the only home for a task with no red, which is what a reader
  currently infers from it being the only one listed without one.
  Updated by: 2.1
- I3: "a repo-relative path that exists … a path inside the change's own directory is refused even
  though it exists, because archiving moves that directory" — the `Durable owner:` rule in this
  repository's `AGENTS.md` Project Conventions. It stays exactly true, and an artifact path now takes
  the opposite rule for the opposite reason, so the two are easy to confuse.
  Updated by: 2.1
- I4: "this one has no honest red" — the wording in the reporting repository's
  `move-keep-hierarchy-from-rtl-into-the-synthesis-flow` tasks.md. It is outside this repository and
  becomes the workaround for a gap that no longer exists.
  Durable owner: https://github.com/TanglmChris/keel/issues/142

## Expectation Coverage

- E1: `equivalence` is a first-class strategy that owes no red and declares what it compares against
  and on which fields (D1, D2). Covered by: 1.1
- E2: Each way the shape can pass while comparing nothing is refused by name, including a base that is
  head (D3). Covered by: 1.1
- E3: The strategy cannot author new behavior with no red anywhere in the change (D4, A1).
  Covered by: 1.2
- E4: Evidence may point at a machine artifact whose identity is checked, inside the directory the
  archive carries (D5, D6, A3). Covered by: 1.3
- E5: Whether Keel runs the A/B itself (A2). Discard reason: deliberately not done rather than
  deferred. It would require a second checkout and running an arbitrary command, making the gate
  non-local, non-deterministic, and slow, and it would put Keel in the position of judging a domain
  field set it cannot understand. The claim stays the author's, recorded before Review, exactly as
  `Fails with:` and `Detects:` are.
