## ADDED Requirements

### Requirement: A redirection is never read as a push target

When the Claude write guard reads `git push` arguments from a `Bash` command, it MUST drop each shell redirection — `>`, `>>`, `<`, a file-descriptor prefix such as `2>`, a duplication such as `2>&1` or `>&2`, and `&>` — together with its target, and MUST NOT read any of them as a refspec or a remote.

#### Scenario: An in-scope push with redirections passes
- **WHEN** `push:flow-*` is declared and a `Bash` call runs `git push --dry-run origin HEAD:refs/heads/flow-probe 2>&1 | tail -1`, or the same with `2>/dev/null`, or `&> out.log`
- **THEN** the guard allows each

#### Scenario: An out-of-scope push with redirections is still refused
- **WHEN** the same declaration holds and a `Bash` call runs `git push origin HEAD:main 2>&1 | tail -1`
- **THEN** the guard denies it naming `main`, not a redirection
