# 换班

长期运行的角色会话，上下文会越积越多，直到被清空。换班就是在你选定的时间做这件事，而且不丢东西：要下班的会话先收尾、留一份交接便条，再清空自己；新的一班从便条开始。

绑定了 `keel chat` 角色时，每一步还会是一条记录，发在协调者（通常是 PM 角色）与该角色的私聊群里，会唤醒对应的会话，事后也能回看。不绑定聊天角色也能换班：`check`、`ready`、`resume` 只需要仓库本身；协调者用手头任何方式通知会话，新会话自己运行 `keel shift resume` 就行。但没有任何东西会唤醒这个新会话，所以自己给自己换班时，应先用 `keel chat role --set <名字>` 绑定角色，再用 `keel shift ready --wake`（#317）；在没有聊天角色的 worktree 里，`ready` 会被拒绝，除非用 `--force-reason` 写明由谁来启动新会话，便条会记下这句。两种情况都不涉及 bot 或 Slack：聊天角色只是存在仓库 git 公共目录里的本地名字。

## 步骤

| 谁 | 命令 | 作用 |
|---|---|---|
| 协调者 | `keel shift request <角色> [说明]` | 有聊天角色时，以待办的形式发换班请求，会唤醒对方；没有时，用任何方式通知会话即可。 |
| 角色 | `keel shift check` | 只读。列出没收尾的事，有任何一项就退出 1。 |
| 角色 | `keel shift ready "<便条>"` | 存便条，有请求的话顺便关掉。`check` 还报东西时拒绝，除非给出 `--force-reason "<为什么可以留着>"`。便条也可以用 `--file` 或标准输入给。 |
| 角色 | 清空会话 | 桌面应用：`clear_session("self")`（由你批准）或 `/clear`；命令行：`/clear`；Codex：开新会话。这些 Keel 都不替你执行。 |
| 协调者 | `keel shift start <角色> [下一步]` | 有聊天角色时：便条还没留下就拒绝，留下后发出开工消息，唤醒清空后的会话。在 Claude 桌面应用上，没有运行中进程的会话看不到聊天记录（#320），所以对在那里写下的便条，它改为打印唤醒它的 `send_message` 步骤。没有时：告诉新会话运行 `keel shift resume`。 |
| 角色（新的一班） | 先 `keel context`，再 `keel shift resume` | 打印便条、移进历史；有聊天角色时还会告诉协调者已就位。 |
| 任何人 | `keel shift status` | 各角色的状态：已请求、便条等待中、已接班。桌面端 `ready --wake` 留下的便条过了 3 分钟还没人接班，会标成桌面唤醒超时，并给出会话 id：用 `list_task_runs` 查唤醒任务那次运行，没送达就用 `send_message` 叫醒它。 |

## 在 Claude 桌面应用上给自己换班

在 Claude 命令行里，`ready --wake` 留下的等待器会在新会话启动后发一条消息把它叫醒。桌面应用不一样（#319）：清空会话后，要等有提示词进来才会启动新会话，所以等待器自己叫不醒任何东西。在桌面应用里运行 `ready --wake`，会把桌面会话 id 记进便条，并改为打印「伙伴唤醒」的步骤，要按顺序做。Remote Control 不用关：开着它也能清空，而关它要等人批准 app 弹出的请求，无人值守时等不到（#324）；清空后 app 会用一个新地址重新连上 Remote Control，远程看的人要打开新地址。整个换班在一分钟内完成：app 每分钟才派发一次定时任务，所以唤醒不排时间，而是马上启动，自己等清空发生。`ready` 会把这个会话的 Claude 进程号记进便条（`Desktop process:`），app 清空会话时会停掉这个进程。先用宿主的 `create_scheduled_task` 建一个不排时间的临时任务 `keel-shift-wake-<角色>`（已存在就用 `update_scheduled_task` 更新），它的提示词先用 Bash 跑 `keel shift await-clear --pid <进程号>`：进程退出就返回 0，120 秒后还在就返回 1。返回 1 时什么都不发，调用 `PushNotification` 通知你，并以 `WAKE FAILED` 开头回复；返回 0 时先对这个会话 id 调用 `get_session`，如果显示会话已归档，就先调用 `unarchive_session` 解除归档，再调用 `send_message` 把接班指令发过去；发送仍因已归档被拒时，再解除归档、重发一次（清空后闲着的会话，在它名下所有 PR 都合并后，可能在唤醒之前就被 app 的自动归档归档，见 #326；解除归档会把原来的 worktree 接回来）；`send_message` 返回 `delivered` 或 `queued` 算送达，重发后仍是别的结果就算唤醒失败，任务要调用 `PushNotification` 通知你（写明会话和返回结果），并以 `WAKE FAILED` 开头回复，让这次运行的摘要里看得到。建好后马上用 `run_scheduled_task` 启动它：唤醒消息如果在清空之前到达，清空会被丢掉，`await-clear` 保证它一定在清空之后。接着用 `set_session_title` 给要换下去的会话改名，让它在醒来的会话改回原名之前显示为换班中；最后清空。Keel 不会替你建任务。醒来的会话先跑 `keel context` 和 `keel shift resume`，再按 `resume` 的提示，如果 `get_session` 显示 Remote Control 是关的，就用 `set_remote_control("self", true)` 重开，并把名字改回来。无人值守时要做到这一点，需要把 `mcp__ccd_session_mgmt__set_remote_control`、`mcp__ccd_session_mgmt__get_session`、`mcp__ccd_session_mgmt__unarchive_session` 和 `mcp__scheduled-tasks__run_scheduled_task` 加进 `permissions.allow`，并在 `keel/config.yaml` 的 `authorize:` 里声明 `shift-restore`；不声明的话，醒来的会话会把这一步当成别的会话的请求，停下来问你。交班前的四步另有一项声明 `self-shift`；不声明，会话做这四步前会先问你。两项声明都不决定要不要换班。

## `check` 查什么

- 未提交的改动。
- 不在任何远端上的提交。仓库没有远端时跳过，并给出提示。
- 还开着的任务写保护（`keel/guard.json`）。
- 工作目录在本 worktree 里的进程，正在执行检查的会话本身除外。
- 在本 worktree 里启动的会话、其 Claude scratchpad 下的临时 worktree。其他临时 worktree（比如别的会话的）只作为提示列出，不影响是否就绪。
- 分配给该角色的未完成待办，以及会唤醒它的未读消息。

项目可以在旁边加自己的检查，比如临时目录下的构建产物：写个脚本，先调用 `keel shift check`，再查本项目特有的项。

## 便条

写下一班冷启动需要的东西：在做什么、下一步、在等谁、东西在哪（分支、文件、issue）。便条存在仓库的 git 公共目录下：有角色时是 `keel-chat/shift/<角色>.md`，没有角色时按 worktree 存为 `keel-chat/shift/worktree/<名字>-<编号>.md`。它在所有 worktree 之外，所以永远不会被提交。它从 `ready` 起存在，到 `resume` 为止。

便条等待期间，`keel context` 和会话启动提示（各宿主都有）都会提到它。会话即使不是被 `start` 叫醒、而是自己启动的，也能看到。

便条不是记录未完成工作的地方：后续事项写进项目的跟踪系统，在便条里引用即可。它也不是 `keel/HANDOFF.md`，`keel context` 不读它。
