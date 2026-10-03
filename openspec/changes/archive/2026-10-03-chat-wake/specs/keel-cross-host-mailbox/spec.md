## RENAMED Requirements

- FROM: `### Requirement: Presence is visible and offline members are never launched`
- TO: `### Requirement: Presence is visible and only an owner-installed waker launches a member`

## MODIFIED Requirements

### Requirement: Presence is visible and only an owner-installed waker launches a member

Every chat hook event and `keel chat` command MUST write the member's `presence/<role>.json` with its last activity; the SessionEnd hook MUST mark it offline. Views MUST show each member as online, idle with age, or offline with age. Posting a mention of an offline member MUST store the record and report the member as offline in the poster's output. Keel MUST NOT start any session except through a waker the owner installed for that role on that machine with `keel chat wake add`.

#### Scenario: A mention of an offline member is queued
- **WHEN** `verify`'s SessionEnd hook has run and `rtl` posts `@verify ping`
- **THEN** the record is stored and the post output names `verify` as offline

## ADDED Requirements

### Requirement: An owner-installed waker starts one turn per addressed record

`keel chat wake add`, run in a worktree with a bound role, MUST register that worktree and role in the machine-local `~/.keel/chat/wake.json` (under `KEEL_HOME` when set) and install a LaunchAgent that watches the role's signal file and runs `keel chat wake run --once --worktree <path>`; `keel chat wake remove` MUST unload and delete it; `keel chat wake status` MUST report each registration with its thread, last turn, and whether the per-hour limit holds it. No registration, thread id, or log MUST be written inside a repository. `keel chat wake run --once` MUST start a host turn only for unread records that wake the role, lie in a group the worktree declares `chat-reply:<group>` for, and are newer than the newest record an earlier turn was given; it MUST run at most one turn at a time per role, MUST NOT start more turns in an hour than the registration's limit (default 10), and MUST start another turn after one ends only for records that arrived meanwhile. For the Codex host, the first turn MUST run `codex exec --json` and record the thread id from its `thread.started` event, and later turns MUST run `codex exec resume <thread>`; every turn MUST run in the worktree with `model_auto_compact_token_limit` (default 100000), workspace-write sandboxing, and the git common directory as an extra writable root, and MUST be given a fixed prompt that permits only answering within the repository's chat-reply authorization and never carries record text.

#### Scenario: An addressed record starts one turn and creates the thread
- **WHEN** `cx` is registered with a waker, `keel/config.yaml` declares `chat-reply:lab`, and `owner` posts `@cx ping` to `lab`
- **THEN** `keel chat wake run --once` starts one `codex exec --json` turn in the worktree with the compaction limit and the git common directory as a writable root
- **AND THEN** `keel chat wake status --json` reports the thread id that turn's `thread.started` event named

#### Scenario: A later record resumes the same thread
- **WHEN** the registration has a thread and another `@cx` record arrives in `lab`
- **THEN** the next run starts `codex exec resume <thread>`

#### Scenario: Nothing addressed, nothing authorized, nothing new
- **WHEN** the only unread record is an `@all` message, or the mention is in a group without a `chat-reply` declaration, or every addressed record was already given to an earlier turn
- **THEN** `keel chat wake run --once` starts no turn

#### Scenario: The hourly limit holds further turns
- **WHEN** the registration's limit is 2 and two turns started in the last hour
- **THEN** a third addressed record starts no turn and `keel chat wake status --json` reports the registration as held

#### Scenario: The waker writes nothing into the repository
- **WHEN** `keel chat wake add` and several runs complete
- **THEN** `git status --porcelain` in the worktree reports nothing new, and the registration, thread id, and log exist under `KEEL_HOME`
