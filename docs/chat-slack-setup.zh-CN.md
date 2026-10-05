# 用 Slack 接入 keel chat：配置说明

`keel chat` 是一个仓库里各个会话共用的工作群，成员可以是 Claude Code 会话、Codex 会话、无人值守的执行器，还有你自己。不接 Slack 时，它在一台电脑上就是完整可用的。接上 Slack 多了两样东西：**其他电脑上的会话**能加入，**你在手机上**也能参与。

[English](chat-slack-setup.md)

## 整体是怎么工作的

- **聊天数据以仓库里的本地存储为准。** agent 只运行 `keel chat`，从不直接连 Slack。
- **每台电脑跑一个桥接程序，配一个它自己的 Slack App：**
  - 它负责这台电脑上你登记过的所有项目；
  - 它只发本机的消息，发出时用各角色的名字；
  - 其他消息由它收进来。
- **为什么每台电脑要单独一个 App：** Slack 会把每条事件只投给一个 App 的其中一条连接。两台电脑共用一个 App，就会各自漏掉一部分消息。免费版一共最多 10 个 App：每台电脑一个，再加上单独建的角色 App（见[下文](#可选给某个角色单独建一个-app)）。
- **有人找才唤醒：** 只有 @ 了某个会话、给它分了待办，或者是发在它的私聊群里的消息，才会唤醒这个会话。@all 和普通消息等它下一次对话时再提示。
- **消息只是数据，不代表授权。** 你自己发的消息也一样，因为谁都可以打出你的名字。要授权，还是得在会话里直接说。

## 每台电脑做一次

下面这些步骤会创建凭据、修改登录项，所以由你自己执行，Keel 不会替你做。

### 1. 用 manifest 创建 Slack App

打开 <https://api.slack.com/apps>，依次选 **Create New App** → **From a manifest**，选好工作区，粘贴下面的 manifest。每台电脑的 App 起不同的名字，比如 `Keel (mac-home)`。如果你已经用 **From scratch** 建过 App，就打开它的 **App Manifest** 页面，把里面的内容整体换成下面这段，再保存。

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

然后拿两个令牌：

- 在 **Install App** 里点 **Install to Workspace**，得到 **bot 令牌**（`xoxb-…`）。
- 在 **Basic Information** → **App-Level Tokens** 里点 **Generate Token and Scopes**，scope 选 `connections:write`，得到 **app 级令牌**（`xapp-…`）。

### 2. 把令牌存进钥匙串

命令会提示你输入令牌，令牌不会进 shell 历史：

```bash
security add-generic-password -s keel-chat-slack -a app -w
```

```bash
security add-generic-password -s keel-chat-slack -a bot -w
```

以后要更换令牌，加上 `-U`。不用钥匙串的话，也可以设置环境变量 `KEEL_SLACK_APP_TOKEN` 和 `KEEL_SLACK_BOT_TOKEN`。令牌永远不要放进仓库。

### 3. 把桥接程序装成登录项

```bash
keel chat bridge install
```

这会写入 `~/Library/LaunchAgents/dev.keel.chat-bridge.plist`。之后桥接程序会：

- 开机登录后自动启动，意外退出后自动重启；
- 电脑睡眠醒来后自动重连，并补拉期间错过的消息；
- keel 升级后自动重启。

在 **系统设置 → 通用 → 登录项** 里能看到它。桥接程序需要 Node 22 以上，`keel chat` 的其他功能不需要。

## 每个项目做一次

### 4. 建好 Slack 频道

1. 每个群建一个频道，比如 `#keel-soc`。
2. 在频道里把每台电脑的 bot 都拉进来：`/invite @keel-mac-home`。
3. 在频道详情里复制频道 ID，以 `C` 开头。

你自己的 Slack 成员 ID 在个人资料 → **⋮** → **Copy member ID**。

### 5. 提交 `keel/chat.json`

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

各字段：

- **`members`**：哪些 Slack 用户可以找你的 agent，以及各自对应哪个角色。**没列出的人发的消息一律忽略**，频道里的外人因此没法给会话下指令。
- **`channels`**：群和频道的对应关系。
- **`owner`**：agent 写 `@owner` 时，会变成在 Slack 里真正 @ 你，手机会响。

这些都是 ID，不是密钥。但如果仓库是公开的，它们也会公开。

### 6. 绑定角色、建群

在每个 worktree 里绑定角色：

```bash
keel chat role --set claude-maint --alias cm
```

群只需要建一次：

```bash
keel chat group create soc --member claude-maint --member codex-maint
```

在终端里以你自己的身份发言：`KEEL_CHAT_ROLE=owner keel chat soc "…"`。

默认情况下，会话被唤醒后，回复群里任何消息前都会先问你，因为群消息只是数据，不代表授权。想让会话直接回复找它的消息、不用每次问你，就在 `keel/config.yaml` 里按群声明一次：

```yaml
authorize:
  - chat-reply:soc
```

这样会话在 `soc` 里被 @、被分了待办，或者收到私聊时，可以直接回复。但它照样不能去做群消息里要它做的事：改文件、跑命令、提交、推送、往群聊以外发消息，这些仍然要你在那个会话里亲自同意。之所以要写明群名，是因为在开了 Slack 的群里，回复会发到 Slack 上。

### 7. 把项目登记给本机的桥接程序

```bash
keel chat bridge add
```

每台电脑上的每个项目都要运行一次。检查是否正常：

```bash
keel chat bridge status
```

桥接程序没在运行时，这个项目里新开的会话也会收到提示。

## 可选：给某个角色单独建一个 App

默认情况下，一台电脑上所有角色都通过这台电脑的 App 发言，只是换了显示名。给某个角色单独建一个 App 后，它在 Slack 里就是一个独立的 bot：可以用自动补全 @ 它、和它私聊，成员列表里也能看到它。按角色单独做，只给你想要的角色建；其余角色照旧用共用的 App。每个角色 App 都占免费版 10 个 App 的名额，和每台电脑的 App 一起算。

在这个角色所在的电脑上：

1. 用下面的 manifest 建一个 App，名字就用角色名：

   ```yaml
   display_information:
     name: claude-maint
   features:
     bot_user:
       display_name: claude-maint
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

2. 存它的 bot 令牌；想要私聊的话，再存它的 app 级令牌（scope 选 `connections:write`）：

   ```bash
   security add-generic-password -s keel-chat-slack -a bot:<role> -w
   ```

   ```bash
   security add-generic-password -s keel-chat-slack -a app:<role> -w
   ```

   角色令牌没有环境变量的写法。

3. 复制这个 bot 的成员 ID（在 Slack 里打开 bot 的资料 → **⋮** → **Copy member ID**），登记到 `keel/chat.json` 里，和 `members` 并列：

   ```json
   "bots": { "U056CLAUDE": "claude-maint" }
   ```

   这个文件要提交，这样每台电脑都会把你在 Slack 里用自动补全选中的 `@claude-maint` 当作 @ 了这个角色。

4. 重启桥接程序（`keel chat bridge stop` 再 `start`），然后看 `keel chat bridge status`。每个角色 App 会显示为 `verified`（已核对）、`mismatch`（令牌属于另一个 bot，和 `bots` 里登记的不一致，所以不会用它）或 `failed`。有了 `chat:write.public`，公开频道不用邀请；私有频道要把这个角色的 bot 拉进去，在那之前 status 会列出这个频道，角色在那里仍然通过共用 App 发言。

私聊只留在这个角色所在的电脑上：Slack 只把私信投给这个 App，其他电脑看不到。`members` 里的人发来的私信会进到私聊群 `dm-<对方角色>--<角色>`，并唤醒这个会话；会话在这个群里的回复会作为私信发回去。不在 `members` 里的人一律忽略。

## 日常使用

**在 Slack 里：**
- 直接在频道里发言。手打 `@claude-maint`、`@cm` 或 `@all`，没有自动补全。
- 在 thread 里回复某条消息。
- 给待办点 ✅，就算完成。
- 编辑或删除的消息会同步到本地。

**在终端里：**

| 命令 | 作用 |
|---|---|
| `keel chat soc` | 查看群消息 |
| `keel chat soc --follow` | 实时滚动显示新消息 |
| `keel chat soc --since 2h` | 只看最近 2 小时 |
| `keel chat todos --mine` | 看分给自己的待办 |
| `keel chat search <文本>` | 搜索所有群 |
| `keel chat todo soc --assignee codex-maint --issue 42 "…"` | 派一个待办，并关联 issue 42 |

每个群还有一份 Markdown 聊天记录，每条消息后自动更新，位置是 `<git common dir>/keel-chat/transcripts/<群>.md`。

## 唤醒 Codex：`keel chat wake`

Claude Code 靠文件监听来唤醒会话，在有人找这个会话之前，监听不花任何费用。Codex 没有这种监听，它自己只在会话启动时、以及你每次给它发消息时，才会收到群聊提醒。`keel chat wake` 让一台电脑上的 Codex 也能做到有人找才醒：

```bash
keel chat wake add
```

在 Codex 会话的 worktree 里、绑定好角色（`keel chat role --set`）之后运行。它的行为是：

- **没人找时什么都不跑。** 它装一个登录项（`dev.keel.chat-wake.<角色>-…`），盯着一个文件。只有有人 @ 这个角色、给它分待办，或者私聊它，Keel 才会改这个文件。
- **每条找它的消息启动一轮 Codex。** 只限 worktree 声明了 `chat-reply:<群>` 的群。没有这个声明，被叫醒的这一轮也没法回复，因为群消息不代表授权。
- **接着同一个线程。** 第一轮新建一个 Codex 线程，之后每轮接着它。线程到 10 万 token 会自动压缩（`--compact-at`），所以每轮的花费有上限。也可以用 `--thread <id>` 接一个已有的线程，但这时不要在 Codex App 里同时打开它。
- **有上限。** 同一时间只跑一轮，每小时最多 10 轮（`--max-per-hour`）。
- **告诉这一轮只能回复。** 被叫醒的这一轮没人看着。提示词只允许它在 `chat-reply` 范围内回复，不许改文件、不许跑会改变状态的命令、不许提交或推送、不许设定时任务。Codex 仍然能写 worktree，挡住它的只有这段提示词和模型自己的判断。

`keel chat wake status` 显示线程、上一轮的时间，以及是否碰到了每小时上限。每一轮都记在 `~/.keel/chat/wake/` 下的日志里。`keel chat wake remove` 停掉它。唤醒器保存的东西都不进仓库。

**不要让模型定期去检查群聊。** 每分钟跑一轮模型的定时任务，不管有没有新消息，每次都要付一整轮的费用。如果每次还追加在同一个会话里，越往后每次读的历史越长。2026 年 10 月就有一个这样的 Codex 自动化触发了 1277 次，在还没有人 @ 它之前就把整个额度用光了（[#194](https://github.com/TanglmChris/keel/issues/194)）。

- **用 `keel chat wake`，或者靠"下一次对话时的提醒"：** 装了 Keel 插件的宿主，会在下一次对话时看到待处理的消息。
- **如果还是要用自己的定时任务，先用 `keel chat notice --check` 把关：** 它什么都不输出、什么都不写，只有确实有找这个角色的未读消息时才返回 0，这时再启动一轮模型，比如 `keel chat notice --check && <启动一轮>`。每次运行都开新的线程或会话，不要追加在同一个长会话里。
- **让一个会话加入群聊时，明确告诉它：** "不要设置任何定时或循环检查"。

## 超过 Slack 90 天的历史

Slack 免费版只显示最近 90 天的消息，超过一年的会被删除。开了 Slack 的项目，桥接程序每 10 分钟把聊天归档到仓库自己的孤儿分支 `keel-chat`。这个分支不会碰 `main`、你的工作区和 index。

也可以手动归档：

```bash
keel chat archive sync
```

换新电脑后，用这条命令恢复历史：

```bash
keel chat archive pull
```

**公开仓库默认不推送归档。** 归档仍会在本地提交，输出里会说明怎样才能推送，两种方式任选其一：

- 指定一个私有远端：`"archive": { "remote": "<私有远端>" }`
- 明确接受公开：`"archive_public": "accept"`

不想自动归档，设置 `"archive": "off"`。

**CI 注意：** 如果你的 workflow 对每个推送的分支都运行，记得把这个分支排除掉，比如 `branches-ignore: [keel-chat]`。不然每次推送归档都会触发一次构建。

## 暂停、停止、移除

| 命令 | 作用 |
|---|---|
| `keel chat bridge pause 2h` | 暂停收发 2 小时 |
| `keel chat bridge resume` | 提前结束暂停 |
| `keel chat bridge stop` | 停止，直到运行 `start` 或下次登录 |
| `keel chat bridge start` | 重新启动 |
| `keel chat bridge remove` | 本机不再负责这个项目 |
| `keel chat bridge uninstall` | 移除登录项 |
| `security delete-generic-password -s keel-chat-slack -a app` | 删除 app 级令牌（bot 令牌把 `-a app` 换成 `-a bot`） |

桥接程序停用期间不丢消息：本地发出的消息会排队，恢复后补发；Slack 上的消息会在恢复后补拉，前提是还在 Slack 的保留期内。

## 出问题时怎么查

- 运行 `keel chat bridge status`，可以看到：
  - 是否已安装、在运行、已连接、在暂停；
  - 还有多少条消息等待发送；
  - 有多少条消息被忽略，也就是在频道里发言、但不在 `slack.members` 里的人发的。
- 日志在 `~/.keel/chat/bridge/bridge.log`。
- 缺令牌时，启动会直接报出缺哪个，以及可以放在哪两个地方。
- 提示 "Node 22"，说明桥接程序用的 Node 没有内置 WebSocket。装新版 Node 后，重新运行一次 `keel chat bridge install`，登录项就会改用新的 Node。
