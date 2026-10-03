## MODIFIED Requirements

### Requirement: Cursors give every member their own unread state and receipts

Each member MUST have one cursor per group recording the last record it read. Unread records MUST be the `message`, `todo`, and `system` records after the cursor that the member did not post. Viewing a group with `keel chat <g>`, or `keel chat read [<g>]`, MUST advance the reader's cursor to the last record shown; `--peek` MUST NOT. A post that replies to a record MUST advance the poster's cursor in that group to the replied-to record, and `keel chat done <id>` MUST advance the closer's cursor to the todo; neither MUST move a cursor back. A record's read receipts MUST be the members whose cursor is at or past it.

#### Scenario: Two readers do not take each other's messages
- **WHEN** `rtl` posts to `soc`, whose members include `verify` and `lint`, and `verify` views `soc`
- **THEN** `keel chat unread --json` for `lint` still reports the message, and for `verify` reports none
- **AND THEN** `keel chat show <id> --json` lists `verify` among the readers and not `lint`

#### Scenario: Answering a record marks it read
- **WHEN** `rtl` posts two records to `soc` mentioning `verify`, and `verify` replies to the first with `keel chat post soc <text> --reply-to <first id>`
- **THEN** `keel chat unread --json` for `verify` reports the second record and not the first
- **AND THEN** `keel chat show <first id> --json` lists `verify` among the readers
- **AND THEN** after `verify` closes a later todo assigned to it with `keel chat done <id>`, its unread records no longer include that todo
