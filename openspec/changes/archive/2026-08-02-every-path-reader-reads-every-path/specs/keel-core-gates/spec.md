## ADDED Requirements

### Requirement: A declared path is extracted by where it ends, not by what it is made of

Keel MUST extract a path declared in free prose — a `Durable owner:`, a `Resolved here:`, or a `keel/archive/…` reference inside `Findings` — by locating a run of non-whitespace containing a path separator, and MUST NOT restrict which characters that run may hold. A path whose directories are named in any script is nameable, because the check being performed is whether the file exists and a path that exists is a path the author may name.

Keel MUST accept a path wrapped in backticks and take it verbatim, which is how a path containing whitespace is declared. `Touch` entries already accept that form, and one authorship must not be spelled two ways depending on which reader will read it.

Keel MUST trim punctuation trailing a bare path, in both ASCII and CJK forms, so that a path ending a sentence names the file rather than a sibling that does not exist.

Every gate reader of a declared path MUST use one extractor. A defect in extraction repaired in one reader and left in the others is how a fixed defect reappears.

#### Scenario: A path with non-ASCII directories is accepted
- **WHEN** a `Durable owner:` names an existing file whose directory names are not ASCII
- **THEN** the gate accepts it
- **AND THEN** no problem reports a truncated prefix of that path as missing

#### Scenario: A path is not required to begin with an ASCII segment
- **WHEN** the first segment of a declared path is not ASCII
- **THEN** the path is still extracted and checked

#### Scenario: A path containing whitespace is declared in backticks
- **WHEN** a declared path contains a space and is wrapped in backticks
- **THEN** the gate reads the whole path rather than stopping at the space

#### Scenario: A path ending a sentence is not extended by its punctuation
- **WHEN** a declared path is immediately followed by sentence punctuation, ASCII or CJK
- **THEN** the punctuation is not treated as part of the path

#### Scenario: A path that does not exist is still refused
- **WHEN** a declared path is extracted in full and no such file exists
- **THEN** the gate refuses it and names the path it looked for
