## RENAMED Requirements

- FROM: `### Requirement: A scope is a declaration Keel carries and never enforces`
- TO: `### Requirement: A scope is a declaration Keel carries, and only a push scope is enforced`

## MODIFIED Requirements

### Requirement: A repository declares standing authorization in a closed vocabulary

Keel MUST read an optional `authorize:` declaration from `keel/config.yaml` naming repository
actions the owner has authorized to proceed without a per-occurrence confirmation. The accepted
action names MUST be a closed set — `commit`, `push`, `release`, `archive`, `continuation`,
`issue`, `protocol-refresh`, `chat-reply`, `issue-close`, `cleanup` — and an absent, empty, or undeclared block MUST leave every action unauthorized.

An action whose credential reaches further than the action itself MUST be declared with the
resource it may reach, and MUST be refused in its bare form. `issue`, `issue-close`, `cleanup`, and `chat-reply` are such actions — `chat-reply` because a reply in a Slack-enabled group leaves the machine — and `issue`'s case is the model: the
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
- **AND THEN** `release`, `archive`, `continuation`, `issue`, `protocol-refresh`, `chat-reply`,
  `issue-close`, and `cleanup` remain unauthorized because they were not listed

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

### Requirement: A scope is a declaration Keel carries, and only a push scope is enforced

Keel MUST NOT represent a scoped authorization as a boundary it enforces, except a `push:<glob>` scope, which the Claude write guard enforces on `git push` as the write-guard capability requires. Keel invokes no tracker
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

## ADDED Requirements

### Requirement: A push authorization may name the branches it reaches

`push` MUST accept an optional scope: a bare `push` MUST keep its meaning, and `push:<glob>` MUST limit the authorization to pushes whose target branch matches one of the declared globs, where `*` matches within one `/`-separated segment and `**` across segments. `push:<glob>` MAY be declared more than once. A glob MUST be drawn from branch-name characters and `*`, and any other scope MUST be refused as malformed. A declaration holding both a bare `push` and a `push:<glob>` MUST be refused, naming both, because the bare form would silently widen the scoped one. `keel --doctor` MUST report the globs beside `push` and state that the Claude write guard enforces them.

#### Scenario: A push scope is reported with its enforcement
- **WHEN** `authorize:` lists `push:claude/*` and `push:worktree-*`
- **THEN** `keel --doctor` reports `push` as authorized, scoped to both globs, and states that the Claude write guard enforces them

#### Scenario: A bare push beside a scoped one is refused
- **WHEN** `authorize:` lists both `push` and `push:claude/*`
- **THEN** Keel reports a configuration error naming both entries, and the declaration authorizes nothing

### Requirement: Closing an issue and cleaning the scratchpad are named and carried

`issue-close:<owner>/<repo>` MUST be an accepted `authorize:` name with the `issue:` form, covering closing an issue on that repository with a comment naming the work that resolved it, and a bare `issue-close` MUST be refused with the form it needs. `cleanup:scratch` MUST be an accepted name whose only scope is `scratch`, covering removal of temporary worktrees and run output under the session's own scratchpad after checking that they are merged and that no process uses them, and never a branch or another session's files; any other scope MUST be refused. Both MUST be carried to `keel --doctor` and the capsule's inherited autonomy entry, and neither is enforced.

#### Scenario: The new names are carried with their scope
- **WHEN** `authorize:` lists `issue-close:acme/widgets` and `cleanup:scratch`
- **THEN** `keel --doctor` reports `issue-close` scoped to `acme/widgets` and `cleanup` scoped to `scratch`, and a task authoring no boundary inherits both entries

#### Scenario: A wrong form is refused with the one it needs
- **WHEN** `authorize:` lists a bare `issue-close`, or `cleanup:runs`
- **THEN** Keel reports a configuration error naming the entry and the `issue-close:<owner>/<repo>` or `cleanup:scratch` form
