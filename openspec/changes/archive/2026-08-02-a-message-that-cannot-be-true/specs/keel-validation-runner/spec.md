## ADDED Requirements

### Requirement: The one-message-many-failures assertion shape is counted

The validation suite MUST report how many assertion sites in `scripts/validate_plugin.py` guard several distinct failures behind one failure message, and MUST compare that number against a recorded count. The counted shape is an `if` whose body is one or more `report(...)` calls followed by exactly one `return`, whose test is an `or`, where at least one operand is a membership test and at least one operand is not.

The comparison MUST fail when the count rises, naming the sites that are not in the recorded set so the author sees which assertion they just wrote. It MUST also fail when the count falls without the recorded number being lowered, because a number that only rises-checks becomes false the first time a site is fixed.

Keel MUST NOT present the count as a defect count. The shape is a signal that one message covers more than one failure; whether a given message misleads is a semantic judgment that stays with `keel-review-checklist`.

#### Scenario: A newly added site fails the suite and is named
- **WHEN** an assertion of the counted shape is added to `scripts/validate_plugin.py`
- **THEN** the scenario fails, reports the count that was found against the recorded count, and names the added site
- **AND THEN** the recorded count is unchanged by the failure

#### Scenario: A stale recorded count fails when sites are fixed
- **WHEN** a counted site is split so that each failure carries its own message, and the recorded count is not lowered
- **THEN** the scenario fails and states that the recorded count is higher than what the file contains
- **AND THEN** lowering the recorded number to the measured one restores the pass

#### Scenario: The count is reported as a shape, not as defects
- **WHEN** the scenario reports the counted sites
- **THEN** the wording states that the count bounds a shape rather than asserting that each site is wrong
