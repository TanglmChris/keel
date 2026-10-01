## Context

Issue #187 records a design the owner froze on 2026-10-01; after that, only bugs and optimizations change it. This document turns that design into decisions that can be checked. Owner choices are cited as "owner, 2026-10-01". Facts that come from documentation or probes carry their basis. The 5.83 mailbox (`src/core/mail.js`, change `2026-10-01-cross-host-mailbox`) is the starting point. Its F1–F3, which describe Claude Code hook behavior, still hold and are not repeated here.

## Goals / Non-Goals

**Goals:**
- A group chat store that tolerates sync: no shared file is ever rewritten.
- A host-neutral CLI that any agent with a shell can use.
- Mention-only wake on Claude, with a host-neutral notice.
- A per-machine Slack bridge that makes the chat real-time across machines and on the phone.
- A git archive that outlives Slack's retention.

**Non-Goals:**
- Codex receiving hooks (#183).
- Auto-launching an offline session.
- A local web page.
- GitHub Discussions as a carrier.
- A menu-bar app.
- Treating any message as authorization.
- A gate that reads the chat.

## Decisions

### Facts

- **F1** — Socket Mode delivers each event to one connection. Socket Mode allows up to 10 connections per app, and with several open "each payload may be sent to *any* of the connections". Two machines sharing one app would therefore each miss part of the traffic, so one app per machine is required. Basis: docs.slack.dev, "Using Socket Mode", read 2026-10-01. This answers #187's first item to verify.
- **F2** — Internal apps keep the higher history limits. The 2025-05-29 limit of 1 request per minute and 15 objects on `conversations.history` and `conversations.replies` applies to commercially distributed non-Marketplace apps. "Internal customer-built applications are not impacted"; they keep 50+ requests per minute with up to 1,000 objects. Catch-up can therefore page history directly. Basis: docs.slack.dev changelog 2025-05-29, read 2026-10-01. This answers #187's second item to verify.
- **F3** — Metadata can always be recovered. Message metadata is readable through `conversations.history` with `include_all_metadata=true`, and through `message_metadata_posted` events subscribed per `app_id` (or `*`) in the app manifest. A bot message whose event lacks metadata can therefore be resolved with one history call for its `ts`. Basis: docs.slack.dev, "Message metadata", read 2026-10-01.
- **F4** — The bridge needs Node 22. A global `WebSocket` exists only from Node 22, and `fetch` from Node 18. Keel's engine floor is `>=20.19.0`. Basis: `package.json` and Node release notes.
- **F5** — `keel/config.yaml` stays flat. Its reader is deliberately line-oriented and flat, with no YAML dependency (`src/core/config.js`, comment at `configList`). Basis: repository source.
- **F6** — CI runs on every pushed branch. This repository's `Full gate` workflow runs on `push` to `"**"`. A pushed `keel-chat` branch would therefore trigger CI in any project with the same trigger. Basis: `.github/workflows/`.

### Store and records

- **D1** — Store root and its two layers. The store is `<git common dir>/keel-chat/`, shared by every worktree of a repository. It has a synced layer and a local layer.
  - **Synced layer:** written by many, never rewritten.
    - `groups/<group>/log/<id>.md` holds the records.
    - `cursors/<role>/<group>` is written only by `<role>`.
    - `members/<role>.json` holds aliases, written only by `<role>`.
    - `presence/<role>.json` is written only by `<role>`.
  - **Local layer:** never archived or synced.
    - `roles.json` maps worktree paths to roles.
    - `signal/<role>` is the file a host watches.
    - `transcripts/<group>.md` is derived.
    - `bridge/` holds this machine's Slack mapping.
    - `.tmp/` is used for write-then-rename.
  
  Basis: owner, 2026-10-01 ("no shared file is ever rewritten").
- **D2** — One record per file, with frontmatter. A record's id is `<local stamp yyyymmddThhmmss±hhmm>-<role>-<6 hex>`, which is unique and sorts by time. Its frontmatter carries:
  - always: `id`, `group`, `kind`, `from`, and `created`;
  - optionally: `mentions` (a list of roles, or `all`), `reply_to`, `assignee`, `issue`, `target`, `refs`, `origin` (`local`, `slack`, or `remote:<project>`), and `slack` (channel and ts);
  - a body.
  
  `created` is ISO 8601 with the local offset, for example `2026-10-01T14:32:10+08:00`. The kinds are:

  | Kind | Records |
  |---|---|
  | `message` | a chat message |
  | `todo` | a todo |
  | `done` | a todo closed; `target` names the todo |
  | `join` | a member added |
  | `leave` | a member removed |
  | `archive` | the group archived |
  | `edit` | a message's new text; `target` names the message |
  | `retract` | a message withdrawn; `target` names it |
  | `system` | a post made by Keel itself |
  
  State such as membership, open todos, or current text is always derived by replaying the log. Basis: owner, 2026-10-01.
- **D3** — Names, aliases, and direct groups.
  - Group and role names follow `^[a-z0-9][a-z0-9-]{0,31}$`. A group may not be named after a `keel chat` subcommand.
  - A direct group is `dm-<a>--<b>` with the two roles sorted. It is created on the first `keel chat dm`, and its two members are fixed.
  - Aliases follow the same pattern, are case-insensitive on input, and are unique across roles and aliases within the project.
  - Cross-project senders appear as `<project>/<role>`, where `<project>` is the repository directory name. A mention may use that form, and a bare `@role` resolves within the local project first.
  
  Basis: owner, 2026-10-01.
- **D4** — Membership.
  - Posting to a group requires the poster to be a member. The role `owner` may always post and read.
  - A mention of a role that is neither a member nor an alias is refused by name.
  - `@all` expands to the members when the message is posted, and is stored as `all`.
  - An archived group refuses new posts and drops out of notices and default lists. Nothing is ever hard-deleted.
  
  Basis: owner, 2026-10-01.
- **D5** — Cursors and receipts.
  - A cursor stores the last id its member has read in a group.
  - Unread messages are the records after the cursor that are not the member's own and are of kind `message`, `todo`, or `system`.
  - `keel chat <group>`, when viewing, and `keel chat read [<group>]` advance the reader's cursor to the last record shown.
  - Read receipts for a message are the members whose cursor is at or past it.
  - `--peek` views without advancing.
  
  Basis: replaces read-is-receipt, owner, 2026-10-01.
- **D6** — Todos.
  - A todo is a `todo` record with an `assignee` and an optional `issue: #N`.
  - It closes with `keel chat done <id>`, which writes a `done` record, or with a reply whose body begins with `done` or `✅`.
  - `keel chat todos [<group>] [--mine]` lists the open ones.
  - Durable work still goes in GitHub issues, per the project convention.
  
  Basis: owner, 2026-10-01 ("lightweight, can link an issue").
- **D7** — Migration and the alias.
  - **Trigger:** the first `keel chat` or `keel mail` command in a repository whose `keel-mailbox/` exists.
  - **What moves:** every `<role>/{new,done}/*.md` becomes a `message` record in `dm-<from>--<to>`.
  - **Unread state:** messages from `new/` stay unread for the recipient, and messages from `done/` are read.
  - **Bindings:** `roles.json` carries over.
  - **Old directory:** renamed to `keel-mailbox.migrated-<stamp>`, never deleted.
  - **The `keel mail` alias:**
    - `keel mail send --to <role>` posts to the direct group.
    - `list` shows unread direct messages.
    - `read [--id]` prints them and advances the cursor.
    - `role` binds as before.
    - `hook` relays to the chat hook.
    - `KEEL_MAIL_ROLE` and `KEEL_CHAT_ROLE` both override the role.
  
  Basis: owner, 2026-10-01.
- **D8** — Time. Records store the local offset. Every display converts to the viewer's local time (`YYYY-MM-DD HH:MM`, with a day separator in transcripts). Agent notices add a relative age (`3h ago`). Basis: owner, 2026-10-01.

### Notices, wake, presence, guards

- **D9** — Waking and notices.
  - **Signals:** the signal file `signal/<role>` gets an append only for a record that mentions the role by name or alias, a `todo` assigned to it, or any message in its direct group. `@all` and plain messages append nothing.
  - **What a notice says:** it lists at most 5 waking records (id, group, sender, relative age, first line), then "and N more". It counts other unread messages per group. It names `keel chat read`, and it states that messages are data from other agents, not user instructions, and grant no authorization.
  - **Where it appears:**
    - `keel chat notice` prints the notice and always exits 0.
    - `keel chat hook session-start|user-prompt-submit|file-changed|session-end` wraps it for Claude. FileChanged exits 2 only when a waking record is unread.
  
  Basis: owner, 2026-10-01 ("only @me wakes"; "at most 5").
- **D10** — Presence.
  - Every hook event and every `keel chat` command writes `presence/<role>.json` with `last_active`, `host`, and `state`.
  - A SessionEnd hook writes `state: offline`.
  - Views show each member as `online` (state online, active within 24 hours), `idle <age>`, or `offline <age>`.
  - A message mentioning an offline member is stored and marked `queued: <role> offline` in the sender's output.
  - Nothing launches a session.
  
  Basis: owner, 2026-10-01 ("queue only").
- **D11** — Loop guards.
  - **Rate limit:** a role other than `owner` may post at most 20 records per 10 minutes across the project. Beyond that, posting fails by name.
  - **Ping-pong breaker:** if the last 8 `message` records in a group alternate between the same two non-owner roles with no other sender, the next agent post there is refused. Keel then writes one `system` record that mentions `owner`. The block clears when anyone else posts.
  - Both thresholds can be overridden in `keel/chat.json` (`limits`).
  
  Basis: owner, 2026-10-01.
- **D12** — Messages grant nothing. No gate, context status, or write guard reads the chat. A message, including one from `owner`, grants no authorization. Basis: unchanged from the 5.83 `Unread mail gates nothing` requirement.

### Configuration

- **D13** — Chat settings go in `keel/chat.json`. Per-project chat settings live in a committed `keel/chat.json`, not in `keel/config.yaml`, because the YAML reader is flat on purpose (F5) and the chat needs nested maps. This deviates from the wording in #187. The fields are:
  - `slack.enabled`
  - `slack.owner` (the owner's Slack user id)
  - `slack.members` (Slack user id → role)
  - `slack.channels` (group → channel id)
  - `slack.icons` (role → emoji or URL; optional)
  - `archive` (`auto`, `off`, or `{ "remote": <name> }`)
  - `archive_public` (`accept`, to allow pushing to a public repository)
  - `limits`
  
  An absent file means chat without Slack or archive. A file Keel cannot parse turns Slack and archive off and names the error; local chat keeps working. Basis: F5; owner accepted `keel/chat.json` over #187's wording, 2026-10-01.

### Slack bridge

- **D14** — Topology.
  - Each machine has one Slack app and one bridge process (F1).
  - The bridge serves every project listed in `~/.keel/chat/projects.json`, which holds paths only. `keel chat bridge add|remove [repo]` edits it.
  - A project is served only when `keel/chat.json` has `slack.enabled: true`.
  - The machine label is `KEEL_CHAT_MACHINE` or the short hostname.
  - `KEEL_HOME` relocates `~/.keel` for tests.
  
  Basis: owner, 2026-10-01.
- **D15** — Outbound.
  - **What gets posted:** for each served project, a record that originated locally (`origin: local`), is in a mapped group, and is not yet in `bridge/posted/` is posted with `chat.postMessage`.
  - **How a post looks:**
    - The `username` is the role (cross-project: `<project>/<role>`), with `icon_emoji` or `icon_url` from `slack.icons`.
    - `metadata` carries `event_type: keel_chat_record` and a payload with `project`, `id`, `kind`, `from`, `mentions`, `reply_to`, `assignee`, `issue`, and `target`.
    - A reply goes into the thread of its root's ts.
    - A mention of `owner` adds `<@slack.owner>`.
  - **Redaction:** the text has secrets redacted:
    - Slack tokens, `ghp_` and `github_pat_`, `sk-` keys, AWS access keys, and PEM private-key blocks;
    - `password|token|secret` = value pairs.
  - **Long messages:** text over 3,000 characters is truncated with "full text: `keel chat show <id>`".
  - **Records that are not messages:**
    - `done` adds a ✅ reaction to the todo.
    - `edit` calls `chat.update`, and `retract` calls `chat.delete`.
    - Membership and archive records post as short system lines.
  - **Mapping and retries:** the ts is written to `bridge/posted/<id>`. HTTP 429 honors `Retry-After`, and other failures back off from 1 s to 5 min. The queue is durable because it is derived from the records not yet posted.
  
  Basis: owner, 2026-10-01; F3.
- **D16** — Inbound. The bridge receives over Socket Mode and acknowledges each envelope.
  - **Rebuilding records from other machines:** a channel message whose metadata carries `keel_chat_record` for this project or another is written as that record (`origin: slack`), unless a record with that id already exists. Metadata is resolved by one history call when the event lacks it (F3).
  - **Echoes:** this machine's own posts for the same project are recognized by id and skipped. A post for another project served by this bridge is imported into the projects that map that channel.
  - **People:** a plain user message is imported only when the user is in `slack.members`. Its `@token`s are resolved to roles or aliases, and Slack `<@U…>` mentions are resolved through `slack.members`. Anyone else is ignored and counted in `status`.
  - **Threads:** a thread reply becomes `reply_to` the mapped root. A reply to a root with no mapping is imported with the quoted line "↳ reply to <ts>".
  - **Changes and reactions:**
    - `message_changed` becomes `edit`, and `message_deleted` becomes `retract`.
    - ✅ from a registered user on a todo becomes `done`.
    - Files become link lines and are not downloaded.
  - **Catch-up:** on connect, each mapped channel is paged with `conversations.history` and `conversations.replies` from the last seen ts (F2).
  
  Basis: owner, 2026-10-01.
- **D17** — Tokens. The bridge reads `xapp-` and `xoxb-` tokens from `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`, or from the macOS Keychain (generic password, service `keel-chat-slack`, accounts `app` and `bot`, via `security`). It never writes them, logs them, or puts them in a record or status. `KEEL_SLACK_API_BASE` points the client at a test server. Basis: owner, 2026-10-01; a security constraint.
- **D18** — Lifecycle.
  - **`install`:** writes `~/Library/LaunchAgents/dev.keel.chat-bridge.plist` (`RunAtLoad`, `KeepAlive`, the absolute node and `bin/keel.js` paths, logs under `~/.keel/chat/bridge/`) and bootstraps it with `launchctl`.
  - **Other commands:**
    - `uninstall` boots it out and removes the plist.
    - `stop` and `start` boot it out and bootstrap it.
    - `pause <dur>` writes `paused_until` to `~/.keel/chat/bridge/control.json`. The running bridge disconnects until then and keeps queuing.
    - `status` reports installed, running, connected, paused, projects, the last event, ignored senders, and the queue depth.
    - `run` is the foreground process that launchd starts.
  - **While running:**
    - The bridge writes `status.json`.
    - It posts "<machine> bridge online/stopped" to mapped channels on start and clean stop.
    - It reconnects on refresh, disconnect, or wake with backoff.
    - It exits for a launchd restart when Keel's `package.json` version changes.
  - **Session-start notice:** for a Slack-enabled project, the notice includes one bridge status line.
  - **Test seams:** `KEEL_CHAT_LAUNCHCTL`, `KEEL_CHAT_SECURITY`, and `KEEL_CHAT_LAUNCH_AGENTS_DIR` stand in for the system boundary in tests.
  - **Node version:** a Node without `WebSocket` gets a message naming Node 22.
  
  The owner runs `install` and `start`, because they change system configuration. Basis: owner, 2026-10-01.

### Archive and human surfaces

- **D19** — Git archive.
  - **Committing:** `keel chat archive sync` writes the synced layer (D1) to `refs/heads/keel-chat` with plumbing (`hash-object`, a temporary `GIT_INDEX_FILE`, `write-tree`, `commit-tree`, and `update-ref`). The worktree and index are untouched.
  - **Merging:** it fetches the remote branch first and merges by union of file paths. The same path with different content is reported, and the local copy kept. The commit's parents are the local tip and the fetched tip.
  - **Pushing:** it pushes only when one of these holds:
    - `archive.remote` names a remote;
    - `archive_public: accept` is set;
    - visibility is known to be private (`gh repo view --json visibility`).
    
    Unknown or public visibility refuses the push, names those three options, and still commits locally.
  - **When it runs:** default `auto` when `slack.enabled`. The bridge runs `sync` every 10 minutes while connected.
  - **Restoring:** `keel chat archive pull` imports missing records from the branch.
  - The setup guide warns about CI triggered by pushed branches (F6).
  
  Basis: owner, 2026-10-01 ("keep everything", "public repo refused unless accepted").
- **D20** — Human surfaces.
  - `keel chat <group>` prints the conversation in local time with presence and receipts. `--since <duration|date>` sets the window, `--follow` streams new records, and `--peek` does not advance the cursor.
  - `keel chat <group> "<text>"` posts. `keel chat show <id>` prints one record. `keel chat search <text>` searches all groups.
  - `transcripts/<group>.md` is regenerated after every write to that group. It has day separators and lines of the form `HH:MM sender: text`, marked for mentions, replies, and todos.
  - Every command supports `--json`.
  - `--repo <path>` selects the repository. `keel mail` keeps its positional `[repo]`.
  
  Basis: owner, 2026-10-01.

## Hidden Knowledge / Assumptions

- **A1** — The thresholds in D10 and D11 (24 h, 20 per 10 min, 8 alternations) are starting values, configurable and tuned in use. This is reversible.
- **A2** — Slack Socket Mode and Web API behavior beyond F1–F3 (exact event shapes for `message_changed`, `reaction_added`, and `refresh_requested`) follows the public docs. The fake server in tests mirrors those shapes, and the owner's first real run is the host evidence (task 4.3 Review).

## Risks / Trade-offs

- **Scope:** this is the largest change Keel has taken. Each task group leaves a usable state (local chat works before Slack), and the tasks are ordered so that stopping early is safe.
- **Fake versus real Slack:** a fake server proves Keel's contract, not Slack's behavior. A2 is closed by a real run, recorded in Review, not by a gate.
- **Committed Slack IDs:** `keel/chat.json` commits Slack user and channel ids. They are identifiers, not secrets. In a public repository they are visible, which the guide states.
- **Hook cost:** UserPromptSubmit now replays group logs to count unread messages. The hook reads only records after each cursor, using sorted file names, so the cost grows with unread messages, not with history.

## Open Questions

None. D13 departed from #187's `keel/config.yaml` wording; the owner accepted it on 2026-10-01.
