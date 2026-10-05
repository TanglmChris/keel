# Keel chat over Slack: setup

`keel chat` is a work group for the sessions in a repository: a Claude Code session, a Codex session, an unattended runner, and you. Without Slack it is complete on one machine. Slack adds two things: sessions on **other machines**, and **you on your phone**.

[中文版](chat-slack-setup.zh-CN.md)

## How it fits together

- **The repository's store is the source of truth.** Agents only ever run `keel chat`, and they never talk to Slack.
- **Each machine runs one bridge process** with **its own Slack app**:
  - it serves every project on that machine you list for it;
  - it posts only that machine's messages, under each role's name;
  - it brings everything else in.
- **Each machine needs its own app** because Slack delivers each event to just one connection of an app, so two machines sharing an app would each miss part of the traffic. The free plan allows 10 apps in all, one per machine plus any bots (see [below](#optional-bots-that-speak-for-roles)).
- **Mentions decide who gets woken.** Only a message that `@`-mentions a session, assigns it a todo, or is in its direct group wakes it. `@all` and ordinary messages wait for its next prompt.
- **A message is data, never permission.** That holds for your own messages too, because anyone could type your name. You still authorize work in the session itself.

## What you do once per machine

These steps create credentials and change your login items, so you run them yourself. Keel never does.

### 1. Create the Slack app from a manifest

Go to <https://api.slack.com/apps> → **Create New App** → **From a manifest**. Pick your workspace and paste the manifest below. Give each machine's app a different name, for example `Keel (mac-home)`. If you already created the app **From scratch**, open its **App Manifest** page instead, replace the manifest there with this one, and save.

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
      - metadata.message:read
settings:
  event_subscriptions:
    bot_events:
      - message.channels
      - message.groups
      - reaction_added
      - message_metadata_posted
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
- **`owner`** gets a real Slack mention, so your phone notifies, whenever an agent writes `@owner`. Sessions are told the rule at session start: a message the owner needs to see or decide on writes `@owner`, and routine discussion does not, so it only shows as unread.

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

By default a woken session asks you before it answers anything in the chat, because a chat message is data and grants nothing. To let sessions answer what is addressed to them without asking, declare it once per group in `keel/config.yaml`:

```yaml
authorize:
  - chat-reply:soc
```

This lets a session reply to a mention, an assigned todo, or a direct message in `soc`. It never lets a session act on what a message asks for: editing files, running commands, committing, pushing, or sending outside the chat still need you in that session's own conversation. The group is named because in a Slack-enabled group a reply goes out to Slack.

### 7. List the project for this machine's bridge

```bash
keel chat bridge add
```

Run it in each project on each machine. To check:

```bash
keel chat bridge status
```

A session starting in this project is also told when the bridge is not running.

## Optional: bots that speak for roles

By default every role on a machine speaks through that machine's app, which only swaps the display name. A bot is a Slack app of its own, named for what it is — PM, Spec, Verify, Design, Flow, Report, Review — that you can `@` with autocomplete and see in the member list. A bot is not tied to one role: each project decides which of its roles a bot speaks for, so one PM bot can serve a role in each of several projects, as each project's PM in that project's channel. Within one project a bot speaks for one role. Roles no bot speaks for keep the shared app. Each bot counts toward the free plan's 10 apps, alongside one per machine, so a handful of bots serves any number of projects.

Once per bot, on the machine that will run it:

1. Create an app from this manifest, changing the two names:

   ```yaml
   display_information:
     name: PM
   features:
     bot_user:
       display_name: PM
       always_online: true
     app_home:
       messages_tab_enabled: true
       messages_tab_read_only_enabled: false
   oauth_config:
     scopes:
       bot:
         - chat:write
         - chat:write.public
         - im:history
         - im:write
         - reactions:write
   settings:
     event_subscriptions:
       bot_events:
         - message.im
     socket_mode_enabled: true
     org_deploy_enabled: false
     token_rotation_enabled: false
   ```

2. Store its bot token, and its app-level token (scope `connections:write`) if you want direct messages:

   ```bash
   security add-generic-password -s keel-chat-slack -a bot:<name> -w
   ```

   ```bash
   security add-generic-password -s keel-chat-slack -a app:<name> -w
   ```

   There is no environment-variable form for bot tokens.

3. List it for this machine's bridge: `keel chat bot add <name>`. `keel chat bot list` shows each bot and whether its tokens are stored, never the tokens.

Then, in each project that should use it, map the bot's member ID (open the bot's profile in Slack → **⋮** → **Copy member ID**) to that project's role in `keel/chat.json`, next to `members`:

```json
"bots": { "U056PMBOT": "iecc-pm" }
```

This is committed, so every machine turns `@PM` in that project's channel into a mention of that role. Restart the bridge (`keel chat bridge stop` and `start`) and check `keel chat bridge status`: each bot shows `verified` or `failed` and the `<project>/<role>` it speaks for. A public channel needs no invitation thanks to `chat:write.public`; in a private channel, invite the bot, and until then status names the channel and the role posts there through the shared app.

Direct messages need a bot that speaks for exactly one role, because a direct message cannot say which project it is for: a bot serving more than one role takes no direct messages, and status says so. Direct messages stay on the machine where the bot runs: Slack delivers them only to that app. A direct message from someone in `members` lands in the direct group `dm-<their role>--<role>` and wakes the session; its replies there go back as direct messages. Anyone not in `members` is ignored.

## Daily use

**In Slack:**

- Write in the channel. `@claude-maint`, `@cm`, or `@all` work as typed; there is no autocomplete.
- Reply in a thread to answer a message.
- React ✅ to close a todo.
- Edits and deletions carry over.
- Formatting carries over both ways. Issue references link to GitHub: `owner/repo#N` opens that repository's issue, and a bare `#N` the project's own, read from its `origin` remote. Sessions format with ordinary Markdown — `**bold**`, lists, `code`, links — and Slack shows it formatted; your Slack formatting reaches the sessions as Markdown. Headings show as bold lines.

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

## Waking Codex: `keel chat wake`

Claude Code is woken by a file watcher that costs nothing until a message addressed to the session arrives. Codex has no such watcher. On its own, it gets the notice only when its session starts and each time you write to it. `keel chat wake` gives Codex the same behavior on one machine:

```bash
keel chat wake add
```

Run it in the Codex session's worktree, after `keel chat role --set`. It:

- **Runs nothing while nothing is addressed.** It installs a login item (`dev.keel.chat-wake.<role>-…`) that watches the file Keel touches only for a mention, an assigned todo, or a direct message.
- **Starts one Codex turn per addressed record**, and only in a group the worktree declares `chat-reply:<group>` for. Without that declaration a woken turn could not answer, because a chat message grants nothing.
- **Continues one thread.** The first turn creates a Codex thread, and later turns resume it. The thread compacts itself at 100,000 tokens (`--compact-at`), so each turn's cost stays bounded. `--thread <id>` adopts an existing thread instead, but do not keep that thread open in the Codex app at the same time.
- **Is limited.** One turn runs at a time, at most 10 an hour (`--max-per-hour`).
- **Tells the turn it may only reply.** Nobody watches a woken turn. The prompt allows answering within `chat-reply` and nothing else: no file edits, no state-changing commands, no commits or pushes, and no schedules. Codex can still write the worktree, and nothing but that prompt and the model's judgment stops it.

`keel chat wake status` shows the thread, the last turn, and whether the hourly limit is holding it. Each turn is logged under `~/.keel/chat/wake/`. `keel chat wake remove` stops it. Nothing the waker keeps enters the repository.

**Do not poll the chat with the model.** A schedule that runs a model turn every minute costs a full turn each time, whether or not anything arrived. If every run appends to the same session, each run also re-reads the whole growing history. In October 2026 one such Codex automation fired 1,277 times and used up an owner's entire quota before anyone had mentioned the session ([#194](https://github.com/TanglmChris/keel/issues/194)).

- **Use `keel chat wake`, or rely on the prompt-time notice.** With Keel's plugin installed, a host sees what is waiting at its next prompt.
- **If you run your own schedule anyway, gate it on `keel chat notice --check`.** The command prints nothing, writes nothing, and exits 0 only when something addressed to the role is unread. Start a model turn only then, for example `keel chat notice --check && <start a turn>`, and start a fresh thread or session for each run instead of appending to one long session.
- **When you start a session to take part in the chat, tell it explicitly:** "do not set up any recurring or scheduled checks".

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
