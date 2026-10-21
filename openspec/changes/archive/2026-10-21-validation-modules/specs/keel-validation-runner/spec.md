## MODIFIED Requirements

### Requirement: One scenario registry drives all validation entry points

The validation runner — `scripts/validate_plugin.py` and the modules under `scripts/validation/` — MUST own a single ordered scenario registry, kept in `scripts/validation/registry.py` and consumed by the `--scenario <name>` dispatch, the `--group <name>` runner, and the `--all` runner. Scenario functions live in modules grouped by responsibility, and each module MUST import the shared helpers it uses by name. `package.json`'s test script MUST invoke the runner once and MUST NOT enumerate scenarios. A scenario that proves its own registration MUST assert registry membership, not `package.json` content.

#### Scenario: Adding a scenario registers once

- **WHEN** a new validator scenario is added to the registry
- **THEN** it is reachable via `--scenario <name>` and included in `--all`
- **AND THEN** `package.json` needs no edit

#### Scenario: Single-scenario CLI stays stable

- **WHEN** an archived or active task Verify command invokes `--scenario <name>`
- **THEN** the invocation, exit-code semantics, and output behavior match the pre-runner contract

#### Scenario: Unknown scenario still fails loudly

- **WHEN** `--scenario` names an unregistered scenario
- **THEN** the runner reports the unknown name and exits non-zero

#### Scenario: Moving scenarios into modules changes no result

- **WHEN** the scenarios are split from one file into modules
- **THEN** the registry lists the same names in the same order, and `--all` prints the same verified count and the same skipped names as before the split

### Requirement: The one-message-many-failures assertion shape is counted

The validation suite MUST report how many assertion sites in `scripts/validate_plugin.py` and the modules under `scripts/validation/` guard several distinct failures behind one failure message, and MUST compare that number against a recorded count. The counted shape is an `if` whose body is one or more `report(...)` calls followed by exactly one `return`, whose test is an `or`, where at least one operand is a membership test and at least one operand is not.

The comparison MUST fail when the count rises, naming the sites that are not in the recorded set so the author sees which assertion they just wrote. It MUST also fail when the count falls without the recorded number being lowered, because a number that only rises-checks becomes false the first time a site is fixed.

Keel MUST NOT present the count as a defect count. The shape is a signal that one message covers more than one failure; whether a given message misleads is a semantic judgment that stays with `keel-review-checklist`.

#### Scenario: A newly added site fails the suite and is named
- **WHEN** an assertion of the counted shape is added to any validation module
- **THEN** the scenario fails, reports the count that was found against the recorded count, and names the added site
- **AND THEN** the recorded count is unchanged by the failure

#### Scenario: A stale recorded count fails when sites are fixed
- **WHEN** a counted site is split so that each failure carries its own message, and the recorded count is not lowered
- **THEN** the scenario fails and states that the recorded count is higher than what the files contain
- **AND THEN** lowering the recorded number to the measured one restores the pass

#### Scenario: The count is reported as a shape, not as defects
- **WHEN** the scenario reports the counted sites
- **THEN** the wording states that the count bounds a shape rather than asserting that each site is wrong

## ADDED Requirements

### Requirement: One group of scenarios runs alone

`validate_plugin.py --group <name> [--jobs N]` MUST run exactly the registered scenarios whose functions are defined in `scripts/validation/<name>.py`, in registry order, with the same process isolation, output buffering, skip accounting, and failure naming as `--all`, and without the baseline. An unknown group MUST be reported with the names of the groups that exist and MUST exit `2`.

#### Scenario: A group runs only its own scenarios
- **WHEN** `--group selfcheck` runs
- **THEN** it runs every registered scenario defined in `scripts/validation/selfcheck.py` and no other, and its summary names the group and the count it verified

#### Scenario: An unknown group fails loudly
- **WHEN** `--group` names a module that defines no registered scenario
- **THEN** the runner names the groups that exist and exits `2`

### Requirement: The runner's self-checks read every validation module

The checks that read the validation runner's own source MUST read `scripts/validate_plugin.py` and every module under `scripts/validation/`: the check that every `validate_*_scenario` function is registered, the scan for commands that would mutate the repository under test and for retired paths, and the standard-library import check. The standard-library import check MUST accept the local `validation` package and nothing else outside the standard library.

#### Scenario: An unregistered scenario in a module is caught
- **WHEN** a module under `scripts/validation/` defines a `validate_*_scenario` function the registry does not list
- **THEN** the `validation-runner` scenario fails naming it

#### Scenario: A mutating command in a module is caught
- **WHEN** a module under `scripts/validation/` runs `run_keel(ROOT, "--install")`
- **THEN** the baseline fails naming the module and line

#### Scenario: A third-party import in a module is caught
- **WHEN** a module under `scripts/validation/` imports a module outside the standard library and the `validation` package
- **THEN** the baseline fails naming the module and the import
