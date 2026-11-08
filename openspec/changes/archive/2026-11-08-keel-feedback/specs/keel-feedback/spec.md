## ADDED Requirements

### Requirement: keel feedback drafts a fixed-structure issue and creates nothing by default

`keel feedback "<summary>"` MUST print a draft issue for the Keel repository with a title and the sections 现象, 期望, 复现, 证据, 影响 and 环境, where 环境 carries the Keel version, Node version, platform, host and the `keel context` status. `--command`, `--output-file`, `--expected`, `--repro` and `--impact` MUST fill their sections. Without `--create` it MUST create nothing and MUST save the draft to a file it names.

#### Scenario: A draft carries the version, the command and its output
- **WHEN** `keel feedback "gate refuses a valid task" --command "keel gate task-start" --output-file out.txt` runs in a project that is not Keel
- **THEN** the draft holds the running Keel version, the command, the file's text and the six sections, names the file it saved, exits 0, and `gh` was asked for no `issue create`

### Requirement: Everything shown is redacted first

Free text, command output and collected facts MUST be redacted before they are printed or saved: tokens, keys, `key=value` secrets, credentials in URLs, Slack IDs and e-mail addresses are replaced, the home directory prints as `~` and the project root as `<project>`. The draft MUST report how many values were redacted and MUST NOT print one. Keel MUST NOT collect a project name, a remote, a role or chat text.

#### Scenario: Secrets in the output do not reach the draft
- **WHEN** the output file holds a GitHub token, a Slack bot token, a Slack user ID, a `Bearer` header, `API_KEY=hunter2`, an e-mail address, a URL with a password and a path under the home directory
- **THEN** none of those values appears in the printed draft or the saved file, the draft reports a redaction count, and the path prints with `~`

### Requirement: Near-duplicates are listed before anything is created

`keel feedback` MUST search the Keel repository with `gh` for near-duplicates and list up to five before offering to create. It MUST NOT comment on, edit, label or close any issue; for supplementing one it MUST print the `gh issue comment` command for the user to run.

#### Scenario: A similar issue is listed and nothing is commented
- **WHEN** the stub `gh` answers the search with issue 12
- **THEN** the draft lists `#12`, its title and URL, prints a `gh issue comment 12` command, and the `gh` log holds no `issue comment`

### Requirement: Creating needs a declaration or a confirmation

`keel feedback --create` MUST run `gh issue create` against the Keel repository, with no label, assignee or milestone, only when the project's `authorize:` declares `issue:TanglmChris/keel` or the caller passes `--confirmed`; otherwise it MUST exit 3, print the draft and run nothing. It MUST print the new issue's URL.

#### Scenario: Refused, confirmed, and authorized
- **WHEN** `--create` runs with neither the declaration nor `--confirmed`, then with `--confirmed`, then in a project declaring `issue:TanglmChris/keel`
- **THEN** the first exits 3 and the `gh` log holds no `issue create`; the second and third each log one `issue create --repo TanglmChris/keel` with `--title` and `--body-file` and no `--label`, and print the URL

### Requirement: A missing or unusable gh loses nothing

When `gh` is missing, not logged in or fails, `keel feedback` MUST still print the draft, save it, print the commands that would create it, and say the duplicate search was not run; `--create` MUST then exit 4.

#### Scenario: No gh on PATH, and a gh that is not logged in
- **WHEN** `keel feedback` runs with no `gh` on PATH, then with `--create --confirmed`, then with a stub `gh` that exits 1
- **THEN** each prints the draft and names its saved file, the first exits 0 and says the search was not run, the others exit 4 and print a `gh issue create` command

### Requirement: The feedback command orders the steps and asks before creating

The command file `plugins/keel/commands/feedback.md` MUST tell the session to run `keel feedback`, show the user the draft and any duplicates, ask whether to create a new issue, leave the supplement to the user, or cancel, and run `--create` only on the first answer, adding `--confirmed` unless the repository declares the authorization.

#### Scenario: The command file names the steps
- **WHEN** `plugins/keel/commands/feedback.md` is read
- **THEN** it names `keel feedback`, the three answers, `--create` and `--confirmed`, and says to create no label and to comment on nothing
