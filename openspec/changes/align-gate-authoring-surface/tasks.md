<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Omitted fields inherit versioned defaults: Owner is the current Keel agent,
     Mode is implementation, Read is this change's proposal/design/specs/tasks
     plus discovered repository context, Acceptance derives from Covers, autonomy
     defaults to hard-stop, and commit/push/sync/archive stay unauthorized. -->

## 1. Review Status vocabulary (issue #1 Case B)

- [x] 1.1 Accept `done`, single-source the accepted Status set, and surface the vocabulary
  - Covers:
    - keel-core-gates / Accepted Review Status vocabulary is single-sourced and includes `done`
    - keel-core-gates / Gate rejections for validated forms name the field and accepted forms
    - keel-expectation-slice-evidence-gates / Gate-validated forms are expressed in the author-facing surface
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - src/core/context.js
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: an otherwise-complete task recording `Review Status: done` is rejected by `task-complete` before the change and passes the Status axis after; the accepted set is one shared constant consumed by both `src/core/gates.js` and `src/core/context.js`, with no second copy of the token list remaining
    - M2: `task-complete` on a `Status` outside the accepted set emits `semantic-review` naming the `Status` field and listing the accepted tokens including `done`
    - M3: both `tasks.md` template copies and both `schema.yaml` `tasks`-instruction copies enumerate the accepted `Status` tokens; `npm test` passes with a validator assertion that the accepted-`Status` set is single-sourced and surfaced
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:525118c3371465158c230ff7f257eca7253bba73044b9e723ce45beaeb9b78ae
    - M1: `Status: done` now completes; a shared `ACCEPTED_REVIEW_STATUSES` constant in `src/core/task-contract.js` is consumed by both `gates.js` and `context.js`, neither of which keeps its own token list.
    - M1.red: pre-fix HEAD — `task-complete` on a `Status: done` fixture returned needs-review; the `pass|passed|complete|completed|ok` regex rejected `done`.
    - M1.green: with the fix the same fixture returns pass; the core-gates scenario `done`-accept assertion passes.
    - M2: the `semantic-review` error names the `Status` field and lists the accepted tokens including `done`.
    - M2.red: pre-fix — a `Status: reviewed` fixture produced the generic "Current-agent Review requires passing Status, Acceptance check, Scope check, and Findings."
    - M2.green: with the fix the same fixture produces "Current-agent Review is incomplete — Status must be one of pass, passed, complete, completed, ok, done (got \"reviewed\")."
    - M3: both `tasks.md` template copies and both `schema.yaml` instruction copies enumerate the accepted `Status` tokens; the accepted set is single-sourced.
    - M3.red: pre-fix — `gates.js` and `context.js` each carried the duplicated `pass|passed|complete|completed|ok` literal and the template enumerated 0 tokens.
    - M3.green: `npm test` → "validation --all passed: baseline plus 50 scenarios"; the new baseline check `validate_review_status_single_source`, the schema/template needles, and the core-gates done/bad-status assertions all pass.
    - Review:
      - Status: pass
      - Acceptance check: pass — the accepted Status vocabulary is single-sourced (`ACCEPTED_REVIEW_STATUSES`), includes `done`, is surfaced in the template and instruction, and the rejection error names the field and lists the tokens.
      - Scope check: pass — changes limited to Touch (`src/core/{task-contract,gates,context}.js`, both `tasks.md` template copies, both `schema.yaml` copies, `scripts/validate_plugin.py`) plus this change's own `tasks.md`.
      - Findings: none
    - Blocker: none

## 2. Expectation Coverage section (issue #1 Case C)

- [ ] 2.1 Ship `## Expectation Coverage` in the template and instruction, and sample it in the close error
  - Covers:
    - keel-expectation-slice-evidence-gates / Gate-validated forms are expressed in the author-facing surface
    - keel-core-gates / Gate rejections for validated forms name the field and accepted forms
  - Touch:
    - src/core/gates.js
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: a `tasks.md` scaffolded from the shipped `keel-spec-driven` template contains a `## Expectation Coverage` section that `change-close` accepts; before the change the template emits no such section and `change-close` fails `expectation-coverage`
    - M2: the `change-close` `expectation-coverage` rejection carries a minimal `- E<n>: … Covered by: <task ids>` format sample
    - M3: both `tasks.md` template copies carry the section (`- None.` default plus an `E<n>` example) and both `schema.yaml` `tasks`-instruction copies require and format it; `npm test` passes with a validator assertion
  - Evidence:
    - Contract: pending task-start capsule and fingerprint
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Findings forms (issue #1 Case D)

- [ ] 3.1 Enumerate the accepted Findings forms in the surface and in the finding-owner error
  - Covers:
    - keel-expectation-slice-evidence-gates / Gate-validated forms are expressed in the author-facing surface
    - keel-core-gates / Gate rejections for validated forms name the field and accepted forms
  - Touch:
    - src/core/gates.js
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: the `finding-owner` error output enumerates the accepted Findings forms (a `discard reason:`/`discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact) and states that `keel/HANDOFF.md` is not an owner
    - M2: both `tasks.md` template copies and both `schema.yaml` `tasks`-instruction copies enumerate those exact accepted Findings forms
    - M3: `npm test` passes with a validator assertion that the surface enumerates the accepted Findings forms and that the `finding-owner` error shows them
  - Evidence:
    - Contract: pending task-start capsule and fingerprint
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: Review Status vocabulary — single-sourced across `gates.js`/`context.js`, includes `done`, enumerated in the tasks template and instruction, and the `semantic-review` error names the field and lists the tokens. Covered by: 1.1
- E2: Expectation Coverage section — shipped in the `keel-spec-driven` tasks template with `- None.` default and an `E<n>` example, required and formatted in the `tasks` instruction, and the `change-close` error carries a format sample. Covered by: 2.1
- E3: Findings forms — the accepted forms are enumerated in the tasks template and instruction, and the `finding-owner` error shows them. Covered by: 3.1
