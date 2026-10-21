## MODIFIED Requirements

### Requirement: Keel overlays every action in the managed set

Keel MUST maintain a managed overlay on the OpenSpec-generated skills of every action in the managed set — `propose`, `apply`, `archive`, and `sync` — for each supported target, except where a target has no surface for an action, and on any OpenSpec command entry for those actions that a repository still holds. The overlay MUST state that Keel rules take precedence over conflicting generic OpenSpec instructions.

The requirement MUST name the set rather than a subset of it. Each action's overlay content is stated by its own requirement below; this one states which actions have an overlay at all, and a statement that names two of four leaves the file disagreeing with itself.

#### Scenario: Claude surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target claude` runs in a repository
- **THEN** the `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.claude/skills/` each contain the Keel overlay marker
- **AND THEN** no file exists under `.claude/commands/opsx/`

#### Scenario: Codex surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target codex` runs with `CODEX_HOME` set
- **THEN** the same four skills under `.codex/skills/` each contain the Keel overlay marker
- **AND THEN** `<CODEX_HOME>/prompts/opsx-propose.md`, `opsx-apply.md`, `opsx-archive.md`, and `opsx-sync.md` each contain the Keel overlay marker
- **AND THEN** the user's real `.codex/prompts` directory is not required for verification

#### Scenario: OpenCode surfaces receive the overlay for the actions it has

- **WHEN** `keel --init --target opencode` runs in a repository
- **THEN** the `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.opencode/skills/` each contain the Keel overlay marker
- **AND THEN** no `opsx-*.md` file exists under `.opencode/commands/`
- **AND THEN** no authoring overlay is written for `propose`, which this target does not receive

#### Scenario: A command file a repository still holds keeps its overlay

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` from an earlier `both` delivery and `keel --install --target claude` runs
- **THEN** that file carries the Keel overlay marker alongside the skills

### Requirement: Thin CLI owns OpenSpec initialization and overlays only
After native plugin migration, `keel --init/--install` MUST use official OpenSpec 1.5.0 to initialize or refresh action skills, install Keel schema and managed authoring/apply/archive/sync overlays, and merge minimal bootstrap guidance. It MUST NOT copy Keel plugin skills, hooks, adapters, or full protocol assets into target-specific project trees.

#### Scenario: Codex init uses plugin plus official OpenSpec
- **WHEN** a Codex project with the Keel plugin runs `keel --init --target codex`
- **THEN** OpenSpec action skills/prompts, Keel schema/overlays, and minimal bootstrap are ready
- **AND THEN** Keel skills/hooks remain supplied by the installed plugin

#### Scenario: Claude init uses plugin plus official OpenSpec
- **WHEN** a Claude project with the Keel plugin runs `keel --init --target claude`
- **THEN** OpenSpec action skills, Keel schema/overlays, AGENTS bootstrap/import, and plugin diagnostics are ready
- **AND THEN** no `.claude/skills/keel-*`, `.claude/hooks/keel-*`, or adapter copy is created by the CLI

#### Scenario: Plugin is missing
- **WHEN** init succeeds for schema/OpenSpec/bootstrap but the native plugin is absent
- **THEN** doctor reports the partial state and native plugin install remediation
- **AND THEN** explicit Keel Core commands remain available

### Requirement: Archive overlay skips already-promoted specs and reminds to clear the guard

The archive overlay MUST sequence the `openspec-sync-specs` skill before archive and direct the
archive to pass `--skip-specs` so a delta already promoted by sync is not
re-applied, and MUST remind the current agent to run `keel guard clear` after
archiving. The gate itself remains read-only and writes nothing.

#### Scenario: Archive after sync skips specs

- **WHEN** the archive overlay guides a change whose delta was promoted through the `openspec-sync-specs` skill
- **THEN** it directs the archive to pass `--skip-specs`
- **AND THEN** it explains this avoids re-applying the already-promoted delta, which upstream openspec rejects

#### Scenario: Archive reminds to clear the guard

- **WHEN** the archive overlay guides a completed archive
- **THEN** it reminds the current agent to run `keel guard clear`
- **AND THEN** the gate performs no guard deletion itself, preserving the read-only guard invariant

## ADDED Requirements

### Requirement: Keel generates OpenSpec workflows as skills only

Every OpenSpec `init` and `update` Keel runs — from `keel --init` and from `keel openspec init|update` — MUST use the user's global OpenSpec configuration with `delivery` replaced by `skills`. Keel MUST NOT write the global configuration, and other `keel openspec` subcommands MUST run against it unchanged.

#### Scenario: A global both delivery still yields skills only

- **WHEN** the user's global OpenSpec configuration declares `delivery: both` and `keel --init --target claude` runs
- **THEN** the five workflow skills exist under `.claude/skills/`, no file exists under `.claude/commands/opsx/`, and no generated skill names an `/opsx:` command
- **AND THEN** the global configuration file is byte-for-byte unchanged

#### Scenario: Command files from a both delivery are removed

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` and `keel --init --target claude` runs
- **THEN** that file no longer exists

#### Scenario: A pass-through update generates skills only

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` and `keel openspec update --force` runs in it
- **THEN** that file no longer exists and the skills carry the Keel overlay
- **AND THEN** `keel openspec config list` still reports the user's own `delivery`

### Requirement: Shipped guidance names the OpenSpec workflows by skill

The archive overlay, `README.md`, `README.zh-CN.md`, the Keel skills, and the Keel OpenSpec schema MUST name the OpenSpec workflows by their skill names — `openspec-propose`, `openspec-apply-change`, `openspec-sync-specs`, `openspec-archive-change`, `openspec-explore` — and MUST NOT name an `/opsx:` command, since Keel generates none.

#### Scenario: No shipped guidance names an opsx command

- **WHEN** the archive overlay text, both READMEs, every `SKILL.md` under `src/skills/` and `plugins/keel/skills/`, and `assets/openspec/schemas/keel-spec-driven/schema.yaml` are read
- **THEN** none contains `/opsx:`
- **AND THEN** the archive overlay names `openspec-sync-specs`
