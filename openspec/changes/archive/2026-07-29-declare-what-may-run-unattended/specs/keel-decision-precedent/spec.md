## MODIFIED Requirements

### Requirement: A precedent answers a recurrence and never reclassifies a decision

A precedent MUST NOT move a decision out of the materiality categories that require asking the
owner. It MAY shorten a decision within its category by supplying the recorded answer and its
rationale; it MAY NOT cause a decision in that category to stop being asked when its own status is
`recorded`, and MAY NOT cause a category to stop being material at all. In particular, a precedent
MUST NOT admit work into an unattended run: whether an issue becomes work is a materiality decision,
and only an owner declaration may authorize it.

#### Scenario: A precedent shortens a question without removing it
- **WHEN** a decision falls in a materiality category and a matching precedent exists
- **THEN** the agent may put the recorded answer to the owner as a recommendation
- **AND THEN** the decision is still the owner's to confirm

#### Scenario: A precedent cannot make a category immaterial
- **WHEN** a precedent covers several decisions in one materiality category
- **THEN** that category remains material for decisions the precedent does not cover
- **AND THEN** no accumulation of precedents removes a category from the must-ask list

#### Scenario: Category mismatch is not a match
- **WHEN** a decision resembles a precedent but falls in a different materiality category
- **THEN** the precedent does not apply
- **AND THEN** the decision is escalated as though no precedent existed

#### Scenario: A precedent cannot admit work into an unattended run
- **WHEN** a precedent records how similar issues were triaged in the past and a new issue resembles them
- **THEN** the precedent does not admit that issue
- **AND THEN** admission comes only from the repository's declared triage policy, because a precedent is a claim about what the owner would decide while a declaration is the decision itself
