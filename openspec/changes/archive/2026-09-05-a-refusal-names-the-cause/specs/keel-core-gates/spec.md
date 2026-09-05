## MODIFIED Requirements

### Requirement: A declared path is extracted by where it ends, not by what it is made of

Keel MUST extract a path declared in free prose — a `Durable owner:`, a `Resolved here:`, or a `keel/archive/…` reference inside `Findings` — by locating a run of non-whitespace, and MUST NOT restrict which characters that run may hold. A path whose directories are named in any script is nameable, because the check being performed is whether the file exists and a path that exists is a path the author may name.

A run containing a path separator MUST be extracted as a path. A run containing no separator MUST also be extracted when it has the shape of a filename — a trailing dot followed by a short run of letters or digits beginning with a letter — because a file at the repository root has no separator and is a legitimate owner. `AGENTS.md`, `README.md`, and `package.json` are nameable without being spelled `./AGENTS.md`, which is a concession to the extractor rather than a path the author meant.

A run with neither a separator nor a filename shape MUST stay unrecognized, and the refusal MUST continue to say so. A value such as `pending` reported as a file that does not exist would send the author to create one; and the filename shape MUST NOT match a version string such as `5.44.0`, which authors write in prose beside an owner.

Existence MUST still decide. A named file that does not exist MUST be refused, and wherever a reader names the missing path it MUST name a separator-free filename the same way, because naming the file the gate looked for is what makes the refusal repairable. This changes nothing about which readers name a path: `Findings` reports one owner refusal for every unusable owner and continues to.

Keel MUST accept a path wrapped in backticks and take it verbatim, which is how a path containing whitespace is declared. `Touch` entries already accept that form, and one authorship must not be spelled two ways depending on which reader will read it.

Keel MUST trim punctuation trailing a bare path, in both ASCII and CJK forms, so that a path ending a sentence names the file rather than a sibling that does not exist. The trim MUST happen before the filename shape is judged, so a root file ending a sentence is still recognized.

Every gate reader of a declared path MUST use one extractor. A defect in extraction repaired in one reader and left in the others is how a fixed defect reappears.

#### Scenario: A path with non-ASCII directories is accepted
- **WHEN** a `Durable owner:` names an existing file whose directory names are not ASCII
- **THEN** the gate accepts it
- **AND THEN** no problem reports a truncated prefix of that path as missing

#### Scenario: A path is not required to begin with an ASCII segment
- **WHEN** the first segment of a declared path is not ASCII
- **THEN** the path is still extracted and checked

#### Scenario: A file at the repository root is nameable
- **WHEN** a `Durable owner:` or a `Resolved here:` names an existing repository-root file such as `AGENTS.md`, with no path separator
- **THEN** the gate accepts it
- **AND THEN** the same file spelled `./AGENTS.md` is accepted as it already was

#### Scenario: A value that is not a path stays unrecognized
- **WHEN** a declared owner is a bare word such as `pending`, or a version string such as `5.44.0`
- **THEN** the gate refuses it as unrecognized rather than reporting a file that does not exist

#### Scenario: A path containing whitespace is declared in backticks
- **WHEN** a declared path contains a space and is wrapped in backticks
- **THEN** the gate reads the whole path rather than stopping at the space

#### Scenario: A path ending a sentence is not extended by its punctuation
- **WHEN** a declared path is immediately followed by sentence punctuation, ASCII or CJK
- **THEN** the punctuation is not treated as part of the path
- **AND THEN** a repository-root file ending a sentence is still recognized as a path

#### Scenario: A path that does not exist is still refused
- **WHEN** a declared path is extracted in full and no such file exists
- **THEN** the gate refuses it and names the path it looked for
- **AND THEN** a reader that names the missing path names a repository-root name as it names one carrying a separator
