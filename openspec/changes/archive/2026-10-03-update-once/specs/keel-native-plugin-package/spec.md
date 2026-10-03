## ADDED Requirements

### Requirement: One owner-run update covers every installed Keel component

`keel --update` MUST update the global CLI and then, for each of Claude Code and Codex whose executable resolves and whose `plugin list --json` reports `keel` installed, update that host's Keel plugin through the host's own documented commands. It MUST report exactly one status line per component — the CLI, the Claude plugin, and the Codex plugin — naming the version before and after, when the update takes effect, and any step the owner must still take. A host that is absent or has no Keel plugin MUST be reported `absent` and MUST NOT fail the command. A Codex marketplace whose source is not a Git repository MUST be reported `manual`, naming its source and the command that would make it upgradable, and MUST NOT be re-pointed. When Codex's hook definitions differ between the installed and the new plugin, the Codex line MUST say Codex will ask for review before those hooks run. The exit status MUST be nonzero only when a step that ran failed. `--dry-run` MUST print each planned command and run none. No hook or projection MAY invoke this behavior.

#### Scenario: Both plugins are updated and each line says when it applies
- **WHEN** `claude` and `codex` both report Keel installed at an older version, from a Git marketplace, and `keel --update` runs
- **THEN** each host's documented update commands run once, in order, after the CLI update
- **AND THEN** the output carries one line per component naming the old and new version, that the Claude plugin applies to running sessions at their next hook call with skills and agents after `/reload-plugins`, and that the Codex plugin applies at the next hook call

#### Scenario: An absent host is not a failure
- **WHEN** `codex` does not resolve, or reports no Keel plugin
- **THEN** the Codex line reads `absent`, no Codex command runs, and the exit status reflects only the steps that ran

#### Scenario: A local Codex marketplace is reported, not re-pointed
- **WHEN** Codex reports the Keel marketplace with a non-Git source
- **THEN** the Codex line reads `manual`, names the source path and `codex plugin marketplace add TanglmChris/keel --ref main`, and no marketplace command runs

#### Scenario: Changed Codex hook definitions are named
- **WHEN** the new Codex plugin's `hooks/codex.json` differs from the installed one
- **THEN** the Codex line says Codex will ask for review in `/hooks` before the changed hooks run

#### Scenario: A failed host step fails the command and says which
- **WHEN** a host update command exits nonzero
- **THEN** that component's line reads `failed` with the command, the other components still report, and `keel --update` exits nonzero

#### Scenario: A dry run runs nothing
- **WHEN** `keel --update --dry-run` runs
- **THEN** it prints the planned CLI and host commands and invokes no host command and no install
