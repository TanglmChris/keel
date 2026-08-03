# Tasks

## 1. One boundary, both readers

- [ ] 1.1 End a change-level section where the tasks begin
  - Covers:
    - keel-task-capsule / A change-level section ends at the next heading or the next task / A section above the task list is read as written
    - keel-task-capsule / A change-level section ends at the next heading or the next task / An entry a task body appeared to close is still refused
    - keel-task-capsule / A change-level section ends at the next heading or the next task / A task's own Covers entries are not section entries
    - keel-task-capsule / A change-level section ends at the next heading or the next task / Both change-level sections share the boundary
    - keel-task-capsule / A change-level section ends at the next heading or the next task / The tail position is unchanged
    - D1 — one `sectionBody()` helper computes both section bodies
    - D2 — section position becomes irrelevant, not required
    - D3 — the entry patterns are left alone
    - D4 — the boundary tests against the task lines already parsed
    - D5 — the heading half adopts `parseTasks()`'s `/^\s*##\s/`
    - D6 — verification drives the gates on real repositories, four cells per section
    - F1 — the reported false positive, reproduced at 5.21.0
    - F2 — the unreported silent false negative
    - F3 — the two slices are character-identical, not merely similar
    - F4 — the mirror boundary is already implemented and already required
    - F5 — the position that avoids the defect is stated nowhere
    - F6 — no archived change flips verdict under the new boundary
    - F7 — both readers already receive the parsed task array
    - A1 — no tasks.md nests a task checkbox inside a section entry
    - A2 — nothing outside this repository parses the two diagnostic codes
    - A3 — a suite scenario passing only because a section absorbed the task list is repaired at the assertion
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario section-ends-where-the-tasks-begin` passes. The scenario builds real repositories and drives `keel gate change-close` and `keel gate task-start`, asserting four cells per section — closed and unclosed, section-above-the-tasks and section-in-the-tail — that a closed entry reports no problem wherever the section sits; that an unclosed entry is refused and named wherever it sits, including when a task body carries a `- none` field entry; that an `E<n>` a task declares under `Covers` is never judged as a section entry; and that the tail cells return the verdicts, codes, and messages they return today.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario task-body-ends-at-heading` still passes, so the mirror boundary this one completes — a task's body ending at the next task or the next heading, and the `--record` anchor search using that same extent — is unchanged.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` still passes, so what closes an entry, the diagnostic codes, and the refusal messages are unchanged.
    - M4 (regression): `npm test` passes with no failing scenario and no exception, which is where a fixture that passed only because its section absorbed the task list would surface.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if narrowing the section changes which closures the gate accepts, rather than only which lines it reads.
    - Stop if the tail position's verdict, code, or message changes for any input.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:09e734c8ca130570e53909dcab26712fd285c2d437b8fa344502f7502756ade6
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario section-ends-where-the-tasks-begin` reports `section-ends-where-the-tasks-begin scenario passed.` Eight cells driven through `keel gate change-close` and `keel gate task-start` on real repositories, four per reader: a closed entry in the tail and the identical section above the task list both report nothing; an unclosed entry is refused in both positions, once, with byte-identical message text; and the file the two positions differ by is one moved section, not one changed character.
    - M1.red: fail, as required, before any change to `src/core/gates.js`. The scenario halted on the reported cell: `section-ends-where-the-tasks-begin M1 the same closed Expectation Coverage section, moved above the task list with not one character changed, was refused.` beside the gate's own output, `E1 lacks behavior coverage, durable owner, or discard rationale. Close it with `Covered by: <task ids>`, a `Discard reason:`, or a `Durable owner:` …` — the whole message, produced through the gate rather than quoted from #71, and identical to the reporter's. Because the scenario returns at its first failing cell, the unreported silent mode was measured separately on the same unfixed tree (`git stash push -- src/core/gates.js`), counting only section-closure problems: an unclosed `E1` beside a `repo-action` task's `- none` Touch returned **1** problem in the tail and **0** above the task list, and an unclosed `I1` in the same two positions returned **1** and **0**. Zero is the defect: the declaration was skipped in silence, on both readers.
    - M1.green: pass. All eight cells hold. The same two silent-mode measurements on the fixed tree return **1** and **1** for `E1`, and **1** and **1** for `I1` — position no longer reaches either verdict. The cell that matters most is the pair asserting message identity: widening what the gate refuses would be worth nothing if the tail position's text had shifted underneath it.
    - M2 (regression): pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-body-ends-at-heading` reports `task-body-ends-at-heading scenario passed.` The mirror boundary this change completes — a task's body ending at the next task or the next `##` heading, and the `--record` anchor search using that same extent — is unchanged, including the planted `Contract` line in the trailing section that proves the anchor search still stops at the heading.
    - M3 (regression): pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` reports `expectation-slice-gates scenario passed.` What closes an entry, the diagnostic codes, and the refusal messages are untouched; this change narrows which lines are read, not what a read line means.
    - M4 (regression): pass. `npm test` reports `validation --all passed: baseline plus 131 scenarios.` — no failing scenario, no exception, none skipped; 130 before this task. A3 predicted that a fixture passing only because its section absorbed the task list would surface here as a failure; none did. The reason is visible in the fixtures: nearly every one writes `## Invalidates` immediately above its task list with `- None.` as the section's first line, where the early return fires on the section's own line and the boundary never mattered.
    - Review:
      - Status: needs-review
      - Acceptance check: the five Covers scenarios are proven. Every assertion runs through `keel gate change-close` and `keel gate task-start` on real repositories rather than against `sectionBody()` directly — that is D6, and it is the point: what #71 costs an author is what the gate prints, and the red half reproduced that exact sentence from the unfixed tree before the helper existed. Both readers are proven, not only the reported one; the Invalidates half carried the same silent false negative (0 problems where the tail returns 1) and nobody had reported it. What is *not* proven is `The tail position is unchanged` as authored — see Findings and Blocker.
      - Scope check: `git status --short` lists exactly `scripts/validate_plugin.py` and `src/core/gates.js` — the two Touch entries — plus this change's own untracked `tasks.md`, which is the record-write layer. No path outside Touch. Every edit went through the file tools the write guard can see; nothing was written by shell redirection or heredoc. The one shell write was a temporary `git stash push -- src/core/gates.js` used to measure the red half, popped, leaving `src/core/gates.js` byte-identical.
      - Findings: one. D5's premise is false as measured, and it costs a tail-position verdict. D5 replaces the heading test `/^##\s+/m` with `parseTasks()`'s `/^\s*##\s/`, on the stated ground that "the difference is only that one tolerates leading whitespace." The tolerance is not cosmetic: it ends the section at an indented `##` line, and every entry after that line is then dropped without being read. Measured on the same repository, section in the **tail**, an `- I2:` with no closure sitting after a `  ## …` line inside the section — unfixed tree: refused, `invalidation-closure: I2 lacks an updating task, a durable owner, or a discard rationale.` Fixed tree: no problem at all. That is a verdict change in the tail position, which Stop Rule 2 names, and it is a *new instance of the failure class this change exists to remove* — a declaration skipped in silence. Durable owner: https://github.com/TanglmChris/keel/issues/71
    - Blocker: Stop Rule 2 fired — "Stop if the tail position's verdict, code, or message changes for any input" — and the decision that clears it is the owner's. Three repairs are defensible and the repository supports more than one. (a) Drop D5: keep `/^##\s+/` for the section boundary, which preserves every tail verdict exactly and still fixes #71, since the task half is what fixes it — at the cost of two heading spellings, which D5 exists to prevent. (b) Keep D5: accept the silent drop as consistent with the archived `2026-07-28-the-gate-reads-what-it-promises` D1, which chose `^\s*##\s` deliberately for task bodies. The asymmetry that makes this uncomfortable is that a dropped *task field* surfaces as a refusal, while a dropped *section entry* surfaces as silence. (c) Make the shared rule stricter in both places, changing `parseTasks()` too — which serves this change's purpose best and reaches `src/core/task-contract.js`, outside this task's Touch and outside the change's Impact. Recommend (a) for this change and (c) as its own change: declining to widen a boundary this change never needed to touch is the null action, and the parity D5 wants is worth having in the direction that drops nothing. The tree is left implementing D5 as authored so the trade-off is visible in the diff rather than described.
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [ ] 2.1 Release 5.22.0
  - Covers:
    - E6 — a reader of the release notes learns that section position stopped mattering, and which shape that passed before now fails
    - I1 — the version markers this change makes stale
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
    - openspec/specs/keel-task-capsule/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.22.0
    - M2: `keel/CHANGELOG.md` carries a 5.22.0 entry naming both failure modes, stating that a section may now sit anywhere in tasks.md, and recording that an unclosed entry a task's `- none` line had been silently closing is now refused
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-section-ends-where-the-tasks-begin --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - M4: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "version=5.21.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.21.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: An author who places `## Expectation Coverage` or `## Invalidates` anywhere but the file's tail gets the verdict the section's content earns, not one the position produced. Covered by: 1.1
- E2: An entry with no closure is never passed silently because a line inside a task body looked like the section's `- None.`. Covered by: 1.1
- E3: An `E<n>` a task declares under its own `Covers` is never judged as a coverage entry. Covered by: 1.1
- E4: Both readers take the boundary from one computation, so the repair cannot survive in the reader nobody reported. Covered by: 1.1
- E5: The tail layout every archived change uses returns the same verdicts, codes, and messages it returns today. Covered by: 1.1
- E6: A reader of the release notes learns that section position stopped mattering, and which previously-passing shape now fails. Covered by: 2.1
