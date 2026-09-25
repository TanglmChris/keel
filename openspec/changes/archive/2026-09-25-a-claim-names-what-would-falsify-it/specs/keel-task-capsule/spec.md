## ADDED Requirements

### Requirement: A check may declare the defect it detects

A check MAY close with `Detects:` followed by two inline-code literals separated by `->`: the
mutation that puts a defect in, and the failure that mutation must produce. `keel gate
task-complete` MUST require the second literal in a `.detects` Evidence entry for the same check.
The clause MUST be part of the check text, so it enters the contract fingerprint and an injection
edited after the fact reports as drift.

This covers what a red cannot. A `.red` proves the check failed before the implementation existed
and a declared failure signature predicts the red of an **absent** feature; neither says anything
about the red of a **broken** one, and the two can be unrelated. A check whose assertion is immune
to the defect it exists to catch passes both.

Keel MUST NOT judge the injection, and MUST NOT run it. An author may declare a mutation any check
would catch. Keel records the claim and places it where Review can see it, which is the standing
every other check result has.

A `(regression)`-tagged check MUST be permitted to declare one. A regression check has no honest red
by construction and is exempt from `.red`/`.green`, so an injection is the only mechanism that can
show it is not vacuous — refusing the clause there would remove it from where it is worth most.

#### Scenario: A declared injection requires its failure in evidence
- **WHEN** a check closes with `Detects:` naming a mutation and the failure it must produce
- **THEN** `task-complete` requires that failure literal in a `.detects` Evidence entry for that check
- **AND THEN** the clause is part of the fingerprint, so editing the injection later reports as drift

#### Scenario: A regression check may declare an injection
- **WHEN** a `(regression)`-tagged check closes with `Detects:`
- **THEN** the declaration is accepted and enforced
- **AND THEN** the check stays exempt from `.red` and `.green`, because the injection is what stands
  in for a red it cannot honestly have

#### Scenario: A malformed injection clause is refused by name
- **WHEN** a check carries a `Detects:` marker that is not a closing clause with both literals
- **THEN** task-start refuses it, naming the check
- **AND THEN** the marker is not ignored, because ignoring it would leave the author believing an
  injection is enforced when none was parsed

### Requirement: A check may bind a number to the measurement behind it

A check MAY close with `Measured:` followed by one inline-code literal, and `keel gate
task-complete` MUST require that literal in the check's own `M<n>` Evidence — the entry where the
command and its output are recorded. A literal the recorded output does not contain is either
unpasted or not measured.

The clause MUST be optional. A universal rule over every number in Evidence MUST NOT be imposed:
measured against this repository's archive it would reach 847 inline-code spans, a majority of them
version strings, counts the author computed, and quoted references that legitimately appear in no
command output, and each would be a false stop.

#### Scenario: A declared measurement must appear in the check's own output
- **WHEN** a check closes with `Measured:` naming a literal
- **THEN** `task-complete` requires that literal in that check's `M<n>` Evidence
- **AND THEN** a literal absent from the recorded output fails, naming the check and the literal

#### Scenario: A number with no declaration is not checked
- **WHEN** Evidence states a number in inline code and no check declared it
- **THEN** no gate requires it to appear in any command output
- **AND THEN** nothing reports the number as verified

### Requirement: Declaration clauses chain on one check

A check is one line, so its declaration clauses MUST be parsed as a trailing sequence and any of
them MUST be permitted to follow another. A failure signature MUST keep its exact existing meaning
whenever it stands alone or comes last.

#### Scenario: Two clauses on one check both parse
- **WHEN** a check closes with a failure signature followed by an injection clause
- **THEN** both are parsed and both are enforced
- **AND THEN** neither is reported as malformed for not being the final clause

#### Scenario: An existing single-clause check is unaffected
- **WHEN** a check closes with a failure signature and nothing after it
- **THEN** it parses exactly as it did before clauses could chain
- **AND THEN** a marker appearing mid-sentence is still not a declaration
