## ADDED Requirements

### Requirement: Every line of the authorize block is read

Keel MUST read every indented, non-comment, non-blank line under `authorize:` as an entry, ending the block only at a line at column zero. A list item MUST contribute its text after `- ` with any trailing ` #` comment removed, and any other indented line MUST contribute its trimmed text. Each entry MUST then be classified like any other, so a line Keel cannot read is reported by name and the declaration authorizes nothing, never shortened silently. The Claude write guard MUST read `push:` entries with the same comment rule.

#### Scenario: An item with a space is refused, not dropped
- **WHEN** `authorize:` lists `commit`, then `push:main branch`, then `release`
- **THEN** `keel --doctor` exits non-zero naming `push:main branch`, and neither `commit` nor `release` is reported authorized

#### Scenario: A trailing comment does not drop an item
- **WHEN** `authorize:` lists `commit  # owner, 2026-10-11` and `push:claude/*  # sessions push their own branches`
- **THEN** `keel --doctor` reports `commit` authorized and `push` scoped to `claude/*`, and the Claude write guard refuses `git push origin HEAD:main`
