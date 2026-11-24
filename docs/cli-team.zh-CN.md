# 用 Claude Code CLI 会话组成团队

`keel chat`、`keel shift`、`keel patrol` 的桌面端用法依赖 Claude 桌面应用：巡检由它的定时任务来跑，会话的唤醒和清空由它的会话工具来做。团队也可以不开桌面应用，把每个角色作为 Claude Code CLI 的后台会话（`claude --bg`）来跑（#369）。本页从头到尾讲这条路径，实测版本为 Claude Code 2.1.303。英文版：[cli-team.md](cli-team.md)。

## 各项由谁负责

| 需要 | 桌面应用 | CLI |
|---|---|---|
| 每个角色一个会话 | 在角色的 worktree 里开一个应用会话 | 在角色的 worktree 里运行 `claude --bg -n <角色>` |
| 唤醒空闲的会话 | @ 提及、指派的待办或私信 | 相同：聊天的文件钩子会唤醒空闲的后台会话 |
| 唤醒已结束的会话 | 对该会话 `send_message` | `keel chat wake now <角色>`，或由 `keel tick` 在每来一条新记录时做一次 |
| 按计划跑巡检 | 宿主定时任务（`host_task:`） | 由 launchd 调用的 `keel tick`（`runner: tick`） |
| 换班 | 会话清空自己，等待器唤醒新一班 | 等待器停掉旧会话、启动一个以开班时间命名的新会话；等待器不在时由 `keel tick` 做同样的事 |
| 打开上一班的对话 | 已归档的应用会话 | 对已停止的会话运行 `claude attach <id>` |

## 设置一个角色

1. 建好角色的 worktree，在里面以交互方式运行一次 `claude`，接受信任提示。信任按目录生效，不从已信任的上级目录继承：在没人信任过的目录里运行 `claude --bg` 会报 `Workspace not trusted`，之后在那里的每次启动也都会失败，包括换班时的那次。
2. 在后台启动会话：`claude --bg -n <角色>`。这个名字就是该会话在 `claude agents` 里的标题。
3. 在这个会话里绑定角色：`keel chat role --set <角色>`。此后它的在线状态会记下这个 CLI 会话的 id 和进程，Keel 正是靠这些来恢复或替换它。

每个角色只跑一个会话。如果同一个角色又绑上了第二个会话（例如对一个还在运行的会话执行了 `claude --resume`），两个会话会用同一个名字发言，共用一个已读游标，谁先读，谁就把记录从另一个那里藏起来了。只要有两个存活会话绑在同一个角色上，`keel context` 会给出警告，`keel chat post`、`dm`、`todo`、`unread`、`read` 也会在 stderr 上警告。遇到时停掉其中一个。

用 `keel chat show <todo-id> --json` 按原 todo ID 查询任务。
`task` 提供同一 ID、群聊中的 `state`（`open` 或 `closed`）
以及关闭记录的 `closureRecordId`，未关闭时为 null。查询不会移动已读游标。
关闭记录保存成员报告的完成情况。任务的验收证据需要单独保留。

## 唤醒

空闲的后台会话和任何 Claude 会话一样被唤醒：只有 @ 提及、指派的待办或私信会唤醒它，其他内容都等它下一次收到提示时再看。

已结束的会话（被停止了，或进程已不在）什么都收不到。`keel chat post` 和 `keel patrol` 会指出被点名的角色里哪些处于这种状态，并给出步骤：`keel chat wake now <角色>` 会用 `claude --bg --resume <会话 id>` 加一句「去读未读记录」的提示，恢复该角色记录下的会话。它不加任何别的参数，因为 `--resume` 带上任何参数都会另起一个新 id 的副本，而不是接着原会话；被恢复的会话沿用它保存的选项，包括权限模式。

`keel tick` 会自己做同样的事，每来一条新记录做一次：每次运行时，凡是 CLI 会话已结束、又有一条会唤醒它的记录在等的角色，都会被恢复；在更新的记录到来之前，不会再次恢复这个角色。已暂停的角色（`keel chat role --park`）不会被动。

## 由 `keel tick` 跑巡检

`keel tick` 是一个不调用模型的单步命令，由宿主调度器每隔几分钟调用一次。每次运行它会恢复已结束的会话（见上文），执行排队的换班交接（见下文），并且只在上一次巡检推荐的下次运行时间已过时，先 `git fetch`，再跑协调者的 `keel patrol --since-last --notify`。`issue_roles:` 声明了路由，或者有角色在等某个 issue 关闭时，它会先用 `gh` 取 issue 状态，作为 `--issues` 传给巡检，所以 `gh` 必须在这个任务的 `PATH` 上并且已登录；取不到时在 `tick/tick.log` 里说一次，`keel --doctor` 也会打印一行 `issue checks`（#473）。Keel 自己不做任何调度，重复运行由 launchd 负责。

```yaml
patrol:
  role: pm
  every: 30m
  runner: tick
  cadence: adaptive
```

`runner: tick` 告诉协调者的新会话和 `keel shift resume`：巡检在会话之外运行，所以不会再提醒它们重建计划任务。`keel tick task` 会打印 launchd 任务：一个 plist，每 300 秒从文件系统根目录调用一次 `keel tick --repo <仓库的主 checkout>`（所以不会有等待 checkout 空闲的工具把 tick 当作占用者，#524），每次运行都会找到各个声明了的角色当前绑定的 worktree（所以把角色绑到别处不需要重装任务），日志写到聊天存储里的 `tick/tick.log`。同时打印安装它的两条命令和卸载它的一条命令。Keel 不替你安装，命令请自己运行。plist 里带的是打印它的那个 shell 的 `PATH`，所以打印时 `claude` 和 `git` 必须都在 `PATH` 上，只是 Claude 插件缓存目录（它属于某一个版本）会被去掉。它运行的是那个 `PATH` 上与打印它的 node 为同一个可执行文件的 `node`，例如 `/opt/homebrew/bin/node`，而不是带版本号的 `Cellar` 目标，所以 `brew upgrade` 不会弄坏这个任务；`keel chat wake add` 和聊天桥也一样。launchd 任务不得写入 `.claude/worktrees/` 下的路径或 `.venv` 里的路径，因为这两处都会被重新生成，任务随后每个间隔都失败，只在 `tick/tick.err` 留一行；打印出的任务因此写主 checkout，只有主 checkout 没有声明 `patrol:` 时才写角色绑定的 worktree，并说明原因。`keel --doctor` 会为每个 `dev.keel.*` LaunchAgent 打印一行 `launchd`，列出 node、`--repo` 或 `WorkingDirectory` 已不存在、或位于 `.claude/worktrees/` 下的那些，并给出重建它的命令。

没有声明 `patrol:` 的仓库同样能拿到这个任务：`keel tick task` 照样打印，指向主 checkout，并说明每次运行只会叫醒已结束的会话、执行交班，不跑巡检；没有协调者的仓库只需要这些（#509）。Keel 读不懂的 `patrol:` 仍然会被拒绝并给出原因，不会被当成没声明。

每次 `keel tick` 运行都会在 `tick/state.json` 里记录 `last_tick`，巡检未到期的那次也记，因为巡检自己的 `last_run` 一次巡检才动一次。`keel --doctor` 据此打印一行 `tick`：正常时给出上次运行的时间；超过 15 分钟（任务周期的三倍）没运行、或仓库声明了 `runner: tick` 却从未记录过运行时，报告为问题。巡检角色的会话启动也用一行说同样的事，`keel context --json` 以 `patrol.tick` 带出。任务没在跑时，tick 自己无法报告，所以只能靠这条痕迹；它只读这一个文件、不向宿主查询，因此不说原因：电脑睡眠与任务从未加载，看到的是同一行（#510）。

每次巡检都会打印一行 `next:`，即推荐的下次运行时间，`keel tick` 会等到这个时间。不声明 `cadence: adaptive` 时，它就是 `every:`（规则 `fixed`）。声明后，取第一条成立的规则：

| 规则 | 条件 | 默认 |
|---|---|---|
| `risk` | 巡检报告了风险 | `30m` |
| `quota` | `--quota` 达到 90 或以上 | `4h` |
| `night` | 当前时间在 `quiet:` 窗口内（如 `23:00-08:30`） | 到窗口结束 |
| `busy` | 有别的角色处于活跃状态，或某个活跃角色有未完成的待办或等待项 | `1h` |
| `idle` | 其他情况 | `3h` |

每个默认值都可以用 `patrol:` 下的同名键覆盖（如 `risk: 15m`）；`min:` 和 `max:` 会给除 `night` 以外的所有规则加上下限和上限。

## 换班

CLI 会话不能清空自己，所以换班改为替换会话。角色和在任何宿主上一样，运行 `keel shift check` 和 `keel shift ready --wake "<便条>"`。在 CLI 会话里，`ready --wake` 会在便条里记下这个会话（`CLI session:` 和 `CLI process:`），在聊天存储里排一个交接，并留一个后台等待器去执行它，然后告诉会话结束本轮。

等待器每隔几秒在 `claude agents` 里查一次这个会话（`keel tick` 每次运行也做同样的事，作为等待器没了时的后备；两者之间有一把锁，不会各启动一个会话；仓库不装 tick 也能换班）。`claude agents` 显示会话还在忙，或者在等输入（它正卡在向你提的问题上），就继续等：交接绝不会打断一场对话。它看的是 status，不是任务状态 state：state 只是对会话最后一条消息的归类，不代表这一轮有没有结束（#393）。会话一旦空闲、已停或已不在，就用 `claude stop` 停掉它（对话会保留），不再恢复它。然后在同一个 worktree 里用 `claude --bg -n "<角色> · <月-日 时:分>" --permission-mode <模式> [--model <模型>] [--effort <档位>]` 加「运行 `keel context` 和 `keel shift resume`」的提示启动一个新会话。新一班从干净的上下文开始，会话 id 是新的，名字也是自己的：角色名加本地开班时间，所以在 `claude agents` 和 claude.ai 上没有两班同名。旧会话保留它启动时的名字，不再改名：改名要恢复旧会话，而开着 Remote Control 的会话会用 claude.ai 上的标题把改名盖回去（#399）。模式取自 `keel/config.yaml`，没有声明时为 `auto`：

声明了 `sync: lock: true` 时，如果按上次拉取到的锁，角色所在 worktree 的分支正被另一台设备持有，排队的交接不会启动新会话：条目会记下 `waiting_on: branch <b> is held by <持有者> until <时间>`，`keel shift status` 会显示它，挂起超过 15 分钟时巡检会报告（#526）。每次 tick 还会为本设备持有的分支锁续租。 声明了 `device-sync` 后，续租先确认远端仍由本设备持有有效锁，再仅按 `push` 或匹配的 `push:<glob>` 推送工作分支，跳过 `push-protected`。推送或续租失败时让租约到期，同一故障只报告一次。提示钩子仅在 TTL 的三分之一过去后续租，不推送工作分支，失败时保持安静。

```yaml
shift:
  permission_mode: auto   # default、acceptEdits、auto、plan 或 bypassPermissions
  keep_old_sessions: 0    # 每个角色保留在列表里的旧班数；默认 0，一个不留
  model: opus             # 可选：新班用这个模型启动，而不是你的默认模型
  effort: high            # 可选：low、medium、high、xhigh 或 max；只在声明时才传
```

新会话用你自己会得到的那个模型启动（#500）。启动命令不指定模型时，由宿主自己挑：2026-11-01 它启动的几个班跑的是 sonnet，尽管用户 `settings.json` 的 `model` 写的是 opus。所以现在启动命令在 `--permission-mode` 之后带 `--model`，取下面第一个写了模型的来源：`shift: model:`、环境变量 `ANTHROPIC_MODEL`、该 worktree 的 `.claude/settings.local.json`、它的 `.claude/settings.json`、最后是 Claude 配置目录（`CLAUDE_CONFIG_DIR`，没有就是 `~/.claude`）里的 `settings.json`。文件不存在、不是合法 JSON，或 `model` 不是字符串，就当它没写，试下一个；托管策略设置不读。都没写时命令也不指定模型，和以前一样。`--effort` 只在 `effort:` 声明时才传，所以宿主自己按模型设的 `effortLevel` 照常生效。`keel shift status` 会显示已交接的这一班用的模型和来源；读不懂的 `model:` 或 `effort:` 会在那里点名并忽略。被恢复的会话沿用保存时的选项。

每次换班都会停掉旧会话。交接之后，该角色最新的 `keep_old_sessions` 个已停会话留在列表里，可以 `claude attach`；更早的，在 Keel 的存储里已有其 transcript 副本之后用 `claude rm` 移除（#397）。不声明时一个不留（#418）：刚交接的那一班也会被移除（它的 worktree 正被使用时除外，见下），所以它不会再和当前一班并列出现在 `claude agents` 和 claude.ai 上——已停的会话在那里看起来和在跑的一样。对在已有 worktree 里启动的会话执行 `claude rm`，不会删掉那个 worktree。自己建了 worktree 的会话（用 `EnterWorktree` 或 `claude --bg -w`）不一样：`claude rm` 会把那个 worktree 一起删掉，所以只要它的 worktree 是新一班的、绑定了某个角色、或有别的会话在里面跑，Keel 就把这个会话留在列表里（#492）。`keel shift ready --wake` 在会话的 worktree 是新一班的、或绑定了某个角色时，会事先说明它会留下，而不是承诺移除；只因别的会话在里面跑而留下的会话，`ready` 不查 `claude agents`，要等 `keel shift status` 事后点名（#506）。只有有 transcript（宿主的或 Keel 的副本）的会话才算一班：从没收到过提示的会话没有 transcript，不占名额，也保留不动（#401）。会话在该角色的某个 worktree 里跑过，或者 Keel 在该角色名下存有它的 transcript，就算该角色的会话，所以 worktree 改名或搬走后，旧会话不会被落下（#462）。不经 Keel 完成的接班——你手动开的会话运行 `keel shift resume`——也同样清理：在 Claude Code 会话里恢复一份由 CLI 会话写下的便条时，会按同样的规则移除该角色的旧会话，并列出移除了哪些（#462）。内容不会丢：`claude rm` 不删宿主的 transcript，Keel 另有一份副本，`keel shift history <角色> --show <会话 id>` 能打印任何一班的完整对话，无论它还在不在列表里。

`keel shift status` 会列出每个交接的状态：等待中、已送达（带新会话的 id）或失败（带错误信息），并给出重新打开旧会话的命令 `claude attach <其 id 的前 8 个字符>`，旧会话已被移除时则给出 `keel shift history <角色> --show <id>`；还会列出这次交接移除的更早会话。交接后留在列表里的旧会话会写明原因：按 `keep_old_sessions` 保留、进程还在跑、transcript 没能复制、它的 worktree 正在用，或 `claude rm` 失败及宿主的报错；打开它，它就会和新一班并存（#492）。失败的交接，或等待超过 15 分钟的交接，会成为巡检风险，从而通知到协调者。`keel tick` 会重试失败的启动，总共最多三次；最后一次仍失败时，status 会给出 `keel chat wake now <角色>`，用来恢复已停止的旧会话。worktree 没被信任过是失败的一种情形：新会话在那里起不来。

在 CLI 上，`keel shift resume` 不要求恢复任何东西：新会话已经带上了角色的名字，`self-shift` 和 `shift-restore` 授权的那些桌面端步骤都不适用。

## 权限

`keel tick` 在所有会话之外运行，不需要任何会话权限。各会话自己通过 Bash 运行 `keel` 和 `git` 命令。交接启动的会话使用声明的 `permission_mode`，被恢复的会话沿用它启动时的模式。所以每个角色的第一个会话，请用你希望它一直保持的模式启动，并像对待无人值守的桌面会话那样，给它工作所需的 `permissions.allow` 条目。仅桌面端需要的条目（`mcp__ccd_session_mgmt__*`、`mcp__scheduled-tasks__*`），以及 `self-shift`、`shift-restore` 两项声明，在这里都不需要。

巡检会将超过 24 小时仍只在本机的分支提交、游离 HEAD 和 stash 列为持续风险。它只读取本地引用，不把未提交文件算入此项；`--since-last --notify` 对不变的风险只通知一次。有范围的巡检覆盖对应角色，仓库巡检还覆盖没有 worktree 的分支和 stash。`keel --doctor` 显示设备标识、持有的分支锁、到期时间、上次续租时间，以及 tick 是否运行过或由 Claude 提示钩子续租。

## 项目旁的 Codex worktree

选择主 checkout 旁的目录和一个新任务分支。默认从所选 checkout 的 HEAD 创建，
也可用 `--base <ref>` 指定其他本地提交。相对目录以 `--repo` 所选 checkout 为基准。

```sh
keel worktrees add --repo /path/to/project --path ../project-worktrees/review --branch codex/review --json
codex -C /path/to/project-worktrees/review
```

将第一条命令返回的 `path` 传给 Codex。要绑定 Keel 角色，在该工作树中运行
`keel chat role --set review`。用 `keel worktrees --repo /path/to/project`
查看全部工作树及角色绑定。再次使用现有工作树时运行 `codex -C <path>`。

创建需要未占用的目录和分支。结束 Codex 会话后，用 `git -C <path> status`
检查并保留本地改动，再用 `git -C /path/to/project worktree remove <path>` 清理。
普通移除会拒绝有未保存改动的工作树，并保留分支。若角色绑定仍残留，
`keel chat role --prune` 会清理该仓库中指向已移除工作树的绑定。

Codex Desktop 的 Worktree 模式和 Handoff 在 `$CODEX_HOME/worktrees` 管理其工作树。
这里创建的 Git 工作树用于 CLI 流程。

## Keel 托管的 Codex 角色

每个角色使用独立 Git worktree。用正确的网络环境启动 `codex app-server --listen unix:///path/to/team.sock`，或使用现有托管守护进程。Keel 只连接指定主机，失败时不会另起服务：

```bash
keel codex start --repo /path/to/role-worktree --role worker --socket /path/to/team.sock --json
keel codex status --repo /path/to/role-worktree --role worker --json
keel codex drain --repo /path/to/repository --json
keel codex handover --repo /path/to/role-worktree --role worker --note "已完成、待完成和授权边界" --json
```

未指定 `--socket` 时，start 使用 `$CODEX_HOME/app-server-control/app-server-control.sock`，通常位于 `~/.codex/`；后续调用使用记录中的端点。`keel tick` 按现有信箱的定向、停用和 no_wake 规则投递未读记录，调度仍由宿主负责。同一角色切换到托管模式前，应停止旧的 `keel chat wake` 监视器，保证只有一个投递者。

成功的 `start` 和交接后继线程会先获得与角色同名的原生线程名称，再被登记为已托管。原生元数据写入会持久化空白线程，不启动隐藏的模型回合，因此首次投递可以晚于创建连接关闭和宿主卸载。命名或身份校验失败时，已创建的编号保留在待初始化记录中。旧空白编号若已丢失且没有 rollout，便无法恢复；Keel 保留注册并报告错误，不静默换成新编号。

需要指定线程级审核者时，在创建角色时显式选择：

```bash
keel codex start --repo /path/to/role-worktree --role worker --socket /path/to/team.sock --approvals-reviewer auto_review --timeout 30000 --json
```

`--approvals-reviewer user|auto_review` 只用于 `start`。`user` 将批准请求交给用户，
`auto_review` 使用原生自动审核；两者都保留 `on-request` 与 `workspace-write`。
显式选择写入角色记录，并由冷派工和交接后继线程继承。Keel 在报告已托管前，
通过原生 `thread/settings/update` 持久化选择，空白线程也不需要模型预热。
不传该参数的调用保持原有行为。宿主必须支持原生 reviewer 与 settings API；
显式选择审核者的角色使用 experimental API 协商。

原生返回的审核者、批准策略或 sandbox 不符时，在启动工作前报错。
持久化失败会保留原线程或后继线程的待定编号，供后续核实；创建回执超时仍视为
结果未知，不自动重试。显式 `--timeout` 控制每个 RPC 的预算，示例为冷启动预留
30 秒。失败后先核对保留记录与宿主的实际结果，再决定下一步。

显式投递用 `keel codex deliver --role worker --record <稳定编号> --text <内容>`，同时指定工作目录。相同编号只启动一个工作回合；结果不确定时保留 pending，不自动重试。忙碌时返回 waiting，等待下一次 drain/tick。需要批准的操作仍在原生 Codex 界面处理。宿主不可达时明确报错，不创建替代会话。新记录遇到身份已核实且确实归 Keel 所有的 notLoaded 线程时，会恢复同一线程并重新核验，忙碌则等待。已投记录直接返回原声明，不为去重而恢复；未知声明继续拒绝重放。冷恢复默认预算为 15 秒，显式 `--timeout` 仍优先；内置信箱 drain 给子进程 40 秒，覆盖有界的 RPC 序列。现有桌面聊天和换班不因此获得自动恢复。创建或交接结果不确定时先核实宿主和保留的记录，不要删记录重试。

确属 Keel 的角色发生原生 cwd 漂移时，可显式运行 `keel codex recover --repo /path/to/role-worktree --role worker --json`。它只在登记端点通过原生 resume 恢复原线程的 cwd/runtime workspace roots，不迁端点、不接管桌面聊天。活跃线程返回 waiting，不执行 resume。原生 writer 拒绝、状态未知、策略或身份不符及超时都需核查；失败或未知的恢复可能已改变原生 cwd，但角色记录、历史和投递声明保持原样，不启动模型回合或替代线程。成功会核对原 ID/cwd，以及已登记/迁移角色的原生策略快照；旧式角色仍核对 on-request、workspace-write 及显式 reviewer；后续授权投递应验证真实执行目录。该命令不修复 App 项目或侧边栏归属，也不绕过其它仍存活的 writer。

交接使用 `keel codex handover`，旧会话和说明保存在现有聊天存储的托管角色历史中，后继在下一次收到定向任务时获得说明。Claude 的 `keel shift` 流程保持原样。专用前台原线程需经过下方显式登记计划，不自动发现或接管桌面聊天，不改变 hook 信任；未实测的守卫与压缩能力仍为 manual。实际双角色验收及限制见 `docs/codex-validation.md`。


## 原生共享桌面接入

Keel 5.230.0 已在 Linux App 26.1023.51421 与原生后台 0.167.2 上实测。
默认桌面 App 的 stdio 执行端与独立 daemon 是不同 writer，即使都能列出同一历史。
前台 App 必须连接托管角色使用的同一原生后台；置顶或读到 ID 不代表共享执行。
这是显式原生宿主配置，Keel 不自动切换。其它 App 版本及 macOS 需各自验证。

已实测版本可通过独立资料目录和进程级 WebSocket 地址接入，不必重启现有 App。
先选择私有目录、已安装的 App 程序，以及已运行且可访问模型的团队后台绝对 socket
路径。执行、凭据与配置归原生 daemon；Keel 不另起投递器或改变原 App 的连接。

```sh
CODEX_ELECTRON_USER_DATA_PATH="/path/to/private-team-profile" \
CODEX_HOME="/path/to/private-team-home" \
CODEX_APP_SERVER_WS_URL="ws+unix://localhost/absolute/path/team.sock:/rpc" \
/path/to/installed/ChatGPT --user-data-dir="/path/to/private-team-profile"
```

目录必须专用于该窗口；相同资料目录已有实例时，启动可能转给旧实例。
强制 CLI 的配置会使原生 URL 路径失效。实际核对连接和角色身份后才执行任务。
不要复制认证文件来补私有资料目录的登录。测试私有目录中的可选 ChatGPT Local Work
执行器未认证，本次 Codex 接入验收不代表那项独立功能可用。

私有前台目录**不隔离后台项目信任**。打开新项目可能在后台配置中登记信任；应由
所有者审查，不能承诺全局零变化。本次测试发现该差异后暂停，获得仅临时测试项的
明确授权，最后恢复了原配置精确哈希。生产项目的信任条目不得作为清理被静默删改。

仅在原执行端的真实回合和工具完成、旧 writer 释放后使用现有 owned 角色 ID，保留
登记端点、历史与声明。`recover` 仅在同端点恢复 cwd，不迁端点。其它 daemon 的
notLoaded 或 goal:null 不证明原 App 空闲。writer 拒绝、操作结果未知或身份不符时
停止恢复，不强行接管、不删除注册、不创建替代 ID。

前台忙时，托管投递返回 waiting，后续 tick 再试。此 App 在后台忙时使用原生
**引导（Guide）**更新当前回合，可能改变预期回答，不保证排成一个独立任务。
独立工作应使用稳定定向记录，在空闲后正常托管投递。原生 queue/add 对同一客户端
UUID 会重复入队，不能代替托管声明账本的幂等性。

上线前必须实测前台输入/后台接续、双向忙碌、原 ID/cwd/策略/声明保留，以及该 App
正常关闭时后台继续执行，再重开核对真实回复。仅在专用窗口的已接收回合和工具结束
后正常关闭它，原生后台保持运行。回退为安全正常退出该窗口，再用不带上述进程变量
的原启动器；无法安全退出时保全并报告，不强杀、不重启后台、不重置全局配置。
原先全 App 空闲后重启的路径仍需其独立明确授权。参见
[真实宿主证据](codex-validation.md)与 [#541](https://github.com/TanglmChris/keel/issues/541)。

## 显式登记已授权的前台原线程（#547）

先在原独立工作树用 `keel chat role --set review` 绑定唯一角色。部署所有者须已授权
明确的原线程、工作树、角色和端点；`--authority` 记录该授权来源，属于调用者声明，
不验证 ACL，也不从名称或普通 DM 推断授权。不要用 `start --thread`，start 会创建新线程。

```sh
keel codex inspect-registration --repo /path/to/owned-worktree --role review --thread ORIGINAL_THREAD_ID --socket /path/to/selected.sock --authority https://example.com/approved-role-list > /tmp/owned-registration.json
cat /tmp/owned-registration.json
keel codex register --plan /tmp/owned-registration.json --json
```

检查只通过原 ID 重新接入原生上下文，不覆盖设置、不发模型请求、不创建替代线程；
原生 resume 可能加载或订阅该线程。同一执行端的活跃线程可登记，无需人为等待全局空闲。
执行时重核唯一规范角色绑定、原生审批/reviewer/沙箱/roots、原身份和当前/历史/待定线程
冲突，再以无覆盖的原子方式登记，不重写现有记录或绑定。计划含端点和身份摘要，请私存。

后续空闲/冷投递及恢复使用原生策略快照。只读 review 保持只读，策略漂移则拒绝，
不扩大权限。已登记前台的 `handover` 拒绝创建替代线程；后继流程需单独授权。
DM 已写入、原生已接纳回合、模型收件、`keel chat read` 已读和业务任务完成是不同阶段，
不能凭投递成功或模型答复宣称邮箱游标已推进。普通协调消息不授予业务代码修改权限。

## 迁移单个自有角色端点（#546）

部署所有者须在交接期间管住该源角色的新输入准入：让实际回合、工具和输入正常完成，
保留待定投递声明，并将前台实际接到批准的目标执行端。这不是全 App 空闲要求。
CLI 无法阻止独立前台新输入，也不改变 App 接线；外国宿主的 notLoaded 不证明源已释放。

```sh
keel codex inspect-migration --repo /path/to/owned-worktree --role worker --to-socket /path/to/approved-target.sock --authority https://example.com/approved-migration > /tmp/owned-migration.json
cat /tmp/owned-migration.json
keel codex migrate --plan /tmp/owned-migration.json --json
keel codex migration-status --plan /tmp/owned-migration.json --json
```

计划固定旧登记摘要、身份、完整分页持久历史及有效策略。检查和执行都会在记录迁移意图和
源端退订前读取目标身份及完整分页历史。原生版本之间缺少历史字段也会导致校验失败。
迁移要求源实际空闲、输入队列和后台终端为空且无 Goal。持久记录意图后，仅取消自己的源订阅，
再等待源端报告同一线程为 `notLoaded`。默认等待上限为 75 秒。显式传入的 `--timeout <ms>`
同时限制卸载等待和单次 RPC。超时后保留原登记供核对。目标接入仍由原生 writer 保护裁决，
并要求保留相同的持久 ID、历史和原策略。
登记只改端点并追加迁移审计，原历史、自定义字段和全部投递声明保留，未知声明仍禁止重放。
旧式默认角色迁移后的投递和恢复同样核对审计中的策略快照。

意图记录后的失败表示**结果未知**，不代表原生状态已回退。先检查 `migration-status`；
重复 migrate 不会自动重做交接。核对结果后，才显式使用
`migrate --plan /tmp/owned-migration.json --reconcile`。它核已加载的目标原线程、源释放、
原已完成历史前缀和有效策略，再比较登记并提交，不打断目标的新工作。目标未加载时拒绝，
不重新获取 writer；部署所有者须先按自己的原生恢复授权核验并接入该原 ID，再核查。
登记有并发变化时检查冲突，不手改或替换记录。登记已提交但最终日志中断时，可在精确匹配
后仅补完状态，不重写登记。

原生冷加载可能把空的内建 profile 来源补成 `:read-only` 或 `:workspace-write`；
仅归一化相匹配的隐式表示，审批、reviewer、沙箱字段、roots 和自定义 profile 仍须一致。
空线程在首个真实回合前可能未持久化显式审批；策略变化就拒绝迁移，不热身或自动修策略。
前台接线、项目 trust、服务布局与生产操作仍需各自明确的部署授权。
