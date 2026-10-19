## MODIFIED Requirements

### Requirement: A resumed note's commits are checked against the remote

`keel shift resume` MUST, after printing a note, list each commit id and `<branch> @ <sha>` the note names — a commit id being 7 to 40 hex digits after `@`, or elsewhere holding at least one letter and one digit or resolving to a commit — and mark each against the remote-tracking refs as `already in origin/<default>`, `branch moved: now <sha>`, `branch gone`, or `not found`. It MUST NOT fetch, and MUST say it did not and when the refs were last fetched. A note that names no commit MUST print no list.

#### Scenario: A stale note's commits are marked
- **WHEN** a note names a commit already on `origin/<default>`, `feat @ <old>` after `feat` moved to `<new>`, `gone-branch @ <sha>` for a branch the remote lacks, `deadbee1`, and the date `20261018`, and the role runs `keel shift resume`
- **THEN** the output marks them `already in origin/<default>`, `branch moved: now <new>`, `branch gone` and `not found`, lists nothing for the date, and says the refs were not fetched

#### Scenario: An all-digit sha is still a commit
- **WHEN** a note names `digits-branch @ <sha>` and the bare `<sha>`, where the sha's first eight characters are all digits and `digits-branch` points at it
- **THEN** the pair is marked current and the bare sha is listed
