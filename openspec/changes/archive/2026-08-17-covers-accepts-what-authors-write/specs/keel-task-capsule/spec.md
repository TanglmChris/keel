## ADDED Requirements

### Requirement: A critical-statement Covers entry may carry a trailing annotation
Keel MUST resolve a `Covers` entry that opens with a `D<n>`/`F<n>`/`A<n>`/`Q<n>` identifier followed by a dash and trailing text as a reference to that critical statement, and MUST NOT degrade it into an unlinked free-text reference. The annotation is not authority: the statement text still comes from `design.md`, and the annotation is not compared against it. An identifier followed by anything other than whitespace or an em dash — `D2-compatible`, `D2:` — is not such an entry, and colon-form and free-text references are unchanged.

#### Scenario: An annotated critical-statement entry resolves as the statement
- **WHEN** a task's Covers entry reads `D2 — an annotation` and `design.md` carries D2 in an accepted shape
- **THEN** `keel gate task-start` resolves the entry as critical-statement authority for D2 with the `design.md` statement text

#### Scenario: An annotated entry whose identifier is absent fails loudly
- **WHEN** a task's Covers entry reads `D2 — an annotation` and D2 does not appear in the change's `design.md`
- **THEN** `keel gate task-start` fails the reference as missing rather than passing it as an unlinked free-text reference

#### Scenario: Colon-form and hyphenated free text stay free text
- **WHEN** a task's Covers entry reads `E1: observable behavior` or opens with text like `D2-compatible`
- **THEN** the entry resolves exactly as it did before this requirement, without becoming a critical-statement reference
