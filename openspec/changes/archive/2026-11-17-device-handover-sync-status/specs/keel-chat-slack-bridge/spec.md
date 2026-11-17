## MODIFIED Requirements

### Requirement: The chat store is archived to an orphan branch without exposing it publicly

`keel chat archive sync` MUST commit the synced layer of the store (records, cursors, members, presence, and the hand-over notes written once under `shift-notes/`) to `refs/heads/keel-chat` using git plumbing, without touching the worktree or the index, merging a fetched remote branch by union of paths. It MUST push only when `archive.remote` is declared, `archive_public: accept` is declared, or the repository is known to be private; otherwise it MUST commit locally and report the refused push naming those options. `keel chat archive pull` MUST import records missing locally. Archive MUST default on for Slack-enabled projects, and the running bridge MUST sync periodically.

#### Scenario: Archive leaves the worktree alone
- **WHEN** `keel chat archive sync` runs in a repository with a dirty worktree
- **THEN** `refs/heads/keel-chat` contains the group's record files, and `git status --porcelain` is unchanged

#### Scenario: A public repository is not pushed
- **WHEN** visibility is reported public and neither `archive.remote` nor `archive_public` is declared
- **THEN** the local branch is updated, no push runs, and the output names `archive_public` and `archive.remote`

#### Scenario: A second machine restores history
- **WHEN** a clone fetches `keel-chat` and runs `keel chat archive pull`
- **THEN** `keel chat soc --peek` shows the archived messages

#### Scenario: A hand-over note reaches a second machine
- **WHEN** `shift-notes/pm/20261116T080000Z-mac-1a2b3c4d.md` is in the store and `keel chat archive sync` pushes, and a second clone runs `keel chat archive pull`
- **THEN** the second clone's store holds that file byte for byte, and no `shift/<role>.md` was archived
