## Context

`durableOwnerVerdict()` in `src/core/gates.js` classifies a declared owner: a tracker URL passes on shape, `keel/HANDOFF.md` is refused by name, and a repo-relative path passes when `fs.existsSync` finds it. `resolutionEvidenceVerdict()` accepts a path the same way for `Resolved here:`. Three readers share the first function — Review `Findings`, `## Invalidates`, and `## Expectation Coverage` — which is what keeps a form accepted in one place from being refused in another.

The existence check is the gate's one real guarantee, and for one class of path it expires by construction. Archiving moves `openspec/changes/<name>/` to `openspec/changes/archive/<date>-<name>/`, so every pointer into the change's own directory is true when written and false immediately afterwards.

## Goals / Non-Goals

**Goals:**
- Refuse the pointer class that is guaranteed to break, at the moment it is written.
- Say what each accepted form is actually worth, so the author is not left believing a check ran that did not.

**Non-Goals:**
- Fetching a tracker reference, at archive or anywhere else. A gate that reaches the network stops being local, offline, and deterministic.
- Rewriting pointers inside archived artifacts. Archived evidence is a record of what was written; editing it to stay true would falsify the record.
- Refusing a path into a *different* live change directory.
- A `keel --doctor` recheck of archived pointers (issue #100's direction 2). It is a reasonable separate change and reports a fact this one prevents.

## Decisions

F1 — Corpus measurement, this repository's 35 archived changes' `tasks.md` and `design.md`, 2026-09-05 against 5.42.0: 10 declarations name a path inside a live change directory — 8 `Durable owner:` and 2 `Resolved here:`. All 10 are dead. All 10 point at the change that wrote them; **zero** point at a different change. Basis: scripted extraction using the gate's own `declaredPath()` shape, with each path's slug compared against its containing archive directory's slug.

F2 — The field report measured the same shape independently in `chip_sec_flow_v2`: 36 pointers into `openspec/changes/`, 35 dead, the survivor being the one change not yet archived. Basis: issue #100, 2026-08-17.

F3 — The gates refuse an archived change rather than recompiling one, so no existing declaration in this repository is affected by a stricter rule. Basis: the resident protocol's Completion gates section, and every change carrying one of F1's 10 pointers is archived.

D1 — A `Durable owner:` or `Resolved here:` naming a path inside the change's own directory is refused, with its own reason rather than folded into `missing`. Basis: F1 and F2 — the pointer is not merely likely to break, it breaks in the next step of the workflow that is refusing it. The existing requirement already draws this line for `keel/HANDOFF.md`: existence is necessary, not sufficient.

D2 — A path inside a *different* live change directory stays accepted. Basis: the resident protocol names "a new OpenSpec change" as a legitimate follow-up owner, F1 measures zero pointers of that shape, and refusing a form the protocol endorses on zero evidence would trade a real defect for an invented one.

D3 — The rule is stated on the change's directory, not on the archive date or the file inside it. Basis: what makes the pointer break is that the directory moves, and every file under it moves together; naming `design.md` specifically would refuse one spelling of one instance of the class.

D4 — `DURABLE_OWNER_FORMS`, the single sentence every refusal quotes — including the new one, which has to name what to write instead — states what each form is worth: a path is checked for existence when it is cited and not re-checked afterwards, and a tracker reference is accepted on shape alone because gates never fetch. Basis: issue #100's direction 4. The gate cannot make the tracker guarantee true, and the failure worth fixing is that it currently reads as though it had.

D5 — The change name reaches the verdict through the existing `selection.change`, threaded as a parameter rather than re-derived from the path being judged. Basis: a path judged against itself cannot tell a self-pointer from a pointer at another change, which is exactly the distinction D2 rests on.

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **A stricter gate refuses a declaration that used to pass.** That is the point, and the direction is toward the truth: what stops passing is exactly what stops being true one step later. F3 bounds the blast radius to changes authored after this ships.
- **The natural landing place goes away.** An author who wanted to write the follow-up down next to the work now has to name a tracker reference, an archived path, or a ledger the repository keeps. The refusal names all three rather than leaving the author to find them, which is what the existing requirement already demands of every refusal here.
- **The tracker branch is still unchecked.** This change makes that legible instead of fixing it, deliberately: fixing it would cost the offline property the whole verdict rests on. `keel-review-checklist` already carries the semantic half — a cited URL must already carry the content it claims to hold — and that stays where a model can judge it.

## Open Questions

None.
