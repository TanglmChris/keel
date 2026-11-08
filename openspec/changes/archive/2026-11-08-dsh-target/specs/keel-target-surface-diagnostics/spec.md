## ADDED Requirements

### Requirement: DSH is a target that shares Codex's repository surface

`--target dsh` MUST be accepted by `--init`, `--install`, `--check`, `--doctor`, `--clear`, `--uninstall`, `keel capabilities` and `keel project`. It MUST write, check and remove exactly the repository files `--target codex` does, and MUST NOT create a DSH-only copy of the skills or protocol. `keel capabilities --target dsh` and `keel project --target dsh` MUST report target `dsh`, all six behaviors as `manual`, and evidence naming what was probed: DSH's factory profiles carry no session-start, resume or compaction hook and the `AGENTS.md` bootstrap is the entry.

#### Scenario: Init for DSH writes the Codex surface and doctor reports DSH
- **WHEN** `keel --init --target dsh` runs in an empty repository and `keel --doctor --target dsh` follows
- **THEN** the repository holds the `AGENTS.md` bootstrap and the OpenSpec skills under `.agents/skills`, and nothing under `.dsh/` or `.claude/`
- **AND THEN** doctor reports `bootstrap: ok`, the capabilities heading `Target capabilities (dsh):` with every behavior `manual`, and the DSH lines `DSH hooks: manual` and `DSH surface: ok`

#### Scenario: Capabilities for DSH are manual and say what was probed
- **WHEN** `keel capabilities --target dsh --json` runs
- **THEN** the target is `dsh`, the six capabilities are all `manual`, and the evidence states that DSH has no session-start, resume or compaction hook and that the `AGENTS.md` bootstrap is the entry

#### Scenario: Project for DSH has the structure of the other targets
- **WHEN** `keel project --target dsh --event startup --json` runs where `keel project --target codex --event startup --json` returns a result
- **THEN** both results carry the same keys and DSH's target field reads `dsh`

#### Scenario: A missing DSH binary is reported and does not fail doctor
- **WHEN** `keel --doctor --target dsh` runs with no `dsh` on PATH
- **THEN** it reports `DSH CLI: not found` and exits 0
- **AND WHEN** a `dsh` that prints a version is on PATH, doctor reports `DSH CLI: ok` with that version

#### Scenario: Uninstall for DSH says the surface is shared
- **WHEN** `keel --uninstall --target dsh --dry-run` runs in a repository initialized for DSH
- **THEN** it says the files are shared with Codex and lists the same removals `--target codex` lists
