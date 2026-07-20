## ADDED Requirements

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
