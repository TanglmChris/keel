## ADDED Requirements

### Requirement: The external agent catalog records facts and is read on demand

Keel MUST bundle a catalog entry for each external model CLI it knows and MUST merge entries from a machine-local `agents.json` under the Keel home directory, where each field a machine entry declares replaces that field of the bundled entry with the same name and a name the bundle lacks adds an entry. An entry MUST carry a command template, the sandbox it offers per mode or none, where it sends data, and pitfalls each stamped with a date and a source, and MUST NOT carry a statement of which work the agent suits. `keel agents` MUST list every entry with its source, whether its executable resolves, and whether the current project allows it. `keel context` and session-start output MUST NOT include the catalog.

#### Scenario: Bundled entries list with their resolution
- **WHEN** `keel agents` runs with no machine file
- **THEN** it lists `codex` and `dsh` as bundled, each with its resolved executable path or `not found`
- **AND THEN** `keel agents codex` prints its template, sandboxes, destination, and every dated pitfall

#### Scenario: A machine entry overrides a bundled one
- **WHEN** the machine file declares `dsh` with a different executable path
- **THEN** `keel agents` lists `dsh` with source `machine` and that path
- **AND THEN** the fields the machine entry did not declare keep their bundled values

#### Scenario: A malformed machine file is reported, not half-read
- **WHEN** the machine file is not valid JSON
- **THEN** `keel agents` names the file and the parse error and lists only the bundled entries

#### Scenario: Session start carries no catalog
- **WHEN** `keel context` runs in a project that allows external agents
- **THEN** its output names no catalog entry and no pitfall

### Requirement: A project declares which external agents it allows and what must not leave

Keel MUST read an optional `external_agents:` block in `keel/config.yaml` with an `allow:` list of agent names and an optional `egress_deny:` list of `- <glob>: <reason>` entries. An absent block MUST allow nothing. An `egress_deny` entry without a reason, or an unrecognized sub-key, MUST be reported by name, and while any is present every brief MUST be refused.

#### Scenario: An absent declaration allows nothing
- **WHEN** `keel/config.yaml` has no `external_agents:` block
- **THEN** `keel agents brief codex` is refused
- **AND THEN** the refusal shows how to declare `external_agents:` with `allow:`

#### Scenario: An agent outside allow is refused
- **WHEN** `allow:` names `codex` and the brief asks for `dsh`
- **THEN** the brief is refused, naming `dsh` and the allowed agents

#### Scenario: A deny entry without a reason refuses every brief
- **WHEN** `egress_deny:` holds an entry with no reason
- **THEN** every brief is refused, naming the entry

### Requirement: The external agent brief is the delegation brief, checked for egress

`keel agents brief <name> --mode helper|implementation --dir <path> --out <file>` MUST compile the same projection `keel project --event subagent-start` compiles for that mode and MUST apply every refusal it applies, including the matching-guard precondition for implementation. It MUST refuse when any Read or Touch path matches an `egress_deny` pattern, naming the path, the pattern, and the reason. On success it MUST write the brief, with the task, Read, Touch, checks, and prohibitions against commit, push, branch switch, issue changes, OpenSpec and Keel state, and writes outside `--dir`, to `--out`, MUST print the command line filled from the catalog template, and MUST state that Keel cannot observe what the agent reads beyond the brief. Keel MUST NOT launch the agent.

#### Scenario: A clean helper brief is written and its command printed
- **WHEN** a helper brief for an allowed `codex` names no denied path
- **THEN** the prompt file holds the task, Read, checks, and prohibitions
- **AND THEN** the printed command uses the read-only sandbox, `--dir`, and the prompt file, and no codex process was started

#### Scenario: A denied path refuses the brief
- **WHEN** the task's Read names a path matching an `egress_deny` pattern
- **THEN** the brief is refused, naming that path, the pattern, and its reason
- **AND THEN** no prompt file is written

#### Scenario: Implementation still needs the matching guard
- **WHEN** an implementation brief is asked for with no active guard for the task
- **THEN** it is refused with the same reason `keel project --event subagent-start --subagent-mode implementation` gives

### Requirement: The checkout is an external agent's write boundary

An implementation brief MUST require `--dir` to be a worktree of the same repository other than the current checkout. A helper brief MUST require the same when the catalog entry offers no read-only sandbox. A directory is a separate worktree of the same repository when its top level differs from the current checkout's and its git common directory is the same.

#### Scenario: Implementation in the session's own checkout is refused
- **WHEN** an implementation brief names the current checkout as `--dir`
- **THEN** it is refused, saying the write guard does not reach an external process and naming how to create a worktree

#### Scenario: A helper with no sandbox needs a worktree
- **WHEN** a helper brief for `dsh`, which offers no sandbox, names the current checkout
- **THEN** it is refused for the same reason

#### Scenario: A separate worktree is accepted
- **WHEN** an implementation brief names a separate worktree of the same repository and the guard matches
- **THEN** the brief is written and the printed command runs the agent in that worktree
