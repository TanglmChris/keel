## ADDED Requirements

### Requirement: A push that carries tags is a tag push

While `push:` or `push-protected:` entries are declared, the Claude write guard MUST treat a `git push` that carries annotated tags as a tag push. A push carries tags when the last of `--follow-tags` and `--no-follow-tags` in its arguments is `--follow-tags`, or, with neither, when `push.followTags` resolves to true for that command, counting the repository's config and every `git -c` the command passes. Such a push MUST NOT pass on a `push:` glob alone: when every target matches a `push-protected:` entry, it MUST take that entry's path — role limit, refusal in a mode that cannot ask, and `ask` — with a reason saying it also pushes annotated tags; otherwise it MUST be denied, naming the tag carriage and `--no-follow-tags`. A `git` command preceded by a `GIT_CONFIG*` environment assignment MUST be denied as a push whose target the guard cannot determine, naming the variable.

#### Scenario: A granted branch pushed with --follow-tags is refused
- **WHEN** `push:flow-*` is declared and a `Bash` call runs `git push --follow-tags origin flow-release`
- **THEN** the call is denied, and the reason names `--follow-tags` and `--no-follow-tags`

#### Scenario: Config that carries tags is refused the same way
- **WHEN** `push:flow-*` is declared and the repository sets `push.followTags=true`, and a `Bash` call runs `git push origin flow-release`, or `git -c push.followTags=true push origin flow-release` runs where it is unset
- **THEN** each call is denied, naming `push.followTags`

#### Scenario: Turning tag carriage off restores the branch push
- **WHEN** the same declaration holds and a call runs `git push --follow-tags --no-follow-tags origin flow-release`, or `git -c push.followTags=false push origin flow-release` where the repository sets it
- **THEN** the call proceeds

#### Scenario: The coordinator is asked about main with its tags
- **WHEN** `push:flow-*` and `push-protected:main@iecc-pm` are declared and the session bound to `iecc-pm` runs `git push --follow-tags origin main` in `default` mode
- **THEN** the guard returns `ask`, and the reason names `main` and annotated tags; the same push from a session bound to `rtl` is denied naming `iecc-pm`

#### Scenario: Environment config is not read past
- **WHEN** `push:flow-*` is declared and a call runs `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push origin flow-release`
- **THEN** the call is denied naming `GIT_CONFIG_COUNT`

## MODIFIED Requirements

### Requirement: A push to a protected branch is asked, not refused

When `keel/config.yaml` declares `push-protected:` entries, the Claude write guard MUST check `git push` as it does for `push:`, whether or not `push:` is declared. A target matching a `push:` glob MUST pass, unless the push carries tags (see "A push that carries tags is a tag push"); otherwise a target matching a `push-protected:` glob MUST return `permissionDecision: "ask"` with a reason naming the branch, so the host asks the user to confirm that one call; any other target MUST be denied. Keel MUST NOT store an approval. When the matching entry names a role and the session is not bound to it, the push MUST be denied naming the role. When the event's `permission_mode` is `bypassPermissions` or `dontAsk`, a protected push MUST be denied naming the mode, because the host cannot be relied on to ask there.

#### Scenario: The coordinator is asked, once per push
- **WHEN** `push-protected:main@iecc-pm` is declared, the session is bound to `iecc-pm` in `default` mode, and runs `git push origin HEAD:main` twice
- **THEN** the guard returns `ask` naming `main` both times, and writes nothing

#### Scenario: Another role is refused
- **WHEN** the same push runs in a session bound to `rtl`
- **THEN** the guard denies it naming `iecc-pm`

#### Scenario: A mode that cannot ask is refused
- **WHEN** the coordinator's push runs with `permission_mode` `bypassPermissions`
- **THEN** the guard denies it naming the mode

#### Scenario: Other branches are unchanged
- **WHEN** `push:claude/*` and `push-protected:main` are declared
- **THEN** a push to `claude/fix` passes and a push to `release` is denied
