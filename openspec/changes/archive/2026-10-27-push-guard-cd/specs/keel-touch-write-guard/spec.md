## MODIFIED Requirements

### Requirement: A push outside the declared branches is refused

While `keel/config.yaml` declares at least one `push:<glob>` entry, the Claude write guard MUST examine every `Bash` call for `git push` invocations, whether or not a task manifest is active and whether or not the rest of the `authorize:` declaration is valid, and MUST deny the call when any push's target branch matches no declared glob, naming the branch and the globs. It MUST determine a target from an explicit refspec — the destination of `src:dst`, `src` alone, `HEAD` as the current branch, `:dst` as a delete — or, with no refspec, from the branch's configured push destination. When it cannot determine a target — `--all`, `--branches`, `--mirror`, `--tags`, an option it does not know, shell expansion in the push, a tag refspec, or no configured push destination — it MUST deny the call and name `git push origin <branch>` as the form to use. When a `cd` or `pushd` precedes the push in the same call, whatever its refspec, it MUST deny the call, say that the directory changes before the push, and name `git -C <directory> push` as the form to use. A `Bash` call with no `git push`, and any call while no `push:<glob>` is declared, MUST pass unchanged. Codex keeps its `manual` guard capability.

#### Scenario: A push to a declared branch passes
- **WHEN** `push:claude/*` is declared and a `Bash` call runs `git add -A && git push -u origin claude/fix`
- **THEN** the call proceeds

#### Scenario: A push to main is refused without a task
- **WHEN** `push:claude/*` is declared, no guard manifest exists, and a `Bash` call runs `git push origin HEAD:main`
- **THEN** the call is denied, naming `main` and `claude/*`

#### Scenario: A push with no refspec uses the branch's push destination
- **WHEN** `push:claude/*` is declared and `git push` runs on a branch whose push destination is `origin/main`
- **THEN** the call is denied naming `main`, and the same command on a branch pushing to `origin/claude/fix` proceeds

#### Scenario: An undetermined target is refused with the explicit form
- **WHEN** `push:claude/*` is declared and a `Bash` call runs `git push --all origin`, or `git push origin "$BRANCH"`
- **THEN** the call is denied and the reason names `git push origin <branch>`

#### Scenario: A directory change before a push is refused with the -C form
- **WHEN** `push:claude/*` and `push-protected:main@chief` are declared in the session's repository, and a `Bash` call runs `cd <other repository> && git push <url> main:main`, or `cd <subdirectory> && git push origin claude/fix`
- **THEN** each call is denied, the reason names `git -C <directory> push` and does not name the role `chief`, and `git -C <other repository> push <url> main:main`, whose repository declares nothing, proceeds

#### Scenario: Nothing is checked without a push scope
- **WHEN** `authorize:` declares a bare `push`, or no `push` at all, and a `Bash` call runs `git push origin HEAD:main`
- **THEN** the guard does not intercept it
