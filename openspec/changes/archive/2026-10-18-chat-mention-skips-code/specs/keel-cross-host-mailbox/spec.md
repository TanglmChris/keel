## MODIFIED Requirements

### Requirement: Groups have maintained membership, direct groups, and archive

`keel chat group create <g> [--member <r>]...`, `group add <g> <r>`, `group remove <g> <r>`, `group archive <g>`, and `group list` MUST maintain groups through `join`, `leave`, and `archive` records. Only members and the role `owner` MAY post to a group; a mention of a role that is neither a member nor an alias MUST be refused by name. Text inside inline code or a fenced block MUST NOT be read for mentions, and an `@` token of 7 to 40 hex digits that names no member or alias MUST be left as text, since it is a commit id rather than a typo. `@all` MUST be stored as `all` and address every member at posting time. `keel chat dm <role> <text>` MUST post to the direct group `dm-<a>--<b>` of the two sorted roles, creating it on first use. An archived group MUST refuse posts and MUST NOT appear in notices or default lists, and no command MAY delete a record.

#### Scenario: A removed member can no longer post
- **WHEN** `rtl` removes `verify` from `soc` and `verify` then posts to `soc`
- **THEN** the post fails naming the group membership, and `keel chat group list --json` shows `soc` without `verify`

#### Scenario: A mention outside the group is refused
- **WHEN** a member of `soc` posts `@stranger hi` and `stranger` is not a member
- **THEN** the post fails naming `stranger` and no record is written

#### Scenario: An archived group is read-only
- **WHEN** `soc` is archived and a member posts to it
- **THEN** the post fails naming the archive, and `keel chat soc --peek` still prints its history

#### Scenario: A commit id or quoted text is not a mention
- **WHEN** a member of `soc` posts `claude/x @638059e4 waiting`, or a message quoting `` `@verifyy` `` in inline code or `@nobody` in a fenced block
- **THEN** the post is written with no mentions
- **AND THEN** a bare `@verifyy` is still refused naming it, and `` `@nobody` `` beside `@verify` records only `verify`
