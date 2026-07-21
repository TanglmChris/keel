# Design — modernize-lens-vocabulary

## Context

`pluggable-domain-lenses` (archived 2026-07-20, shipped in the published 5.2.0)
introduced pluggable lenses but authored its `keel-domain-profiles` spec delta as
`## ADDED` only. The old profile surface was never `## MODIFIED`, so the retired
"bundled references" mechanism still lives in the `--profile` rejection, in one
self-contradicting spec, and in the validator needle that pins it.

## Facts

- **F1** — The `--profile` rejection text ("…bundled with the
  `keel-align-expectations` skill as on-demand references") appears in
  `bin/keel.js:380` and `scripts/install_to_repo.py:1013` (help) + `:1021` (fail).
- **F2** — `openspec/specs/keel-domain-profiles/spec.md` self-contradicts: the
  "Obsolete profile flags are rejected clearly" scenario (`:20`) says
  "domain references are bundled," while "Keel supports pluggable domain lenses"
  (`:25`) says "not as content bundled inside `keel-align-expectations`."
- **F3** — `scripts/validate_plugin.py:1791` asserts the literal `"bundled"` is
  present in the rejection, so the misdirection is test-locked.
- **F4** — The literal capability id `keel-domain-profiles` is not referenced by
  any live (non-archive) code as a string; it exists only as the spec directory
  name and as the validator's own scenario key `"domain-profiles"` /
  `validate_domain_profiles_scenario`. Archived change deltas reference it as
  history.
- **F5** — OpenSpec has no capability-rename or preamble-edit primitive.
  `findSpecUpdates` maps a change's `specs/<cap>/` to `openspec/specs/<cap>/` by
  directory name; `RENAMED` is requirement-level (FROM/TO headings) only; and
  `buildUpdatedSpec` preserves the target's `## Purpose` preamble verbatim — no
  delta touches it. A fully-REMOVED capability would also rebuild to an
  invalid empty spec. Therefore the directory rename and the Purpose rewrite MUST
  be direct edits to the live `openspec/specs/` tree, promoted with
  `openspec archive --skip-specs` (the flow the archive overlay documents after
  `/opsx:sync`, from issue #3). The change's `specs/` delta files stay as the
  valid-format durable record; they are not applied by `--skip-specs`.

## Decisions

### D1 — Rename the capability `keel-domain-profiles` → `keel-domain-lenses` (decided at review 2026-07-21)

Review chose the full rename over keeping the id stable: the capability now holds
five requirements, four of them about lenses and one about the v3 profile
retirement, so `keel-domain-lenses` names it honestly. Per F5 the rename is a
direct `git mv` of `openspec/specs/keel-domain-profiles/` →
`openspec/specs/keel-domain-lenses/` plus renaming the validator's
`validate_domain_profiles_scenario` → `validate_domain_lenses_scenario`, the
`"domain-profiles"` registry key → `"domain-lenses"`, and its message strings.
The archived `pluggable-domain-lenses` delta keeps referencing the old id as
history (archived changes are immutable record, not live authority).

### D2 — Fix the reject message and resolve the contradiction as the material core

The new rejection states the current mechanism, e.g.: *"--profile is no longer
supported: domain guidance is now user-authored lenses in `keel/lenses/*.md`
(scaffold with `keel lenses add`)."* The `keel-domain-profiles` reject scenario
THEN clause changes from "domain references are bundled" to reporting the
pluggable-lens mechanism. The validator needle moves off `"bundled"` onto a
stable anchor of the new wording (e.g. `"keel/lenses"` or `"lenses"`).

### D3 — Keep/sweep/fix boundary

The word "profile" is overloaded. It is preserved wherever it names the **retired
v3 artifact** and rewritten only where it names the **current concept** 5.2.0
renamed to "lens."

| Site | Text | Action |
|------|------|--------|
| `bin/keel.js:378` | `--profile` flag name | **KEEP** (users still type it) |
| `bin/keel.js:380` | reject "bundled…references" | **FIX → lenses** (D2) |
| `bin/keel.js:1344` | `/^keel-profile-/` matcher | **KEEP** (v3 skill dirs) |
| `bin/keel.js:1377,1379` | "legacy profiles" / "v3 keel-profile-* skills" | **KEEP** (v3 artifact) |
| `install_to_repo.py:1011,1013,1021` | `--profile` arg + help + fail | **KEEP** flag; **FIX** help+fail text (D2) |
| `validate_plugin.py:1791` | `"bundled"` needle | **FIX → new-wording anchor** (D2) |
| `validate_plugin.py:71-73` | `keel-profile-web/hardware/hardware-dsl` | **KEEP** (v3 artifact names) |
| `keel-domain-profiles/spec.md:3` | Purpose "optional Keel domain profiles" | **SWEEP → lenses** |
| `keel-domain-profiles/spec.md:5-16,90,99` | "removes domain profiles", migration, "keel-profile-*" | **KEEP** (v3 retirement/migration) |
| `keel-domain-profiles/spec.md:20` | reject scenario "are bundled" | **FIX → lenses** (D2) |
| `keel-skill-sourcing-and-portability/spec.md:62,76,77,115,117,124` | "generic/selected/domain profile" (current concept) | **SWEEP → lens** |
| `keel-expectation-slice-evidence-gates/spec.md:33` | "a domain profile identifies…" | **SWEEP → lens** |
| `keel-expectation-alignment/spec.md:87` | "grill and profile guidance is consolidated" | **SWEEP → lens** |
| `keel-target-surface-diagnostics/spec.md:26` | "v3 profile-install state" | **KEEP** (v3 artifact) |
| `design.md` templates ×2, L24 | "risk-triggered grill or domain profiles" | **SWEEP → lenses** |
| `keel/CHANGELOG.md` (all) | historical entries | **KEEP** (append-only history) |

## Risks

- Sweeping requirement **headings** (e.g. "Generic profiles and dedicated skills
  remain separate" → "Generic lenses…") is a heading rename; OpenSpec deltas treat
  a heading change as identity change. The spec-delta authoring must use
  `## MODIFIED Requirements` with the exact existing heading, and handle any
  heading rename explicitly so `openspec archive` applies cleanly. This is the
  main authoring risk and is why the sweep is its own task, separate from the
  code/needle fix.

## Task slicing

- **1.1 — Fix the misdirection in code + validator** (D2, code only): rewrite the
  `--profile` rejection text in `bin/keel.js` and `scripts/install_to_repo.py`
  (help + fail) to point at pluggable lenses, and repoint the
  `validate_plugin.py` `domain-profiles` needle off `"bundled"` onto a stable
  anchor of the new wording. Behavior-adjacent (message text); strategy
  regression-first (red asserts new text present / old absent before the fix).
- **2.1 — Sweep stale generic vocabulary in the other specs + templates** (D3
  SWEEP rows, excluding the renamed capability): `keel-skill-sourcing-and-portability`,
  `keel-expectation-slice-evidence-gates`, `keel-expectation-alignment`, and both
  design.md template copies, plus any validator needle pinning the old words.
  Direct live edits; strategy characterization (grep evidence: current-concept
  "profile" gone from swept files, v3-artifact "profile" preserved, `npm test`
  green).
- **3.1 — Rename the capability + modernize its content** (D1 + D2 spec side + D3
  Purpose): `git mv` `keel-domain-profiles` → `keel-domain-lenses`, rewrite its
  Purpose line, fix the reject scenario THEN clause off "are bundled", and rename
  the validator scenario function/key/messages. Per F5 this is direct live-spec
  editing; promotion is `openspec archive --skip-specs`. Strategy
  characterization (grep + `npm test` green + `openspec validate` on the change).

## Archive note

Because tasks 2.1 and 3.1 edit the live `openspec/specs/` tree directly (F5), the
change is closed with `keel gate change-close --action archive` followed by
`openspec archive modernize-lens-vocabulary --skip-specs --yes`. The change's
`specs/` delta files are the valid-format durable record and are intentionally
not re-applied.

The change carries one formal delta, `specs/keel-domain-lenses/spec.md` (ADDED),
recording the renamed capability's full requirement set with the reject scenario
moved off "are bundled." The generic-vocabulary sweep of the other three
capabilities (task 2.1) is recorded by the D3 table above rather than by separate
per-capability delta files: those edits are vocabulary-only, preserve every
requirement's meaning and scenarios, and — under `--skip-specs` — no delta is
applied, so D3 is the complete and authoritative site list.
