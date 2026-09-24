## ADDED Requirements

### Requirement: The routing rule reaches the agent that makes the decision

The block `keel --init` installs MUST state the Full/Lite routing rule: which work takes the
complete OpenSpec flow, which takes the local one, the size heuristic that separates them, and
that a project may declare the paths the heuristic gets wrong. Routing is the first decision of a
session and decides whether an OpenSpec change is created at all, so a rule reachable only from
Keel's own README is reachable only by an agent that already went looking. Keel MUST NOT claim to
enforce routing: the decision precedes the change, so no gate can bind to it, and what Keel
provides is that the rule and the project's exceptions are in front of the agent when it decides.

#### Scenario: A consuming repository receives the routing rule
- **WHEN** `keel --init` writes its block into a repository's `AGENTS.md`
- **THEN** the installed block states both modes, the size heuristic, and that a project may
  declare exceptions
- **AND THEN** the block stays inside its declared line budget, so the rule is carried in one line
  rather than by relaxing the budget that keeps the block resident

#### Scenario: Routing is carried and not gated
- **WHEN** work is routed to either mode
- **THEN** no Keel gate accepts or refuses that routing decision
- **AND THEN** nothing reports routing as verified, because a decision taken before any change
  exists has nothing to verify it against

### Requirement: A project declares the paths the size heuristic gets wrong

Keel MUST read an optional `full_mode_paths:` declaration from `keel/config.yaml`, naming paths
whose change always routes Full regardless of diff size. Each entry MUST carry a reason, and an
entry without one MUST NOT be read as a declaration: a bare path states that a file is special and
leaves a reader unable to recognise the sibling the list does not name, and the reason is the part
that transfers.

Keel MUST NOT accept a declaration in the opposite direction. There is no key by which a project
holds a path *out* of the complete flow however large its change, because every other declaration
in this file removes a confirmation and never a gate.

The path's shape MUST be checked and its existence MUST NOT be: an entry may name a file that does
not exist yet, which is the case the declaration most needs to cover.

#### Scenario: A declared path carries the reason it must route Full
- **WHEN** `keel/config.yaml` declares `full_mode_paths:` with an entry naming a path and a reason
- **THEN** Keel resolves that path as always routing Full, and carries the reason with it
- **AND THEN** the entry is resolved whether or not a file exists at that path

#### Scenario: An entry with no reason is refused by name
- **WHEN** an entry names a path and gives no reason after it
- **THEN** Keel reports the entry as unreadable, naming it and the form it requires
- **AND THEN** the entry does not silently become a bare path declaration

#### Scenario: There is no declaration for the opposite direction
- **WHEN** a repository declares a key intended to hold paths in the local flow however large
  their change
- **THEN** Keel reads no such key, and the paths it names route by the ordinary rule
- **AND THEN** no surface reports such a key as a declaration Keel honors

### Requirement: An unreadable routing declaration routes everything Full

When Keel cannot fully read `full_mode_paths:`, every change MUST route Full until the declaration
is corrected, and the reason MUST be reported. The other declarations in this file fail closed,
and closed for them means less proceeds without a human — `authorize:` authorizes nothing,
`triage:` admits nothing. The shared principle is to fail toward more scrutiny, and for a
declaration whose purpose is to add process, more scrutiny is more Full mode. Failing the other
way would lower the process floor on a typo, which is what the one-directional design exists to
prevent.

#### Scenario: A malformed entry raises the floor rather than dropping it
- **WHEN** `full_mode_paths:` contains an entry Keel cannot read
- **THEN** every change routes Full while the declaration stands uncorrected
- **AND THEN** the report names the entry that could not be read, so the state is attributable
  rather than mysterious

#### Scenario: An absent declaration changes nothing
- **WHEN** `keel/config.yaml` is absent, declares no `full_mode_paths:` block, or declares an
  empty one
- **THEN** routing resolves exactly as it does without this capability
- **AND THEN** no surface reports a routing declaration

### Requirement: The declared exceptions are reported where the decision is made

`keel context` MUST report a repository's declared routing paths when it declares any, so the
exceptions arrive at the session's first decision rather than in a file the agent may not open. It
MUST stay silent when nothing is declared, because a line printed every session for the
repositories that declared nothing teaches a reader to skip the line.

#### Scenario: A declaring repository sees its exceptions at session start
- **WHEN** `keel context` runs in a repository declaring `full_mode_paths:`
- **THEN** the projection reports the declared paths with their reasons
- **AND THEN** the projection's status and next action are unchanged by the declaration

#### Scenario: A repository declaring nothing sees nothing
- **WHEN** `keel context` runs in a repository with no `full_mode_paths:` declaration
- **THEN** the projection reports no routing line at all
