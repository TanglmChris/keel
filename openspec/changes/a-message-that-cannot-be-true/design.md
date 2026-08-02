## Context

Keel's checks are worth reading because they are local, deterministic, and reproducible. What they *say* when they fire is a separate property, and nothing enforces it. A check can be perfectly correct about whether to fail and still describe the wrong failure — and a reader acting on that sentence goes to a place with no problem in it, which costs more than no message at all.

Three shipped surfaces state something the reader cannot act on. In every one, the true statement had no form available: the Review had no marker for a fixed finding, the assertion had one message slot for several failures, and the guard had one denial for two different manifest states.

## Goals / Non-Goals

**Goals:**
- Every disposition a finding can actually have is writable, so no author has to record a repair as a dismissal.
- The count of one-message-many-failures assertion sites is visible and can only go down.
- A refusal names an action that resolves the state it is refusing.

**Non-Goals:**
- No judgment of whether a *particular* sentence misleads. That needs a model and stays in `keel-review-checklist`. What is added here is a count, not a verdict.
- No mass rewrite of the 75 existing sites. This change records the number and adds nothing to it.
- The guard does not stop failing closed. A stale manifest still denies; only what it says changes.

## Decisions

**F1** — The Findings ownership requirement is written three times and applied differently in one of them. `openspec/specs/keel-core-gates/spec.md:47` reads "**WHEN** Review identifies an *unresolved* finding"; `src/skills/keel-review-checklist/SKILL.md:35` reads "each *unresolved* finding with a durable owner"; `src/core/gates.js:352` `findingOwnerIsDurable` is called for every Findings value that is not `none`. *Basis:* read all three.

**F2** — Measured live in 5.11.0 task 1.4: the Findings text "Closed here; no follow-up is owed" produced `finding-owner` and refused the task. Nothing but a `Discard reason:`, a tracker URL, or an existing path gets past it, so the recorded disposition for a fix was `Discard reason:`. *Basis:* the refusal happened during that task and its wording is in the archived tasks.md.

**F3** — `## Invalidates` already carries the state Findings lacks. `- I<n>: …` is closed by `Updated by:` naming tasks *of this change*, by a `Durable owner:`, or by a `Discard reason:` — three states, where Findings has two. *Basis:* `src/core/gates.js:799`, and AGENTS.md's Completion gates section.

**F4** — Assertion shapes in `scripts/validate_plugin.py`, measured 2026-08-02 by AST: 1069 `if` statements whose body is one or more `report(...)` calls plus exactly one `return`; 287 of those have an `or` test; **75** have at least one membership disjunct (`in`/`not in`) and at least one disjunct that is not. All three defects issue #43 records fall inside the 75. *Basis:* parsed the file and counted.

**F5** — The write guard denies against an archived change. `taskIsChecked` reads `openspec/changes/<change>/tasks.md`; after `openspec archive` that path does not exist, the read throws, the function returns `false` ("not checked"), and control reaches the Touch comparison. *Basis:* measured at the start of this change — the first write was refused against `the-name-is-not-the-thing#2.1`, whose directory had moved to `openspec/changes/archive/2026-08-01-the-name-is-not-the-thing/` one commit earlier.

**F6** — `keel guard status` classifies the same state correctly, reporting `Status: drifted` and "Guarded task … no longer resolves". It compiles the capsule to know that; the hook cannot afford to and must not guess. *Basis:* ran both against the same manifest.

**D1** — **A finding may be recorded as resolved in the task that found it, and that disposition must carry evidence.** *Basis:* F1–F3. The requirement the gate enforces becomes the one the spec and the skill already state — *unresolved* findings need an owner. The evidence requirement is what keeps the third state from being a hole: a bare "resolved" marker would let any finding out of the check by asserting its own conclusion, which is strictly weaker than the two states that exist. Requiring evidence also states the criterion honestly — if no check proves it, the fix is not proved, and the honest disposition is still an owner or a discard.

**D2** — **The accepted evidence is an `M<n>` check label or an existing repo-relative path.** *Basis:* both are shape-checkable offline with machinery the gate already has — `M<n>` is the capsule's own vocabulary for "the check that proves this", and path existence is what `durableOwnerVerdict` already verifies. A URL is deliberately *not* accepted here: a tracker reference means someone else will do it later, which is the durable-owner state, not this one.

**D3** — **The marker is `Resolved here:`.** *Basis:* it names the state rather than the action, matching `Durable owner:` and `Discard reason:`; "here" is the task, which is the only scope the gate can check. `Closed here:` was rejected because "closed" is the vocabulary GitHub applies to the issues that hold *deferred* work, and the two states would read alike in the same sentence.

**D4** — **The three dispositions get a stated criterion, in the checklist and in AGENTS.md.** *Basis:* the gap that produced F2 was not a missing marker alone — it was that an author reaching the gate picks whichever marker passes. The criterion is: fixed in this task with a check that proves it → `Resolved here:`; still real and someone must do it → `Durable owner:`; considered and deliberately not doing it → `Discard reason:`. Absent the criterion, the new marker becomes the easiest exit and the other two decay.

**D5** — **The assertion shape is recorded as a count, not enforced as a lint.** *Basis:* F4. A pass/fail lint cannot ship against 75 pre-existing sites, and the alternatives are worse: rewriting 75 assertions in the file every other correctness claim rests on is a large blind diff, and exempting them by annotation writes the debt into the source without bounding it. A recorded count fails when a new site appears and names it, which is the edit-time signal issue #43 asks for, and it is the same mechanism the suite already uses for its scenario count.

**D6** — **The count fails in both directions.** *Basis:* a number that only rises-check would silently become false the first time someone fixes a site, and a false number is what this whole change is about. Fixing sites is expected; lowering the constant is one line, and the failure says so.

**D7** — **The rule is the simple one: an `or` test with at least one membership disjunct and at least one non-membership disjunct.** *Basis:* a heuristic list of "verdict guard" patterns (`returncode`, `is None`, `len(`, `.get("status")`) was measured first and returned 68. The simple rule returns 75, covers every site the heuristic did that matters, and can be restated exactly by the next reader — a rule nobody can reimplement is a number nobody can check.

**D8** — **The guard distinguishes a vanished change from an unmatched task, and refuses the first by name.** *Basis:* F5 and F6. `fs.existsSync` on the change directory is one syscall in a hook that already reads a file from that directory, so the cost is nil. The two states are genuinely different: an unmatched task id inside a live tasks.md is the parse miss the current comment correctly refuses to guess about, while a directory that is not there is a fact. It still denies — allowing would make `openspec archive` silently disable the guard — and it names `keel guard clear`, which is the action that resolves it.

## Risks / Trade-offs

- **The count is a number in a file that must stay true.** Same failure mode as the scenario count, same mitigation: it is asserted in both directions, so a stale one fails rather than lying.
- **`Resolved here:` could become the easy exit.** D1's evidence requirement and D4's criterion are the mitigation; the residual risk is an author citing an `M<n>` that does not actually cover the finding, which is a semantic judgment and stays with `keel-review-checklist`.
- **The rule counts sites that are not defects.** Deliberate. It is a debt counter, not a verdict — the message says so, and the review still decides whether any given sentence misleads.
- **One valid disposition satisfies a Findings block that holds several findings.** `Findings` is free prose and the gate cannot split it, so a block containing a resolved finding and an unresolved one passes on the resolved one. This is not introduced here: one valid `Durable owner:` has satisfied a block with a second unowned finding since the owner forms shipped. Making it strict requires one-finding-per-line Findings, which is a protocol change with its own cost — every existing Review would have to be reshaped — and it is recorded rather than done. What bounds the risk today is that the review reads the whole block; what would fix it is structure, not another marker.

## Hidden Knowledge / Assumptions

**A1** — The 75 sites include correct assertions whose message genuinely covers every disjunct. *Basis:* inspected a sample. *Owner:* the scenario's own wording states that the count is a bound on a shape and not a defect count, so the next reader does not read 75 as 75 bugs.

**A2** — `openspec archive` moves the change directory rather than leaving a marker behind. *Basis:* verified — `openspec/changes/the-name-is-not-the-thing/` is absent and `openspec/changes/archive/2026-08-01-the-name-is-not-the-thing/` exists. *Owner:* the guard scenario archives a real change and drives the hook, rather than deleting a directory to simulate it.

## Coupled Iteration Contract

Not required. No task in this change regenerates an artifact that must be verified together with its source.
