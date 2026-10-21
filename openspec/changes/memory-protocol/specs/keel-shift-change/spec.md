## ADDED Requirements

### Requirement: The shift check reminds the session to recheck memory
`keel shift check` MUST print a note that tells the session to recheck what it wrote to memory before it writes the hand-off note. The note MUST appear in the text output and in the `--json` `notes`. It MUST NOT count as an item or change readiness. `/keel:shift` MUST tell the session to act on that note.

#### Scenario: A clean worktree is ready and is reminded about memory
- **WHEN** `keel shift check` runs in a clean worktree bound to a role
- **THEN** it exits 0 as ready, and both its text and its `--json` `notes` carry the memory note
