## ADDED Requirements

### Requirement: A scoped authorization may name the roles it applies to

Every scoped `authorize:` entry — `issue:`, `issue-close:`, `cleanup:`, `chat-reply:`, `push:<glob>` and `push-protected:` — MAY end in `@<pattern>`, where the pattern uses chat-role characters and `*`. Such an entry MUST apply only to a session whose chat role matches the pattern, and an entry without one MUST apply as before. What a session reads as authorized — the capsule's inherited autonomy, `keel context`, its chat-reply groups, and `keel --doctor`'s per-action lines — MUST leave out entries for other roles, except `push-protected`, which stays listed with its pattern because the guard refuses other roles by name. A session bound to no role MUST get no role-limited entry. The Claude write guard MUST keep the push check on while any push entry is declared for any role, and MUST allow a branch only through an entry that matches the session's role, refusing a branch that another role's entry covers by naming that pattern. `keel --doctor` MUST list, for each role bound in the repository, the scoped entries that apply to it. A malformed pattern MUST be refused like a malformed scope.

#### Scenario: Grants follow the role
- **WHEN** `authorize:` lists `push:design-*@rtl`, `push:review-*@ver*`, `issue:acme/widgets@rtl` and `chat-reply:soc@verify`, with `rtl` and `verify` bound
- **THEN** `keel --doctor` in rtl's worktree reports `issue` authorized and `chat-reply` not authorized, verify's reports the reverse, and both list the entries per role; the guard allows `git push origin design-x` from rtl and refuses it from verify naming `rtl`, allows `review-x` from verify, and refuses `design-x` from a session of role `spec`, which no entry names

#### Scenario: A malformed role pattern is refused
- **WHEN** `authorize:` lists `issue:acme/widgets@Not A Role`
- **THEN** `keel --doctor` exits non-zero naming the entry

## MODIFIED Requirements

### Requirement: A protected branch is pushed only with the user's approval of that push

`authorize:` MAY declare `push-protected:<branch glob>` or `push-protected:<branch glob>@<role pattern>`, more than once. The glob MUST use branch-name characters and `*`, and the role pattern MUST use chat-role characters and `*`; anything else MUST be refused as malformed, and a bare `push` beside it MUST be refused naming both. `keel --doctor` MUST report `push-protected` with its globs and roles and state that the Claude write guard asks the user for each push to them.

#### Scenario: A protected branch is reported
- **WHEN** `authorize:` lists `push:claude/*` and `push-protected:main@iecc-pm`
- **THEN** `keel --doctor` reports `push-protected` scoped to `main@iecc-pm` and that each push to it is asked

#### Scenario: A malformed protected entry is refused
- **WHEN** `authorize:` lists `push-protected:main@Not A Role`, or a bare `push` beside `push-protected:main`
- **THEN** `keel --doctor` exits non-zero naming the entry
