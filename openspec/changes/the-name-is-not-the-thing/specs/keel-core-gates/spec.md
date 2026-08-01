## ADDED Requirements

### Requirement: Git path output is read in a form that carries no escaping

Keel MUST read changed and dirty paths from Git in NUL-separated form, so that no path it compares against Touch has been quoted or escaped. Keel MUST NOT rewrite backslashes in Git path output: Git emits forward slashes on every platform, and rewriting them corrupts any escape sequence that reaches the reader.

A path a task declares in Touch MUST be attributed to Touch whatever characters it contains, including non-ASCII characters, spaces, quotes, and backslashes.

#### Scenario: A non-ASCII path in Touch is not an outside-Touch failure
- **WHEN** a task declares a path containing non-ASCII characters in Touch and that file is the only change
- **THEN** `task-complete` attributes it inside Touch
- **AND THEN** no `outside-touch` problem names an escaped or partially decoded form of the path

#### Scenario: Spaces and quotes survive the read
- **WHEN** changed paths contain spaces, double quotes, or backslashes
- **THEN** each is compared against Touch as the filesystem spells it
- **AND THEN** the comparison does not depend on which Git subcommand reported the path

#### Scenario: A rename reports both endpoints undamaged
- **WHEN** a rename is reported whose endpoints contain characters Git would otherwise escape
- **THEN** both endpoints are attributed independently
- **AND THEN** neither endpoint is dropped or merged into the other
