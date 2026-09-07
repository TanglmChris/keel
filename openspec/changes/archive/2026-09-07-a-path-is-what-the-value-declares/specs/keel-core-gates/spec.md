## MODIFIED Requirements

### Requirement: A declared path is extracted by where it ends, not by what it is made of

Keel MUST extract a path declared in free prose — a `Durable owner:`, a `Resolved here:`, or a `keel/archive/…` reference inside `Findings` — by locating a run of non-whitespace, and MUST NOT restrict which characters that run may hold. A path whose directories are named in any script is nameable, because the check being performed is whether the file exists and a path that exists is a path the author may name.

The declaration is what the value opens with. A value that begins with a backticked path MUST be read as declaring that path, because that is how a path containing whitespace is declared. Otherwise the first bare run MUST be taken. A backticked span elsewhere in the value MUST be used only when neither of those produced a path, so that a value naming its owner and then citing another file is not read as declaring the citation. A `Findings` value is free prose in which naming the owner and then quoting a file is ordinary, and an extractor that preferred the quotation would answer with a file the author never declared — a file that usually exists, so the gate would accept rather than refuse.

A run containing a path separator MUST be extracted as a path. A run containing no separator MUST also be extracted when it has the shape of a filename — a trailing dot followed by a short run of letters or digits beginning with a letter — because a file at the repository root has no separator and is a legitimate owner. `AGENTS.md`, `README.md`, and `package.json` are nameable without being spelled `./AGENTS.md`, which is a concession to the extractor rather than a path the author meant.

A run with neither a separator nor a filename shape MUST stay unrecognized, and the refusal MUST continue to say so. A value such as `pending` reported as a file that does not exist would send the author to create one; and the filename shape MUST NOT match a version string such as `5.44.0`, which authors write in prose beside an owner.

Existence MUST still decide. A named file that does not exist MUST be refused, and wherever a reader names the missing path it MUST name a separator-free filename the same way, because naming the file the gate looked for is what makes the refusal repairable. This changes nothing about which readers name a path: `Findings` reports one owner refusal for every unusable owner and continues to.

Keel MUST trim punctuation trailing a bare path, in both ASCII and CJK forms, so that a path ending a sentence names the file rather than a sibling that does not exist. The trim MUST happen before the filename shape is judged, so a root file ending a sentence is still recognized.

A bare run MUST end at whitespace **or** at a sentence terminator of a script that does not separate words with whitespace. In such a script a path is followed immediately by its terminator, so a run bounded only by whitespace swallows the rest of the sentence and yields a path that cannot exist. ASCII punctuation MUST keep its existing treatment — permitted inside the run and trimmed from its end — because `a.b/c-d.e` and `f(1)/g` are paths and ASCII prose does supply the whitespace that ends them. The asymmetry follows from the writing system and is not an inconsistency.

Adding terminators MUST NOT narrow the alphabet. A directory named in any script stays nameable, so a path whose segments are CJK words is extracted in full and only its punctuation ends it.

Every gate reader of a declared path MUST use one extractor. A defect in extraction repaired in one reader and left in the others is how a fixed defect reappears.

#### Scenario: A path with non-ASCII directories is accepted
- **WHEN** a `Durable owner:` names an existing file whose directory names are not ASCII
- **THEN** the gate accepts it
- **AND THEN** no problem reports a truncated prefix of that path as missing

#### Scenario: A path is not required to begin with an ASCII segment
- **WHEN** the first segment of a declared path is not ASCII
- **THEN** the path is still extracted and checked

#### Scenario: A path in a sentence without spaces ends at its punctuation
- **WHEN** a declared path is followed immediately by a CJK sentence terminator and more prose, with no whitespace between the path and the terminator
- **THEN** the extracted path is the path alone
- **AND THEN** a path whose own segments are CJK words is still extracted in full

#### Scenario: A citation does not outrank the declaration
- **WHEN** a value names a path and then, later in the same value, quotes another path in backticks
- **THEN** the gate reads the path the value opened with
- **AND THEN** the quoted path is read only when the value declares no path before it

#### Scenario: A file at the repository root is nameable
- **WHEN** a `Durable owner:` or a `Resolved here:` names an existing repository-root file such as `AGENTS.md`, with no path separator
- **THEN** the gate accepts it
- **AND THEN** the same file spelled `./AGENTS.md` is accepted as it already was

#### Scenario: A value that is not a path stays unrecognized
- **WHEN** a declared owner is a bare word such as `pending`, or a version string such as `5.44.0`
- **THEN** the gate refuses it as unrecognized rather than reporting a file that does not exist

#### Scenario: A path containing whitespace is declared in backticks
- **WHEN** a value begins with a backticked path containing a space
- **THEN** the gate reads the whole path rather than stopping at the space
- **AND THEN** a value that declares no other path still reads a backticked path written later in it

#### Scenario: A path ending a sentence is not extended by its punctuation
- **WHEN** a declared path is immediately followed by sentence punctuation, ASCII or CJK
- **THEN** the punctuation is not treated as part of the path
- **AND THEN** a repository-root file ending a sentence is still recognized as a path

#### Scenario: A path that does not exist is still refused
- **WHEN** a declared path is extracted in full and no such file exists
- **THEN** the gate refuses it and names the path it looked for
- **AND THEN** a reader that names the missing path names a repository-root name as it names one carrying a separator
