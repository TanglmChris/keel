## ADDED Requirements

### Requirement: The configuration file and the Chinese docs follow their sources
`keel/config.yaml` MUST document each declaration in `CONFIG_DECLARATIONS` exactly once, in that order. Each `docs/*.zh-CN.md` MUST carry the same number of headings and code fences as its English page and name every `keel` command that page names.

#### Scenario: The configuration file documents its declarations in order
- **WHEN** the validator reads the `# <name> (optional):` comment blocks of `keel/config.yaml`
- **THEN** each declaration of `CONFIG_DECLARATIONS` has exactly one, in that order

#### Scenario: A Chinese doc matches its English page
- **WHEN** `docs/<page>.zh-CN.md` exists
- **THEN** its heading and code-fence counts equal those of `docs/<page>.md`
- **AND THEN** it names every `keel` command `docs/<page>.md` names
