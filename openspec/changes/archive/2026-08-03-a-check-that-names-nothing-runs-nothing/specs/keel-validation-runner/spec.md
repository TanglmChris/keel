## ADDED Requirements

### Requirement: A scenario name written into an active task contract is checked against the registry

A task's `Verify` block names the scenarios its checks will run, and a name the registry does not hold makes that check unrunnable while the contract still reads as covered. Validation MUST read the `tasks.md` of every active change and MUST fail when a scenario reference names a scenario that is not registered, reporting the file, the 1-indexed line, and the name.

Two reference forms MUST be recognized: a name following `--scenario`, and a backticked lowercase token inside a `Verify` or `Commands` `M<n>` check whose text asserts that something stays green. Both forms carry no false positive against every task contract this repository has written, and that is the reason they are the recognized ones. Validation MUST NOT read every backticked token in a check as a scenario reference: gate stages, diagnostic codes, skill names, capability names, and hook events share the same spelling, and a check that reports them would be wrong more often than right.

Archived changes MUST NOT be scanned. An archived task records what was true when it ran, and a scenario renamed afterwards is not a defect in the record.

The check MUST be able to fail when the active set is empty. A run whose assertions all came from a set that resolved to nothing is indistinguishable from a run that verified something, so the recognized forms MUST be asserted against content the scenario controls, and not only against whatever the working tree happens to contain.

#### Scenario: An unregistered name in a regression check fails the suite
- **WHEN** an active change's `Verify` block declares a check asserting that a backticked name stays green, and no scenario by that name is registered
- **THEN** validation fails, naming the `tasks.md`, the line, and the name
- **AND THEN** the message states the two forms that are read as scenario references

#### Scenario: An unregistered name after `--scenario` fails the suite
- **WHEN** an active change's `tasks.md` names a scenario after `--scenario` and no scenario by that name is registered
- **THEN** validation fails, naming the file, the line, and the name

#### Scenario: Vocabulary that is not a scenario name is left alone
- **WHEN** a check names a gate stage, a diagnostic code, a skill, a capability, or a hook event in backticks
- **THEN** validation reports nothing, because those are not scenario references
- **AND THEN** a registered scenario named in either recognized form also reports nothing

#### Scenario: Archived changes are not scanned
- **WHEN** an archived change's `tasks.md` names a scenario that is no longer registered
- **THEN** validation reports nothing, because renaming a scenario does not make a completed record wrong

#### Scenario: An empty active set does not stand in for verification
- **WHEN** the repository has no active change, which is its normal state between changes
- **THEN** the scenario still asserts each recognized form against content it controls, and fails if the extractor stops reporting a planted unregistered name
- **AND THEN** the run does not report the check as verified on the strength of an empty scan
