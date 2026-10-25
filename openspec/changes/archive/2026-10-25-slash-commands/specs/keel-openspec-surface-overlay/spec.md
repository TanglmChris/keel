## MODIFIED Requirements

### Requirement: Archive surface binds archiving to its gate

The archive overlay MUST state that archiving is gated by `keel gate change-close` and `review-checklist`, and that follow-up ownership is verified before it. The overlay MUST direct the agent to consult the repository's standing authorization for the archive action rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared. It MUST NOT restrict what a subagent may do.

#### Scenario: Archive overlay names its gate

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay names `keel gate change-close` and `review-checklist`
- **AND THEN** it contains no sentence limiting subagents to assessment or barring them from archiving

#### Scenario: Archive overlay routes confirmation to the declaration

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says a repository that standing-authorizes `archive` does not need the per-occurrence archive confirmation
- **AND THEN** the overlay says the completion gate and follow-up ownership checks still run unchanged

### Requirement: Keel overlays Codex and Claude propose authoring surfaces
Keel MUST add one managed authoring overlay to OpenSpec propose surfaces for Codex and Claude that invokes expectation alignment before specs and executable tasks finalize while preserving official OpenSpec artifact order, paths, and templates.

#### Scenario: Codex propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Codex target after this change
- **THEN** the installed OpenSpec propose skill and applicable Codex command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through `align-expectations`

#### Scenario: Claude propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Claude target after this change
- **THEN** the installed OpenSpec propose skill and applicable Claude command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through the same portable skill authority

#### Scenario: OpenCode receives no v4 authoring overlay
- **WHEN** Keel handles an OpenCode compatibility target during v4
- **THEN** existing portable OpenSpec artifacts remain readable and manual
- **AND THEN** Keel does not create a new OpenCode-specific alignment overlay, discovery file, or automation path

### Requirement: The sync surface carries the overlay that governs it

Keel MUST project its OpenSpec surface overlay onto the sync surface on every target that receives the overlay for propose, apply, and archive. A surface that performs a gated action MUST state the gate that governs it, because the agent performing the action reads that surface and may not be reading the protocol file at the same moment.

The sync overlay MUST state that `keel gate change-close --action sync` and `review-checklist` run before it completes, and that OpenSpec is invoked through `keel openspec`. It MUST also state that sync promotes the change's spec delta, so an archive that follows one uses `--skip-specs`. It MUST NOT restrict what a subagent may do.

Keel MUST NOT add `sync` to the standing-authorization vocabulary as part of covering this surface. Naming the gate that governs an action and deciding whether a repository may authorize it once are separate.

#### Scenario: Installing projects the overlay onto the sync surface
- **WHEN** Keel installs its OpenSpec surface overlay into a repository
- **THEN** the sync command surface and the sync skill carry the overlay marker, alongside propose, apply, and archive
- **AND THEN** uninstalling removes it from the sync surface as it does from the others

#### Scenario: The sync overlay names the gate and the delta consequence
- **WHEN** the sync overlay is read
- **THEN** it names `keel gate change-close --action sync` and `review-checklist`
- **AND THEN** it states that sync promotes the spec delta and that a following archive uses `--skip-specs`

#### Scenario: Explore is deliberately uncovered
- **WHEN** the overlay is projected
- **THEN** the explore surface receives none, because it reaches no gate and changes no state
