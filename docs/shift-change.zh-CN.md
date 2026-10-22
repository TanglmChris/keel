# 换班

长期运行的角色会话，上下文会越积越多，直到被清空。换班就是在你选定的时间做这件事，而且不丢东西：要下班的会话先收尾、留一份交接便条，再清空自己；新的一班从便条开始。

绑定了 `keel chat` 角色时，每一步还会是一条记录，发在协调者（通常是 PM 角色）与该角色的私聊群里，会唤醒对应的会话，事后也能回看。不绑定聊天角色也能换班：`check`、`ready`、`resume` 只需要仓库本身；协调者用手头任何方式通知会话，新会话自己运行 `keel shift resume` 就行。但没有任何东西会唤醒这个新会话，所以自己给自己换班时，应先用 `keel chat role --set <名字>` 绑定角色，再用 `keel shift ready --wake`（#317）；在没有聊天角色的 worktree 里，`ready` 会被拒绝，除非用 `--force-reason` 写明由谁来启动新会话，便条会记下这句。两种情况都不涉及 bot 或 Slack：聊天角色只是存在仓库 git 公共目录里的本地名字。

## 步骤

| 谁 | 命令 | 作用 |
|---|---|---|
| 协调者 | `keel shift request <角色> [说明]` | 有聊天角色时，以待办的形式发换班请求，会唤醒对方；没有时，用任何方式通知会话即可。 |
| 角色 | `keel shift check` | 只读。列出没收尾的事，有任何一项就退出 1。 |
| 角色 | `keel shift ready "<便条>"` | 存便条，有请求的话顺便关掉。`check` 还报东西时拒绝，除非给出 `--force-reason "<为什么可以留着>"`。便条也可以用 `--file` 或标准输入给。 |
| 角色，在另一个 worktree 里工作 | `keel shift ready --role <角色> "<便条>"` | 在没有绑定角色的 worktree 里，把便条记在该角色名下，并关掉它的请求（#290）。不带 `--role` 时，只要有任何角色的请求还开着，未绑定 worktree 里的 `ready` 就会被拒绝，免得便条落在没有请求能找到的地方。 |
| 角色 | 清空会话 | 桌面应用：`clear_session("self")`（由你批准）或 `/clear`。交互式命令行：`/clear`。后台命令行会话（`claude --bg`）：什么都不用做——`ready --wake` 之后，等待器会在会话结束后几秒内换上新会话，等待器不在了 `keel tick` 也会做同样的事（[docs/cli-team.zh-CN.md](cli-team.zh-CN.md)）。Codex：开新会话。这些 Keel 都不替你执行。 |
| 协调者 | `keel shift start <角色> [下一步]` | 有聊天角色时：便条还没留下就拒绝，留下后发出开工消息，唤醒清空后的会话。在 Claude 桌面应用上，没有运行中进程的会话看不到聊天记录（#320），所以对在那里写下的便条，它改为打印唤醒它的 `send_message` 步骤。没有时：告诉新会话运行 `keel shift resume`。 |
| 角色（新的一班） | 先 `keel context`，再 `keel shift resume` | 打印便条、移进历史；有聊天角色时还会告诉协调者已就位。在没有绑定角色的 worktree 里开的新会话，用 `keel shift resume --role <角色>` 读该角色的便条。 |
| 任何人 | `keel shift status` | 各角色的状态：已请求、便条等待中、已接班。桌面端 `ready --wake` 留下的便条过了 3 分钟还没人接班，会标成桌面唤醒超时，并给出会话 id：用 `list_task_runs` 查唤醒任务那次运行，没送达就用 `send_message` 叫醒它。按 worktree 存的便条会写明该由哪个 worktree 运行 `keel shift resume`；仍处于已请求状态的角色，会列出此后写下的 worktree 便条。 |

## 找回以往某一班的对话

清空会保留会话，但会开一个新的 transcript 文件，而宿主的 transcript 搜索只覆盖当前这一个（#304）。所以绑定了角色的会话，其聊天 hook 会记下它跑过的每个 transcript，以及开始时间和被下一个替换的时间；同一 worktree 里宿主定时任务的运行不算在内。`keel shift history <角色>` 按新到旧列出这些 transcript 和该角色以往的交班便条；`keel shift history <角色> --grep "<文字>"` 打印每段里的匹配行，没有命中时退出 1；`keel shift history <角色> --show <会话 id>`（前 8 个字符即可）打印某一班的完整对话——每条提问、回复、工具调用和工具结果，按顺序、不截断——无论这个会话还在不在 `claude agents` 里（#397）。宿主会删掉旧 transcript（Claude Code 按 `cleanupPeriodDays`，没设置时是 30 天），所以每当角色的会话开始新的 transcript，hook 就把每个已结束的 transcript——以及 `history` 为该角色找到、但还没有记录的更早的 transcript，找到后一并记录（#361）——原样 gzip 压缩，复制进 Keel 的存储 `<git common dir>/keel-chat/shift/transcripts/<角色>/`（#343）。副本只留在本机：聊天归档不同步 `shift/`。宿主文件没了以后，`history` 会把那一段标为 `(kept)`，`--grep` 改搜副本。Codex 会话同样覆盖，因为 Codex 的 hook 会传入它的 rollout 文件；`--grep` 两种格式都能读。不做任何清理；要回收空间，删掉那个目录即可。

## 什么时候换班

在任务边界换班，在任务内部压缩（#313）。角色在做一项连续的任务时，上下文满了就让宿主压缩：中途换班会丢掉压缩本来能保留的工作状态，便条也只好带上做了一半的推理。一项完整的任务做完了，就换班，哪怕上下文还很少：下一项不相关的任务从干净的状态开始。这时，如果角色已经拿到下一项任务（有分配给它、还开着的待办），用 `keel shift ready --wake`；否则用普通的 `keel shift ready`，等协调者带着新工作来 `start`。

`keel patrol --nudge` 遵循同样的规则：分配给某个角色的待办关闭时，它会提醒那个角色换班，并写明该用上面两种中的哪一种。上下文大小不作为依据。

## 给自己换班

在 Claude Code 里，`/keel:shift` 会按顺序做完下面这些步骤（#386）：`keel shift check`，处理它报出的每一项（宿主在会话下面运行的保持唤醒进程，例如 `caffeinate`，检查本身就不会列出，#447），写便条，然后 `keel shift ready --wake --file -`，再照 `ready` 为当前宿主打印的内容做。要不要换班它不替你决定：由负责人来输入它。Codex 没有插件命令，那里这些步骤要手动做。

没有被任何请求点名的角色——最后换班的协调者，或者任何决定给自己换班的会话——和其他角色一样运行 `ready`，但没有人负责启动它的新会话，`ready` 也会这么说。它不能对自己 `keel shift start`，那会被拒绝。`status` 会说它的便条由它自己的下一个会话接班：往那个会话里输入，或者用 `keel shift ready --wake`（见下）。

`keel shift ready --wake` 补上了这个缺口。除了存便条，它还留下一个脱离的一次性等待器。当该角色的下一个会话启动时——清空或全新启动后的一次 SessionStart，晚于这次 `ready`，并且 15 秒后仍是该角色最新的一次启动——等待器以 `keel-shift` 的身份给该角色写一条消息，让它运行 `keel context` 和 `keel shift resume`，然后退出。在 Claude 命令行里，这条消息会像其他消息一样唤醒新会话。桌面应用不一样（#319）：清空会话后，要等有提示词进来才会启动新会话，所以等待器自己叫不醒任何东西。在桌面应用里运行 `ready --wake`，会把桌面会话 id 记进便条，并改为打印「伙伴唤醒」的步骤，要按顺序做。Remote Control 不用关：开着它也能清空，而关它要等人批准 app 弹出的请求，无人值守时等不到（#324）；清空后 app 会用一个新地址重新连上 Remote Control，远程看的人要打开新地址。整个换班在一分钟内完成：app 每分钟才派发一次定时任务，所以唤醒不排时间，而是马上启动，自己等清空发生。`ready` 会把这个会话的 Claude 进程号记进便条（`Desktop process:`），app 清空会话时会停掉这个进程。先用宿主的 `create_scheduled_task` 建一个不排时间的临时任务 `keel-shift-wake-<角色>`（已存在就更新它），它的提示词先用 Bash 跑 `keel shift await-clear --pid <进程号>`：进程退出就返回 0，120 秒后还在就返回 1。返回 1 时什么都不发，调用 `PushNotification`，并以 `WAKE FAILED` 开头回复；返回 0 时先对这个会话 id 调用 `get_session`，如果显示会话已归档，就先调用 `unarchive_session`，再调用 `send_message`；发送仍因已归档被拒时，再解除归档、重发一次。`send_message` 返回 `delivered` 或 `queued` 算送达；重发后仍是别的结果就算唤醒失败，任务要调用 `PushNotification`（写明会话和返回结果），并以 `WAKE FAILED` 开头回复，让这次运行的摘要里看得到。清空后闲着的会话，在它名下所有 PR 都合并后，可能在唤醒到达之前就被 app 的自动归档归档（#326）；解除归档会把原来的 worktree 接回来。然后马上用 `run_scheduled_task` 启动这个任务：唤醒消息如果在清空之前到达，清空会被丢掉，`await-clear` 保证它一定在清空之后。接着用 `set_session_title` 给要换下去的会话改名，让它在醒来的会话改回原名之前显示为换班中；最后清空。Keel 不会替你建任务。醒来的会话先跑 `keel context` 和 `keel shift resume`，再按 `resume` 的提示，如果 `get_session` 显示 Remote Control 是关的，就用 `set_remote_control("self", true)` 重开，并把名字改回来。无人值守时要做到这一点，需要把 `mcp__ccd_session_mgmt__set_remote_control`、`mcp__ccd_session_mgmt__get_session`、`mcp__ccd_session_mgmt__unarchive_session` 和 `mcp__scheduled-tasks__run_scheduled_task` 加进 `permissions.allow`，并在 `keel/config.yaml` 的 `authorize:` 里声明 `shift-restore`；不声明的话，醒来的会话会把这一步当成别的会话的请求，停下来问你。交班前的四步另有一项声明 `self-shift`；不声明，会话做这四步前会先问你。两项声明都不决定要不要换班。便条已经被接班时，等待器什么都不写；两小时后它就放弃。它是「Keel 不调度任何东西」的唯一例外：它从不重复。在该角色 worktree 里启动的宿主定时任务运行不会触发它：那次运行的第一条提示词（`<scheduled-task …`）一到，Keel 就恢复该角色的在线状态并忽略那个会话（#300）。它需要聊天角色，而且只看得到在绑定了该角色的 worktree 里打开的会话；在别处开的新会话，仍然需要有人往里输入。

## 协调者自己的换班

协调者最后换班（#289）。在 Claude 上，没有任何东西会唤醒清空后的会话，所以协调者如果在启动其他角色之前先清空自己，整个团队都要等到有人往它的新会话里输入。因此它的 `keel shift check` 会列出每个便条在等、而它此后还没有 `start` 的角色，它的 `ready` 在它对这些角色运行 `keel shift start`（或给出 `--force-reason`）之前会被拒绝。之后它和其他角色一样，带着自己的便条运行 `ready`，`status` 和新会话的投影都会显示出来。它的新一班运行 `keel shift resume` 时，输出会列出还在等 `start` 的角色。

清空会毁掉、Keel 又看不到的会话状态——比如巡查这样的定时任务、Remote Control——要写进便条，让下一班能重建；声明了 `patrol:` 时，新一班无论如何都会被提醒巡查的事。

## `check` 查什么

- 未提交的改动。
- 不在任何远端上的提交。仓库没有远端时跳过，并给出提示。
- 还开着的任务写保护（`keel/guard.json`）。
- 工作目录在本 worktree 里的进程，正在执行检查的会话本身除外。
- 在本 worktree 里启动的会话、其 Claude scratchpad 下的临时 worktree。其他临时 worktree（比如别的会话的）只作为提示列出，不影响是否就绪。
- 分配给该角色的未完成待办，以及会唤醒它的未读消息。
- 对发起过换班请求的角色：便条在等、而它此后还没有 `start` 的角色（`unstarted`）。

项目可以在旁边加自己的检查，比如临时目录下的构建产物：写个脚本，先调用 `keel shift check`，再查本项目特有的项。

## 便条

写下一班冷启动需要的东西：在做什么、下一步、在等谁、东西在哪（分支、文件、issue）。便条存在仓库的 git 公共目录下：有角色时是 `keel-chat/shift/<角色>.md`，没有角色时按 worktree 存为 `keel-chat/shift/worktree/<名字>-<编号>.md`。它在所有 worktree 之外，所以永远不会被提交。它从 `ready` 起存在，到 `resume` 为止。

便条等待期间，`keel context` 和会话启动提示（各宿主都有）都会提到它。会话即使不是被 `start` 叫醒、而是自己启动的，也能看到。

便条不是记录未完成工作的地方：后续事项写进项目的跟踪系统，在便条里引用即可。它也不是 `keel/HANDOFF.md`，`keel context` 不读它。
