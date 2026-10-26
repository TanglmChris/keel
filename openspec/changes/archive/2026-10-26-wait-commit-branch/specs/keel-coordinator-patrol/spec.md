## ADDED Requirements

### Requirement: A commit wait names the branch it waits for

`keel chat wait <group> --commit <sha> --branch <name>` MUST record the condition `commit <sha> on <remote>/<name>`, and the patrol MUST hold it only when `refs/remotes/<remote>/<name>` contains the commit. When `keel/config.yaml` declares `branches:` with at least one `trunk:`, a commit wait without `--branch` MUST be recorded against the remote's default branch and each declared trunk, as `commit <sha> on <remote>/<a> or <remote>/<b>`, and MUST hold when any of them contains the commit. Otherwise a commit wait without `--branch` MUST keep the condition `commit <sha> on <remote>`, and `keel chat wait`, `keel chat waits`, and the patrol's met notice MUST render it as on any branch of that remote.

#### Scenario: A wait for main is not met by a feature branch
- **WHEN** `verify` runs `keel chat wait soc --commit <sha> --branch main` while `<sha>` is pushed only to `origin/feature`, `rtl` runs `keel patrol`, and then `<sha>` is pushed to `origin/main` and `rtl` runs `keel patrol` again
- **THEN** the first patrol leaves the wait open and sends nothing, and the second marks it met and sends `verify` one message naming `origin/main`

#### Scenario: Declared trunks are the default, and an undeclared wait says any branch
- **WHEN** `branches:` declares `trunk:` `integ`, `verify` waits with `--commit <sha>` and no `--branch`, `<sha>` is pushed only to `origin/feature` and then to `origin/integ`, with `rtl` patrolling after each push; and separately, in a repository declaring no `branches:`, `verify` waits with `--commit <sha>`
- **THEN** the first wait's echo names `origin/main or origin/integ`, the first patrol leaves it open and the second marks it met; and the second wait's echo and `keel chat waits` say `any branch of origin`
