## ADDED Requirements

### Requirement: Locked validation dependency excludes the affected Zod release

The shipped shrinkwrap MUST resolve a Zod version outside GHSA-mrhx-c7xc-m3w5's affected range, compatible with the carried OpenSpec release. The repair MUST preserve the declared OpenSpec range, its locked version and unrelated dependency entries, and MUST verify public OpenSpec behavior and package regression before release.

#### Scenario: Patched dependency is installed
- **WHEN** a clean installation uses the repaired shrinkwrap
- **THEN** the installed Zod is at least 4.6.6 and npm audit does not report GHSA-mrhx-c7xc-m3w5
- **AND THEN** the existing OpenSpec public validation checks still pass
