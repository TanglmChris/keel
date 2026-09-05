# keel-release-artifact Specification

## Purpose

Define what the published Keel package contains and what determines it.

## Requirements

### Requirement: The published package is determined by the repository, not by the machine

What the published package contains MUST be a function of the repository's tracked contents. Two people packing the same commit MUST produce the same set of files, and a file that exists only because someone ran a tool on their machine MUST NOT ship.

`package.json`'s `files` array names the directories that ship. Declaring it means the repository's ignore file no longer filters inside those directories, and build residue is not on the packer's default exclusion list — so the repository MUST carry its own packaging exclusions.

Those exclusions MUST be written where the packer reads them. A packaging ignore file at the repository root is not consulted for a directory named by `files`, so an exclusion placed there looks correct and does nothing; one placed inside a directory guards only that directory. Excluding through the `files` declaration itself keeps the exclusion beside the inventory it qualifies and covers every included directory at once.

A verification check MUST assert that every file in the packed set is tracked by Git. This states the requirement directly and cannot be satisfied by a machine's leftovers; a recomputed list of expected files would have to reimplement the packer's inclusion rules and would drift from them.

#### Scenario: Build residue does not ship

- **WHEN** the repository's own tooling has been run, leaving generated files inside a directory named by `files`
- **THEN** the packed set is the same as it is on a clean checkout
- **AND THEN** no compiled or cached artifact appears in it
- **AND THEN** the exclusion is written where the packer reads it, rather than in a root ignore file it does not consult

#### Scenario: Every packed file is tracked

- **WHEN** the verification suite runs
- **THEN** it packs the repository and asserts that every file in the result is tracked by Git
- **AND THEN** it names any untracked file it found, so the fix is to the packaging rules rather than to the check
