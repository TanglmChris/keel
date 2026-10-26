## Purpose

Define how a role declares what it is waiting for in the chat, and how a host-scheduled `keel patrol`, run as the coordinator's role, notifies the roles whose conditions are met and routes labelled issue updates to roles, writing nothing when nothing is new and never fetching or scheduling.

## Requirements

### Requirement: A role declares what it is waiting for in the chat

`keel chat wait <group> --commit <sha> [--remote <name>] [note]` and `keel chat wait <group> --issue <n> --closed [note]` MUST write a `wait` record from the caller's role in a group it belongs to, carrying the condition. A wait MUST NOT make anything unread or wake any role. `keel chat waits [--json]` MUST list every wait that no `met` record targets, with its role, group, and condition. Exactly one condition MUST be given, and anything else MUST be refused naming the forms.

#### Scenario: A declared wait is listed until met
- **WHEN** `verify` runs `keel chat wait soc --commit <sha>`
- **THEN** `keel chat waits --json` lists it with role `verify` and condition `commit <sha> on origin`, and nobody has it unread

#### Scenario: A malformed wait is refused
- **WHEN** `keel chat wait soc` names no condition, or both `--commit` and `--issue`
- **THEN** it exits non-zero naming the two forms

### Requirement: Patrol notifies the roles whose conditions are met and writes nothing otherwise

`keel patrol [--issues <file>] [--idle <duration>] [--json]` MUST run as the caller's bound role and MUST NOT fetch, schedule, or call a model. For each open wait in the groups that role can read, it MUST check the condition — a commit contained in a `refs/remotes/<remote>/` ref; an issue that `--issues` lists as closed — and for each that holds MUST write a `met` record targeting the wait and send the waiting role a direct message naming the condition and the wait, unless the waiter is the patrolling role. Without `--issues`, issue conditions MUST be reported unchecked. Patrol MUST list each bound role's presence, last activity, and open todo count, marking a role idle beyond `--idle`. It MUST exit 0 when it wrote nothing, 2 when the patrolling role has something to act on — a risk, or a wait of its own now met — 3 when it wrote records only for other roles, and 1 on an error; idleness MUST NOT change the exit status.

#### Scenario: A landed commit wakes the waiting role once
- **WHEN** `verify` waits for a commit, the commit reaches `origin`, and `rtl` runs `keel patrol` twice
- **THEN** the first run exits 3, marks the wait met, and `verify` has a direct message from `rtl` naming the commit unread
- **AND THEN** the second run exits 0 and writes nothing

#### Scenario: Nothing new writes nothing
- **WHEN** no condition holds and no mapped issue changed
- **THEN** `keel patrol` exits 0, the chat store's logs are unchanged, and the digest lists the roles

#### Scenario: An issue condition needs the caller's issue data
- **WHEN** a role waits for issue 42 to close and patrol runs without `--issues`, then with `--issues` listing 42 as `CLOSED`
- **THEN** the first run reports the condition unchecked and exits 0, and the second marks it met and exits 3

#### Scenario: Only what the coordinator must handle exits 2
- **WHEN** the coordinator runs `keel patrol --since-last --notify` after only the remote tip moved, again after its primary checkout gains an uncommitted file, then `keel patrol` after another role's wait is met, and after its own wait is met
- **THEN** the runs exit 3, 2, 3 and 2, and `keel patrol --help` names exit 3

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

### Requirement: The patrolling role is reminded to re-arm its schedule

`keel/config.yaml` MAY declare `patrol:` with `role:` naming a chat role and `every:` a duration of the form `<n>s`, `<n>m`, `<n>h`, or `<n>d`. In a worktree bound to that role, `keel context` MUST carry `patrol` with the role and interval, the SessionStart and compaction projection MUST state that the role runs `keel patrol` at that interval and that a session's schedule ends with the session, and `keel shift resume` MUST end with the same reminder. Keel MUST NOT create the schedule. A declaration missing either value, or with a malformed one, MUST be reported and MUST remind nobody; a worktree bound to another role MUST get no reminder.

#### Scenario: A new shift of the coordinator is reminded
- **WHEN** `patrol:` declares `role: iecc-pm` and `every: 30m`, and a worktree bound to `iecc-pm` starts a session and runs `keel shift resume`
- **THEN** `keel context --json` carries `patrol` with `iecc-pm` and `30m`, the projection names `keel patrol` and `30m`, and the resume output ends with the reminder

#### Scenario: Other roles and broken declarations are quiet
- **WHEN** the worktree is bound to `rtl`, or `every:` reads `soon`
- **THEN** no `patrol` field or reminder appears, and the malformed declaration is reported in warnings

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

### Requirement: Quota thresholds are reported once each, and nudging pauses near the limit

`keel patrol --quota <percent>` MUST treat each threshold in `--quota-alerts` (default 90, 95, 99) that the figure has reached as a risk once per quota period, reporting the highest newly reached threshold, and MUST start a new period when the figure drops below the previous run's. At or above `--quota-quiet-at` (default 90), `--nudge` MUST send nothing and say so.

#### Scenario: Each threshold is reported once, and a new period starts over
- **WHEN** the coordinator runs `keel patrol --since-last --notify --nudge` with `--quota` 50, 91, 93, 96, then 10, then 92, while `verify` has an addressed message waiting
- **THEN** 50 reports nothing and nudges `verify`, 91 reports `past 90%` and nudges nobody, 93 reports nothing, 96 reports `past 95%`, 10 reports nothing, and 92 reports `past 90%` again

### Requirement: A patrol recommends its next run

`keel patrol` MUST print `next: <duration> (<rule>)` and, with `--json`, carry `next_after_s`, `next_rule` and `next_at`. With `cadence: adaptive` declared under `patrol:`, the first matching rule MUST choose it: `risk` when the run found a risk (default 30m), `quota` when `--quota` is 90 or more (4h), `night` when the local time is inside `quiet: HH:MM-HH:MM` and there is no risk (until the window ends), `busy` when a role other than the patrolling one is not idle or an open wait or todo is assigned to a role that is not idle (60m), and `idle` otherwise (3h); `risk:`, `quota:`, `busy:`, `idle:` and `quiet:` MUST override those defaults, and `min:` and `max:` MUST clamp the result. Without `cadence: adaptive` it MUST recommend `every:` with rule `fixed`.

#### Scenario: Each rule is chosen by its own condition
- **WHEN** the coordinator patrols with `cadence: adaptive`: with every other role idle, after another role's session starts, with `--quota 92` reported once already, after its primary checkout gains an uncommitted file under `--since-last`, and inside a `quiet:` window
- **THEN** the rules are `idle` (3h), `busy` (1h), `quota` (4h), `risk` (30m) and `night` (until the window ends)
- **AND THEN** without `cadence: adaptive` the rule is `fixed` at `every:`, and `min: 50m` raises a 45m `busy` to 50m, printed as `next: 50m (busy)`

### Requirement: A host-run tick runs the patrol when due

`keel tick` MUST be one model-free step: for each role `patrol:` declares that is bound to a worktree and whose last recorded `next_at` is absent or has passed, it MUST fetch `origin` there and run `keel patrol --since-last --notify` as that role, then record that role's `next_at`; for each other declared role it MUST say the patrol is not due and run nothing. `keel tick task` MUST print a launchd job that calls `keel tick` every 300 seconds, and the commands that install it, and MUST create nothing. With `runner: tick` under `patrol:`, the patrolling role's reminder MUST name `keel tick` and MUST NOT ask it to re-create a session schedule.

#### Scenario: The patrol runs only when due
- **WHEN** `patrol:` declares `runner: tick` and `keel tick` runs three times, the third after the recorded `next_at` was moved into the past
- **THEN** the first and third run the patrol and record a `next_at`, and the second says the patrol is not due and runs none

#### Scenario: The launchd job is printed, not installed
- **WHEN** `keel tick task` runs
- **THEN** it prints a plist with `StartInterval` 300 and `tick` and the bound worktree in its arguments, the `launchctl bootstrap` command, and `Keel creates nothing`, and writes no file

### Requirement: Keel's launchd jobs name a node that outlives an upgrade

The LaunchAgents that `keel tick task` prints and `keel chat wake add` and the chat bridge write MUST name, as their first program argument, the `node` on `PATH` whose real path is the running node's, and `process.execPath` only when none is; and MUST leave every directory inside a Claude plugin cache out of their `PATH`. `keel --doctor` MUST report each `dev.keel.*` LaunchAgent whose first program argument does not exist, naming the file, the missing path and the command that re-creates it, and MUST report none as a problem when every such path exists.

#### Scenario: The printed job names the symlink, not its target
- **WHEN** `keel tick task` runs under a node reached through `<bin>/node`, a symlink to a versioned directory, with a plugin cache directory first on `PATH`
- **THEN** the plist's first program argument is `<bin>/node`, and its `PATH` holds `<bin>` and no plugin cache directory

#### Scenario: The chat waker's LaunchAgent does the same
- **WHEN** `keel chat wake add` writes its LaunchAgent under the same conditions
- **THEN** its first program argument is `<bin>/node` and its `PATH` holds no plugin cache directory

#### Scenario: Doctor reports a job whose node is gone
- **WHEN** the LaunchAgents directory holds `dev.keel.tick.x.plist` naming a node path that does not exist, and `keel --doctor` runs, and then the plist names an existing path
- **THEN** the first run prints a `launchd` problem line naming `dev.keel.tick.x.plist`, the missing path and `keel tick task`; the second prints `launchd: ok`

### Requirement: The tick passes free disk and a declared quota to the patrol

Before each patrol run, `keel tick` MUST measure free space on that patrol's worktree filesystem and pass it as `--disk-free-gb`, with `--disk-min-gb` from the first `patrol:` item declaring `disk_min_gb:`, and patrol's default otherwise. When a `patrol:` item declares `quota_file:`, the tick MUST read the first number in that file and pass it as `--quota` only when the file was modified within the last 6 hours, and it MUST run no command to obtain it. The tick MUST print a quota line when the quota state — read, stale, unreadable, or unchecked when no `quota_file:` is declared — differs from its previous run's, and not otherwise.

#### Scenario: Low disk reaches the owning coordinator once
- **WHEN** `patrol:` lists scoped `pm-a` and `pm-b` with `runner: tick` and `disk_min_gb` far above the machine's free space, and `keel tick` runs the patrols twice
- **THEN** pm-a, the first listed, is sent one `keel-patrol` message naming free disk below the floor, and pm-b none

#### Scenario: A quota file drives the quota risk, and its absence is said once
- **WHEN** `quota_file:` names a file reading `91`, then `96`, between due ticks, and later the file is made 7 hours old; and separately no `quota_file:` is declared
- **THEN** the owning coordinator is sent `past 90%` and then `past 95%` once each, the old file makes the tick print that quota is stale, and with none declared the first tick prints that quota is not checked and the next one prints no quota line

### Requirement: The tick fetches issue state for the patrol when something needs it

When a patrol is due and `keel/config.yaml` declares a readable `issue_roles:` route, or a chat group holds an open `issue #<n> closed` wait, `keel tick` MUST run `gh issue list --state all --search "sort:updated-desc" --limit 100 --json number,title,state,labels,updatedAt` once in that step, and `gh issue view <n>` with the same fields for each waited issue the list did not return, and MUST pass what it read to every patrol it runs in that step as `--issues`. When neither holds, it MUST run no `gh`. When a `gh` call cannot start, fails, or prints no JSON, the tick MUST still pass what it read and MUST print a line saying issue checks are not run and why when that state differs from its previous one, and not otherwise. `keel --doctor` MUST print an `issue checks` line from the tick's last recorded issue state, naming the reason when the checks are not run.

#### Scenario: A tick routes a labelled issue and meets an issue wait
- **WHEN** `patrol:` lists scoped `pm-a` and `pm-b` with `runner: tick`, `issue_roles:` routes the label `dev` to `dev-b`, `dev-a` waits in `team-a` for issue 42 to close, `gh issue list` returns issue 7 labelled `dev` and not issue 42, `gh issue view 42` returns it `CLOSED`, and `keel tick` runs both patrols
- **THEN** `dev-b` is sent one message naming issue 7, `dev-a` is sent one message that `issue #42 closed` is met, and a second due tick sends neither again

#### Scenario: A failed fetch is said once and shown by the doctor
- **WHEN** `gh` exits 1 for two due ticks of a repository declaring `issue_roles:`
- **THEN** the first tick prints a line saying issue checks are not run that names the failure, the second prints no such line, and `keel --doctor` prints `issue checks` as not checked with that reason

#### Scenario: Nothing needs issues, so no gh runs
- **WHEN** a repository declares no `issue_roles:` and holds no issue wait, and `keel tick` runs a due patrol
- **THEN** no `gh` command runs

### Requirement: A standing risk reaches the coordinator once

Under `keel patrol --since-last`, each risk about a CLI hand-off and each risk about a session whose directory is gone MUST be recorded by its text in the patrolling role's snapshot, and MUST be counted among the run's risks — and so sent by `--notify` — only when that text is absent from the previous run's snapshot, a first run included. A standing risk whose text was recorded by the previous run MUST be printed as sent before and MUST NOT be sent or raise the exit status. Without `--since-last`, every such risk MUST be reported on every run.

#### Scenario: An unchanged moved-session risk is sent once
- **WHEN** verify's ended CLI session is recorded in a directory that no longer exists and the coordinator runs `keel patrol --since-last --notify` three times
- **THEN** the coordinator is sent exactly one `keel-patrol` message naming verify's session, the second and third runs print it as sent before and do not exit 2, and a plain `keel patrol` still reports it as a risk
