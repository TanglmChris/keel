## ADDED Requirements

### Requirement: A push to a protected branch is asked, not refused

When `keel/config.yaml` declares `push-protected:` entries, the Claude write guard MUST check `git push` as it does for `push:`, whether or not `push:` is declared. A target matching a `push:` glob MUST pass; otherwise a target matching a `push-protected:` glob MUST return `permissionDecision: "ask"` with a reason naming the branch, so the host asks the user to confirm that one call; any other target MUST be denied. Keel MUST NOT store an approval. When the matching entry names a role and the session is not bound to it, the push MUST be denied naming the role. When the event's `permission_mode` is `bypassPermissions` or `dontAsk`, a protected push MUST be denied naming the mode, because the host cannot be relied on to ask there.

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
