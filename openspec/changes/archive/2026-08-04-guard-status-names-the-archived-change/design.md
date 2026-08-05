## Context

`guardStatus()` in `src/core/guard.js` calls `loadTaskContract()` and, on `null`, reports authority drift with an instruction to reauthorize. `loadTaskContract()` returns `null` from two places for two unrelated reasons: the tasks file is not there, or the task id is not in it. One return value, two states, and only one of them has a reauthorization to perform.

The write guard hook already draws this line. It was taught to in 5.12.0, after the same conflation denied a write by naming a task inside an archived change and telling the reader to reauthorize it. The hook tests the change *directory* rather than the contract, because a directory that is not there is a fact it can establish without compiling anything.

This change carries that same test to the surface that describes the manifest, rather than the one that refuses a write.

## Goals / Non-Goals

**Goals:**

- `keel guard status` names the action that resolves the state it is reporting.
- An archived-change manifest and a task-id parse miss are distinguishable by a machine reader, not only by prose.
- The parse-miss path is provably unchanged — message, code, and status.
- Both surfaces answer "is the change gone?" by testing the same object, so the next repair cannot land in one and miss the other.

**Non-Goals:**

- Relaxing fail-closed. F7 — the published requirement states it and the reason still holds.
- Changing the `drifted` status word, or any other status vocabulary. D2.
- Changing what `keel guard start` or `keel gate task-start` say about a change that is gone. D5.
- Making `keel guard status` search `openspec/changes/archive/` to report which archived directory the change became. D6.
- #52, #49, #65, #72. Different mechanisms, separately owned on their issues.

## Decisions

- **F1** — reproduced 2026-08-04 at 5.26.0 on the current tree, through the shipped CLI on one scratch repository. `guard start --change demo --task 1.1`, then the change directory relocated to `openspec/changes/archive/2026-08-04-demo`, then `guard status`: `Status: drifted` with `Problem: Guarded task demo#1.1 no longer resolves; reauthorize through \`keel gate task-start\` and \`keel guard start\`.` The directory restored with the task renumbered to `9.9` — a live change whose task id is absent — produces **byte-identical** output. *Basis: direct execution of `node bin/keel.js`.*
- **F2** — the advice is a dead end, not merely imprecise. Against the archived state: `keel gate task-start --change demo --task 1.1` returns `gate input error: missing OpenSpec tasks file: …/openspec/changes/demo/tasks.md`, and `keel guard start --change demo --task 1.1` returns `guard input error: task demo#1.1 does not exist`. Both are true statements and neither names `keel guard clear`, so a reader who follows the status message in order meets three commands and no exit. *Basis: direct execution against the F1 fixture.*
- **F3** — the hook already draws the line this surface does not. `plugins/keel/scripts/pretooluse-guard.js:208-217` tests `openspec/changes/<change>` for existence and denies with a message naming the missing directory and `keel guard clear`; its comment records that `keel guard status` "already classifies it as drifted", which is true of the status word and not of the advice under it. *Basis: the source at 5.26.0.*
- **F4** — the conflation is a single `null` from two causes. `loadTaskContract()` returns `null` at `src/core/task-contract.js:1090` when `openspec/changes/<change>/tasks.md` does not exist, and at `:1094` when no parsed task carries the id. The caller cannot recover which from the return value, which is why the hook tests the filesystem rather than the contract. *Basis: the source at 5.26.0.*
- **F5** — the status word is consumed, the problem code is not. `guardStatus(repo).status` is read at `src/core/capabilities.js:211` and interpolated into a capability evidence string; nothing else in `src/`, `bin/`, `plugins/`, or `scripts/` reads either field. `keel context` does not call it at all. So holding `drifted` fixed holds every other surface fixed, and a new problem code is a pure addition. *Basis: `grep` for `guardStatus`, `authority-drift`, and `"drifted"` across the tree.*
- **F6** — the reason this surface was skipped is written down. `openspec/changes/archive/2026-08-02-a-message-that-cannot-be-true/design.md:31` records F6 of that change: "`keel guard status` classifies the same state correctly, reporting `Status: drifted` and \"Guarded task … no longer resolves\". It compiles the capsule to know that; the hook cannot afford to and must not guess." The first clause is what a reader would act on and it is half right — the classification is correct, the instruction attached to it is not. A measurement of the word stood in for a measurement of the message. *Basis: that file.*
- **F7** — fail-closed is settled and stays. `openspec/specs/keel-touch-write-guard/spec.md:214`: "Keel MUST keep denying the write. Failing closed is what stops archiving a change from silently disabling the guard, so the outcome does not change — only what the refusal says." The cost this preserves is real — the first write after an archive needs `keel guard clear` — and the reason is that any automatic expiry makes `openspec archive` a silent off switch. *Basis: the published spec.*
- **F8** — the owner decided this on the issue, in the open. https://github.com/TanglmChris/keel/issues/56 records the decision on 2026-08-04: implement the discrimination under the `no longer resolves` criterion, keep the fail-closed stance unchanged, and change only what the message says. It also records the correction that made it necessary — an earlier comment claiming 5.12.0 had fixed this surface was reading the hook's three `keel guard clear` mentions and not `guardStatus()`. *Basis: the issue thread.*

- **D1** — `guardStatus()` tests `openspec/changes/<change>` for existence, the same object `pretooluse-guard.js` tests, and branches before the existing drift problem is constructed. Testing the same object is the point: two surfaces that answered "is the change gone?" by different means would eventually disagree about a state a user is looking at from both. *Basis: F3, F4.*
- **D2** — the status word stays `drifted` and only the problem changes. This is F8's instruction read literally, and F5 is why it costs nothing to obey: a new word would rewrite a capability evidence string for a state whose classification was never wrong. The manifest *has* drifted from the repository; what was missing is which way. *Basis: F5, F8.*
- **D3** — the new problem carries code `stale-manifest`, distinct from `authority-drift`. Two states that need different actions must be separable by a `--json` reader without matching on prose, and this is the field that separates them. The word matches the hook's own wording for the same state. *Basis: F1, F3.*
- **D4** — a change directory that exists while its `tasks.md` does not keeps the existing message. That is a third state — a live change mid-authoring — and reauthorizing it after writing its tasks file is genuinely the way out. Testing the directory rather than the tasks file is what keeps this state on the old path, and it is why D1 tests the directory even though `loadTaskContract` reads the file. *Basis: F4.*
- **D5** — `keel guard start` and `keel gate task-start` are not touched. Their messages are true (F2) and each names the specific thing it could not find; the defect is that a third surface sends the reader to them. Rewording two commands that are correct, to compensate for one that is not, is the shape that leaves three messages to keep in agreement. *Basis: F2.*
- **D6** — the message says the directory no longer exists rather than naming the archived directory it became. Reporting "archived as `2026-08-04-demo`" means searching `openspec/changes/archive/` and guessing at a suffix match, which invents a fact for the case where the change was simply deleted. The hook says it the same way, and the action is identical either way. *Basis: F3.*
- **D7** — verification drives the shipped CLI on scratch repositories in both states and asserts the pair is no longer identical, rather than unit-testing the branch. The defect was two states sharing an output; the check has to be able to see two outputs. The parse-miss cell is a regression cell — it asserts an unchanged message — and is therefore compared against the recorded 5.26.0 text rather than against the other cell. *Basis: F1.*

## Assumptions

Candidate expectations nobody stated, labelled rather than assumed silently. Each is accepted on repository authority named beside it; none is accepted on silence.

- **A1** — a new problem code is additive rather than an interface change. Accepted on F5: no code in this repository reads a guard problem code, and an external `--json` consumer matching `authority-drift` keeps every occurrence it had except the one that was telling it the wrong thing. Had F5 found a consumer, this would have been a question.
- **A2** — the status message mirrors the hook's wording for the same state instead of a second phrasing. Two surfaces describing one fact in two vocabularies is the drift D1 exists to prevent, one level up. Accepted on F3.
- **A3** — the parse-miss cell is a check that passes before and after this change, which is also what a broken check looks like, so it is proven able to fail by mutation rather than accepted green. *Precedent applied: `an-assertion-that-never-failed-proves-nothing` — without it this cell would have been left as a passing comparison.*
- **A4** — the requirement keeps its title, `A manifest whose change is gone is refused as stale`, though `keel guard status` reports rather than refuses. A rename is a separate delta operation for a heading whose subject is unchanged, and the `Covers` references of the archived change that introduced it point at this name.

## Risks / Trade-offs

- **A reader still pays for fail-closed.** Nothing here removes the `keel guard clear` step after an archive; F7 keeps it deliberately. The improvement is that the step is now named. Accepted, and recorded on the issue as the owner's decision.
- **A `--json` consumer matching on `authority-drift` sees one fewer occurrence.** F5 says there is no such consumer in this repository. External consumers get a new code rather than a changed one, which is the additive direction.
- **The two surfaces still hold two copies of the directory test.** The hook is deliberately standalone — it requires only node builtins, so it can run before the package is installed — and sharing a module with `src/core/` would give that up for four lines. The spec scenario that names both surfaces is what keeps them in agreement instead.
