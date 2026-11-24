## ADDED Requirements

### Requirement: The bundled DSH entry discovers local installations

The bundled DSH executable MUST prefer the executable native DeepSeek Harness application bundle on macOS when present and use PATH otherwise. An explicit machine executable MUST override both defaults. Catalog output and the filled command of an authorized brief MUST use the same resolution when the executable is present. Discovery MUST NOT grant allowance or launch DSH.

#### Scenario: A standalone installation resolves
- **WHEN** the bundle is unavailable and DSH is installed on PATH
- **THEN** the catalog and the command of an authorized brief both identify the PATH executable

#### Scenario: Native bundle, machine overrides and missing installation
- **WHEN** an executable bundle is present on macOS
- **THEN** the catalog chooses the bundle ahead of PATH
- **AND THEN** an explicit machine executable takes priority over both and a missing explicit path remains unresolved
