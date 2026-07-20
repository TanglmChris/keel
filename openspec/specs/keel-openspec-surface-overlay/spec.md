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

The apply overlay MUST require the current agent to select the task or small contiguous task group, obey the selected task contract, and personally review evidence before marking tasks complete.

#### Scenario: Apply overlay prevents ownership transfer

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says the current agent remains the Keel task owner
- **AND THEN** the overlay says target-native subagents return report/evidence only and cannot mark tasks complete

### Requirement: Archive surface enforces Keel archive ownership

The archive overlay MUST require the current agent to own sync/archive decisions and completion-gate review.

#### Scenario: Archive overlay prevents archive delegation

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says the current agent owns final sync/archive decisions
- **AND THEN** the overlay says target-native subagents cannot archive, sync, change acceptance, or bypass completion gates

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

