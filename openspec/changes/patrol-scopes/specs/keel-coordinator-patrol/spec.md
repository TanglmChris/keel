## ADDED Requirements

### Requirement: Several roles may patrol, each over the roles it coordinates

`patrol:` MAY be a list of mappings, each opened by `- role:` and carrying the keys a single mapping carries plus `scope: group:<name>`; a single mapping MUST keep meaning one patrolling role over the whole repository. An item Keel cannot read, or a role declared a second time, MUST be reported and patrol nothing while the other items apply. A scoped declaration MUST cover the members of its chat group, an unscoped declaration MUST cover the roles in no declared scope, and a role in two scopes MUST be covered by both and nudged at most once per window; a patrolling role MUST NOT cover itself, and a role `patrol:` does not declare MUST cover every role. The repository-wide items — the remote default branch tip, the primary checkout, binding drift, disk, and quota — MUST belong to the unscoped declaration when there is one and to the first declared otherwise. Each declared role MUST get its own declaration's reminder in `keel context`, the projection, and `keel shift resume`, and its own cadence in the next-run recommendation.

#### Scenario: Each coordinator is reminded of its own declaration
- **WHEN** `patrol:` lists `pm-a` (`every: 30m`, `scope: group:team-a`), `pm-b` (`every: 45m`, `host_task: team-b-patrol`, `scope: group:team-b`), and an item with `every: soon`
- **THEN** `keel context --json` in pm-a's worktree carries `patrol` with `pm-a` and `30m`, pm-b's carries `pm-b`, `45m`, and `team-b-patrol`, dev-a's carries none, and the broken item is reported in warnings
- **AND THEN** `keel patrol task` in pm-b's worktree renders `team-b-patrol`, in dev-a's worktree it is refused naming `pm-a`, `pm-b`, and `--role`, and with `--role pm-a` it renders `keel-patrol-pm-a`

#### Scenario: Each coordinator nudges and routes only the roles it covers
- **WHEN** `team-a` holds pm-a, dev-a, and flow, `team-b` holds pm-b, dev-b, and flow, an unscoped `chief` is also declared, dev-a, dev-b, flow, and lead each have an addressed message waiting past `--idle`, and issue 170 carries labels routed to flow and dev-b
- **THEN** pm-a's `--nudge` nudges dev-a and flow only, pm-b's nudges dev-b only, and chief's nudges lead only
- **AND THEN** pm-a's `--issues` sends flow one message naming #170 and dev-b none, and pm-b's then sends dev-b one and flow no second

#### Scenario: Repository-wide risks reach one coordinator
- **WHEN** the primary checkout gains an uncommitted file between two `--since-last --notify` runs of each declared role
- **THEN** with the unscoped `chief` declared only chief is sent the risk, and with only `pm-a` and `pm-b` declared only pm-a is

#### Scenario: The tick runs each declared patrol when due
- **WHEN** `patrol:` lists `pm-a` and `pm-b` with `runner: tick`, `keel tick` runs twice, and then pm-b's recorded `next_at` is moved into the past and it runs again
- **THEN** the first tick runs both patrols, the second runs neither and says both are not due, and the third runs pm-b's only

## MODIFIED Requirements

### Requirement: Issue labels route issue updates to roles

`keel/config.yaml` MAY declare `issue_roles:`, one `<label>: <role>` per line, where the key MAY instead name a set of labels joined by ` + ` (a `+` with whitespace on both sides); a quoted key is one label and is not split. A route matches an issue that carries every label of its key. When `keel patrol` receives `--issues` (the JSON `gh issue list --json number,title,state,labels,updatedAt` prints), it MUST drop each matching route whose label set is a strict subset of another matching route's set, and MUST send each role of the remaining routes one direct message for that issue's `updatedAt`, recorded with ref `issue:#<n>@<updatedAt>`, and MUST NOT send it again while that ref exists in a direct group between that role and any patrolling role. A declared patrolling role MUST route only to the roles its declaration covers. A line it cannot read, including a set with an empty or repeated label, MUST be reported and route nothing.

#### Scenario: A labelled issue reaches its role once per update
- **WHEN** `issue_roles:` maps `role:verify` to `verify` and `--issues` lists issue 157 with that label
- **THEN** patrol sends `verify` one direct message naming #157 and exits 3; a second run with the same `updatedAt` exits 0; a run with a later `updatedAt` sends one more

#### Scenario: A set of labels routes to the team that carries them all
- **WHEN** `issue_roles:` maps `design` to `design-iecc`, `design + dmc_rmw` to `design-rmw`, and `flow` to `flow`, and `--issues` lists issue 160 labelled `design`, `dmc_rmw`, and `flow`, and issue 161 labelled `design` alone
- **THEN** `design-rmw` and `flow` each get one direct message naming #160 and `design-iecc` gets none naming it, and `design-iecc` gets one naming #161 that `design-rmw` does not

#### Scenario: A set that cannot be read routes nothing
- **WHEN** `issue_roles:` holds `design + : design-rmw` and `design + design: design-rmw`, and `--issues` lists an issue labelled `design`
- **THEN** both lines are reported and `design-rmw` gets no message

### Requirement: A patrol run reports only what changed since the last one

`keel patrol --since-last` MUST keep a snapshot per patrolling role of the shift status and each role's idleness and open todos for the roles its declaration covers, of the remote default branch tip and the primary worktree's uncommitted path count when its declaration owns the repository-wide items, and of the role's waking unread records older than `--idle`, and MUST report only the entries that differ from the previous run's snapshot. A first run MUST record a baseline and report no change. It MUST exit 2 when it found a risk, 3 when it reported a change or wrote anything with no risk, and 0 otherwise. With `--notify`, a run MUST send the patrolling role one direct message from `keel-patrol` listing only its risks — the primary checkout gaining uncommitted paths after a clean run, a host-reported `--disk-free-gb` dropping below `--disk-min-gb`, and a role that has left two unread nudges in a row unanswered — and MUST send nothing when there is none, however much changed; `--notify` without `--since-last` MUST be refused. Only the declaration that owns the repository-wide items MUST report the checkout and disk risks. Every run MUST append one line to the patrolling role's run log.

#### Scenario: Only a change is reported, once
- **WHEN** the coordinator runs `keel patrol --since-last --notify` three times, with `verify` running `keel shift ready` and a new commit reaching the remote between the first and second runs
- **THEN** the first run reports a baseline and exits 0, the second reports the shift status line and the remote tip as changed and exits 3 with no message, since neither is a risk, and the third reports nothing and exits 0

#### Scenario: Only risks reach the coordinator, and every run is logged
- **WHEN** the primary checkout gains an uncommitted file, the host reports 12 GB free, and `verify` leaves two unread nudges unanswered
- **THEN** each of the three is sent to the coordinator once in a message from `keel-patrol`, and the role's run log holds one line per run

### Requirement: The patrol's host task is declared and rendered, never installed by Keel

`patrol:` MAY declare `host_task:` and `model:`; Keel MUST NOT choose a model. With `host_task:` declared, the patrolling role's reminder MUST name the host task and ask to confirm it is still enabled instead of to re-create a session schedule. `keel patrol task` MUST print a self-contained host task — its id, a cron suggested from `every:`, the declared model or a statement that none is declared, and a prompt that runs `keel patrol --since-last --notify` against the role's worktree by path — and MUST create nothing. It MUST render the declaration `--role <role>` names, else the one whose role is bound to the calling worktree, else the only declaration when there is one, and MUST otherwise be refused naming the declared roles; it MUST be refused without a valid `patrol:` or without a worktree bound to the chosen role.

#### Scenario: The host task is rendered from the declaration
- **WHEN** `patrol:` declares `role: rtl`, `every: 30m`, and `host_task: soc-patrol`, and `keel patrol task` runs
- **THEN** it prints task id `soc-patrol`, cron `*/30 * * * *`, that no model is declared, and a prompt containing `keel patrol --repo <rtl's worktree> --since-last --notify`, and no file under the repository changes

#### Scenario: A declared host task changes the reminder
- **WHEN** `patrol:` declares `host_task: soc-patrol` and a session starts in the worktree bound to its role
- **THEN** `keel context` carries `patrol.hostTask` `soc-patrol` and the session-start note says the host task outlives the session and asks to confirm it is enabled

### Requirement: The patrol nudges idle roles directly

`keel patrol --nudge` MUST consider every bound role the patrolling role's declaration covers, other than the patrolling role itself, and MUST send an idle role one direct message from `keel-patrol` when addressed records, excluding Keel's own senders, have waited longer than `--idle` (at most once per two hours), when a todo assigned to it has been closed since the patrol last looked (once per closure, naming `keel shift ready --wake` when another todo is still open for it and plain `keel shift ready` otherwise; the first run only records existing closures), or when a note filed with `keel shift ready --wake` has waited longer than `--idle` with no wake since (once per note). A note filed without `--wake` MUST NOT be nudged to resume. `--context` and `--shift-at` MUST be refused, naming their retirement: context never triggers a shift. When the role nudged has a recorded desktop session whose process is not running, the run MUST also report a risk naming that session id and `send_message`, since the nudge alone wakes nothing (#331). A role whose park is in effect (`keel chat role --park`) MUST NOT be nudged, MUST NOT produce an unanswered-nudge risk, and MUST NOT be reported as unattended binding drift; the patrol's role line MUST say it is parked.

#### Scenario: Roles are nudged once each, and parked notes are left alone
- **WHEN** `verify` has an addressed message waiting, `lint` holds two todos it has read, and the coordinator runs `keel patrol --nudge`, `lint` closes one todo, the coordinator runs it twice more, `lint` closes the other and it runs again, then `lint` files a note with `ready --wake` that no wake reaches and `verify` files one without it
- **THEN** the first run nudges `verify` for unread and not `lint`, the second nudges `lint` to change shift naming `ready --wake`, the third nudges nobody, the fourth nudges `lint` naming plain `ready` and the coordinator, a later run nudges `lint` to resume and not `verify`, no run nudges `lint` over the patrol's own message, and `--context` is refused

#### Scenario: A nudge to an idle desktop session is a risk at once
- **WHEN** `verify`'s hooks ran on the desktop app as session `local_test-331` whose process has since exited, an addressed message has waited past `--idle`, and the coordinator runs `keel patrol --nudge`
- **THEN** the run nudges `verify` and reports a risk naming `local_test-331` and `send_message`, on that first nudge

#### Scenario: A parked role is left alone
- **WHEN** `verify` has an addressed message waiting past `--idle`, `rtl` parks `verify`, and the coordinator runs `keel patrol --nudge` twice
- **THEN** neither run nudges `verify` or reports a risk for it, and the role line for `verify` says `parked`; after `keel chat role --unpark verify` the next run nudges `verify`

### Requirement: A host-run tick runs the patrol when due

`keel tick` MUST be one model-free step: for each role `patrol:` declares that is bound to a worktree and whose last recorded `next_at` is absent or has passed, it MUST fetch `origin` there and run `keel patrol --since-last --notify` as that role, then record that role's `next_at`; for each other declared role it MUST say the patrol is not due and run nothing. `keel tick task` MUST print a launchd job that calls `keel tick` every 300 seconds, and the commands that install it, and MUST create nothing. With `runner: tick` under `patrol:`, the patrolling role's reminder MUST name `keel tick` and MUST NOT ask it to re-create a session schedule.

#### Scenario: The patrol runs only when due
- **WHEN** `patrol:` declares `runner: tick` and `keel tick` runs three times, the third after the recorded `next_at` was moved into the past
- **THEN** the first and third run the patrol and record a `next_at`, and the second says the patrol is not due and runs none

#### Scenario: The launchd job is printed, not installed
- **WHEN** `keel tick task` runs
- **THEN** it prints a plist with `StartInterval` 300 and `tick` and the bound worktree in its arguments, the `launchctl bootstrap` command, and `Keel creates nothing`, and writes no file
