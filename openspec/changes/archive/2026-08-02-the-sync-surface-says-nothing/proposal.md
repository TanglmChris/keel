# The sync surface says nothing

## Why

`AGENTS.md` names two actions that are gated the same way:

> `/opsx:sync` and `/opsx:archive` completion is gated by `keel gate change-close --action sync|archive` plus `keel-review-checklist`, not a runtime hook

`/opsx:archive` carries a Keel overlay that says so. `/opsx:sync` carries no
overlay at all. `OPENSPEC_OVERLAY_ACTIONS` in `bin/keel.js` is
`["propose", "apply", "archive"]`, so `.claude/commands/opsx/sync.md` and
`.claude/skills/openspec-sync-specs/SKILL.md` — and their Codex projections —
receive nothing. Measured 2026-08-02: neither file contains the string
`change-close`, `keel gate`, or `keel openspec`.

An agent that invokes `/opsx:sync` from that file reads generic upstream
OpenSpec instructions and is told nothing about the gate that decides whether
the sync may complete, nothing about `keel-review-checklist`, and nothing about
invoking OpenSpec through `keel openspec` when a bare `openspec` is not on PATH.
The protocol states the requirement in a file the agent may not be reading at
that moment; the surface it *is* reading contradicts it by silence.

This is the half of #34's L0 that is genuinely missing. The other half — the
per-occurrence confirmations a standing authorization should remove — shipped in
5.5.0: the apply and archive overlays already say a standing-authorized action
proceeds without asking, and that the authorization removes the confirmation and
not the proof. `sync` is not in the `authorize:` vocabulary and this change does
not add it, because widening what a repository can standing-authorize is a
different decision from telling a surface which gate governs it.

## What Changes

- The Keel overlay projects onto the sync surface — `/opsx:sync` and the
  `openspec-sync-specs` skill — on every target that receives the others.
- The sync overlay states for its action what the archive overlay states for
  its own: the current agent owns the decision, `keel gate change-close --action
  sync` and `keel-review-checklist` run before it completes, subagents assist
  with bounded assessment only and cannot sync, generic delegation language is
  not authority to transfer Keel ownership, and OpenSpec is invoked through
  `keel openspec`.
- The sync overlay names, from its own side, the consequence archive already
  documents: sync promotes the spec delta, so an archive that follows one uses
  `--skip-specs` or re-applies a delta that is already promoted.
- `keel --doctor` reports the overlay across every managed action rather than
  naming a hardcoded pair.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-openspec-surface-overlay`: the overlay covers the sync surface, and its
  body states the gate that governs sync.
- `keel-target-surface-diagnostics`: the overlay diagnostic reports every
  managed action rather than a hardcoded pair.

## Impact

- `bin/keel.js` — `OPENSPEC_OVERLAY_ACTIONS`, the sync overlay body, the overlay
  title, and the doctor line.
- `.claude/commands/opsx/sync.md`, `.claude/skills/openspec-sync-specs/SKILL.md`,
  `.codex/skills/openspec-sync-specs/SKILL.md` — the projected overlay.
- `scripts/validate_plugin.py` — scenarios.
- Out of scope, stated so it is not read as an oversight: `/opsx:explore`
  receives no overlay and still will. It reads and reports, reaches no gate, and
  changes no state, so there is nothing for an overlay to govern.
