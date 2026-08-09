## Why

`#75` fixed the one place `apply/archive` was a literal instead of a derived label:
`refreshOpenSpecSurfaceOverlay`'s summary line now reads `overlayActionLabel()`, which has named
`apply/archive/sync` since `sync` joined the managed set in 5.22.0. The published spec prose was
never revisited when `sync` joined. It still says `apply/archive` in nine places across two spec
files.

## Measurement (2026-08-05, 5.30.0)

```
$ grep -rn "apply/archive" openspec/specs/ | grep -v "apply/archive/sync"
openspec/specs/keel-openspec-surface-overlay/spec.md:3    Purpose
openspec/specs/keel-openspec-surface-overlay/spec.md:7    Requirement body
openspec/specs/keel-openspec-surface-overlay/spec.md:34   Scenario WHEN
openspec/specs/keel-openspec-surface-overlay/spec.md:41   Scenario WHEN
openspec/specs/keel-openspec-surface-overlay/spec.md:42   Scenario THEN
openspec/specs/keel-openspec-surface-overlay/spec.md:121  Requirement body
openspec/specs/keel-target-surface-diagnostics/spec.md:115 Requirement body
openspec/specs/keel-target-surface-diagnostics/spec.md:119 Scenario WHEN
openspec/specs/keel-target-surface-diagnostics/spec.md:121 Scenario THEN
```

Reproduces the count `#79` reported at 5.24.0: nine lines, unchanged since.

## What Changes

Seven of the nine lines are updated, through the normal `MODIFIED Requirements` delta, to name
`sync` alongside `apply` and `archive`, because the behavior they describe is verifiably general —
checked against the code each line describes, not assumed from the grep alone:

- `keel-openspec-surface-overlay/spec.md:34,41,42` (Requirement: Keel refreshes existing overlays
  idempotently) — `refreshOpenSpecSurfaceOverlay` (bin/keel.js:1274) iterates
  `openspecOverlaySurfacesForTarget`, which spans every managed action, and applies the same
  replace-or-skip-missing logic to all of them. The requirement's own MUST sentence is already
  action-agnostic; only its illustrative scenario wording says `apply/archive`.
- `keel-openspec-surface-overlay/spec.md:121` (Requirement: Thin CLI owns OpenSpec initialization
  and overlays only) — already separates `authoring` from the action-labeled group in the same
  sentence (`authoring/apply/archive overlays`); extending the action group to `apply/archive/sync`
  keeps that existing convention rather than inventing a new one.
- `keel-target-surface-diagnostics/spec.md:115,119,121` (Requirement: Missing Keel overlays are
  visible) — doctor's own status line already reads `Keel ${overlayActionLabel()} overlay`
  (bin/keel.js:1468), so a missing sync marker is reported under literally that line today. A
  sibling requirement in the same file ("The overlay diagnostic reports every managed action",
  added after this one) already requires the summary label to include `sync`; this older
  requirement's scenario text predates that fix and still shows the pre-sync wording for the same
  surface.

One line is deliberately left unchanged:

- `keel-openspec-surface-overlay/spec.md:7`, inside the requirement titled "Keel overlays apply
  and archive surfaces". That requirement's own scenarios test only the apply and archive skill
  and command files, on all three targets — never sync. A separate requirement, "The sync surface
  carries the overlay that governs it", covers sync on its own terms, and its own text names
  `propose, apply, and archive` as the pre-existing group sync is projected onto — confirming the
  two requirements are deliberately layered (apply+archive, then propose, then sync added on top)
  rather than one drifting description of a single set. Rewording line 7 to name sync would either
  duplicate the sync requirement's scenarios or misstate this requirement's own scope.

One line is out of reach of this change's mechanism:

- `keel-openspec-surface-overlay/spec.md:3` (Purpose) has the same drift, but OpenSpec's delta
  format has no `Purpose` operation — only `ADDED`/`MODIFIED`/`REMOVED`/`RENAMED Requirements`
  (confirmed against `node_modules/@fission-ai/openspec/dist/core/parsers/change-parser.js` and the
  `openspec instructions specs` instruction text). `specs-apply.js`'s only `Purpose` handling writes
  a `TBD` placeholder when a capability is created; an existing spec's Purpose is never touched by
  sync or archive. Fixing it would mean hand-editing the published store outside the archive/sync
  flow this repository otherwise relies on for every published-spec write. Filed as
  `TanglmChris/keel#86` rather than done here, with the measurement and rationale recorded there.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-openspec-surface-overlay`: two requirements' prose names `sync` alongside `apply` and
  `archive` where the described behavior already covers it.
- `keel-target-surface-diagnostics`: the "Missing Keel overlays are visible" requirement's prose
  names `sync` alongside `apply` and `archive`, matching the literal doctor output line and the
  sibling requirement that already derives it.

## Impact

- `openspec/specs/keel-openspec-surface-overlay/spec.md` — four lines (three scenario lines in one
  requirement, one requirement-body line in another).
- `openspec/specs/keel-target-surface-diagnostics/spec.md` — three lines.
- No code change. `overlayActionLabel()`, `openspecOverlaySurfacesForTarget`, and
  `refreshOpenSpecSurfaceOverlay` are unchanged; this aligns spec prose to behavior they already
  have.
- No change to `keel-openspec-surface-overlay/spec.md:5-7`'s own scope (left as-is; see Why).
- Purpose line drift (`keel-openspec-surface-overlay/spec.md:3`) is out of scope; tracked as
  `TanglmChris/keel#86`.
