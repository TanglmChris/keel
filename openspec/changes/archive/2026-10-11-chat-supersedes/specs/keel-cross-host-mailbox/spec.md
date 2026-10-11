## ADDED Requirements

### Requirement: A record can supersede an earlier one, and unread shows only the current version, newest first

`keel chat post <group> <text> --supersedes <id>` MUST post a record carrying `supersedes: <id>` and MUST refuse, naming why, a target that is not in the same group, is not a message or todo by the same author, is retracted, or is already superseded, naming in the last case the record that superseded it. The superseded record MUST be kept. A group view MUST mark a superseded record `(superseded by <id>)` and its successor `(supersedes <id>)`. A record that a later record in its group supersedes MUST NOT be unread for anyone, so it MUST NOT appear in `keel chat unread` or the wake notice and MUST NOT wake a session. `keel chat unread` and the wake notice MUST list records newest first.

#### Scenario: A rule change supersedes the old rule
- **WHEN** `pm` posts "verify owns integration" in `team`, then posts "design owns integration" with `--supersedes` naming the first
- **THEN** `verify`'s `keel chat unread` lists only the second, and `keel chat team` shows the first marked `(superseded by <id>)` and the second `(supersedes <id>)`

#### Scenario: Superseding is refused when it would not be the author's current version
- **WHEN** `verify` tries to supersede `pm`'s record, or `pm` tries to supersede the first record again, or a retracted record, or a record in another group
- **THEN** each is refused naming why, the second naming the record that already superseded it

#### Scenario: Unread lists newest first
- **WHEN** `pm` posts three messages mentioning `verify` in turn
- **THEN** `verify`'s `keel chat unread` and its wake notice list them from the last posted to the first
