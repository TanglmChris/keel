## Purpose

Define how a repository declares standing authorization for named repository actions, how a task inherits or overrides it, what it can never authorize, and how the authorization source is reported.
## Requirements

### Requirement: A repository declares standing authorization in a closed vocabulary

Keel MUST read an optional `authorize:` declaration from `keel/config.yaml` naming repository
actions the owner has authorized to proceed without a per-occurrence confirmation. The accepted
action names MUST be a closed set — `commit`, `push`, `release`, `archive`, `continuation`,
`issue`, `protocol-refresh` — and an absent, empty, or undeclared block MUST leave every action unauthorized.

An action whose credential reaches further than the action itself MUST be declared with the
resource it may reach, and MUST be refused in its bare form. `issue` is such an action: the
credentials that open one are account-wide, while `commit`, `push`, `release`, and `archive` are
bounded by the checkout the declaration sits in, and so is `protocol-refresh`. Accepting a bare `issue` would make the narrow
form optional and the wide one the default, so the bare entry MUST be reported with the required
form rather than granted.

When the unrecognized entries include `sync`, the reported error MUST also name `sync` as a value
of `change-close --action` rather than an `authorize:` name, and point at `archive` as the name to
declare if the intent was to authorize that gate — `sync` and `archive` appear together in the
CLI's own `--action sync|archive` vocabulary, and a reader who copies from it reasonably copies
both, only one of which this declaration accepts. Keel MUST report the same configuration error
through `keel context`'s warnings, not only through `keel --doctor`, so a session that runs `keel
context` first learns the declaration authorizes nothing without a separate, explicitly-invoked
diagnostic call.

#### Scenario: A declared action is authorized for the whole repository
- **WHEN** `keel/config.yaml` declares `authorize:` listing `commit` and `push`
- **THEN** Keel resolves `commit` and `push` as standing-authorized for that repository
- **AND THEN** `release`, `archive`, `continuation`, `issue`, and `protocol-refresh` remain
  unauthorized because they were not listed

#### Scenario: No declaration preserves current behavior
- **WHEN** `keel/config.yaml` is absent, or declares no `authorize:` block, or declares an empty one
- **THEN** no action is standing-authorized
- **AND THEN** every autonomy default resolves exactly as it does without this capability

#### Scenario: An unrecognized action name is reported, not granted
- **WHEN** the `authorize:` block lists a name outside the closed set
- **THEN** Keel reports a configuration error naming the offending entry and the accepted names
- **AND THEN** the unrecognized entry authorizes nothing, and is not silently dropped

#### Scenario: A `sync` entry names the `change-close --action` confusion specifically
- **WHEN** the `authorize:` block lists `sync` among its entries
- **THEN** the reported configuration error states that `sync` is a `change-close --action` value,
  not an `authorize:` name
- **AND THEN** it points at `archive` as the name to declare instead
- **AND THEN** an unrecognized entry that is not `sync` (for example `deploy`) does not gain this
  sentence

#### Scenario: `keel context` reports the same failure without a separate `--doctor` call
- **WHEN** `keel/config.yaml`'s `authorize:` block lists an unrecognized action
- **THEN** `keel context`'s warnings include the same configuration error `keel --doctor` reports
- **AND THEN** `keel context`'s `status` and `nextAction` are unchanged by the broken declaration,
  exactly as an uncommitted git path is reported without changing selection

#### Scenario: A tracker action is declared with the repository it reaches
- **WHEN** the `authorize:` block lists `issue:<owner>/<repo>` whose scope is two non-empty
  segments
- **THEN** Keel resolves opening an issue on that named repository as standing-authorized
- **AND THEN** no other repository is authorized by that entry, whatever the agent's credentials
  can reach

#### Scenario: A bare tracker action is refused with the form it needs
- **WHEN** the `authorize:` block lists `issue` with no scope
- **THEN** Keel reports a configuration error naming `issue` and the `issue:<owner>/<repo>` form it
  requires
- **AND THEN** the declaration authorizes nothing, including the entries listed beside it

#### Scenario: A malformed scope is an unrecognized entry
- **WHEN** the `authorize:` block lists a scoped entry whose scope is not two non-empty segments
- **THEN** Keel reports it as an unrecognized entry, naming it
- **AND THEN** the whole declaration authorizes nothing, exactly as any other unrecognized entry
  voids it

### Requirement: A task inherits standing authorization only where it authored none

Keel MUST apply a standing authorization as the default a task did not author. A task that
declares its own `Autonomy boundary:` MUST keep that boundary unchanged, and a standing
authorization MUST NOT override, widen, or narrow it.

#### Scenario: A task without an authored boundary inherits the declaration
- **WHEN** a task declares no `Autonomy boundary:` and the repository authorizes `commit`
- **THEN** the compiled capsule resolves `commit` as authorized instead of `Default: hard-stop`
- **AND THEN** actions the repository did not declare still resolve to hard-stop

#### Scenario: An authored boundary wins over the declaration
- **WHEN** a task declares an explicit `Autonomy boundary:` and the repository declares an
  `authorize:` block
- **THEN** the compiled capsule carries the task's authored boundary
- **AND THEN** the repository declaration does not alter it

#### Scenario: The capsule names where an authorization came from
- **WHEN** a capsule carries an authorization inherited from the repository declaration
- **THEN** the capsule and the gate result identify the repository declaration as its source
- **AND THEN** a reader can distinguish an inherited authorization from a task-authored one

### Requirement: Standing authorization covers the action and never its proof

Keel MUST NOT let a standing authorization weaken, skip, or make conditional any gate, evidence
requirement, semantic Review, or write guard. A standing authorization MUST authorize only the
decision to proceed with a named action once its own checks have passed.

#### Scenario: A failing gate still stops a declared action
- **WHEN** `push` is standing-authorized and the task's completion gate returns `fail` or
  `needs-review`
- **THEN** the gate result is unchanged by the declaration
- **AND THEN** the action does not proceed on the strength of the authorization

#### Scenario: A declaration does not suppress reporting
- **WHEN** an action proceeds under a standing authorization
- **THEN** its command evidence, gate result, and Review are recorded exactly as they would be
  without the declaration
- **AND THEN** the declaration removes the confirmation, not the record

#### Scenario: A declaration is not a trigger
- **WHEN** an action is standing-authorized but the workflow has not reached the point where that
  action occurs
- **THEN** Keel does not initiate the action
- **AND THEN** no scheduler, backlog selection, or next-task inference is implied by the
  authorization

### Requirement: A continuation authorization covers one approved between-task boundary

A standing `continuation` authorization MUST cover exactly the boundary between a durably complete
task and the next unchecked task of the same change, inside a change whose `tasks.md` the owner
approved, and MUST cover nothing else. It removes only the between-task confirmation: each next
task MUST still start through `keel gate task-start` with its own recorded fingerprint, and every
gate, evidence requirement, semantic Review, and write-guard step MUST run unchanged. A stop with
its own trigger — a blocker, fingerprint drift, an out-of-scope need, a material choice escalated
by alignment, an unresolved `Q<n>`, a task's own Stop Rules — MUST halt exactly as it does without
the declaration. A `continuation` authorization MUST NOT initiate work, MUST NOT select work
outside the change or outside the approved `tasks.md` order, and MUST NOT authorize any repository
action — `commit`, `push`, `release`, and `archive` each still require their own name.

#### Scenario: Continuation authorizes no repository action
- **WHEN** `keel/config.yaml` declares `authorize:` listing only `continuation`
- **THEN** Keel resolves `continuation` as standing-authorized and reports it so
- **AND THEN** `commit`, `push`, `release`, and `archive` all remain unauthorized

#### Scenario: A capsule inherits continuation and names its source
- **WHEN** a task authors no `Autonomy boundary:` and the repository authorizes `continuation`
- **THEN** the compiled capsule carries the inherited authorization naming `keel/config.yaml` as
  its source
- **AND THEN** actions the repository did not declare still resolve to hard-stop

#### Scenario: The declaration is inert to gates and selection
- **WHEN** two otherwise identical repositories differ only in a declared `continuation`
- **THEN** every gate returns the same status and problem set in both
- **AND THEN** `keel context` reports the same status and next action in both

#### Scenario: The next task still starts through its own gate
- **WHEN** a `continuation` authorization spans the boundary after a durably complete task
- **THEN** the next unchecked task of the same change still starts through `keel gate task-start`
- **AND THEN** its own fingerprint is recorded before implementation, exactly as an attended start
  records one

### Requirement: A scope is a declaration Keel carries and never enforces

Keel MUST NOT represent a scoped authorization as a boundary it enforces. Keel invokes no tracker
client, observes none that an agent runs, and cannot prevent a write to a repository the scope
does not name. The scope MUST therefore be carried to the surfaces the agent and the owner read —
the doctor line and the compiled capsule's inherited autonomy entry — and the shape of the scope
MUST be checked without checking that the named repository exists, because a check that reached
the network would trade the local, offline, deterministic evaluation the verdict rests on.

#### Scenario: The doctor reports the scope beside the action
- **WHEN** `keel --doctor` runs against a repository declaring a scoped tracker authorization
- **THEN** the per-action line for `issue` reports it as authorized and names the scope it is
  bounded to
- **AND THEN** the line does not report `not authorized` merely because the declared entry is not
  the bare action name

#### Scenario: The scope's shape is checked and its existence is not
- **WHEN** a scoped entry names a repository that does not exist or cannot be reached
- **THEN** Keel accepts it on its shape and performs no network call to confirm it
- **AND THEN** an entry whose shape is wrong is still refused, so the check is on the form rather
  than on nothing

### Requirement: A protocol-refresh authorization covers refreshing an older managed protocol

`protocol-refresh` MUST be an accepted `authorize:` name that takes no scope. It MUST cover exactly one action: running the refresh `keel context` names while it reports the repository's managed protocol as older than the running Keel. It MUST NOT cover committing the result, and it MUST NOT cover a refresh while a task's write guard is active. Like every standing authorization, it MUST remove only the confirmation.

#### Scenario: The name is accepted and reported
- **WHEN** `keel/config.yaml` declares `authorize:` listing `protocol-refresh`
- **THEN** the declaration is read without error, and `keel --doctor` reports `protocol-refresh` as authorized

#### Scenario: Other names stay unauthorized
- **WHEN** only `protocol-refresh` is declared
- **THEN** `commit`, `push`, `release`, `archive`, `continuation`, and `issue` remain unauthorized
