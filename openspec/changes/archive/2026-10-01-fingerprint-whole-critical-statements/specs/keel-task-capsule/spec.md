## ADDED Requirements

### Requirement: A cited multi-line critical statement is wholly fingerprinted

Keel MUST include the full owned text of a cited `D<n>`/`F<n>`/`A<n>`/`Q<n>` statement in the compiled authority and contract fingerprint. A change to an owned continuation or nested list item MUST move the fingerprint, while unrelated sibling text MUST NOT.

#### Scenario: A nested detail changes an active contract
- **WHEN** a task cites `D1` and a nested detail under its accepted `design.md` list item changes after the task records its fingerprint
- **THEN** a fresh `task-start` fingerprint differs
- **AND THEN** `task-complete` refuses the old recorded contract as drift

#### Scenario: A continuation line changes an active contract
- **WHEN** a task cites `D1` and an indented non-list continuation owned by that item changes
- **THEN** a fresh `task-start` fingerprint differs

#### Scenario: A sibling change is not the cited authority
- **WHEN** a task cites `D1` and only a peer list item, same-level paragraph after a blank line, or following heading changes
- **THEN** the task fingerprint remains unchanged

### Requirement: Critical identifiers in unresolved Covers entries fail visibly

Keel MUST NOT accept a `Covers` entry containing critical-statement identifiers as an unlinked legacy task reference when it purports to cite multiple critical statements. A valid single opening reference with supporting prose MUST continue to bind only the opening reference, and a resolved question mentioned beside its closing fact MUST NOT become an unresolved-question blocker.

#### Scenario: Non-ASCII separated references fail
- **WHEN** a `Covers` entry is `D1、D2`
- **THEN** `task-start` fails with a diagnostic naming the unparsed entry and how to express separate references

#### Scenario: Prose-wrapped references fail
- **WHEN** a `Covers` entry is prose ending in `（D1、D2）`
- **THEN** `task-start` fails rather than compiling a legacy task reference

#### Scenario: Existing supported references remain linked
- **WHEN** a `Covers` entry is a bare `D1`, an ASCII-comma list `D1, D2`, or one `D1 — annotation`
- **THEN** each opening critical reference resolves to its `design.md` authority

#### Scenario: A closed question remains supporting detail
- **WHEN** a `Covers` entry opens with a fact and mentions a resolved `Q1` only as supporting detail
- **THEN** the existing resolved-question scope rule does not demand a fallback for `Q1`
