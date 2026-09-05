## Context

`OPENSPEC_OVERLAY_ACTIONS` in `bin/keel.js` is the managed set: `propose`, `apply`, `archive`, `sync`. Two consumers read it — `openspecOverlaySurfacesForTarget()`, which enumerates the files each action's overlay is written to, and `overlayActionLabel()`, which joins the set minus `propose` for the doctor's command-surface line.

The spec that defines this capability opens with a Purpose and a requirement written when the set was two actions. `propose` and `sync` arrived later as new requirements appended further down the same file, so the file's summary and its contents disagree, and nothing notices.

The existing requirement "Every overlay summary names the managed action set" already fixed this shape once, for the runtime summaries: it made every reported label derived and added a check that fails when one drifts. The spec's own statement of the set was not part of that.

## Goals / Non-Goals

**Goals:**
- Make the top of the overlay spec say what the file below it covers.
- Make that agreement checked rather than reread, keyed off the same constant the runtime derives from.

**Non-Goals:**
- Changing `OPENSPEC_OVERLAY_ACTIONS`, any overlay content, or any installed behavior. This change reads the code and edits prose.
- A file-wide scan for action words. Three correct spellings in the specs would fail one.
- Extending the check to every spec. The invariant is specific: this capability's summary names this capability's managed set.

## Decisions

F1 — Drift measurement across `openspec/specs/` (2026-09-05, 5.43.0): 9 statements name a proper subset of the managed set, all in `keel-openspec-surface-overlay/spec.md` — Purpose (line 3), the opening requirement's name (5) and body (7), its three per-target scenario names (9, 15, 22), and the two install/refresh scenarios (34, 41, 42) that say `apply/archive/sync` about behavior covering `propose` as well. Basis: scripted enumeration of slash-joined and "X and Y" action spellings, each classified against the code's set and read in context.

F2 — Three spellings match the same pattern and are correct. `apply/archive/sync` in `keel-target-surface-diagnostics` (115, 119, 121) is `overlayActionLabel()`'s output, which excludes `propose` deliberately. `sync/archive decisions` (64, 69) names what the current agent owns, not what Keel overlays. `authoring/apply/archive/sync` (121) names all four, with `propose` spelled as authoring. Basis: same enumeration, each occurrence read in context against the code path it describes.

F3 — OpenSpec 1.6.0's change parser recognizes four delta operations, all Requirement-scoped: `ADDED`, `MODIFIED`, `REMOVED`, `RENAMED Requirements`. A spec's `## Purpose` is written once by `specs-apply.js` when a capability is created, as `TBD - created by archiving change <name>. Update Purpose after archive.`, and no operation reaches it afterwards. Basis: `node_modules/@fission-ai/openspec/dist/core/parsers/change-parser.js` and `.../specs-apply.js`, read 2026-09-05. This is why the Purpose line survived issue #79's sweep: no change was going to touch it.

D1 — The check asserts two named locations, not a scan. The Purpose line and the requirement that states the managed overlay must each name every action in `OPENSPEC_OVERLAY_ACTIONS`. Basis: F2 — a scan would refuse three correct statements, and a check that cannot tell a correct statement from a drifted one costs more than the drift, which is the argument issue #58 established in this repository and #65 applied again.

D2 — The managed set is read from `bin/keel.js` rather than restated in the check. Basis: a literal in the check is the same defect one layer out; the existing summary requirement already refuses a literal for the same reason.

D3 — `propose` is named in the spec's statement of the managed set even though `overlayActionLabel()` excludes it. Basis: the two answer different questions. The spec says what Keel overlays, which is four actions; the doctor label counts state-changing command surfaces, which is three. The reworded requirement says both, so the exclusion reads as a decision rather than an omission.

D4 — Task 1.1 owns `openspec/specs/keel-openspec-surface-overlay/spec.md` end to end, including the promotion the release task usually performs. Basis: the check this task adds reads the published file, so a task that fixed only half of it could not pass its own check — the split that change `an-owner-outlives-the-change` had to merge. The delta in this change carries the requirement-level half as the authoring record, and the release task validates that the delta and the promoted store agree rather than performing the promotion.

D5 — The Purpose line is edited directly in the published spec, with no delta entry. Basis: F3. Recording why in the spec is part of this change, so the next reader does not look for the delta operation that would have caught it.

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **The check is narrow by construction.** It watches two locations and will not notice a fifth managed action drifting into a scenario body elsewhere in the file. That is the trade D1 accepts: F2 shows the wide version is wrong, and the narrow version covers the statement a reader actually reads first.
- **A wording change could move the check's target.** The check locates the requirement by name, so a rename that the check does not know about would make it look for a heading that is gone. It fails in that case rather than passing vacuously, which is the direction that gets noticed.
- **No behavior changes**, so rollback is a revert of two files.

## Open Questions

None.
