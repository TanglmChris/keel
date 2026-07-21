# Modernize domain-lens vocabulary and fix the retired-mechanism misdirection

## Why

The 5.2.0 `pluggable-domain-lenses` change renamed the domain-guidance vocabulary
from "reference/profile" to "lens" across most surfaces (AGENTS.md, schema,
templates, READMEs, the four skills). But its spec delta was authored as
`## ADDED Requirements` only: it added the new lens requirements without
`## MODIFIED` on the pre-existing "profile" surface. Two defects survived on the
published 5.2.0 HEAD.

1. **Contradiction / active misdirection (material).** The `--profile` rejection
   — in `bin/keel.js` and `scripts/install_to_repo.py` — tells the user that
   web/hardware/hardware-dsl guidance "is bundled with the `keel-align-expectations`
   skill as on-demand references." That is the exact mechanism 5.2.0 retired:
   domain guidance is now user-authored lenses in `keel/lenses/*.md`, scaffolded
   with `keel lenses add`, explicitly **not** bundled in a skill. The message now
   directs users to a mechanism that no longer exists. This is not merely stale
   wording — the `keel-domain-profiles` spec self-contradicts: its reject scenario
   asserts "domain references are bundled" while the same file's pluggable-lenses
   requirement states "not as content bundled inside `keel-align-expectations`."
   The `domain-profiles` validator scenario pins the wrong word (`"bundled"`),
   locking the misdirection in.

2. **Stale generic vocabulary.** Several specs and the `keel-spec-driven`
   design.md template still call the *current* domain-guidance concept a
   "profile" where 5.2.0 renamed it to "lens" everywhere else.

## What changes

- **Fix the misdirection and resolve the contradiction:** rewrite the `--profile`
  rejection (CLI + installer help and failure) to state that domain guidance is
  now user-authored pluggable lenses (`keel/lenses/*.md`, `keel lenses add`) and
  the flag is no longer supported; update the `keel-domain-profiles` reject
  scenario to match; repoint the validator needle off `"bundled"` onto the new
  wording.
- **Sweep the stale generic vocabulary:** rename the *current-concept* "profile"
  to "lens" in the affected specs (`keel-skill-sourcing-and-portability`,
  `keel-expectation-slice-evidence-gates`, `keel-expectation-alignment`, the
  `keel-domain-profiles` Purpose line) and both copies of the design.md template.

## Non-goals

- **No runtime behavior change** beyond the text of the `--profile` rejection.
  The flag stays rejected; only the message changes.
- **No version bump or release.** 5.2.0 is already published; this lands on
  `main` unreleased and folds into a later release decided separately.
- **Preserve v3-artifact "profile" references.** The `--profile` flag name, the
  `keel-profile-*` skill matcher and messages, the legacy-migration scenarios,
  "v3 profile-install state," and all CHANGELOG history name the retired v3
  artifact accurately and stay unchanged — renaming them to "lens" would make
  them wrong. See design.md for the full keep/sweep/fix boundary.
- **Capability directory id.** Whether to rename `keel-domain-profiles` →
  `keel-domain-lenses` is an open decision recorded as D1 in design.md
  (recommendation: keep the id stable). Awaiting review.
