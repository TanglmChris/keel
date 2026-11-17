## ADDED Requirements

### Requirement: Installed validation dependency is reproducible
The published Keel package MUST provide the same supported validation dependency after clean installation and upgrade. Public OpenSpec commands MUST exercise that dependency, with behavior equivalent to the release-tested dependency. Installation divergence MUST NOT be concealed by suppressing validation findings.

#### Scenario: Clean and upgraded installations validate the same project
- **WHEN** the published package is installed into an empty prefix or upgrades an existing Keel installation
- **THEN** its actual OpenSpec version and strict validation behavior agree with the release-tested version
