<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1). -->

## 1. Diagnostics name the thing the author has to change

- [x] 1.1 A Covers question reference is the subject of its entry, not any substring of it
  - Covers:
    - keel-task-capsule / A Covers question reference is the subject of its entry
    - keel-validation-runner / A narrowed refusal is asserted from both sides
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `covers-question-reference-scope` drives `node bin/keel.js gate task-start` over two fixtures and asserts both sides of the narrowed match: a `Covers` entry that opens with a fact reference and names a resolved `Q1` in its supporting text produces no `unresolved-authority` diagnostic, while an entry that opens with `Q1` and declares no authorized fallback still produces one naming `Q1`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d015b122ec667a1e7ee717dd82079145c650af8f6995467ae620f94712b200b6
    - M1: `python scripts/validate_plugin.py --scenario covers-question-reference-scope` passes, and `npm test` reports baseline plus 82 scenarios with the neighbouring `unresolved-authority-names-field` scenario still passing.
    - M1.red: before the fix the scenario failed with "naming a resolved question as supporting detail still demands a fallback for it", printing the real diagnostic for the out-of-scope fixture: `Q1 is referenced in Covers but task 1.1 declares no authorized fallback.` The in-scope fixture was already refused, so the red isolated exactly the reported defect.
    - M1.green: after matching the identifier only where it opens a Covers entry, the fixture whose entry opens with `F13 (Q1 resolved: …)` produces no `unresolved-authority` diagnostic while the fixture whose entry opens with `Q1:` still produces one naming `Q1`.
    - Review:
      - Status: pass
      - Acceptance check: both scenarios of the requirement are asserted in one run — the subject fixture proves `task-start` still refuses and names the question, the detail fixture proves a cited resolved question is no longer treated as unresolved authority. The refusing case is what distinguishes the narrowing from a deletion of the check.
      - Scope check: only `src/core/task-contract.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`. The change directory's own tasks.md carries Evidence under the record-write layer.
      - Findings: none
    - Blocker: none

- [x] 1.2 A non-concrete check names the unfilled-slot token that made it non-concrete
  - Covers:
    - keel-task-capsule / A non-concrete check names the token that made it non-concrete
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `non-concrete-check-names-token` asserts that a `M2` check carrying a bare unfilled slot outside inline code yields a `missing-command-check` diagnostic whose message contains that slot text, that replacing exactly what the diagnostic names removes the diagnostic, and that a `M2` whose value is `pending` keeps the unqualified wording with no token named.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a36f477dbe403ad17dc087f3c127361895157b729b2243d4deeb285e8ae7f4b3
    - M1: `python scripts/validate_plugin.py --scenario non-concrete-check-names-token` passes, and `npm test` reports baseline plus 83 scenarios.
    - M1.red: before the fix the scenario failed with "the diagnostic did not name the slot it matched", printing the wording issue #28 item 5 quotes verbatim: `M2 must define a concrete public check.`
    - M1.green: the diagnostic now names the matched slot and tells the author to replace it or fence it in inline code; substituting the named slot with a concrete URL clears it, and a check whose value is `pending` still gets the unqualified wording because there is no slot to name.
    - Review:
      - Status: pass
      - Acceptance check: both scenarios of the requirement are asserted — the named-token case and the empty-check case that must keep the unqualified wording. The scenario also applies exactly what the diagnostic asks and asserts it clears, so the message is verified as actionable rather than merely more specific.
      - Scope check: only `src/core/task-contract.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`.
      - Findings: none
    - Blocker: none

- [x] 1.3 A task declaring no verification form reports one problem, and no defaulted field is required
  - Covers:
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `absent-verification-form-is-one-problem` asserts that a task declaring neither `Verify` nor `Commands` produces a single diagnostic naming `Verify` as the compact field to add, and produces no `missing-field` diagnostic for `Owner`, `Mode`, `Read`, `Acceptance`, `Report`, `Candidate Boundary`, or `Stop Rules`.
    - M2: the same scenario asserts that an expanded task declaring `Commands`, `Covers`, `Evidence` and a boundary but omitting every defaulted field passes `node bin/keel.js gate task-start`, that the same task with `Commands` removed still fails, and that a `Candidate Boundary` diagnostic appears only once the task declares `Coupling: required`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cdec9dadb31d687411ec4b966e50229084d7b5ef1a6b37ff4bf28e32f851c1f1
    - M1: `python scripts/validate_plugin.py --scenario absent-verification-form-is-one-problem` passes; `npm test` reports baseline plus 84 scenarios.
    - M1.red: before the fix the scenario printed the whole cascade issue #28 item 4 reports — ten diagnostics, `Owner`, `Mode`, `Read`, `Commands`, `Acceptance`, `Candidate Boundary`, `Stop Rules`, `Report`, a boundary line, and an Evidence-label mismatch — and reported "expected exactly one diagnostic naming Verify, found 0".
    - M1.green: a task declaring neither form now produces one `missing-verification-form` diagnostic naming `Verify` and the `Strategy:` and check entries it needs, and no `missing-field` diagnostic for any of the seven defaulted or coupling-owned fields. The orphan Evidence label is no longer restated, because it is a consequence of the same absence.
    - M2: the same scenario asserts the expanded path; `python scripts/validate_plugin.py --scenario core-gates` also passes, which is the near-empty-task case that keeps its `Covers` diagnostic.
    - M2.red: the first implementation returned early on the missing form and swallowed everything else, which broke `core-gates`: its fixture declares only `Owner:` and asserts a diagnostic naming `Covers`, and that diagnostic had disappeared. The red was the real regression, not a fixture artifact.
    - M2.green: the diagnostic now replaces only the expanded v3 cascade — the compact `Covers` and `Evidence` requirements still report — so an expanded task declaring `Commands`, `Covers`, `Touch` and `Evidence` and omitting every defaulted field passes, removing `Commands` from it still fails, and `Candidate Boundary` is required only once the task declares `Coupling: required`.
    - Review:
      - Status: pass
      - Acceptance check: both added scenarios of the requirement are proven — the one-problem case and the defaulted-field case — and the narrowing keeps a refusing case on each side: `Commands` removed still fails, `Coupling: required` still demands its boundary, and a near-empty task still learns that `Covers` is missing. The removed fields were verified in design F4 to resolve to defaults, derive from Covers, be consumed nowhere, or be owned by the coupling contract.
      - Scope check: only `src/core/task-contract.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`. The stale fixture comment corrected in the suite is I6 of this change's Invalidates.
      - Findings: none
    - Blocker: none

- [x] 1.4 task-complete refuses to infer a task that has never started
  - Covers:
    - keel-core-gates / task-complete infers only a task that has started
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `python scripts/validate_plugin.py` scenario `task-complete-selection-requires-a-started-task` asserts that `node bin/keel.js gate task-complete` with no task named refuses on selection when the first unchecked task records no fingerprint in its Evidence `Contract` anchor, that the message names the inferred task, the most recently checked task, and the explicit selection flag, that the same change passes selection once that anchor records a fingerprint, and that `task-start` with no task named still selects the first unchecked task.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8dd04f4e3fae85f485f061c6ba7335ece596a98cb0a8b159cb84bc493071916b
    - M1: `python scripts/validate_plugin.py --scenario task-complete-selection-requires-a-started-task` passes; `npm test` reports baseline plus 85 scenarios.
    - M1.red: before the fix the scenario reported that no-arg `task-complete` did not refuse on selection, and printed the problem list it got instead: the empty list. The unstarted task did not merely report the wrong problems — it passed clean, which is a sharper defect than issue #28 item 6 describes and is filed separately.
    - M1.green: no-arg `task-complete` now returns `ambiguous-completion-selection`, naming the inferred task `1.2`, the most recently checked task `1.1`, and both `--task` and `task-start --record` as the ways out. The same fixture with a recorded anchor on `1.2` selects `1.2` and produces no selection problem, and no-arg `task-start` still selects `1.2` with no selection problem, so the refusal did not leak into the stage whose job is to start an unstarted task.
    - Review:
      - Status: pass
      - Acceptance check: all three scenarios of the requirement are asserted — the unstarted refusal with every named element checked, the started task evaluating as before, and `task-start` keeping its first-unchecked default. The refusal is verified as actionable in both directions it offers.
      - Scope check: only `src/core/gates.js` and `scripts/validate_plugin.py` changed, both declared in Touch; base `HEAD`.
      - Findings: an explicitly named task whose `Contract` anchor is `pending` still passes `task-complete` with nothing compared, so the fingerprint guarantee holds only for tasks that recorded an anchor. Out of scope here, because making an unrecorded anchor a hard failure changes completion for every consumer repo and is a decision of its own. Durable owner: https://github.com/TanglmChris/keel/issues/30
    - Blocker: none

## 2. The shipped statements agree with the shipped behavior

- [x] 2.1 Promote the deltas, restate the affected authoring rules, and archive the change
  - Covers:
    - keel-task-capsule / A Covers question reference is the subject of its entry
    - keel-core-gates / task-complete infers only a task that has started
  - Touch:
    - openspec/specs/keel-task-capsule/spec.md
    - openspec/specs/keel-core-gates/spec.md
    - openspec/specs/keel-validation-runner/spec.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - scripts/validate_plugin.py
    - AGENTS.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the deltas are promoted into `openspec/specs`, `npx openspec validate diagnostics-name-the-cause` reports no error, `python scripts/validate_plugin.py` reports pass at the raised scenario count, and both copies of `schema.yaml` and both copies of the tasks template state that an unresolved question blocks only when it opens a Covers entry.
    - M2: `node bin/keel.js gate change-close . --change diagnostics-name-the-cause --action archive --json` returns pass, after which this task is authorized to archive the change with `--skip-specs`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fa13f010bad496c4b1f93df8e3e985f96400371aadf6682ee03f1b6af98f7f9b
    - M1: `npx openspec validate diagnostics-name-the-cause` reports "Change 'diagnostics-name-the-cause' is valid" with the three deltas promoted into `openspec/specs`; `npm test` reports baseline plus 85 scenarios; `diff` confirms both `schema.yaml` copies and both tasks-template copies are byte-identical, and each pair now states that the identifier blocks only where it opens a Covers entry, so a resolved question can be cited beside the fact that closed it.
    - M2: `node bin/keel.js gate change-close . --change diagnostics-name-the-cause --action archive --json` returns pass once this task is checked, and the change is then archived with `--skip-specs` under the authorization this task carries.
    - Review:
      - Status: pass
      - Acceptance check: every statement the change made stale is corrected in the same change, which is what E3 asks. The two behavior rules this task restates — the question-reference scope and the completion-selection refusal — are the two an author reads before writing a task, so they are carried in AGENTS.md as well as in the specs and the shipped schema.
      - Scope check: the promoted specs, both schema copies, both template copies, `scripts/validate_plugin.py`, `AGENTS.md`, and `keel/CHANGELOG.md` changed, all declared in Touch; base `HEAD`.
      - Findings: this task needed one reauthorization. Invalidates I2 named the shipped template sentence but not the `task_template_snippets` assertion in the suite that pins it, so promoting the wording broke `expectation-slice-gates` on a file outside the original Touch. Recorded as I7 and the Touch expanded before continuing. The lesson generalizes: a declared invalidation should be grepped for its own wording, since the assertion that pins a sentence lives nowhere near it. Durable owner: https://github.com/TanglmChris/keel/issues/28
    - Blocker: none

## Invalidates

- I1: "without an authorized fallback blocks implementation" — the `tasks` instruction prose in both copies of `openspec/schemas/keel-spec-driven/schema.yaml`. It stays true only for a question that opens a Covers entry. Updated by: 2.1
- I2: "requires an authorized fallback" — the Covers slot comment in both copies of `openspec/schemas/keel-spec-driven/templates/tasks.md`. Updated by: 2.1
- I3: "the parser falls back to expanded-v3 mode (demands Owner/Mode/Commands/…)" — gotcha 2 in the native memory file `keel-dogfood-authoring-gotchas.md`. After 1.3 an absent verification form is reported as one missing field, and the expanded set no longer names `Owner` or `Mode`. Updated by: 2.1
- I4: "Fill Evidence + Review → check the box → `keel gate task-complete`" — step 4 of the loop in the native memory file `dogfood-full-discipline.md`. That order is the reverse of the documented one and contradicts the loop recorded in `keel-dogfood-authoring-gotchas.md`; 1.4 makes the order load-bearing for no-arg selection. Updated by: 2.1
- I7: "unresolved Q" — the entry reading `unresolved Q<n>` in the `task_template_snippets` required-text list in the `expectation-slice-gates` scenario in `scripts/validate_plugin.py`, which pins the template sentence I2 replaces. Updated by: 2.1
- I6: "is a genuine expanded v3 task and must keep its existing required-field diagnostics" — the fixture comment in the `non-concrete-verify-diagnostic` scenario in `scripts/validate_plugin.py`. After 1.3 that task is reported as one missing verification form instead. Updated by: 1.3
- I5: "must define a concrete public check" — the unqualified wording quoted in issue #28 item 5. After 1.2 it appears only for an empty or `pending` check. Durable owner: https://github.com/TanglmChris/keel/issues/28

## Expectation Coverage

- E1: A diagnostic must name the field, token, or task the author has to change, rather than a consequence of it Covered by: 1.1, 1.2, 1.3, 1.4
- E2: A narrowed refusal must keep a case that still refuses, so the narrowing cannot be mistaken for a removal Covered by: 1.1, 1.3
- E3: Every shipped statement about the changed rules must be corrected in the same change Covered by: 2.1
