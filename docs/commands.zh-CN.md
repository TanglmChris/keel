# Keel 的 slash 命令与技能

[English](commands.md) | **中文**

装了 Keel 插件的 Claude Code 会话里能输入哪些命令，以及每个命令实际运行什么。所有入口都带插件命名空间：`/keel:<名字>`。

## 命令

每个命令只负责安排某个 `keel` 命令行流程的步骤；实际工作由命令行完成，结论由门禁给出。

| 命令 | 运行 | 用途 |
|---|---|---|
| `/keel:context` | `keel context` | 查看状态、选中的任务、下一步，以及 Keel 版本和协议版本是否一致 |
| `/keel:start [change] [task]` | `keel gate task-start` | 开始一个任务：编译任务契约、记录指纹、开启写保护 |
| `/keel:done [change] [task]` | `keel gate task-complete` | 完成一个任务：记录证据、走 review checklist，再过门禁 |
| `/keel:chat` | `keel chat unread` | 读本角色的未读聊天，并处理发给它的内容 |
| `/keel:shift` | `keel shift check`、`keel shift ready --wake` | 给本会话换班：检查遗留事项、写交接便条、安排唤醒 |

这五个是 Claude Code 命令。Codex 插件只带技能、不带命令，所以在 Codex 上直接运行对应的 `keel` 命令行流程。

## 你可以手动调用的技能

| 技能 | 用途 |
|---|---|
| `/keel:align-expectations [change 或需求]` | 在 spec 和任务定稿前，对齐需求、隐含期望、验收标准和决策权 |
| `/keel:handoff [create、validate 或 clear]` | 在下一步无法推断时，写入、检查或清除可选的 `keel/HANDOFF.md` 指针 |

## 只由模型调用的技能

这些技能不出现在 slash 菜单里，由协议安排模型在固定节点调用：`debug-failure` 用在任务的命令或检查失败时，`review-checklist` 用在完成门禁，`tdd-or-test-first` 用在任务需要先有测试或证据的实现之前。在 Codex 上它们显示为 `keel:<名字>`。

## 已退役

- `keel docx` 和 Markdown 转 Word 的技能已在 5.202.0 退役（#464）：导出文档不属于 Keel 的职责。
- 5.202.0 之前技能名为 `keel-<名字>`。一个仓库的协议块会继续用旧名，直到下次运行 `keel --init`；协议块比正在运行的 Keel 旧时，`keel context` 会提示刷新。
- 不再生成 OpenSpec 自带的 `/opsx:*` 命令（#406）；仓库里残留的会被 `keel --init` 删除。它的工作流就是 `openspec-*` 这几个技能。
