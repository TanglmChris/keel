## Context

`specAuthority()` resolves a `Covers` reference against a capability's spec. It has four exits: a resolved authority, an ambiguity, a named scenario miss, and a terminal `return` that says only that the reference could not be resolved. The first three name what they read. The fourth does not, and it is the one an author reaches by making the most natural mistake in the notation — writing `capability / scenario` because the scenario is the thing they actually mean to cover.

The function is holding the answer while it refuses. It has already opened the spec, already parsed its headings, and the name the author typed is very often a heading in the file it just read. Nothing about the fix is a new capability; it is spending facts already in hand.

## Goals / Non-Goals

**Goals:**
- An unresolved reference into an existing capability states which segment failed.
- A second segment that names a Scenario is reported as one, with the Requirement it belongs to and the corrected reference.
- A capability that names no spec at all is distinguished from one whose spec lacks the name.
- What the gate accepts is provably unchanged.

**Non-Goals:**
- `criticalAuthority()` and #49 item 1 (Q1). Neighbouring function, different mechanism, and a material acceptance question underneath it.
- #49 item 2, the `Findings` durable-owner imperative position, and the two block-field parsing supplements. Separate mechanisms, separately owned on the issue.
- Heuristic matching. A near-miss on a Requirement name is still a refusal; `Ambiguous or missing reference fails` requires that Keel not match a similar heading heuristically, and reporting what a spec contains is not matching it.
- Changing the `unresolved-covers` code.

## Decisions

- **F1** — reproduced 2026-08-02 at 5.20.0 in a scratch repository, five references against one spec. `demo-cap / A published store passes the pinned validator` (a real Scenario in segment 2) returns `Covers reference could not be resolved: …` and nothing more. `demo-cap / No such requirement / Something else happens` returns the same sentence. `demo-cap / The store validates itself / No such scenario` returns `Missing Covers scenario: …`. `demo-cap / The store validates itself / a / b` returns the full hierarchy sentence. `demo-cap / The store validates itself` passes. *Basis: direct execution of `node bin/keel.js gate task-start --json`.*
- **F2** — the terminal `return` is `src/core/task-contract.js:601-608`. It appends `collisionHint()` and otherwise reports the reference alone. The hierarchy sentence lives at `:536-540`, guarded by `parts.length > 3`, so no path with 2 or 3 segments can reach it. *Basis: the source at 5.20.0.*
- **F3** — `specCandidatePaths()` (`:473`) returns two paths: the change's own delta spec, then the published spec. `specAuthority()` loops them and `continue`s when the requirement is absent, so the terminal return means *every* candidate was tried. A diagnostic naming what was read must therefore describe the candidates that exist, not one file. *Basis: the source at 5.20.0.*
- **F4** — `headingSections()` (`:449`) already extracts `### Requirement:` and, given a requirement's content, `#### Scenario:`. Both parses the new diagnostic needs are the same two calls the resolving path makes. *Basis: the source, and the resolving path at `:551` and `:569`.*
- **F5** — this is the same class as the fix already shipped for over-segmentation. `Over-segmented capability reference does not degrade silently` and `Separator collision is named` are both published requirements about this function saying what it read. The gap is that they were written for the two cases that had been reported. *Basis: `openspec/specs/keel-task-capsule/spec.md:92-100`.*
- **F6** — the accepted shape for a critical statement is `^\s*D2\s*[—-]\s*(.+?)$` (`:631`), a line beginning with the bare token. Measured 2026-08-02 at 5.20.0 across four design.md shapes: `- **D2** — text`, `**D2** — text`, and `- D2 — text` all return `Missing Covers critical statement: D2`, identical to a design.md with no `D2` in it. Every design.md in this repository writes `- **F1** — …` or `**F1** — …`; none uses the accepted shape. The only fixture exercising it (`scripts/validate_plugin.py:1448`) writes `D1 — …` unbulleted, which is why the suite is green. *Basis: direct execution, and `grep` over the eleven archived design.md files.*

- **D1** — the terminal return branches on what the candidate specs actually hold, in three cases: no candidate spec exists; a candidate exists and the name matches a Scenario; a candidate exists and the name matches nothing. Each names the fact it found. The hierarchy sentence is reused verbatim from `:536-540` rather than rephrased, because an author who has read one of these should recognize the other. *Basis: F2, F4, F5.*
- **D2** — the Scenario case spells the corrected reference — `capability / <parent requirement> / <name>` — rather than only stating the rule. The author's error is a missing middle segment whose value the diagnostic now knows; printing the rule and withholding the value would repeat the shape of the defect. *Basis: F1 — the reporter had the rule available on #49's item and still spent a round.*
- **D3** — a Scenario name matching in more than one Requirement is reported as the Requirements it appears under, without a corrected reference. There is no single correction to offer, and inventing one would send the author to a reference that fails as ambiguous. *Basis: D2's reasoning applied where its precondition does not hold.*
- **D4** — the `unresolved-covers` code is unchanged and every case still fails. The verdict is the same — the reference does not resolve — and only the explanation changes. A new code would make consumers keying on `unresolved-covers` miss these cases. This follows `missing-field`, which kept its code when it gained the named token in 5.20.0. *Basis: F5, and the 5.20.0 precedent in the archived change `a-field-the-schema-does-not-have`.*
- **D5** — verification runs through `keel gate task-start` on real repositories, not by calling `specAuthority()` directly. The reported cost is what an author sees at the gate, and a unit test of the branch would assert the half that was never expensive. *Basis: F1 — the reproduction is already at that level.*
- **D6** — the scenario asserts that a resolvable reference still resolves and that the gate still returns `fail` for each new case. Reading more of the spec on the failure path is the direction in which a refusal could accidentally become a pass; that is asserted rather than argued. *Basis: the same bound the 5.20.0 suppression carried.*

## Hidden Knowledge / Assumptions

- **A1** — a spec whose `#### Scenario:` headings sit outside any `### Requirement:` is malformed, and the new read returns no match for it rather than throwing. `headingSections()` returns an empty list for content with no match, so the branch degrades to the third case. *Basis: F4. Owner: this change — the failure mode if wrong is the generic sentence, which is today's behavior.*
- **A2** — no consumer outside this repository parses the text of the `unresolved-covers` message. `grep` over `src`, `plugins`, `scripts`, and `openspec` finds the phrase only at its emission site and in the suite's own assertions. *Basis: that grep at 5.20.0. Owner: this change — the code is unchanged, so a consumer keying on the code is unaffected.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- The diagnostic prints spec heading text into an error message, so a long Requirement name makes a long sentence. That is the same trade the separator-collision hint already makes, and the name is the actionable part.
- Reading the spec a second time on the failure path costs one parse of a file already in memory, on a path that is about to refuse. Not measured, because the alternative is the author reading the file themselves.

## Open Questions

- **Q1** — should `criticalAuthority()` accept the design.md shapes this repository actually writes? F6 measures that it accepts only a bare token at line start, and that no design.md here is written that way, so a bare `D<n>` in `Covers` fails against every design document the project has produced — reported as `Missing`, which sends the author to add something already present. The escape hatch is worse than the defect: adding a trailing gloss makes the entry pass as an unlinked `legacy-task-reference`, so the authority link is silently dropped, and that is what this repository's own tasks.md files do. Widening the accepted shape changes what the gate accepts; leaving it and only fixing the wording institutionalizes a shape nobody writes. Both are user-visible, so alignment surfaced this rather than resolving it. **This question opens no `Covers` entry and blocks no task in this change** — nothing here touches `criticalAuthority()`, and D1's three cases are correct whichever way Q1 is answered. *Durable owner: https://github.com/TanglmChris/keel/issues/49 — recorded there with the four-shape measurement, so a later run authoring against item 1 finds it before writing either fix.*

## Alignment

Ran `keel-align-expectations` before tasks finalized. No `keel/lenses/` directory exists and the declared precedent store `../decision-precedents` is absent, so the domain-agnostic path applied and no precedent informed any decision here.

Quick path for the work itself: the request, the reproduction, and the intended observable outcome agree; every change is to message text on a path that refuses either way, and the reference set that resolves is unchanged. Deep path fired once, on Q1 — a contradiction between what #49 item 1 assumes the parser wants and what the repository's own design documents contain.

Candidate expectations inferred and **not** taken as authority: that a near-miss Requirement name should be suggested by edit distance (rejected in Non-Goals — the published requirement forbids heuristic heading matching), and that the diagnostic should list every Requirement the spec declares (rejected — for a large spec that is a wall of text, and D2 gives the one name that is actionable). Neither is user-accepted, so neither becomes a requirement.
