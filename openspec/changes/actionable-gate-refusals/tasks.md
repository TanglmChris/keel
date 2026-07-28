## 1. A regression check can stand on its own

- [x] 1.1 A tagged check is exempt from red-green, and a strategy cannot be emptied
  - Covers:
    - keel-task-capsule / A regression check declares itself and is exempt from red-green / A regression guard stands as its own check
    - keel-task-capsule / A regression check declares itself and is exempt from red-green / A red-green strategy cannot be emptied out
    - keel-task-capsule / A regression check declares itself and is exempt from red-green / Untagged checks compile unchanged
    - D3 the exemption is a per-check tag reusing the layer-tag mechanism
    - D4 a red-green strategy retains at least one untagged check
    - D5 a tagged check still requires concrete bare-label evidence
    - F3 the layer tag is emitted only when it is not the default, which is what keeps fingerprints still
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: under a red-green strategy, a task with one untagged behavior check and one `(regression)` check completes with `.red`/`.green` recorded only for the untagged one, and still fails when the tagged check's bare-label Evidence is missing
    - M2: a task whose every check is tagged `(regression)` is refused with a diagnostic saying at least one check must carry the strategy, distinguishable from a missing-evidence refusal
    - M3: a task declaring only untagged checks compiles to the byte-identical capsule and fingerprint it compiled before the tag existed, so no recorded Contract anchor is invalidated
  - Rationale: this task builds the tag, so it cannot use it. M3 keeps red-green honestly — emitting the tag unconditionally moves every untagged fingerprint, which is a real red rather than a manufactured one.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1bc962c81d81545d792825264ff7ca071fbd1881987fcdd996e1ffe08b7579af
    - M1: pass. New scenario `regression-check-tag`. Under `vertical-tdd`, a fixture with an untagged `M1` and an `M2 (regression)` completes with `.red`/`.green` recorded only for `M1`. D5 holds in the same scenario: setting `M2: pending` fails completion with a problem naming `M2`, so the exemption is from red-green and not from evidence. The tag also appears in the compiled capsule as `regression: true`, making it a visible term of the contract.
    - M1.red: before the parser accepted the tag, the same fixture failed at task-complete with `invalid-command-label: Command entry must use an M<n> label: M2 (regression): the existing suite stays green` — the author's entry was not merely unexempt, it was unparseable.
    - M1.green: the label parser now accepts a comma-separated tag set (`fast`, `full`, `regression`), and the completion gate skips red-green for tagged labels while still requiring their bare-label Evidence.
    - M2: pass. A task under `vertical-tdd` whose every check is tagged is refused at task-start with `regression-only-strategy`, distinct from any missing-evidence code, and the message tells the author to untag the check that proves the new behavior or name a non-red-green strategy.
    - M2.red: with `regressionOnlyProblems` short-circuited to return nothing, the all-tagged fixture returned `status: pass` from task-start and the scenario failed `accepted a red-green strategy whose every check is tagged` — the tag as pure escape hatch, which is what D4 exists to prevent.
    - M2.green: the check restored; the fixture fails with the single expected code.
    - M3: pass. An untagged check compiles to a capsule entry with exactly the keys `label` and `check`, and the two untagged tasks of this change — 1.1 and 3.1 — recompile to `sha256:1bc962c81d81…` and `sha256:1f2732fd4ae9…`, byte-identical to the fingerprints captured before any code in this task was written.
    - M3.red: emitting the key unconditionally (`emitted.regression = Boolean(entry.regression)`) failed the scenario with `changed the compiled shape of an untagged check`, and both real fingerprints moved — 1.1 to `ccbae397676c` and 3.1 to `47059c642974`. So the check guards a live property rather than a hypothetical one.
    - M3.green: the key emitted only when true; both fingerprints return to their pre-change values.
    - Review:
      - Status: pass
      - Acceptance check: every check runs the real CLI against a temporary repository and asserts on the gate's own JSON, which is the interface an author meets. The three covered scenarios map directly: "A regression guard stands as its own check" to M1 including its D5 half, "A red-green strategy cannot be emptied out" to M2, and "Untagged checks compile unchanged" to M3, whose evidence is the two real fingerprints rather than only the fixture's key set.
      - Scope check: three files changed, all declared in Touch. Both mutations were reverted by restoring a byte copy of `src/core/task-contract.js` taken before the first one; `grep` for the mutation markers returns nothing and `npm test` passes with baseline plus 77 scenarios.
      - Findings: recompiling an archived task no longer reproduces its recorded fingerprint — all 47 anchors under `openspec/changes/archive/` differ, including two recorded earlier today. This predates and is unaffected by this change (verified: a live task recompiles to exactly the value the gate reports), and archived tasks are never resumed, so nothing is blocked. It does mean the archive cannot serve as a fingerprint-stability corpus, which is why M3 uses before-and-after values instead. Durable owner: https://github.com/TanglmChris/keel/issues/24
    - Blocker: none

## 2. An owner can be a file the repo keeps

- [ ] 2.1 Widen the durable-owner vocabulary and make every refusal name its forms
  - Covers:
    - keel-expectation-slice-evidence-gates / A durable owner may be any file the repository keeps, and a refusal names what it accepts / A repo ledger is a legitimate owner
    - keel-expectation-slice-evidence-gates / A durable owner may be any file the repository keeps, and a refusal names what it accepts / An owner that does not exist is refused
    - keel-expectation-slice-evidence-gates / A durable owner may be any file the repository keeps, and a refusal names what it accepts / The pointer override is still not an owner
    - keel-expectation-slice-evidence-gates / A durable owner may be any file the repository keeps, and a refusal names what it accepts / A refusal states the accepted forms
    - keel-core-gates / Gate rejections for validated forms name the field and accepted forms / Findings rejection shows the accepted ownership forms
    - D1 a durable owner may be any repo-relative path that exists
    - D2 keel/HANDOFF.md stays refused although it exists
    - F2 the two closure checks take no repo and both call sites have one
    - A1 widening the shared form reaches Findings and Expectation Coverage, which is intended
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a `Durable owner:` naming a repo-relative file that exists closes an entry in all three places the form is shared — Review `Findings`, `## Expectation Coverage`, and `## Invalidates` — and a path with no file behind it is refused with a diagnostic saying the path does not exist, distinct from the closure-missing diagnostic
    - M2: `keel/HANDOFF.md` is still refused although the file exists, and the refusal says it is a pointer override rather than a durable owner
    - M3 (regression): the previously accepted forms still close — `openspec/changes/…`, `keel/archive/…`, `https://…`, and a discard rationale — so the widening adds vocabulary without dropping any
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. The authoring surface says both

- [ ] 3.1 The template, the schema instruction, and the resident protocol carry the new forms
  - Covers:
    - keel-expectation-slice-evidence-gates / Gate-validated forms are expressed in the author-facing surface / Accepted Findings forms are documented for authors
    - keel-task-capsule / A regression check declares itself and is exempt from red-green / Red and green are additional to the bare label
    - D6 the template states that red and green accompany the bare label rather than replacing it
  - Touch:
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the tasks template and the `tasks` artifact instruction the CLI returns both enumerate the existing-repo-path owner form and describe the `(regression)` tag, and both state that `.red`/`.green` accompany the bare `M<n>` label rather than replacing it
    - M2: the resident protocol states the red-green exemption and the widened owner vocabulary, and the two schema copies and two template copies stay byte-identical to each other
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- I1: "accepts an absolute `https://…` reference as a durable owner, alongside a `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` path, and an existing `openspec/changes/…` artifact" — the Project Conventions section of `AGENTS.md`. It presents a closed list that a repo-relative path is about to join. Updated by: 3.1
- I2: "red-green strategies record concrete per-label `.red`/`.green` Evidence that `keel gate task-complete` enforces" — the verification discipline section of `AGENTS.md`. True of every check today; true of every untagged check afterwards. Updated by: 3.1
- I3: "Red-green strategies record per-label `.red` and `.green` Evidence for the same check" — the tasks template guidance comment and the `tasks` artifact instruction, in both the repo-local and packaged schema copies. Wrong in two ways after this change: it omits the exemption, and it reads as replacing the bare label rather than adding to it. Updated by: 3.1
- I4: "Findings: none, or carry a durable owner — a \"Discard reason:\"/\"Discard rationale:\" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md" — the Review guidance comment in both tasks template copies. Same closed list as I1. Updated by: 3.1
- I5: "the accepted forms: a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, an existing `openspec/changes/<change>/…` artifact, or an absolute `http`/`https` tracker reference" — a scenario in the live `keel-core-gates` spec, with a parallel enumeration in `keel-expectation-slice-evidence-gates`. These are spec-level rather than prose, so both are carried as `## MODIFIED Requirements` deltas in this change rather than as a documentation edit. Updated by: 3.1
- I6: "Review Findings must be `none` or carry a durable owner — a …" — `keel/archive/follow-ups/2026-07-27-guard-json-gitignore.md`. Discard reason: archive notes are historical evidence by definition and are kept unedited; the project convention already records that notes predating a fix describe the older boundary. Recorded because a symptom search finds it.

## Expectation Coverage

- E1: an author can name their repository's own ledger as a durable owner Covered by: 1.1
- E2: a refusal tells the author what would be accepted, so the boundary is not found by trial Covered by: 1.1, 3.1
- E3: a regression guard can be its own check without a fabricated red Covered by: 2.1
- E4: the exemption cannot hollow out a red-green strategy Covered by: 2.1
- E5: no existing task's recorded contract fingerprint moves Covered by: 2.1
- E6: an author meets both rules in the shipped surface rather than at the gate Covered by: 3.1
- E7: an author can tag a genuinely behavioral check `(regression)` and evade red-green for it. Discard reason: accepted as a residual in design; the tag is visible in the capsule and the fingerprint, D4 keeps at least one real check, and `keel-review-checklist` already judges whether a behavioral task's checks prove its Acceptance. A declaration can always be misdeclared.
- E8: widening the shared owner form also widens Review `Findings` and `## Expectation Coverage`, which issue #20 did not ask for. Durable owner: openspec/changes/actionable-gate-refusals/design.md
