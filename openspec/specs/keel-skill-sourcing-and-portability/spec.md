# keel-skill-sourcing-and-portability Specification

## Purpose
TBD - created by archiving change skill-sourcing-and-portability-policy. Update Purpose after archive.
## Requirements
### Requirement: Dedicated skill guidance is evidence-led

Keel MUST require a new or materially expanded dedicated skill to be grounded
in durable source research, provenance and license review, realistic trigger
cases, and real-task evaluation before its implementation task is complete.

#### Scenario: Authoring a dedicated skill
- **WHEN** a Keel change proposes a new or materially expanded dedicated skill
- **THEN** its OpenSpec design or task evidence identifies first-party or
  otherwise authoritative sources and explains what non-obvious expertise the
  skill contributes
- **AND THEN** it records source provenance, license implications, realistic
  positive and negative trigger cases, and the required real-task evidence

#### Scenario: Source authority is missing
- **WHEN** a proposed dedicated skill lacks adequate domain sources or license
  authority
- **THEN** Keel keeps the skill task non-executable or limits it to a
  read-only research spike
- **AND THEN** the agent does not invent domain authority or copy unlicensed
  external skill content

#### Scenario: External patterns are adapted
- **WHEN** Keel learns from an external skill whose content is not being
  vendored
- **THEN** Keel records the source and writes original guidance from the
  reusable pattern
- **AND THEN** external content is copied only when its license permits the use
  and required attribution is preserved

### Requirement: Keel skills have one portable authority

Each Keel-maintained skill MUST have one canonical source whose portable
`SKILL.md` semantics are preserved across every declared target projection.

#### Scenario: Building declared target copies
- **WHEN** Keel builds a skill declared for Claude, Codex, and OpenCode
- **THEN** each generated target contains the canonical skill name,
  description, instructions, and bundled resources
- **AND THEN** deterministic validation detects a missing, stale, or divergent
  declared target projection

#### Scenario: Adding runtime-specific metadata
- **WHEN** a target supports UI metadata or plugin wiring beyond the Agent
  Skills portable format
- **THEN** Keel keeps that metadata additive and outside the portable skill
  authority
- **AND THEN** target metadata does not redefine the skill's behavior,
  ownership, or trigger meaning

### Requirement: Runtime discovery remains target-native

Keel MUST install portable skills into target-native surfaces without becoming
the runtime authority for skill discovery or activation.

#### Scenario: Installing a portable skill
- **WHEN** Keel installs a core skill or explicitly selected lens for a
  target
- **THEN** it writes the packaged skill to that target's supported skill root
- **AND THEN** the target runtime remains responsible for discovery and
  activation

#### Scenario: Diagnosing file presence
- **WHEN** Keel check or doctor observes a skill file at the expected target
  path
- **THEN** Keel may report packaged file presence and integrity
- **AND THEN** it does not claim native activation without runtime evidence

#### Scenario: Optional guidance remains optional
- **WHEN** Keel installs into a project without an explicitly selected or
  already-installed domain lens
- **THEN** it does not install optional lens or dedicated stack guidance
- **AND THEN** no discovery registry or handoff state is created to compensate

### Requirement: Skill quality uses progressive and behavioral evidence

Keel MUST evaluate skill quality with deterministic structural checks and
proportionate semantic behavior evidence. Deterministic assertions on skill
text MUST pin document structure and spec-traceable contract anchors, not
editorial prose.

#### Scenario: Validating discovery metadata
- **WHEN** a Keel-maintained skill is added or materially changed
- **THEN** deterministic validation checks Agent Skills-compatible naming,
  description specificity, referenced resource paths, manifest routing, and
  declared-target projection integrity

#### Scenario: Evaluating trigger behavior
- **WHEN** a task changes a skill's discovery description or scope
- **THEN** its Evidence records realistic prompts that should trigger and
  near-miss prompts that should not trigger the skill
- **AND THEN** semantic Review states whether those cases distinguish the skill
  from adjacent skills and generic agent behavior

#### Scenario: Evaluating task behavior
- **WHEN** a task adds or materially changes procedural skill guidance
- **THEN** Commands or explicit smoke evidence exercise at least one real task
  through the intended public workflow
- **AND THEN** detailed conditional knowledge lives in referenced resources
  when it is not required on every activation

#### Scenario: Deterministic text assertions stay spec-traceable
- **WHEN** deterministic validation asserts on the literal text of a
  Keel-maintained skill
- **THEN** every pinned exact phrase is a short contract anchor traceable to a
  requirement or scenario of a governing capability spec
- **AND THEN** editorial wording that no durable authority names may be
  rewritten without touching the validator

### Requirement: Generic lenses and dedicated skills remain separate

Keel MUST keep generic lenses limited to cross-stack authoring and
verification while concrete stack guidance remains project- or
plugin-owned.

#### Scenario: Guidance is cross-stack
- **WHEN** guidance applies across a domain regardless of framework or vendor
- **THEN** Keel may place its risk prompts, durable artifact placement, and
  evidence expectations in a generic optional lens

#### Scenario: Guidance is stack-specific
- **WHEN** guidance depends on a framework, vendor API, tool command, or team
  convention
- **THEN** Keel keeps it in a project or plugin skill with its own sourcing and
  quality evidence
- **AND THEN** it does not make that guidance Keel Core authority

### Requirement: keel-* skills are plugin-delivered, not CLI-installed

Keel's `keel-*` behavioral skills MUST be delivered through the installed Keel
plugin (shipped in `plugins/keel/skills/`), and the thin CLI installer MUST NOT
copy them into any target's skill root. `keel --init` / `keel --install` MUST NOT
create `keel-*` skill files, no installer code path may source `keel-*` skills
from the retired `dist/` tree, and Keel's own surfaces MUST describe this delivery
truthfully.

#### Scenario: CLI init creates no keel-* skill files

- **WHEN** `keel --init` or `keel --install` runs for any target
- **THEN** it creates no `keel-*` skill files under the target's skill root
- **AND THEN** no installer code path attempts to source `keel-*` skills from `dist/`

#### Scenario: The plugin carries the keel-* skills

- **WHEN** the Keel package is published
- **THEN** the `keel-*` skills ship inside `plugins/keel/skills/` via the package `files` list
- **AND THEN** the installed plugin is the single delivery surface for those skills

#### Scenario: CLI help states plugin delivery

- **WHEN** `keel --help` describes where the `keel-*` skills come from
- **THEN** it states they are delivered by the Keel plugin
- **AND THEN** it does not claim the CLI installs them under a target skill root

