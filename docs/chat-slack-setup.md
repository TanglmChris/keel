# Keel chat over Slack: setup

`keel chat` is a work group for the sessions in a repository: a Claude Code session, a Codex session, an unattended runner, and you. Without Slack it is complete on one machine. Slack adds two things: sessions on **other machines**, and **you on your phone**.

[中文版](chat-slack-setup.zh-CN.md)

## How it fits together

- **The repository's store is the source of truth.** Agents only ever run `keel chat`, and they never talk to Slack.
- **Each machine runs one bridge process** with **its own Slack app**:
  - it serves every project on that machine you list for it;
  - it posts only that machine's messages, under each role's name;
  - it brings everything else in.
- **Each machine needs its own app** because Slack delivers each event to just one connection of an app, so two machines sharing an app would each miss part of the traffic. The free plan allows 10 apps, which means 10 machines.
- **Mentions decide who gets woken.** Only a message that `@`-mentions a session, assigns it a todo, or is in its direct group wakes it. `@all` and ordinary messages wait for its next prompt.
- **A message is data, never permission.** That holds for your own messages too, because anyone could type your name. You still authorize work in the session itself.

## What you do once per machine

These steps create credentials and change your login items, so you run them yourself. Keel never does.

### 1. Create the Slack app from a manifest

Go to <https://api.slack.com/apps> → **Create New App** → **From a manifest**. Pick your workspace and paste the manifest below. Give each machine's app a different name, for example `Keel (mac-home)`.

```yaml
display_information:
  name: Keel (mac-home)
features:
  bot_user:
    display_name: keel-mac-home
    always_online: true
oauth_config:
  scopes:
    bot:
      - chat:write
      - chat:write.customize
      - channels:history
      - groups:history
      - reactions:read
      - reactions:write
settings:
  event_subscriptions:
    bot_events:
      - message.channels
      - message.groups
      - reaction_added
    metadata_subscriptions:
      - app_id: "*"
        event_type: keel_chat_record
  socket_mode_enabled: true
  org_deploy_enabled: false
  token_rotation_enabled: false
```

Then:

- **Install App** → **Install to Workspace**. This gives the **bot token** (`xoxb-…`).
- **Basic Information** → **App-Level Tokens** → **Generate Token and Scopes**, with scope `connections:write`. This gives the **app-level token** (`xapp-…`).

### 2. Put the tokens in the Keychain

Each command prompts for the token, so it never lands in your shell history:

```bash
security add-generic-password -s keel-chat-slack -a app -w
```

```bash
security add-generic-password -s keel-chat-slack -a bot -w
```

To replace a token later, add `-U`. Instead of the Keychain you can set `KEEL_SLACK_APP_TOKEN` and `KEEL_SLACK_BOT_TOKEN`. Tokens never belong in a repository.

### 3. Install the bridge as a login item

```bash
keel chat bridge install
```

This writes `~/Library/LaunchAgents/dev.keel.chat-bridge.plist`. The bridge then starts at login, restarts if it stops, reconnects after sleep, catches up on what it missed, and restarts itself after a Keel upgrade. You can see it under **System Settings → General → Login Items**. The bridge needs Node 22 or newer; the rest of `keel chat` does not.

## What you do once per project

### 4. Make the Slack channels

1. Create one channel per group, for example `#keel-soc`.
2. Invite each machine's bot into it: `/invite @keel-mac-home`.
3. Copy the channel ID from the channel's details. It starts with `C`.

Find your own Slack member ID under your profile → **⋮** → **Copy member ID**.

### 5. Commit `keel/chat.json`

```json
{
  "slack": {
    "enabled": true,
    "owner": "U012OWNER",
    "members": { "U012OWNER": "owner" },
    "channels": { "soc": "C034CHANNEL" },
    "icons": { "claude-maint": ":robot_face:", "codex-maint": ":gear:" }
  }
}
```

The fields:

- **`members`** maps the Slack users who may reach your agents to roles. **Anyone not listed is ignored**, which is what keeps strangers in the channel from instructing a session.
- **`channels`** maps groups to channels.
- **`owner`** gets a real Slack mention, so your phone notifies, whenever an agent writes `@owner`.

These are identifiers, not secrets, but in a public repository they are public.

### 6. Bind roles and make groups

In each worktree:

```bash
keel chat role --set claude-maint --alias cm
```

Then create the group once:

```bash
keel chat group create soc --member claude-maint --member codex-maint
```

From a terminal you post as yourself with `KEEL_CHAT_ROLE=owner keel chat soc "…"`.

### 7. List the project for this machine's bridge

```bash
keel chat bridge add
```

Run it in each project on each machine. To check:

```bash
keel chat bridge status
```

A session starting in this project is also told when the bridge is not running.

## Daily use

**In Slack:**

- Write in the channel. `@claude-maint`, `@cm`, or `@all` work as typed; there is no autocomplete.
- Reply in a thread to answer a message.
- React ✅ to close a todo.
- Edits and deletions carry over.

**In a terminal:**

| Command | What it does |
|---|---|
| `keel chat soc` | Read the group. |
| `keel chat soc --follow` | Keep printing new messages. |
| `keel chat soc --since 2h` | Show only the last two hours. |
| `keel chat todos --mine` | List the open todos assigned to you. |
| `keel chat search <text>` | Search every group. |
| `keel chat todo soc --assignee codex-maint --issue 42 "…"` | Assign a todo, linked to issue 42. |

There is also a Markdown transcript per group, regenerated after each message, at `<git common dir>/keel-chat/transcripts/<group>.md`.

## History beyond Slack's 90 days

Slack's free plan shows 90 days and deletes messages after a year. For a Slack-enabled project, the bridge archives the chat every ten minutes to the repository's own orphan branch `keel-chat`. That branch never touches `main`, your worktree, or your index. You can also run it by hand:

```bash
keel chat archive sync
```

On a new machine, restore the history with:

```bash
keel chat archive pull
```

**A public repository is never pushed by default.** The archive is still committed locally, and the output names the two ways to allow a push:

- `"archive": { "remote": "<a private remote>" }`
- `"archive_public": "accept"`

`"archive": "off"` turns automatic archiving off.

**CI:** if your workflows run on every pushed branch, exclude this one, for example `branches-ignore: [keel-chat]`. Otherwise each archive push starts a build.

## Pausing, stopping, removing

| Command | What it does |
|---|---|
| `keel chat bridge pause 2h` | Hold sending and receiving for two hours. |
| `keel chat bridge resume` | End a pause early. |
| `keel chat bridge stop` | Stop until `start` or your next login. |
| `keel chat bridge start` | Start a stopped bridge. |
| `keel chat bridge remove` | Stop serving this project on this machine. |
| `keel chat bridge uninstall` | Remove the login item. |
| `security delete-generic-password -s keel-chat-slack -a app` | Delete the app-level token; repeat with `-a bot` for the bot token. |

Nothing is lost while the bridge is down. Local messages wait and are sent later. Slack messages are caught up when it returns, as long as Slack still keeps them.

## When something looks wrong

- **`keel chat bridge status`** tells you whether the bridge is installed, running, connected, or paused, and how many messages wait to be sent.
- **Ignored senders** are people who wrote in the channel but are not in `slack.members`.
- **The log** is `~/.keel/chat/bridge/bridge.log`.
- **A missing token** is named on start, with both places to put it.
- **"Node 22"** means the bridge's Node lacks a built-in WebSocket. Install a newer Node, then run `keel chat bridge install` again so the login item uses it.
