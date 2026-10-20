## ADDED Requirements

### Requirement: Both READMEs state the CLI and carry the same sections
`README.md` MUST name every subcommand and flag that `keel --help` lists, every standing-authorization name the code accepts, and every exit code the CLI returns, and MUST NOT restate a limit the protocol removed. `README.zh-CN.md` MUST meet the same command and name checks and carry the same number of `##` and `###` sections as `README.md`.

#### Scenario: The English README states the CLI
- **WHEN** `keel --help` lists a subcommand or flag, or `src/core/config.js` accepts a standing-authorization name
- **THEN** `README.md` names it
- **AND THEN** the README's count of authorization names equals the code's, and it describes exit codes 0 through 4

#### Scenario: The Chinese README matches the English one
- **WHEN** the validator reads `README.zh-CN.md`
- **THEN** it names every subcommand, flag, and authorization name the English README must name
- **AND THEN** its `##` and `###` section counts equal those of `README.md`
