## ADDED Requirements

### Requirement: A coverage claim is compared against the capsule it names

When an `## Expectation Coverage` entry closes with `Covered by:` and cites one or more
critical-statement identifiers (`F<n>`, `D<n>`, `A<n>`, `Q<n>`), `keel gate change-close`
MUST compare those identifiers against the `Covers:` of each task the entry names, and
MUST refuse the entry when no named task covers a cited identifier.

The refusal MUST name the entry, the identifier, and where that identifier is covered:
the task of this change whose `Covers:` names it, or that no task of this change does.

Keel MUST NOT require an entry to cite any identifier. An entry citing none MUST pass
unchanged and MUST NOT be reported as deficient.

`keel gate change-close` MUST report how many `Covered by:` entries cited an identifier
and were compared, and how many cited none and were not, whenever the section declares
any entry. Keel MUST NOT suppress that report when every entry was compared, because a
line that appears only sometimes teaches a reader that its absence means full coverage.

Keel MUST NOT judge whether the named task's checks prove the expectation. The comparison
is between two declared identifier lists; sufficiency remains `keel-review-checklist`'s.

#### Scenario: A coverage claim names a task that does not cover the identifier

- **WHEN** an entry cites `F4` and is covered by a task whose `Covers:` does not name `F4`, while another task of the change does
- **THEN** `change-close` fails, naming the entry, `F4`, and the task that covers it

#### Scenario: A coverage claim names an identifier no task covers

- **WHEN** an entry cites an identifier that no task of the change names in its `Covers:`
- **THEN** `change-close` fails, naming the entry, the identifier, and that no task of this change covers it

#### Scenario: A coverage claim that agrees with its capsule passes

- **WHEN** an entry cites identifiers and every one of them appears in the `Covers:` of a task the entry names
- **THEN** the comparison raises no problem

#### Scenario: An entry citing no identifier is not refused

- **WHEN** an entry closes with `Covered by:` and cites no critical-statement identifier
- **THEN** the comparison raises no problem for it

#### Scenario: The close reports how much of the section it compared

- **WHEN** `change-close` evaluates a section declaring at least one entry
- **THEN** it reports the number of `Covered by:` entries it compared and the number it did not, whatever those numbers are
