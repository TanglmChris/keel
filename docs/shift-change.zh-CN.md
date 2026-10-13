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
| 协调者 | `keel shift start <角色> [下一步]` | 有聊天角色时：便条还没留下就拒绝，留下后唤醒清空后的会话。没有时：告诉新会话运行 `keel shift resume`。 |
| 角色（新的一班） | 先 `keel context`，再 `keel shift resume` | 打印便条、移进历史；有聊天角色时还会告诉协调者已就位。 |
| 任何人 | `keel shift status` | 各角色的状态：已请求、便条等待中、已接班。 |

## 在 Claude 桌面应用上给自己换班

在 Claude 命令行里，`ready --wake` 留下的等待器会在新会话启动后发一条消息把它叫醒。桌面应用不一样（#319）：清空会话后，要等有提示词进来才会启动新会话，所以等待器自己叫不醒任何东西。在桌面应用里运行 `ready --wake`，会把桌面会话 id 记进便条，并改为打印「伙伴唤醒」的做法：清空之前，用宿主的 `create_scheduled_task` 建一个一次性定时任务，定在清空后几分钟触发；它的提示词调用 `send_message`，把接班指令发给这个会话 id。Keel 不会替你建任务。清空还会让 Remote Control 断开，所以这条消息要让醒来的会话先调用 `set_remote_control("self", true)`，`keel shift resume` 也会提醒这一步。无人值守时要做到这一点，需要把 `mcp__ccd_session_mgmt__set_remote_control` 加进 `permissions.allow`，否则宿主的自动模式会拒绝这次调用。清空本身也要把 `mcp__ccd_session_mgmt__clear_session` 加进去：否则清空会停在等批准，而 Remote Control 已关，人不在电脑前就批不了；唤醒消息会先到并排进队列，app 为了不抹掉它就会拒绝这次清空。

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
