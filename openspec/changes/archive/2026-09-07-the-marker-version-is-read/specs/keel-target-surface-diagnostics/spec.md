## ADDED Requirements

### Requirement: Doctor reports protocol version drift

`keel --doctor` MUST report the protocol version declared by the repository's
`keel:start` marker beside the version of the Keel CLI that is running, on every
run, whether or not they agree. When they disagree it MUST report a warning rather
than `ok`, MUST name which of the two is behind, and MUST name the remedy for that
direction. When the marker is absent, or carries no readable `version=`, doctor MUST
report that the two are not comparable and name the missing term, rather than
reporting agreement.

The comparison MUST read the declared version from the working tree and the running
version from the running CLI, so that it holds where no Keel plugin is installed,
enabled, trusted, or active.

Protocol version drift MUST NOT change doctor's exit code.

#### Scenario: The install is ahead of the repository

- **WHEN** doctor runs in a repository whose `keel:start` marker declares a version older than the running CLI
- **THEN** doctor reports the line as a warning naming both versions
- **AND THEN** it names the repository as the term that is behind, and `keel --init` as the remedy
- **AND THEN** doctor's exit code is what it would have been without the drift

#### Scenario: The repository is ahead of the install

- **WHEN** doctor runs in a repository whose `keel:start` marker declares a version newer than the running CLI
- **THEN** doctor reports the line as a warning naming both versions
- **AND THEN** it names the install as the term that is behind, and updating the Keel package as the remedy

#### Scenario: The two agree

- **WHEN** the marker version and the running CLI version are equal
- **THEN** doctor reports the line as `ok` and prints both versions

#### Scenario: Nothing is declared

- **WHEN** the repository has no `keel:start` marker, or its marker carries no readable `version=`
- **THEN** doctor reports the line as not comparable and names the missing term
- **AND THEN** it does not report the versions as agreeing
