## Context

`OPENSPEC_OVERLAY_ACTIONS` (bin/keel.js:82) has named `["propose", "apply", "archive", "sync"]`
since `sync` joined in 5.22.0. `overlayActionLabel()` (bin/keel.js:1088) derives the prose label
`apply/archive/sync` from that list, excluding `propose` because its overlay governs authoring
rather than a state-changing command. Every output line that reports the managed action set
(`--doctor`'s overlay line, the refresh summary, the removal summary) now reads that derived
label — `#75` fixed the last literal copy in code.

Published spec prose is not derived; it is written once and never re-read against the set it
describes. `#79` found nine lines still saying `apply/archive` after grepping
`openspec/specs/`, and flagged one of them (`keel-openspec-surface-overlay/spec.md:121`, inside
"Thin CLI owns OpenSpec initialization and overlays only") as using yet a third wording
(`authoring/apply/archive`) and asked whether `propose` counts and whether the three different
phrasings across the file should unify.

## Goals / Non-Goals

**Goals:**

- Every spec-prose line whose described behavior demonstrably spans `apply`, `archive`, and
  `sync` today names all three, matching the derived label the code already produces for the same
  behavior.
- The one requirement whose scope is genuinely just `apply` and `archive` — because `sync` has its
  own dedicated requirement layered on top — is left unchanged, and that reasoning is recorded so
  a future reader does not "fix" it again into a duplicate of the sync requirement.
- The one line this change's mechanism cannot reach (Purpose, which OpenSpec's delta format has no
  operation for) is not silently dropped: it is filed as `TanglmChris/keel#86` with the same
  measurement and rationale, so it stays findable.

**Non-Goals:**

- Merging or restructuring requirements. `sync`'s overlay obligations stay in their own
  requirement ("The sync surface carries the overlay that governs it"); this change only touches
  wording, not requirement boundaries.
- Introducing a derivation mechanism for spec prose. Spec files are prose by design (per `#79`'s
  own framing: "规格是散文，不是输出，派生不了，也没有断言能比对它" — spec is prose, not output;
  it cannot be derived, and no assertion can compare it). This change re-aligns the words to
  current behavior; it does not make them self-updating.
- Changing whether `propose` is counted in the derived action label. `overlayActionLabel()`
  already excludes it, deliberately, with its own recorded rationale; this change follows that
  existing convention rather than revisiting it.

## Decisions

- D1 — Classify each of the nine flagged lines by checking the actual code behavior the
  surrounding requirement describes, not by treating the grep match itself as sufficient evidence
  of drift. Basis: `#79`'s own "实现要点" section flags that the three different existing
  phrasings need to be "统一到一个说法" (unified to one wording) with judgment, not a blind
  find-replace — and a blind replace risks rewriting a requirement (line 7) that is correct as
  written.

- D2 — For the seven lines that changed, use exactly the string `apply/archive/sync`, matching
  `overlayActionLabel()`'s own output and the wording `keel-target-surface-diagnostics`'s sibling
  requirement ("The overlay diagnostic reports every managed action") already settled on. Basis:
  one wording across code output and spec prose is what makes the two comparable at all; inventing
  a fourth phrasing here would add a fourth thing to unify later.

- D3 — Leave `keel-openspec-surface-overlay/spec.md:7` unchanged. Basis: F1/F2 below — the
  requirement's own scenarios test only apply and archive surfaces, and the separate sync
  requirement's own text ("onto every target that receives the overlay for propose, apply, and
  archive") names `propose, apply, archive` as the pre-existing base it is projected onto,
  confirming the layering is intentional rather than an unrevised generalization.

- D4 — Extend `keel-openspec-surface-overlay/spec.md:121`'s existing `authoring/apply/archive`
  phrasing to `authoring/apply/archive/sync`, keeping `authoring` named separately from the derived
  action group. Basis: this line already distinguishes authoring from the action-labeled group in
  the same sentence, matching `overlayActionLabel()`'s own exclusion of `propose`; extending the
  action group preserves an existing convention instead of adding a new one.

- F1 — Verified 2026-08-05 by reading `keel-openspec-surface-overlay/spec.md` in full: the
  requirement titled "Keel overlays apply and archive surfaces" (lines 5-26) has three scenarios,
  each testing only `.../openspec-apply-change/SKILL.md`, `.../openspec-archive-change/SKILL.md`,
  `opsx/apply.md`, and `opsx/archive.md` — never a sync surface — on Claude, Codex, and OpenCode.

- F2 — Verified 2026-08-05 by reading the same file: the requirement "The sync surface carries the
  overlay that governs it" (lines 212-232) is a separate, later requirement with its own scenario
  ("Installing projects the overlay onto the sync surface") that specifically asserts the sync
  command surface and sync skill carry the marker. Its body text reads "onto every target that
  receives the overlay for propose, apply, and archive," naming that trio as the pre-existing
  group sync joins — not as an oversight.

- F3 — Verified 2026-08-05 by reading `bin/keel.js`: `refreshOpenSpecSurfaceOverlay` (line 1274)
  and `openspecOverlaySurfacesForTarget` (line 1058) both iterate `OPENSPEC_OVERLAY_ACTIONS`
  uniformly (filtering only `propose` on the `opencode` target), so the idempotent
  replace-or-skip-missing behavior "Keel refreshes existing overlays idempotently" describes
  already applies identically to `sync` today — confirming lines 34/41/42 describe general
  behavior, not an apply/archive-specific one.

- F4 — Verified 2026-08-05 by reading `bin/keel.js:1456-1471`: doctor's status line is literally
  `` `Keel ${overlayActionLabel()} overlay` ``, i.e. `Keel apply/archive/sync overlay` today, built
  from the same `openspecOverlaySurfacesForTarget` surface list — so a missing sync marker is
  reported under that exact line, confirming `keel-target-surface-diagnostics/spec.md:115,119,121`
  describe current three-action behavior, not two.

- D5 — File `keel-openspec-surface-overlay/spec.md:3` (Purpose) as a new GitHub issue
  (`TanglmChris/keel#86`) rather than hand-editing the published spec store outside the archive/sync
  flow. Basis: F5 below — no delta operation reaches Purpose, and every other published-spec write
  in this repository's history went through archive/sync; a one-off exception for a single line
  trades a documented, findable gap for a precedent of writing published specs by hand.

- F5 — Verified 2026-08-05 by reading `node_modules/@fission-ai/openspec/dist/core/specs-apply.js`
  and the `openspec instructions specs` instruction text: delta files support only `### Requirement`
  operations under `ADDED`/`MODIFIED`/`REMOVED`/`RENAMED Requirements` headers. The merge logic's
  only `Purpose` handling (line 296) writes a `TBD` placeholder when a capability is created; an
  existing spec's Purpose section is never read from or written by a delta. `git log` over every
  `openspec/specs/*/spec.md` Purpose change found no prior direct edit — the one match was a whole-
  file capability rename, not a targeted Purpose edit.

## Hidden Knowledge / Assumptions

- A1 — `overlayActionLabel()`'s exclusion of `propose` is an existing, separately-justified
  convention (bin/keel.js:1086-1087 comment); this change reuses it rather than re-litigating it.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- Leaving line 7 unchanged (D3) means the nine-line count from `#79`'s grep is not fully zeroed by
  this change — the residual line is a correct requirement scope, not a missed fix, and this
  design records why so a future grep-driven pass does not "complete" it incorrectly.
- Filing the Purpose line as `#86` instead of fixing it (D5) leaves one genuine piece of drift in
  place. The alternative (hand-editing the published store) was rejected as a worse trade: it would
  establish that published specs can be written outside archive/sync, which is a bigger and more
  durable risk than one stale Purpose sentence.

## Open Questions

None — `#79` raised whether `propose` counts and how to unify wording; both are resolved by D2/D4
against the existing `overlayActionLabel()` convention rather than left open.
