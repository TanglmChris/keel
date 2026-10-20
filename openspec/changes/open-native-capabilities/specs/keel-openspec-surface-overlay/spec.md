## ADDED Requirements

### Requirement: Apply surface binds work to the task contract

The apply overlay MUST direct the agent through the unchecked tasks of an approved `tasks.md` in order, each started by `keel gate task-start` and completed by `keel gate task-complete`, with every stop trigger still halting. It MUST route confirmations to the repository's standing authorization without removing an undeclared one, and MUST NOT restrict what a subagent may do.

#### Scenario: Apply overlay continues through an approved task list

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says the agent works through the unchecked tasks of an approved `tasks.md` in order, each through its own `task-start` and `task-complete`
- **AND THEN** it says a stop trigger still halts

#### Scenario: Apply overlay routes confirmation to the declaration

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says a standing-authorized action proceeds without a per-occurrence confirmation
- **AND THEN** the overlay says an undeclared action still requires the confirmation it requires today
- **AND THEN** the overlay says a standing authorization never substitutes for a gate, evidence, or Review

### Requirement: Archive surface binds archiving to its gate

The archive overlay MUST state that archiving is gated by `keel gate change-close` and `keel-review-checklist`, and that follow-up ownership is verified before it. The overlay MUST direct the agent to consult the repository's standing authorization for the archive action rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared. It MUST NOT restrict what a subagent may do.

#### Scenario: Archive overlay names its gate

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay names `keel gate change-close` and `keel-review-checklist`
- **AND THEN** it contains no sentence limiting subagents to assessment or barring them from archiving

#### Scenario: Archive overlay routes confirmation to the declaration

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says a repository that standing-authorizes `archive` does not need the per-occurrence archive confirmation
- **AND THEN** the overlay says the completion gate and follow-up ownership checks still run unchanged

### Requirement: Subagents are the model's choice and are treated as the main agent is

Keel's resident protocol, consumer bootstrap, and generated overlays MUST state that a subagent is the model's choice and is treated as the main agent is, and that the gates, the `Touch` write guard, and the evidence rules apply to whoever runs a step. They MUST NOT require activation, a brief, a guard manifest, a tier declaration, or a rerun by another agent before a subagent may act. They MUST NOT encourage or discourage subagent use, parallelism, number, or a concrete model.

#### Scenario: The neutral sentence is all the surfaces say
- **WHEN** the protocol, the bootstrap, or a generated apply, archive, or sync surface is read
- **THEN** it states that a subagent is the model's choice and is treated as the main agent is
- **AND THEN** it names no helper/delegate split, mandatory brief, refusal without a guard manifest, or rerun duty

## MODIFIED Requirements

### Requirement: The sync surface carries the overlay that governs it

Keel MUST project its OpenSpec surface overlay onto the sync surface on every target that receives the overlay for propose, apply, and archive. A surface that performs a gated action MUST state the gate that governs it, because the agent performing the action reads that surface and may not be reading the protocol file at the same moment.

The sync overlay MUST state that `keel gate change-close --action sync` and `keel-review-checklist` run before it completes, and that OpenSpec is invoked through `keel openspec`. It MUST also state that sync promotes the change's spec delta, so an archive that follows one uses `--skip-specs`. It MUST NOT restrict what a subagent may do.

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

## REMOVED Requirements

### Requirement: Apply surface enforces Keel task ownership
**Reason**: #414 — the owner decided subagents are treated as the main agent is, so no surface assigns ownership of a step to one agent or limits subagents to report/evidence.
**Migration**: replaced by "Apply surface binds work to the task contract", which keeps the confirmation-routing scenario and adds continuing through an approved task list.

### Requirement: Archive surface enforces Keel archive ownership
**Reason**: #414 — archiving is bound by `keel gate change-close` and `keel-review-checklist`, which apply to whoever runs them; the ownership clause and the subagent bar are removed.
**Migration**: replaced by "Archive surface binds archiving to its gate", which keeps the confirmation-routing scenario.

### Requirement: Target-native subagent gate is documented
**Reason**: #414 — the helper/delegate split, the guard precondition, and the rerun duty are removed from model-facing text.
**Migration**: replaced by "Subagents are the model's choice and are treated as the main agent is".
