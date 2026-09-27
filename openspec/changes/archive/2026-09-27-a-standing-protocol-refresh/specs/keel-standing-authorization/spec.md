## ADDED Requirements

### Requirement: A protocol-refresh authorization covers refreshing an older managed protocol

`protocol-refresh` MUST be an accepted `authorize:` name that takes no scope. It MUST cover exactly one action: running the refresh `keel context` names while it reports the repository's managed protocol as older than the running Keel. It MUST NOT cover committing the result, and it MUST NOT cover a refresh while a task's write guard is active. Like every standing authorization, it MUST remove only the confirmation.

#### Scenario: The name is accepted and reported
- **WHEN** `keel/config.yaml` declares `authorize:` listing `protocol-refresh`
- **THEN** the declaration is read without error, and `keel --doctor` reports `protocol-refresh` as authorized

#### Scenario: Other names stay unauthorized
- **WHEN** only `protocol-refresh` is declared
- **THEN** `commit`, `push`, `release`, `archive`, `continuation`, and `issue` remain unauthorized

## MODIFIED Requirements

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
