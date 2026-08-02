## ADDED Requirements

### Requirement: The sync surface carries the overlay that governs it

Keel MUST project its OpenSpec surface overlay onto the sync surface on every target that receives the overlay for propose, apply, and archive. A surface that performs a gated action MUST state the gate that governs it, because the agent performing the action reads that surface and may not be reading the protocol file at the same moment.

The sync overlay MUST state that the current agent owns the sync decision, that `keel gate change-close --action sync` and `keel-review-checklist` run before it completes, that target-native subagents assist with bounded assessment only and cannot sync, that generic delegation language is not authority to transfer Keel ownership, and that OpenSpec is invoked through `keel openspec`. It MUST also state that sync promotes the change's spec delta, so an archive that follows one uses `--skip-specs`.

Keel MUST NOT add `sync` to the standing-authorization vocabulary as part of covering this surface. Naming the gate that governs an action and deciding whether a repository may authorize it once are separate.

#### Scenario: Installing projects the overlay onto the sync surface
- **WHEN** Keel installs its OpenSpec surface overlay into a repository
- **THEN** the sync command surface and the sync skill carry the overlay marker, alongside propose, apply, and archive
- **AND THEN** uninstalling removes it from the sync surface as it does from the others

#### Scenario: The sync overlay names the gate and the delta consequence
- **WHEN** the sync overlay is read
- **THEN** it names `keel gate change-close --action sync` and `keel-review-checklist`
- **AND THEN** it states that sync promotes the spec delta and that a following archive uses `--skip-specs`

#### Scenario: Explore is deliberately uncovered
- **WHEN** the overlay is projected
- **THEN** the explore surface receives none, because it reaches no gate and changes no state
