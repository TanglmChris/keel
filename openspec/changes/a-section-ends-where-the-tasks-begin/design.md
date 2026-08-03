## Context

Two change-level sections in tasks.md are read by two functions in `src/core/gates.js`. Each finds its heading, then takes everything up to the next `## ` heading as the section body. In a Markdown document with headings throughout, that is the right bound. A tasks.md is not that document: its dominant structure is a list, and the thing that follows a change-level section is almost always a task item.

The repository has already met this exact problem from the other side. When a change-level section sat *after* the last task, that section's lines were appended to the last task's open field — its `Evidence`, in every shipped template — and a token quoted in the section made the task's Evidence non-concrete. The fix ended a task's body at the next task **or** the next heading, and shipped as a requirement that also says every consumer of a task's extent must use that one boundary. The section readers were not brought along, and they hold the mirror half of the same defect.

## Goals / Non-Goals

**Goals:**
- A change-level section's extent is the section the author wrote, wherever it sits in the file.
- A declaration is never skipped because a line inside a task body looked like its `- None.`.
- Both readers get the fix, through one computation rather than two that agree today.
- The tail position — the shape every archived change uses — is provably unchanged.

**Non-Goals:**
- Requiring or documenting a section position. D2.
- Changing what closes an entry. `Covered by:`, `Updated by:`, `Durable owner:`, and `Discard reason:` are untouched, as is every diagnostic code and message.
- Tightening the entry patterns to demand top-level indentation. #71 offers this as an alternative; D3.
- #65 and #51. Different mechanisms, separately owned on their issues.

## Decisions

- **F1** — reproduced 2026-08-02 at 5.21.0 in a scratch repository, one tasks.md and one edit. With `## Expectation Coverage` as the file's last section, `keel gate change-close --change demo --action sync` returns `pass`. With the identical section moved above the task list, it returns `fail`: `E1 lacks behavior coverage, durable owner, or discard rationale.` for an `E1` closed by `Covered by: 1.1`. The entry the gate actually judged is the `- E1: public behavior` line the task declares under `Covers`. *Basis: direct execution of `node bin/keel.js`.*
- **F2** — the same slicing also produces a silent false negative, which #71 does not report. In the same repository, with the section above the task list, a task body carrying `    - none` as a field entry, and `- E1:` given **no closure at all**, `change-close` returns `pass`. The `- None.` early return (`gates.js:1029`) matched inside a task body and returned an empty problem list for the whole section. *Basis: direct execution.*
- **F3** — the two slices are duplicated, not merely similar. `invalidationProblems()` at `gates.js:924-925` and `expectationProblems()` at `gates.js:1027-1028` are character-identical, and so are the `- None.` early return and the shape of the entry pattern beneath each. *Basis: the source at 5.21.0.*
- **F4** — the mirror boundary is already implemented and already required. `parseTasks()` (`src/core/task-contract.js:76-91`) ends a task's body at the next task or the next `##` heading, whichever comes first; `keel-task-capsule / A task body ends at the next task or the next heading` states that boundary and adds "Every consumer of a task's extent MUST use that same boundary rather than recomputing one." *Basis: the source, and `openspec/specs/keel-task-capsule/spec.md:313-333`.*
- **F5** — the position that avoids the defect is stated nowhere. `grep` over `AGENTS.md`, both schema copies, both tasks-template copies, and both diagnostics finds no requirement, recommendation, or mention of where either section goes. Across the archive it is nonetheless uniform: 21 of 21 tasks.md put `## Invalidates` and `## Expectation Coverage` within the last 25 lines. *Basis: that grep, and `grep -n "^## Invalidates"` over `openspec/changes/archive/*/tasks.md`.*
- **F6** — no archived change flips verdict under the new boundary. 0 of 148 archived task checkboxes are indented; 0 of 256 `E<n>` entries and 0 of 123 `I<n>` entries are indented; exactly one archived tasks.md carries a standalone `- none` inside a task body — `2026-08-01-declare-who-runs-the-task:104`, the `Touch` of a `repo-action` task — and both of its sections sit after that line, so the old slicing never reached it. *Basis: `grep` over `openspec/changes/archive/*/tasks.md`.*
- **F7** — both readers already receive the parsed task array. `invalidationProblems(repo, selection.content, selection.tasks)` at `gates.js:246` and `expectationProblems(...)` at `gates.js:1178` are passed the result of `parseTasks(content)`, whose entries carry `line`. *Basis: the source at 5.21.0.*

- **D1** — one `sectionBody()` helper computes both section bodies, ending at the next `##` heading or the next task, whichever comes first. Fixing only `expectationProblems()` — which is what #71 reports — would leave F3's identical lines in the other reader; `A declared path is extracted by where it ends` already records that a defect repaired in one reader and left in the others is how a fixed defect reappears. *Basis: F3, F4.*
- **D2** — section position becomes irrelevant, not required. #71 offers both endings. Requiring the tail would refuse a layout that nothing has ever documented as wrong (F5), would need a new diagnostic to be honest, and buys nothing: what the checks judge is the section's content. Cancelling an undocumented rule costs no author anything, because no author was following it deliberately. *Basis: F5.*
- **D3** — the entry patterns are left alone. #71's second candidate — require `E<n>` at the section's top-level indentation — would also fix F1, but not F2, whose `- none` is what an indented pattern would still have to exclude by position anyway. Two mechanisms where one suffices is F3 repeating itself, and the indentation rule would newly refuse an author who indents a real entry. *Basis: F1, F2, F6.*
- **D4** — the boundary tests each line against the task lines already parsed, rather than re-matching a checkbox pattern. A second pattern that must agree with `parseTasks()` is exactly the duplication F3 describes; identity against `line` cannot drift. *Basis: F7.*
- **D5** — the heading half adopts `parseTasks()`'s `/^\s*##\s/` in place of `/^##\s+/m`, so the two boundaries are one rule rather than two that resemble each other. Both match every heading either has ever seen; the difference is only that one tolerates leading whitespace. *Basis: F4 — the published requirement says "that same boundary", and two spellings are not one boundary.*
- **D6** — verification drives `keel gate change-close` and `keel gate task-start` on real repositories, asserting four cells per section: closed and unclosed, section-before-tasks and section-in-tail. The tail cells are the regression F6 argues for and are asserted rather than argued. A unit test of the slice would prove the half that was never in doubt. *Basis: F1, F2, F6.*

## Hidden Knowledge / Assumptions

- **A1** — no tasks.md nests a task checkbox inside a change-level section entry. 0 of 148 archived checkboxes are indented (F6), and `parseTasks()` already reads an indented `- [ ] 1.1 …` as a task, so such a line is a task by the repository's existing definition. *Basis: F6. Owner: this change — if wrong, the section ends early and its later entries are reported unclosed, which is a refusal an author can see, not a silent pass.*
- **A2** — nothing outside this repository parses the text of `expectation-closure` or `invalidation-closure`. Neither code nor message changes here, so a consumer keying on either is unaffected regardless. *Basis: the diff. Owner: this change.*
- **A3** — a suite scenario that passes today only because its section absorbed the task list is asserting something untrue, and is repaired at the assertion rather than by preserving the boundary. None is known to exist; the full run is what would surface one. *Basis: F6 covers the archive but not the fixtures. Owner: this change — the failure mode is a red suite, which is visible.*
