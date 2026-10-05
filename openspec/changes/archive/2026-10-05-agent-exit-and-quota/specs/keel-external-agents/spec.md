## MODIFIED Requirements

### Requirement: The external agent brief is the delegation brief, checked for egress

`keel agents brief <name> --mode helper|implementation --dir <path> --out <file>` MUST compile the same projection `keel project --event subagent-start` compiles for that mode and MUST apply every refusal it applies, including the matching-guard precondition for implementation. It MUST refuse when any Read or Touch path matches an `egress_deny` pattern, naming the path, the pattern, and the reason. On success it MUST write the brief, with the task, Read, Touch, checks, and prohibitions against commit, push, branch switch, issue changes, OpenSpec and Keel state, and writes outside `--dir`, to `--out`, MUST print the command line filled from the catalog template, run in a subshell whose exit status is written to a file beside the result and named in the output, and MUST state that Keel cannot observe what the agent reads beyond the brief. Keel MUST NOT launch the agent.

#### Scenario: A clean helper brief is written and its command printed
- **WHEN** a helper brief for an allowed `codex` names no denied path
- **THEN** the prompt file holds the task, Read, checks, and prohibitions
- **AND THEN** the printed command uses the read-only sandbox, `--dir`, and the prompt file, and no codex process was started

#### Scenario: The printed command records the exit status
- **WHEN** the printed command is run with a stub agent that exits with status 3
- **THEN** the exit file beside the result holds `3`
- **AND THEN** the calling shell's working directory is unchanged even when the template changes directory

#### Scenario: A denied path refuses the brief
- **WHEN** the task's Read names a path matching an `egress_deny` pattern
- **THEN** the brief is refused, naming that path, the pattern, and its reason
- **AND THEN** no prompt file is written

#### Scenario: Implementation still needs the matching guard
- **WHEN** an implementation brief is asked for with no active guard for the task
- **THEN** it is refused with the same reason `keel project --event subagent-start --subagent-mode implementation` gives
