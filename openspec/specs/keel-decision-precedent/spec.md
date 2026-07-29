## Purpose

Define how a repository declares a precedent store it owns, what a precedent record must carry, when a precedent may be applied and must be cited, how promotion works, and what a precedent can never authorize.
## Requirements

### Requirement: A repository declares a precedent store it owns

Keel MUST read an optional precedent store directory declared in `keel/config.yaml`. Keel MUST NOT
bundle any precedent, MUST NOT create or populate the store, and MUST NOT reach the network to
obtain it. An absent declaration MUST leave every surface behaving as it does without this
capability.

#### Scenario: A declared store is read from the local filesystem
- **WHEN** `keel/config.yaml` declares a precedent store path that exists
- **THEN** Keel reads the precedent files in that directory
- **AND THEN** it performs no network access to reach or refresh them

#### Scenario: No declaration is a valid state
- **WHEN** `keel/config.yaml` declares no precedent store, or declares one that does not exist
- **THEN** every surface behaves exactly as it does without a store
- **AND THEN** no prompt demands that a store be created

#### Scenario: The store path is declarable rather than fixed
- **WHEN** two repositories declare the same store path outside either repository
- **THEN** both read the same precedents
- **AND THEN** Keel requires no per-repository copy of them

### Requirement: A precedent record carries its rationale, not only its conclusion

Each precedent MUST be self-describing: an `Applies when:` header naming the decisions it covers,
the materiality category it belongs to, a status of `recorded` or `authorized`, the decision, and
the rationale that produced it. Keel MUST report a precedent missing its rationale as incomplete.
The check MUST be structural; Keel MUST NOT judge whether the reasoning is sound.

#### Scenario: A complete precedent is usable
- **WHEN** a precedent declares `Applies when:`, a category, a status, a decision, and a rationale
- **THEN** Keel treats it as available to the decision it covers

#### Scenario: A conclusion without a reason is reported incomplete
- **WHEN** a precedent records a decision but no rationale
- **THEN** Keel reports it as incomplete and names the missing field
- **AND THEN** it is not applied to any decision, because a conclusion alone cannot be transferred
  to a situation that is not literally the recorded one

#### Scenario: Completeness is a shape check
- **WHEN** a precedent carries a rationale Keel cannot evaluate
- **THEN** Keel reports it complete on the presence of the field alone
- **AND THEN** no surface claims Keel judged the reasoning

### Requirement: Applying a precedent in the owner's place is stated explicitly

When a precedent supplies an answer that, in its absence, would have caused the agent to ask the
owner, the agent MUST state that it applied that precedent and name it. Decisions that would not
have interrupted the owner MUST NOT be cited, so that a citation always marks a decision made in
the owner's place.

#### Scenario: A precedent that replaces a question is cited
- **WHEN** a precedent answers a decision the agent would otherwise have escalated
- **THEN** the agent names the precedent it applied in its response
- **AND THEN** the owner can see, in one line, a decision that was made for them

#### Scenario: A routine decision is not cited
- **WHEN** a precedent informs a decision that would not have interrupted the owner
- **THEN** the agent does not cite it
- **AND THEN** citations stay a signal rather than a running commentary

### Requirement: Promotion to auto-applicable is an owner act

A precedent MUST enter the store as `recorded` and MUST become `authorized` only when the owner
accepts a promotion the agent proposes. Keel MUST NOT promote a precedent by usage count, age, or
any other automatic threshold.

#### Scenario: A recorded precedent still escalates
- **WHEN** a `recorded` precedent covers a decision that would interrupt the owner
- **THEN** the agent still asks, and may cite the precedent as its recommendation
- **AND THEN** the decision remains the owner's

#### Scenario: Promotion is proposed and accepted
- **WHEN** the agent judges a `recorded` precedent ready to apply without asking
- **THEN** it proposes the promotion to the owner and names the precedent
- **AND THEN** the status changes only after the owner accepts

#### Scenario: No threshold promotes anything
- **WHEN** a `recorded` precedent has been cited any number of times
- **THEN** its status is unchanged
- **AND THEN** no surface promotes it automatically, because a threshold crosses with no one
  watching

### Requirement: A precedent answers a recurrence and never reclassifies a decision

A precedent MUST NOT move a decision out of the materiality categories that require asking the
owner. It MAY shorten a decision within its category by supplying the recorded answer and its
rationale; it MAY NOT cause a decision in that category to stop being asked when its own status is
`recorded`, and MAY NOT cause a category to stop being material at all.

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

### Requirement: A precedent has no authority over proof

A precedent MUST NOT weaken, skip, or make conditional any gate, evidence requirement, semantic
Review, or the write guard. It informs a decision and never substitutes for a proof.

#### Scenario: A gate is unaffected by the store
- **WHEN** a repository declares a precedent store containing any number of `authorized` precedents
- **THEN** every gate returns the same status, problems, and failure text as it would with no store
- **AND THEN** no evidence, Review, or guard requirement is relaxed
