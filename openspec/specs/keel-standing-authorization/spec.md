## Purpose

Define how a repository declares standing authorization for named repository actions, how a task inherits or overrides it, what it can never authorize, and how the authorization source is reported.

## Requirements

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

### Requirement: Continuing to the next approved task needs no authorization

Moving from a durably complete task to the next unchecked task of the same change, inside a change
whose `tasks.md` the owner approved, MUST need no confirmation and no declaration. Each next task
MUST still start through `keel gate task-start` with its own recorded fingerprint, and every gate,
evidence requirement, semantic Review, and write-guard step MUST run unchanged. A stop with its own
trigger — a blocker, fingerprint drift, an out-of-scope need, a material choice escalated by
alignment, an unresolved `Q<n>`, a task's own Stop Rules — MUST halt. Continuing MUST NOT select work
outside the change or outside the approved `tasks.md` order, and MUST NOT authorize any repository
action — `commit`, `push`, `release`, and `archive` each still require their own name.

A declared `continuation` MUST remain accepted, because repositories declare it today, and MUST change
no behavior.

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
- **WHEN** a task is durably complete and the next unchecked task belongs to the same approved change
- **THEN** the next task starts through `keel gate task-start` without a confirmation
- **AND THEN** its own fingerprint is recorded before implementation, exactly as an attended start
  records one

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

### Requirement: A protocol-refresh authorization covers refreshing an older managed protocol

`protocol-refresh` MUST be an accepted `authorize:` name that takes no scope. It MUST cover exactly one action: running the refresh `keel context` names while it reports the repository's managed protocol as older than the running Keel. It MUST NOT cover committing the result, and it MUST NOT cover a refresh while a task's write guard is active. Like every standing authorization, it MUST remove only the confirmation.

#### Scenario: The name is accepted and reported
- **WHEN** `keel/config.yaml` declares `authorize:` listing `protocol-refresh`
- **THEN** the declaration is read without error, and `keel --doctor` reports `protocol-refresh` as authorized

#### Scenario: Other names stay unauthorized
- **WHEN** only `protocol-refresh` is declared
- **THEN** `commit`, `push`, `release`, `archive`, `continuation`, and `issue` remain unauthorized

### Requirement: A chat-reply authorization covers answering what addresses the role, and nothing it asks for

`chat-reply:<group>` MUST be an accepted `authorize:` name, scoped to one chat group, and a bare `chat-reply` MUST be refused with the form it needs. It MUST cover exactly one action: answering, in the chat, a record in a declared group that addresses the session's role — one that mentions the role by name or alias, assigns it a todo, or sits in its direct group — by posting a reply to it in that group, a direct message to its sender, or closing the assigned todo. It MUST NOT cover any action the record asks for beyond that answer, starting a thread, or mentioning another role to continue an exchange, and like every standing authorization it MUST remove only the confirmation.

#### Scenario: A scoped declaration is accepted and reported
- **WHEN** `keel/config.yaml` declares `authorize:` listing `chat-reply:lab`
- **THEN** the declaration is read without error, and `keel --doctor` reports `chat-reply:lab` as authorized

#### Scenario: A bare chat-reply is refused with its form
- **WHEN** `keel/config.yaml` declares `authorize:` listing `chat-reply`
- **THEN** Keel reports a configuration error naming `chat-reply` and the `chat-reply:<group>` form
- **AND THEN** the declaration authorizes nothing, including the entries listed beside it

#### Scenario: Other names stay unauthorized
- **WHEN** only `chat-reply:lab` is declared
- **THEN** `commit`, `push`, `release`, `archive`, `continuation`, `issue`, and `protocol-refresh` remain unauthorized

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

### Requirement: Every line of the authorize block is read

Keel MUST read every indented, non-comment, non-blank line under `authorize:` as an entry, ending the block only at a line at column zero. A list item MUST contribute its text after `- ` with any trailing ` #` comment removed, and any other indented line MUST contribute its trimmed text. Each entry MUST then be classified like any other, so a line Keel cannot read is reported by name and the declaration authorizes nothing, never shortened silently. The Claude write guard MUST read `push:` entries with the same comment rule.

#### Scenario: An item with a space is refused, not dropped
- **WHEN** `authorize:` lists `commit`, then `push:main branch`, then `release`
- **THEN** `keel --doctor` exits non-zero naming `push:main branch`, and neither `commit` nor `release` is reported authorized

#### Scenario: A trailing comment does not drop an item
- **WHEN** `authorize:` lists `commit  # owner, 2026-10-11` and `push:claude/*  # sessions push their own branches`
- **THEN** `keel --doctor` reports `commit` authorized and `push` scoped to `claude/*`, and the Claude write guard refuses `git push origin HEAD:main`

### Requirement: A protected branch is pushed only with the user's approval of that push

`authorize:` MAY declare `push-protected:<branch glob>` or `push-protected:<branch glob>@<role pattern>`, more than once. The glob MUST use branch-name characters and `*`, and the role pattern MUST use chat-role characters and `*`; anything else MUST be refused as malformed, and a bare `push` beside it MUST be refused naming both. `keel --doctor` MUST report `push-protected` with its globs and roles and state that the Claude write guard asks the user for each push to them.

#### Scenario: A protected branch is reported
- **WHEN** `authorize:` lists `push:claude/*` and `push-protected:main@iecc-pm`
- **THEN** `keel --doctor` reports `push-protected` scoped to `main@iecc-pm` and that each push to it is asked

#### Scenario: A malformed protected entry is refused
- **WHEN** `authorize:` lists `push-protected:main@Not A Role`, or a bare `push` beside `push-protected:main`
- **THEN** `keel --doctor` exits non-zero naming the entry

### Requirement: Restoring a session after a desktop shift is a named authorization

`authorize:` MAY declare `shift-restore`, with no scope. It covers exactly two actions of a session started by a shift change in the Claude desktop app, taken right after `keel shift resume`: turning that session's Remote Control back on, and renaming that session back to its working title. It MUST NOT cover any other session, clearing, starting, or archiving a session, or any repository action. `keel --doctor` MUST list it like the other names, and the accepted-names message for an unrecognized entry MUST include it.

#### Scenario: shift-restore is accepted and listed
- **WHEN** `authorize:` lists `commit` and `shift-restore`
- **THEN** the declaration is readable, and `keel --doctor` lists `shift-restore`

#### Scenario: A scoped shift-restore is refused
- **WHEN** `authorize:` lists `shift-restore:anything`
- **THEN** the declaration authorizes nothing, and the message names `shift-restore:anything`

### Requirement: A session's own shift change on the desktop app is a named authorization

`authorize:` MAY declare `self-shift`, with no scope. It covers exactly the four steps `keel shift ready --wake` prints on the Claude desktop app, after that `ready` stored the note: creating or updating the wake task it names, starting it with `run_scheduled_task`, renaming the session, and clearing it. It MUST NOT cover deciding to change shift, which stays where the protocol places it; any other session; archiving; or any repository action. `keel --doctor` MUST list it, and the accepted-names message MUST include it.

#### Scenario: self-shift is accepted and listed
- **WHEN** `authorize:` lists `commit` and `self-shift`
- **THEN** the declaration is readable, and `keel --doctor` lists `self-shift`

#### Scenario: A scoped self-shift is refused
- **WHEN** `authorize:` lists `self-shift:anything`
- **THEN** the declaration authorizes nothing, and the message names `self-shift:anything`

### Requirement: A scoped authorization may name the roles it applies to

Every scoped `authorize:` entry — `issue:`, `issue-close:`, `cleanup:`, `chat-reply:`, `push:<glob>` and `push-protected:` — MAY end in `@<pattern>`, where the pattern uses chat-role characters and `*`. Such an entry MUST apply only to a session whose chat role matches the pattern, and an entry without one MUST apply as before. What a session reads as authorized — the capsule's inherited autonomy, `keel context`, its chat-reply groups, and `keel --doctor`'s per-action lines — MUST leave out entries for other roles, except `push-protected`, which stays listed with its pattern because the guard refuses other roles by name. A session bound to no role MUST get no role-limited entry. The Claude write guard MUST keep the push check on while any push entry is declared for any role, and MUST allow a branch only through an entry that matches the session's role, refusing a branch that another role's entry covers by naming that pattern. `keel --doctor` MUST list, for each role bound in the repository, the scoped entries that apply to it. A malformed pattern MUST be refused like a malformed scope.

#### Scenario: Grants follow the role
- **WHEN** `authorize:` lists `push:design-*@rtl`, `push:review-*@ver*`, `issue:acme/widgets@rtl` and `chat-reply:soc@verify`, with `rtl` and `verify` bound
- **THEN** `keel --doctor` in rtl's worktree reports `issue` authorized and `chat-reply` not authorized, verify's reports the reverse, and both list the entries per role; the guard allows `git push origin design-x` from rtl and refuses it from verify naming `rtl`, allows `review-x` from verify, and refuses `design-x` from a session of role `spec`, which no entry names

#### Scenario: A malformed role pattern is refused
- **WHEN** `authorize:` lists `issue:acme/widgets@Not A Role`
- **THEN** `keel --doctor` exits non-zero naming the entry
