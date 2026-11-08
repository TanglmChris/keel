## ADDED Requirements

### Requirement: A declared tag grant lets a session push the tags it names

`keel/config.yaml` MUST accept `push-tag:<tag glob>[@<role>]` in `authorize:`. The Claude write guard MUST allow a `git push` of an explicit tag (`refs/tags/<name>`, `<src>:refs/tags/<name>` or `tag <name>`) when a `push-tag:` entry matches this session's role and the tag name, and MUST otherwise deny it naming `push-tag:` or the role whose grant matches. Bulk tag pushes and tag deletion keep their verdicts, and `keel --doctor` MUST list the grant.

#### Scenario: A granted role pushes a granted tag
- **WHEN** `push-tag:cbb-parked-*@kaiwu-pm-cbb` is declared and a session bound to that role runs `git push origin refs/tags/cbb-parked-1101-design`, then `git push origin tag cbb-parked-1101-design`, then `git push origin HEAD:refs/tags/cbb-parked-1101-verify`
- **THEN** each is allowed without an ask

#### Scenario: Another role or another tag is denied by name
- **WHEN** a session of a different role runs the first push, and the granted role pushes `refs/tags/other-1`
- **THEN** both are denied, the first naming role `kaiwu-pm-cbb`, the second naming `push-tag:`

#### Scenario: Tags outside an explicit refspec keep their verdicts
- **WHEN** `push-tag:` and `push:claude/*` are declared and a session runs `git push --tags origin`, `git push --follow-tags origin claude/x`, `git push origin --delete refs/tags/cbb-parked-1101-design` and `git push origin :refs/tags/cbb-parked-1101-design`
- **THEN** each is denied as before, none by the tag grant

#### Scenario: Tags beside a branch are judged each by its own rule
- **WHEN** `push:claude/*` and `push-tag:v*` are declared and a session pushes `claude/x` and `refs/tags/v1` in one command, then `main` and `refs/tags/v1`
- **THEN** the first is allowed and the second is denied for `main`

#### Scenario: A repository declaring only tag grants limits only tags
- **WHEN** only `push-tag:v*` is declared and a session pushes `git push origin feature-1`, then `git push origin refs/tags/v1`, then `git push origin refs/tags/w1`
- **THEN** the first two are allowed and the third is denied naming `push-tag:`
