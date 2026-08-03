## Purpose

Define Keel's managed overlay for OpenSpec-generated apply/archive target surfaces and the target-native subagent gate.
## Requirements
### Requirement: Keel overlays apply and archive surfaces

Keel MUST maintain a managed overlay on OpenSpec-generated apply/archive skills and command entries for each supported target. The overlay MUST state that Keel rules take precedence over conflicting generic OpenSpec instructions.

#### Scenario: Claude apply and archive surfaces receive the overlay

- **WHEN** `keel --init --target claude` runs in a repository
- **THEN** `.claude/skills/openspec-apply-change/SKILL.md` and `.claude/skills/openspec-archive-change/SKILL.md` contain the Keel overlay marker
- **AND THEN** `.claude/commands/opsx/apply.md` and `.claude/commands/opsx/archive.md` contain the Keel overlay marker

#### Scenario: Codex apply and archive surfaces receive the overlay

- **WHEN** `keel --init --target codex` runs with `CODEX_HOME` set
- **THEN** `.codex/skills/openspec-apply-change/SKILL.md` and `.codex/skills/openspec-archive-change/SKILL.md` contain the Keel overlay marker
- **AND THEN** `<CODEX_HOME>/prompts/opsx-apply.md` and `<CODEX_HOME>/prompts/opsx-archive.md` contain the Keel overlay marker
- **AND THEN** the user's real `.codex/prompts` directory is not required for verification

#### Scenario: OpenCode apply and archive surfaces receive the overlay

- **WHEN** `keel --init --target opencode` runs in a repository
- **THEN** `.opencode/skills/openspec-apply-change/SKILL.md` and `.opencode/skills/openspec-archive-change/SKILL.md` contain the Keel overlay marker
- **AND THEN** `.opencode/commands/opsx-apply.md` and `.opencode/commands/opsx-archive.md` contain the Keel overlay marker

### Requirement: Keel refreshes existing overlays idempotently

Keel MUST replace an existing managed overlay block instead of duplicating it, and MUST skip missing OpenSpec files during `keel --install` instead of creating incomplete generated surfaces.

#### Scenario: Install refreshes an existing overlay

- **WHEN** an initialized target has an apply/archive OpenSpec file with an outdated Keel overlay block
- **AND WHEN** `keel --install --target <target>` runs
- **THEN** the file contains exactly one current Keel overlay block
- **AND THEN** other OpenSpec-generated content remains present

#### Scenario: Install skips missing OpenSpec files

- **WHEN** `keel --install --target <target>` runs before OpenSpec has generated apply/archive files
- **THEN** Keel does not create placeholder OpenSpec apply/archive files
- **AND THEN** `keel --doctor --target <target>` reports the missing overlay or missing surface with remediation

### Requirement: Apply surface enforces Keel task ownership

The apply overlay MUST require the current agent to select the task or small contiguous task group, obey the selected task contract, and personally review evidence before marking tasks complete. The overlay MUST direct the agent to consult the repository's standing authorization rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared.

#### Scenario: Apply overlay prevents ownership transfer

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says the current agent remains the Keel task owner
- **AND THEN** the overlay says target-native subagents return report/evidence only and cannot mark tasks complete

#### Scenario: Apply overlay routes confirmation to the declaration

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says a standing-authorized action proceeds without a per-occurrence confirmation
- **AND THEN** the overlay says an undeclared action still requires the confirmation it requires today
- **AND THEN** the overlay says a standing authorization never substitutes for a gate, evidence, or Review

### Requirement: Archive surface enforces Keel archive ownership

The archive overlay MUST require the current agent to own sync/archive decisions and completion-gate review. The overlay MUST direct the agent to consult the repository's standing authorization for the archive action rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared.

#### Scenario: Archive overlay prevents archive delegation

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says the current agent owns final sync/archive decisions
- **AND THEN** the overlay says target-native subagents cannot archive, sync, change acceptance, or bypass completion gates

#### Scenario: Archive overlay routes confirmation to the declaration

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says a repository that standing-authorizes `archive` does not need the per-occurrence archive confirmation
- **AND THEN** the overlay says the completion gate and follow-up ownership checks still run unchanged

### Requirement: Target-native subagent gate is documented

Keel resident protocol text MUST describe the target-native subagent gate without forbidding bounded same-target helper use.

#### Scenario: Resident protocol allows bounded target-native helpers

- **WHEN** Keel installs resident protocol text for Claude Code, Codex, or OpenCode
- **THEN** the text says the current agent owns Keel execution decisions
- **AND THEN** the text allows bounded target-native subagents as helpers when the current agent decides they are useful
- **AND THEN** the text prohibits cross-runtime delegation or Keel ownership transfer unless the selected task or user explicitly authorizes it

### Requirement: Keel overlays Codex and Claude propose authoring surfaces
Keel MUST add one managed authoring overlay to OpenSpec propose surfaces for Codex and Claude that invokes expectation alignment before specs and executable tasks finalize while preserving official OpenSpec artifact order, paths, and templates.

#### Scenario: Codex propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Codex target after this change
- **THEN** the installed OpenSpec propose skill and applicable Codex command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through `keel-align-expectations`

#### Scenario: Claude propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Claude target after this change
- **THEN** the installed OpenSpec propose skill and applicable Claude command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through the same portable skill authority

#### Scenario: OpenCode receives no v4 authoring overlay
- **WHEN** Keel handles an OpenCode compatibility target during v4
- **THEN** existing portable OpenSpec artifacts remain readable and manual
- **AND THEN** Keel does not create a new OpenCode-specific alignment overlay, discovery file, or automation path

### Requirement: Apply returns newly discovered expectations to alignment
The existing apply overlay MUST require the current agent to stop and return to authoring alignment when implementation exposes a material expectation, acceptance boundary, or user-owned decision absent from durable authority.

#### Scenario: Implementation discovers missing product authority
- **WHEN** implementation encounters a material behavior or boundary not covered by the task capsule and OpenSpec artifacts
- **THEN** apply stops before accepting or implementing that choice
- **AND THEN** the current agent reruns alignment and reauthors affected proposal/design/spec/task authority

#### Scenario: Implementation discovers a factual detail
- **WHEN** implementation discovers a repository fact that does not change accepted behavior or scope
- **THEN** the current agent may record the fact and continue within the existing task boundary
- **AND THEN** it does not invoke a product interview unnecessarily

### Requirement: Thin CLI owns OpenSpec initialization and overlays only
After native plugin migration, `keel --init/--install` MUST use official OpenSpec 1.5.0 to initialize or refresh action skills/commands, install Keel schema and managed authoring/apply/archive overlays, and merge minimal bootstrap guidance. It MUST NOT copy Keel plugin skills, hooks, adapters, or full protocol assets into target-specific project trees.

#### Scenario: Codex init uses plugin plus official OpenSpec
- **WHEN** a Codex project with the Keel plugin runs `keel --init --target codex`
- **THEN** OpenSpec action skills/prompts, Keel schema/overlays, and minimal bootstrap are ready
- **AND THEN** Keel skills/hooks remain supplied by the installed plugin

#### Scenario: Claude init uses plugin plus official OpenSpec
- **WHEN** a Claude project with the Keel plugin runs `keel --init --target claude`
- **THEN** OpenSpec action skills/commands, Keel schema/overlays, AGENTS bootstrap/import, and plugin diagnostics are ready
- **AND THEN** no `.claude/skills/keel-*`, `.claude/hooks/keel-*`, or adapter copy is created by the CLI

#### Scenario: Plugin is missing
- **WHEN** init succeeds for schema/OpenSpec/bootstrap but the native plugin is absent
- **THEN** doctor reports the partial state and native plugin install remediation
- **AND THEN** explicit Keel Core commands remain available

### Requirement: Overlay refresh preserves official and user content
The thin CLI MUST update one managed overlay block in each supported official OpenSpec surface, preserve other generated/user content, and diagnose missing surfaces without manufacturing incomplete OpenSpec files.

#### Scenario: OpenSpec update changes generated content
- **WHEN** OpenSpec 1.5.0 or later refreshes an action skill or command
- **THEN** Keel reapplies exactly one current overlay without replacing the official content

#### Scenario: Surface is missing
- **WHEN** install runs before OpenSpec generated an overlay target
- **THEN** Keel skips that target and doctor reports the official init/update remediation

### Requirement: Keel makes openspec invocable for skill-driven agents

Keel MUST provide a `keel openspec` passthrough that forwards its arguments to
Keel's resolved openspec command, and Keel's overlays MUST direct skill-driven
agents to use it in place of a bare `openspec` command that may not be on PATH.

#### Scenario: Passthrough invokes the resolved openspec

- **WHEN** `keel openspec` runs with arguments
- **THEN** Keel forwards the arguments to its resolved openspec command
- **AND THEN** the passthrough works even when bare `openspec` is not on PATH

#### Scenario: Overlays direct agents to the passthrough

- **WHEN** an apply or archive overlay references invoking openspec directly
- **THEN** it directs the agent to `keel openspec` rather than a bare `openspec` that may be unavailable

### Requirement: Archive overlay skips already-promoted specs and reminds to clear the guard

The archive overlay MUST sequence `/opsx:sync` before archive and direct the
archive to pass `--skip-specs` so a delta already promoted by sync is not
re-applied, and MUST remind the current agent to run `keel guard clear` after
archiving. The gate itself remains read-only and writes nothing.

#### Scenario: Archive after sync skips specs

- **WHEN** the archive overlay guides a change whose delta was promoted through `/opsx:sync`
- **THEN** it directs the archive to pass `--skip-specs`
- **AND THEN** it explains this avoids re-applying the already-promoted delta, which upstream openspec rejects

#### Scenario: Archive reminds to clear the guard

- **WHEN** the archive overlay guides a completed archive
- **THEN** it reminds the current agent to run `keel guard clear`
- **AND THEN** the gate performs no guard deletion itself, preserving the read-only guard invariant

### Requirement: The consumer bootstrap names the record-write exemption

The bootstrap is the whole resident protocol a consumer repository receives, and
it is the only place many consumers will ever read what Touch bounds. Saying
Touch is the write boundary "for product files" is accurate but relies on the
reader inferring what the qualifier excludes; the inference that actually gets
made is that the task's own `tasks.md` must be declared in Touch, which is the
misreading that produced a reported defect.

The bootstrap MUST name the exemption outright: a task's own change directory is
writable without being declared in Touch. Because the block is under a byte
budget, the room MUST be found by dropping lower-value content rather than by
raising the budget — the budget exists so resident context stays cheap, and
raising it to fit each addition removes the pressure that keeps it short.

#### Scenario: A consumer learns the exemption from the bootstrap alone

- **WHEN** a consumer repository's installed bootstrap is read
- **THEN** it states that Touch bounds product writes and that the change's own directory is exempt
- **AND THEN** a reader does not have to infer the exemption from a qualifier

#### Scenario: The block stays within its budget

- **WHEN** the bootstrap block is measured after the exemption is named
- **THEN** it is still under the byte and line budgets, which are unchanged
- **AND THEN** the content dropped to make room is named in the change that dropped it

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

### Requirement: Uninstalling removes the overlay it installed

The overlay is written into files OpenSpec owns, and every line of it is about Keel — the gate to run, the checklist to run, how to invoke OpenSpec, where standing authorization is declared. Once Keel is removed those instructions name commands that no longer exist, in files that were never Keel's. `keel --uninstall` and `keel --clear` MUST therefore remove the overlay block from every surface that installing projects it onto, on every target, driven by the same surface list that writes it so that a surface added to one direction cannot be missed by the other.

The removal MUST take the overlay block and the whitespace separating it from the content before it, and nothing else. The file MUST be preserved: the bytes that preceded the overlay MUST be unchanged, and a surface MUST NOT be deleted or emptied because its Keel block was removed. Removing the block is the whole obligation — restoring the file to its pristine upstream state is `openspec update`'s concern, not uninstall's.

A `--dry-run` uninstall MUST report each surface it would clean and MUST write nothing, because a plan that reports nothing for a run that writes is the failure mode this surface has already produced once on the install side.

A surface carrying no overlay, and a surface whose file does not exist, MUST be counted rather than treated as an error, so that uninstalling twice, or uninstalling a repository that never received the overlay, succeeds.

#### Scenario: Uninstalling removes the overlay from every surface installing wrote it to
- **WHEN** a repository is installed and then uninstalled on any target
- **THEN** no surface that received the overlay still carries the marker, including surfaces outside the repository such as the Codex prompt directory
- **AND THEN** the surfaces are the ones the shared surface list names, not a second list written beside it

#### Scenario: The surrounding OpenSpec content survives
- **WHEN** the overlay is removed from a surface
- **THEN** the file still exists and its content is exactly the bytes that preceded the overlay
- **AND THEN** the blank line the install side inserted before the block is removed with it, so the file does not end in trailing blank lines

#### Scenario: A dry run reports the removal without performing it
- **WHEN** `--uninstall` runs with `--dry-run` against an installed repository
- **THEN** each surface that would be cleaned is named in the output
- **AND THEN** every surface still carries its overlay afterwards

#### Scenario: Uninstalling twice is not an error
- **WHEN** uninstall runs against a repository whose surfaces carry no overlay, or whose surface files are absent
- **THEN** it succeeds, reporting nothing removed rather than failing
