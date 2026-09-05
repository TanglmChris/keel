## MODIFIED Requirements

### Requirement: A durable owner may be any file the repository keeps, and a refusal names what it accepts

The accepted durable-owner forms are shape checks. A gate runs without network
and cannot confirm that a URL resolves or that an archive path is the right one,
so a whitelist of prefixes verifies nothing beyond spelling. A repo-relative path
is the one form a gate can actually check, and refusing it while accepting the
unverifiable ones inverts the rigour.

A `Durable owner:` MUST therefore be accepted when it names a repo-relative path
that exists in the repository the gate is running against, in addition to the
forms already accepted. A path that does not exist MUST be refused, which is a
check the prefix whitelist could not make.

Existence is necessary and not sufficient, and two paths that exist MUST still be
refused. `keel/HANDOFF.md` is refused because the protocol defines it as a
pointer override rather than an owner. A path inside the selected change's own
directory is refused because archiving moves that directory: the check would be
true when it ran and false immediately afterwards, and a pointer that must break
leaves a Review reading as closed while the trail ends halfway. The refusal MUST
say that the directory moves when the change is archived, so the author repairs
the pointer rather than the spelling. The same rule MUST apply to a
`Resolved here:` path, which names the same kind of file and moves with it.

A path inside a *different* live change directory MUST stay accepted. A new
OpenSpec change is a legitimate owner of deferred work, and the rule above is
about the directory the workflow is about to move, not about change directories
in general.

Every refusal MUST state what the accepted forms are worth: a repo-relative path
is checked for existence at the moment it is cited and is not re-checked
afterwards, and a tracker reference is accepted on its shape because a gate that
fetched it would stop being local and offline. An author MUST NOT be left to
infer that a check ran which did not.

The same vocabulary MUST apply wherever a durable owner closes an entry —
Review `Findings`, `## Expectation Coverage`, and `## Invalidates` — so a form
accepted in one place is never refused in another. Every refusal of an owner or
a closure MUST state the forms it would accept, because an author who cannot
see the boundary can only find it by trial.

#### Scenario: A repo ledger is a legitimate owner

- **WHEN** an entry closes with a `Durable owner:` naming a repo-relative file that exists
- **THEN** the gate accepts it
- **AND THEN** the same path is accepted whether it closes an invalidation, an expectation, or a review finding

#### Scenario: An owner that does not exist is refused

- **WHEN** a `Durable owner:` names a repo-relative path with no file behind it
- **THEN** the gate refuses the entry and says the path does not exist
- **AND THEN** the refusal is distinguishable from an entry that named no owner at all

#### Scenario: The pointer override is still not an owner

- **WHEN** a `Durable owner:` names `keel/HANDOFF.md`
- **THEN** the gate refuses it even though the file exists
- **AND THEN** the refusal states that this file is a pointer override rather than a durable owner

#### Scenario: A pointer into the change's own directory is not an owner

- **WHEN** a `Durable owner:` names a path inside the selected change's own directory, such as its `design.md`
- **THEN** the gate refuses it even though the file exists
- **AND THEN** the refusal states that the directory moves when the change is archived, and names the forms that survive it
- **AND THEN** the same path is refused whether it closes an invalidation, an expectation, or a review finding

#### Scenario: Resolution evidence inside the change's own directory is refused too

- **WHEN** a `Resolved here:` names a path inside the selected change's own directory
- **THEN** the gate refuses it for the same reason

#### Scenario: A different live change is still a legitimate owner

- **WHEN** a `Durable owner:` names a path inside a live change directory that is not the selected change's
- **THEN** the gate accepts it

#### Scenario: A refusal states the accepted forms

- **WHEN** a gate refuses an entry for lacking a closure or a valid owner
- **THEN** the diagnostic names the forms it accepts, including the existing-path form
- **AND THEN** the diagnostic says a path is checked for existence when cited and not re-checked afterwards, and that a tracker reference is accepted on shape because gates never fetch it
- **AND THEN** the author does not have to discover the boundary by trying candidates
