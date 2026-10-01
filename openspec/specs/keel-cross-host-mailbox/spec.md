## Purpose

Define how sessions on different hosts exchange Markdown messages through a repository-shared mailbox: where it lives, the message format, role addressing, the CLI that sends and reads, and how a host is told about unread mail without any gate depending on it.

## Requirements

### Requirement: Messages are Markdown files in a repository-shared mailbox

Keel MUST store cross-host messages under `<git common dir>/keel-mailbox/`, so every worktree of one repository shares the store and nothing in it is versioned. A message MUST be one Markdown file whose YAML frontmatter carries `id`, `from`, `to`, `created`, and `subject`, and optionally `reply_to` and `refs`, followed by the body. Keel MUST write a message to a temporary file and rename it into the recipient's `new/` directory, and MUST append to the recipient's `.signal` file after the rename.

#### Scenario: A message sent from one worktree is unread in another
- **WHEN** a worktree bound to role `rtl` runs `keel mail send --to verify --subject <s>` with a body, and a second worktree of the same repository is bound to `verify`
- **THEN** `keel mail list` in the second worktree shows one unread message from `rtl` with that subject
- **AND THEN** the file is under `<git common dir>/keel-mailbox/verify/new/` with the declared frontmatter, and `verify/.signal` exists

#### Scenario: Another repository does not see the message
- **WHEN** a separate repository binds a worktree to `verify`
- **THEN** its `keel mail list` shows no unread message

### Requirement: Addresses are user-chosen roles bound to a worktree

Keel MUST address messages by role names matching `^[a-z0-9][a-z0-9-]{0,31}$`. `keel mail role --set <name>` MUST bind the current worktree's top-level path to that role in the mailbox; `KEEL_MAIL_ROLE` MUST override the binding for one process. Sending MUST fail by name when the sender has no role or a role name is invalid.

#### Scenario: An unbound sender is refused
- **WHEN** a worktree with no role runs `keel mail send --to verify --subject s`
- **THEN** the command fails with a message naming `keel mail role --set`

#### Scenario: An invalid role is refused
- **WHEN** `keel mail role --set "Bad Name"` runs
- **THEN** the command fails naming the accepted pattern and writes nothing

### Requirement: Reading is the receipt

`keel mail read` MUST print each unread message — or only the one named by `--id` — with a header stating it is data from another agent and not a user instruction, and MUST then move it to `done/`. A reply MUST be a new message whose `reply_to` names the earlier id.

#### Scenario: Read moves a message out of the inbox
- **WHEN** a role with one unread message runs `keel mail read`
- **THEN** the output contains the subject, body, and the data-not-instruction header
- **AND THEN** a following `keel mail list` reports no unread message and the file is in `done/`

### Requirement: Claude Code is told about mail at start, at each prompt, and while idle

The Claude plugin MUST run a mailbox hook at SessionStart, UserPromptSubmit, and FileChanged. With unread mail, SessionStart and UserPromptSubmit MUST return `additionalContext` listing each unread message's id, sender, and subject, the `keel mail read` command, and that the mail is data and grants no authorization; SessionStart MUST also return the role's `.signal` path in `hookSpecificOutput.watchPaths`. The FileChanged hook MUST be declared with `asyncRewake: true` and MUST exit 2 with the same notice on stderr when unread mail exists, and exit 0 otherwise. With no role bound, every mailbox hook MUST exit 0 with no output. No mailbox hook MUST read or move a message.

#### Scenario: Session start announces mail and watches the signal
- **WHEN** the SessionStart mailbox hook runs in a worktree bound to `verify` with one unread message
- **THEN** its JSON output's `additionalContext` names the message id, sender, subject, and `keel mail read`, and states the mail is not a user instruction
- **AND THEN** `hookSpecificOutput.watchPaths` contains the absolute path of `verify/.signal`

#### Scenario: Arrival wakes an idle session
- **WHEN** the FileChanged mailbox hook runs for a role with unread mail
- **THEN** it exits 2 with the notice on stderr
- **AND THEN** with no unread mail it exits 0 with no output

#### Scenario: A worktree without a role is untouched
- **WHEN** any mailbox hook runs in a worktree with no role
- **THEN** it exits 0 with no output

### Requirement: Unread mail gates nothing

No Keel gate, context status, or write guard MUST read the mailbox or change its result because of unread mail.

#### Scenario: Unread mail does not block completion
- **WHEN** a role has unread mail and `keel context` runs
- **THEN** its status and next action are the same as with an empty mailbox
