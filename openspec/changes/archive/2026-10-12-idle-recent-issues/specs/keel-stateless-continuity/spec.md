## ADDED Requirements

### Requirement: An idle result points at the issues the branch was working on

When `keel context` reports `idle`, it MUST carry a `recent` field listing up to five issue numbers that this branch's commits beyond the default branch reference as `#<n>`, newest commit first and without repeats, together with the range read. It MUST derive them from Git alone, MUST NOT add them to the result's reasons or select anything from them, and MUST omit the field when there is no default branch, the branch adds no commit, or no commit references an issue. The SessionStart and compaction projection MUST print the list on one line marked as a pointer.

#### Scenario: An idle branch names its recent issues
- **WHEN** a worktree's branch has commits beyond `main` mentioning `#162`, then `#182`, then `#162` again, and no change is active
- **THEN** `keel context --json` reports `idle` with `recent.issues` `[162, 182]` and its reasons unchanged
- **AND THEN** the session projection prints them as recently referenced

#### Scenario: Nothing to point at adds nothing
- **WHEN** the session is on the default branch, or its commits reference no issue
- **THEN** the result has no `recent` field and the projection no such line
