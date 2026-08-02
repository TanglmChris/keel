## ADDED Requirements

### Requirement: The interpreter diagnostic agrees with the runner that uses it

`keel --doctor` MUST report the interpreter it resolved together with the version that interpreter reported, and MUST NOT report an interpreter as usable when the validation runner would refuse it. Both surfaces MUST read the minimum version from one definition, so a change to the minimum cannot move one and leave the other behind.

Keel MUST NOT install or select an interpreter. The diagnostic reports what it found and what the requirement is.

#### Scenario: An interpreter below the minimum is reported as a problem
- **WHEN** the resolved interpreter reports a version below the runner's minimum
- **THEN** `keel --doctor` reports it as a problem rather than ok, naming the version found and the minimum required
- **AND THEN** the runner refusing the same interpreter and the doctor reporting it disagree in no case

#### Scenario: The reported line carries the version
- **WHEN** `keel --doctor` reports the interpreter check
- **THEN** the line names the resolved command and the version it reported
- **AND THEN** an interpreter that cannot be run at all is reported as missing rather than as a version problem

### Requirement: The interpreter search covers versioned names

Keel MUST look for versioned interpreter names before reporting that no usable interpreter exists, so a refusal is issued only when none is installed. The unversioned names MUST be tried first, so a machine where the default interpreter already satisfies the minimum is unaffected. An interpreter named by `KEEL_PYTHON` MUST be used without a search, because an explicit choice is not overridden by discovery.

The versioned names MUST be derived from the declared minimum rather than listed separately, so raising the minimum cannot leave a name behind that no longer qualifies.

#### Scenario: A versioned interpreter is found when the default is too old
- **WHEN** the default `python3` reports a version below the minimum and a versioned interpreter at or above it is on PATH
- **THEN** the runner uses the versioned interpreter and does not refuse
- **AND THEN** the refusal appears only when no candidate reaches the minimum, and names each candidate with the version it reported

#### Scenario: An explicit interpreter is not searched around
- **WHEN** `KEEL_PYTHON` names an interpreter
- **THEN** Keel uses it and tries no other candidate
