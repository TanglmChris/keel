## Context

Keel governs OpenSpec's command surfaces by injecting an overlay into them, because those files are upstream text that Keel does not own and cannot rewrite. The overlay is how a generic instruction gets a Keel qualification without forking the file.

Three of the four state-changing surfaces receive one. The fourth is `sync`, which is one of the two actions `keel gate change-close` exists for.

## Goals / Non-Goals

**Goals:**
- The surface an agent reads while performing an action states the gate that governs it.
- The overlay's coverage is derived from one list, so a surface cannot be added to the managed set and left out of the diagnostic.

**Non-Goals:**
- No change to what `authorize:` accepts. `sync` is not standing-authorizable today and this change does not make it so.
- No overlay on `explore`. It reaches no gate and changes no state.
- No new hook, command, or gate. The seam already exists; one action is missing from it.

## Decisions

**F1** — `OPENSPEC_OVERLAY_ACTIONS` is `["propose", "apply", "archive"]` in `bin/keel.js:75`. `.claude/commands/opsx/sync.md` and `.claude/skills/openspec-sync-specs/SKILL.md` contain no `keel:openspec-surface-overlay` marker, and no occurrence of `change-close`, `keel gate`, or `keel openspec`. *Basis:* read the constant, grepped the files.

**F2** — `AGENTS.md` gates sync and archive identically: "`/opsx:sync` and `/opsx:archive` completion is gated by `keel gate change-close --action sync|archive` plus `keel-review-checklist`". *Basis:* the shipped managed block.

**F3** — The archive overlay already documents the interaction from its own side: "When `/opsx:sync` has already promoted the change's spec delta, run the archive with `--skip-specs` so the promoted delta is not re-applied; archive is not idempotent over an already-synced delta." Nothing on the sync surface says sync is what promotes it. *Basis:* `bin/keel.js` archive overlay body.

**F4** — `keel --doctor` prints the literal label `Keel apply/archive overlay`, a hardcoded pair rather than a description of the managed set. *Basis:* `bin/keel.js:1325`.

**D1** — **`sync` joins the managed actions rather than being handled specially.** *Basis:* F1. The overlay machinery is already per-action, with a title and a body chosen by action name; sync is missing from a list, not missing a mechanism. Adding it to the list is what makes the projection, the installer, the uninstaller, and the doctor cover it together.

**D2** — **The sync overlay mirrors the archive overlay's structure, not its content.** *Basis:* F2. The two actions are gated identically and owned identically, so the ownership, subagent, and delegation-language rules are the same statements with `sync` in them. What differs is the artifact consequence: archive warns about re-applying a promoted delta, and sync is the thing that promotes it, so sync says so from its side. A reader who only ever sees one of the two surfaces then still knows the pairing exists.

**D3** — **The doctor label is derived from the managed action list.** *Basis:* F4. A hardcoded `apply/archive` was correct when the set was those two; it silently became wrong the moment a third was managed, which is exactly the class of defect 5.13.0 spent a release on. Deriving it means the next action added cannot leave the diagnostic behind.

**D4** — **`explore` stays uncovered, and the proposal says so.** *Basis:* an overlay qualifies an instruction that could otherwise lead an agent past a Keel boundary. Explore reads and reports; it reaches no gate, writes no state, and has no boundary to qualify. Recording the decision matters more than the decision: an empty overlay on explore would read as governance where there is none, and silence about why it was skipped reads as an oversight to the next person who greps for the marker.

**D5** — **`sync` is not added to `authorize:`.** *Basis:* the `authorize:` vocabulary is commit, push, release, archive, and widening it changes what a repository can decide once and stop being asked about. That is a product decision about autonomy with its own consequences, and it is not required by anything here — this change tells the sync surface which gate governs it, which is true whether or not sync is ever standing-authorizable.

## Risks / Trade-offs

- **The overlay adds text to a surface an agent reads on every sync.** The body is kept to the statements that change behavior, matching the archive overlay's length; the token cost is the same one already accepted for three surfaces.
- **A repository that installed an earlier Keel has no sync overlay until it reinstalls.** That is true of every overlay change and is what `keel --doctor` reports; the derived label means the doctor now names sync as missing rather than staying silent about it.

## Hidden Knowledge / Assumptions

**A1** — Every target that receives the propose/apply/archive overlay also has a sync surface at the path the projection expects. *Basis:* `.claude/commands/opsx/sync.md`, `.claude/skills/openspec-sync-specs/SKILL.md`, and `.codex/skills/openspec-sync-specs/SKILL.md` all exist in this repository. *Owner:* the scenario installs into a fresh fixture and asserts the marker lands on the sync surface for each target, so a target whose sync surface is named differently fails rather than silently receiving nothing.

## Coupled Iteration Contract

Not required. No task in this change regenerates an artifact that must be verified together with its source.
