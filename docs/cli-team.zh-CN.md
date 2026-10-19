# 用 Claude Code CLI 会话组成团队

`keel chat`、`keel shift`、`keel patrol` 的桌面端用法依赖 Claude 桌面应用：巡检由它的定时任务来跑，会话的唤醒和清空由它的会话工具来做。团队也可以不开桌面应用，把每个角色作为 Claude Code CLI 的后台会话（`claude --bg`）来跑（#369）。本页从头到尾讲这条路径，实测版本为 Claude Code 2.1.303。英文版：[cli-team.md](cli-team.md)。

## 各项由谁负责

| 需要 | 桌面应用 | CLI |
|---|---|---|
| 每个角色一个会话 | 在角色的 worktree 里开一个应用会话 | 在角色的 worktree 里运行 `claude --bg -n <角色>` |
| 唤醒空闲的会话 | @ 提及、指派的待办或私信 | 相同：聊天的文件钩子会唤醒空闲的后台会话 |
| 唤醒已结束的会话 | 对该会话 `send_message` | `keel chat wake now <角色>`，或由 `keel tick` 在每来一条新记录时做一次 |
| 按计划跑巡检 | 宿主定时任务（`host_task:`） | 由 launchd 调用的 `keel tick`（`runner: tick`） |
| 换班 | 会话清空自己，等待器唤醒新一班 | 等待器停掉旧会话并给它改名、启动新会话；等待器不在时由 `keel tick` 做同样的事 |
| 打开上一班的对话 | 已归档的应用会话 | 对已停止的会话运行 `claude attach <id>` |

## 设置一个角色

1. 建好角色的 worktree，在里面以交互方式运行一次 `claude`，接受信任提示。信任按目录生效，不从已信任的上级目录继承：在没人信任过的目录里运行 `claude --bg` 会报 `Workspace not trusted`，之后在那里的每次启动也都会失败，包括换班时的那次。
2. 在后台启动会话：`claude --bg -n <角色>`。这个名字就是该会话在 `claude agents` 里的标题。
3. 在这个会话里绑定角色：`keel chat role --set <角色>`。此后它的在线状态会记下这个 CLI 会话的 id 和进程，Keel 正是靠这些来恢复或替换它。

每个角色只跑一个会话。如果同一个角色又绑上了第二个会话（例如对一个还在运行的会话执行了 `claude --resume`），两个会话会用同一个名字发言，共用一个已读游标，谁先读，谁就把记录从另一个那里藏起来了。只要有两个存活会话绑在同一个角色上，`keel context` 会给出警告，`keel chat post`、`dm`、`todo`、`unread`、`read` 也会在 stderr 上警告。遇到时停掉其中一个。

## 唤醒

空闲的后台会话和任何 Claude 会话一样被唤醒：只有 @ 提及、指派的待办或私信会唤醒它，其他内容都等它下一次收到提示时再看。

已结束的会话（被停止了，或进程已不在）什么都收不到。`keel chat post` 和 `keel patrol` 会指出被点名的角色里哪些处于这种状态，并给出步骤：`keel chat wake now <角色>` 会用 `claude --bg --resume <会话 id>` 加一句「去读未读记录」的提示，恢复该角色记录下的会话。它不加任何别的参数，因为 `--resume` 带上任何参数都会另起一个新 id 的副本，而不是接着原会话；被恢复的会话沿用它保存的选项，包括权限模式。

`keel tick` 会自己做同样的事，每来一条新记录做一次：每次运行时，凡是 CLI 会话已结束、又有一条会唤醒它的记录在等的角色，都会被恢复；在更新的记录到来之前，不会再次恢复这个角色。已暂停的角色（`keel chat role --park`）不会被动。

## 由 `keel tick` 跑巡检

`keel tick` 是一个不调用模型的单步命令，由宿主调度器每隔几分钟调用一次。每次运行它会恢复已结束的会话（见上文），执行排队的换班交接（见下文），并且只在上一次巡检推荐的下次运行时间已过时，先 `git fetch`，再跑协调者的 `keel patrol --since-last --notify`。Keel 自己不做任何调度，重复运行由 launchd 负责。

```yaml
patrol:
  role: pm
  every: 30m
  runner: tick
  cadence: adaptive
```

`runner: tick` 告诉协调者的新会话和 `keel shift resume`：巡检在会话之外运行，所以不会再提醒它们重建计划任务。`keel tick task` 会打印 launchd 任务：一个 plist，每 300 秒在协调者的 worktree 里调用一次 `keel tick`，日志写到聊天存储里的 `tick/tick.log`。同时打印安装它的两条命令和卸载它的一条命令。Keel 不替你安装，命令请自己运行。plist 里带的是打印它的那个 shell 的 `PATH`，所以打印时 `claude` 和 `git` 必须都在 `PATH` 上，只是 Claude 插件缓存目录（它属于某一个版本）会被去掉。它运行的是那个 `PATH` 上与打印它的 node 为同一个可执行文件的 `node`，例如 `/opt/homebrew/bin/node`，而不是带版本号的 `Cellar` 目标，所以 `brew upgrade` 不会弄坏这个任务；`keel chat wake add` 和聊天桥也一样。`keel --doctor` 会为每个 `dev.keel.*` LaunchAgent 打印一行 `launchd`，列出 node 已不存在的那些，并给出重建它的命令。

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

等待器每隔几秒在 `claude agents` 里查一次这个会话（`keel tick` 每次运行也做同样的事，作为等待器没了时的后备；两者之间有一把锁，不会各启动一个会话；仓库不装 tick 也能换班）。会话还在忙，或者它的任务状态仍是 `working`（它正卡在向你提的问题上），就继续等：交接绝不会打断一场对话。会话一旦结束或已不在，就让它退役：先 `claude stop`（对话会保留），再用 `/rename <角色> · shifted <日期时间>` 恢复它一次，给旧会话一个说明它已换班的名字（会话 id 不变），然后再 `claude stop` 一次。30 秒内改名没有出现在 `claude agents` 里，会记在 `keel shift status` 里，不会耽误交接。然后在同一个 worktree 里用 `claude --bg -n <角色> --permission-mode <模式>` 加「运行 `keel context` 和 `keel shift resume`」的提示启动一个新会话。新一班从干净的上下文开始，会话 id 也是新的。模式取自 `keel/config.yaml`，没有声明时为 `auto`：

```yaml
shift:
  permission_mode: auto   # default、acceptEdits、auto、plan 或 bypassPermissions
```

`keel shift status` 会列出每个交接的状态：等待中、已送达（带新会话的 id）或失败（带错误信息），并给出重新打开旧会话的命令 `claude attach <其 id 的前 8 个字符>`。失败的交接，或等待超过 15 分钟的交接，会成为巡检风险，从而通知到协调者。worktree 没被信任过是失败的一种情形：新会话在那里起不来。

在 CLI 上，`keel shift resume` 不要求恢复任何东西：新会话已经带上了角色的名字，`self-shift` 和 `shift-restore` 授权的那些桌面端步骤都不适用。

## 权限

`keel tick` 在所有会话之外运行，不需要任何会话权限。各会话自己通过 Bash 运行 `keel` 和 `git` 命令。交接启动的会话使用声明的 `permission_mode`，被恢复的会话沿用它启动时的模式。所以每个角色的第一个会话，请用你希望它一直保持的模式启动，并像对待无人值守的桌面会话那样，给它工作所需的 `permissions.allow` 条目。仅桌面端需要的条目（`mcp__ccd_session_mgmt__*`、`mcp__scheduled-tasks__*`），以及 `self-shift`、`shift-restore` 两项声明，在这里都不需要。
