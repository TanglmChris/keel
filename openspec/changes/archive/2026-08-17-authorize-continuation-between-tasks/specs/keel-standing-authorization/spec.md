## MODIFIED Requirements

### Requirement: A repository declares standing authorization in a closed vocabulary

Keel MUST read an optional `authorize:` declaration from `keel/config.yaml` naming repository
actions the owner has authorized to proceed without a per-occurrence confirmation. The accepted
action names MUST be a closed set — `commit`, `push`, `release`, `archive`, `continuation` — and
an absent, empty, or undeclared block MUST leave every action unauthorized.

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
- **AND THEN** `release`, `archive`, and `continuation` remain unauthorized because they were not
  listed

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

## ADDED Requirements

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
