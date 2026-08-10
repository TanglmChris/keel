## Context

`src/core/gates.js`'s `scopeEvidence` (line 610), called only from `taskComplete` (line 919),
implements the no-`--base` attribution branch today by reading `manifest.startedDirty` — a bare
array of path strings `startGuard` (`src/core/guard.js`) records at the moment `keel gate
task-start` authorizes a task — and subtracting every one of those paths from the currently-dirty
set before comparing what remains against Touch. The subtraction is unconditional: a path already
dirty at task start stays exempt from attribution for the rest of the task's life, whether or not
the task goes on to write it again.

`#72`'s repro: two tasks of one change, each declaring one file in its own Touch, run in this
repository's normal order (no commit between tasks). Task 1 finishes and its output is now dirty.
Task 2 starts — that output enters its `startedDirty` set, because it is dirty at that instant for
a legitimate reason. Task 2 then appends undeclared content to that same file. `task-complete`
subtracts the path because it was dirty at start, so the write is invisible to both `task-complete`
and `change-close --action archive`. The issue measured this shape as normal rather than rare:
81% of this repository's 44 archived changes carry ≥2 tasks, and 70% of tasks are not their
change's first, so most tasks begin with a tree already carrying a prior task's legitimate output.

The owner decided (2026-08-05, dasauto#18) on **甲**: record a content signature per dirty path at
task start, and attribute a path only when its content no longer matches that signature at
completion — not the previously-recommended **丙** (exempt only the union of prior tasks' own
Touch), which an unattended run's own measurement (2026-08-04) showed replays 458 times across 44
archived changes without ever catching the reproduced defect, with at least one of those 458
already proven a false positive by its own task's Review.

## Goals / Non-Goals

**Goals:**

- For a path already dirty when the task started, distinguish "still the content recorded then"
  (stays exempt) from "content changed since" (now attributed), so the reproduced defect —
  content actually rewritten after task start — is caught.
- Keep every currently-passing exemption for a pre-existing dirty path that the task does not
  touch again exactly as it is today; this is not a reopening of the false-positive class 5.16.0
  removed.
- Change only the mechanism the owner authorized (甲); do not fold in 丙, 乙, or any new
  attribution mechanism for `change-close` or the write guard that the issue text did not
  authorize.

**Non-Goals:**

- Reworking `--base`-driven comparison, `pathAllowed`, glob matching, the completed-sibling
  exclusion, rename-endpoint handling, or the guard-manifest/change-directory exemptions — all
  unchanged, F1/F2 below.
- Adding dirty-path attribution logic to `change-close`, which performs none today (F1). The
  issue's own text ("change-close 不做归因，所以它也不是最后一道网" — change-close performs no
  attribution, so it is not a backstop either) states this as the existing reason that gate
  cannot catch the defect, not as a request to add a comparison there; doing so would be a second,
  un-owner-authorized material decision about what `change-close` should newly refuse.
- Making the write guard content-aware. It denies purely by Touch membership and never reads
  `startedDirty` (F3); its blindness to shell-issued writes is a separate, already-shipped
  concern (5.15.0/5.16.0), not this issue's material — "the three layers share one blind spot"
  in the issue text names the unconditional exemption as that shared blind spot, not a claim that
  all three call the same comparison code.
- 丙 (Touch-union exemption) and 乙 (commit after every task) — both already decided against by
  the owner (2026-08-05); not reopened.

## Decisions

- D1 — Record `{path, sha256}` per dirty path instead of a bare path string, with `sha256: null`
  standing for "nothing to read" (a deleted path, or one about to be created) rather than omitting
  the entry. Basis: `null` compares equal to itself the same way a real hash does, so a path that
  stays absent between task start and completion still reads as unchanged, and one that gets
  created or deleted reads as changed — no branch needs a separate absence case.

- D2 — Read the current signature with the same `contentSignature` helper that builds the
  recorded one, exported once from `guard.js` and required by `gates.js`, rather than a second
  hashing implementation living in `gates.js`. Basis: `guard.js`'s own file header already states
  this repository's precedent for shared worktree-reading code ("One implementation is the
  point: a baseline and a comparison that disagreed... would attribute a path nobody wrote") —
  this is that same principle applied to content hashing instead of path reading.

- D3 — Touch only the no-`--base` branch of `scopeEvidence` (`src/core/gates.js`, the `if
  (!base)` block). The `--base` branch already computes candidates from a real git diff against
  a caller-supplied commit plus current dirty paths, with no "since task start" concept to
  refine, and the existing "An explicit base takes precedence over the recorded set" scenario
  already requires that a path changed since an explicit base stays attributed regardless of
  task-start state — this decision keeps that scenario true unmodified.

- D4 — Extend the existing `default-completion-attributes-writes` scenario
  (`scripts/validate_plugin.py:7035`) with one new assertion rather than add a new scenario
  function. Basis: the existing scenario already builds the exact fixture this needs — a path
  dirty at task start, a `--record`ed `task-start`, and a `gate()` helper — the same
  extend-rather-than-duplicate call `the-owner-instruction-comes-first`'s design made (its D2)
  for the same-shaped reason. Each new assertion is its own single-condition `if`, matching
  `assertion-shape-count`'s (`#43`) existing constraint against one condition covering two
  distinct failure causes.

## Hidden Knowledge / Assumptions

- A1 — F1 confirms `scopeEvidence` has exactly one call site and `changeClose` performs no
  dirty-path comparison at all, so there is no second call site this change needs to touch to
  address `change-close`; see Non-Goals for why adding one there is out of scope rather than
  merely deferred.
- A2 — F3 confirms the write guard never reads `startedDirty`; "cover all three layers" in the
  issue text is read as "the same blind spot affects all three surfaces' outcome," which this
  change addresses by fixing the one place the comparison exists, not as "make three code paths
  perform the same new comparison."

## Facts

- F1 — Verified 2026-08-10 by reading `src/core/gates.js`: `scopeEvidence` (line 610) is called
  only from `taskComplete` (line 919); `changeClose` (line 1186) never calls it and contains no
  comparison against `manifest.startedDirty` or any other dirty-path baseline.
- F2 — Same file/date: `attributeChanged`, `pathAllowed`, `completedSiblingOwners`, and the
  `--base` branch of `scopeEvidence` read only `touch`, `base`, and `tasks` — none reads
  `manifest.startedDirty`, so D3's boundary touches nothing else that consumes it.
- F3 — Verified 2026-08-10 by reading `plugins/keel/scripts/pretooluse-guard.js` in full: it
  reads `manifest.touch` (lines 56-58, 265, 269), `manifest.authority` (lines 59-61, 229), and
  calls `taskIsChecked` (line 254); it never reads `manifest.startedDirty` and has no dirty-path
  concept.
- F4 — Verified 2026-08-10 by diff: `plugins/keel/skills/keel-review-checklist/SKILL.md` and
  `src/skills/keel-review-checklist/SKILL.md` are byte-identical, both stating the unconditional
  exemption in prose ("a path already dirty when the task started is never attributed even if
  the task changed it again") that needs the same correction.
- F5 — Verified 2026-08-10 by grep: `keel/CHANGELOG.md:232-234` documents the original (5.16.0)
  unconditional-exemption mechanism as dated release narration ("A path already dirty when the
  task started is not attributed even if the task modified it again"), true of what 5.16.0
  shipped. This is historical narration, not evergreen documentation of the current mechanism;
  `## Invalidates` records it with a discard rationale rather than editing the past entry.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A path already dirty at task start, edited, then edited back to byte-identical content by
  completion, is still exempt — a content signature cannot see an edit that leaves no trace in
  the final content. This is the same class of limit `git diff` itself has (a no-op round-trip
  diffs empty), not a regression against the unconditional mechanism or 丙, neither of which
  could see it either.
- Hashing every dirty-at-start path's current content on each `task-complete` call adds one file
  read per baseline entry, bounded by the size of the dirty set at task start — this repository's
  own `#72` measurement puts that at a handful of paths per task in the common case, and
  `hashAuthority` already does the same per-path read for `authority` entries in the same
  manifest.

## Open Questions

None.
