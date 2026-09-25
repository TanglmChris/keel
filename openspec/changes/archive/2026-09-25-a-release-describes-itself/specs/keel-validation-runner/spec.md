# keel-validation-runner

## ADDED Requirements

### Requirement: A release describes itself

The release check SHALL refuse a changelog in which the version being released is not described: a
`TODO` token in that version's heading, a `- TODO:` bullet within its section, or more than one
`## <version>` heading for it. The refusal SHALL name the offending line, and SHALL consider only the
version being released.

#### Scenario: An unfilled stub is refused

- **WHEN** the changelog's section for the released version carries a `TODO` heading or bullet
- **THEN** the check fails, naming that line

#### Scenario: Two sections for one version are refused

- **WHEN** the changelog carries two `## <version>` headings for the released version
- **THEN** the check fails, reporting that the version is described twice

#### Scenario: An older unfilled section is not the current author's problem

- **WHEN** a `TODO` appears in a section for a version other than the one being released
- **THEN** the check passes
