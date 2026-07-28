## ADDED Requirements

### Requirement: The suite does not write to the repository it validates

A validation run MUST leave the repository byte-identical. A scenario that
mutates the tree it is checking corrupts two things at once: it dirties an
author's working copy with changes unrelated to their work, and — the worse
half — it can satisfy the very condition another check is asserting. A check
whose input is produced by its own test run cannot fail, and is therefore not
verification, however green it reports.

Scenarios MAY invoke Keel against the repository root for read-only purposes.
A scenario MUST NOT invoke a mutating Keel command against the repository root;
where the behavior under test needs a repository of a particular shape, the
scenario MUST build a fixture with that shape. A scenario that runs an install
MUST assert what the install did **not** write, not only the one effect it came
to check.

#### Scenario: A run leaves the tree unchanged

- **WHEN** the full validation suite runs against a clean checkout
- **THEN** the repository is byte-identical afterwards
- **AND THEN** no marker, overlay, or generated surface is rewritten as a side effect of testing

#### Scenario: A mutating invocation against the repository root is refused

- **WHEN** a scenario passes the repository root to a Keel command that writes
- **THEN** the check fails, naming the scenario and the invocation
- **AND THEN** read-only invocations against the repository root remain legal

#### Scenario: Install behavior is proven on a fixture with the required shape

- **WHEN** a scenario needs Keel to classify a repository a particular way
- **THEN** it builds a fixture carrying the signals the classifier actually reads
- **AND THEN** it asserts both the effect under test and the absence of other writes
