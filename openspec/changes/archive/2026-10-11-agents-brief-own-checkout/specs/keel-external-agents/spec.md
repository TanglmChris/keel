## MODIFIED Requirements

### Requirement: The checkout is an external agent's write boundary

An implementation brief MUST require `--dir` to be a worktree of the same repository other than the current checkout. A helper brief MUST require the same when the catalog entry offers no read-only sandbox. The current checkout is the one `--repo` names, or else the one containing the current directory. A directory is a separate worktree of the same repository when its top level differs from the current checkout's and its git common directory is the same, wherever it lies, including under the repository's `.claude/worktrees/`. A refusal because `--dir` is the current checkout MUST name that checkout and whether it came from `--repo` or the current directory, and MUST say to run from the session's own checkout or pass `--repo`.

#### Scenario: Implementation in the session's own checkout is refused
- **WHEN** an implementation brief names the current checkout as `--dir`
- **THEN** it is refused, saying the write guard does not reach an external process and naming how to create a worktree

#### Scenario: A helper with no sandbox needs a worktree
- **WHEN** a helper brief for `dsh`, which offers no sandbox, names the current checkout
- **THEN** it is refused for the same reason

#### Scenario: A separate worktree is accepted
- **WHEN** an implementation brief names a separate worktree of the same repository and the guard matches
- **THEN** the brief is written and the printed command runs the agent in that worktree

#### Scenario: A helper worktree beside the session's worktree is accepted
- **WHEN** a session in `<repo>/.claude/worktrees/review` asks for a `dsh` helper brief with `--dir <repo>/.claude/worktrees/dsh_review`
- **THEN** the brief is written

#### Scenario: The refusal names the checkout it compared against
- **WHEN** the same brief is asked for from inside `<repo>/.claude/worktrees/dsh_review`
- **THEN** it is refused, naming that worktree as the checkout the command runs in, saying it came from the current directory, and naming `--repo`
