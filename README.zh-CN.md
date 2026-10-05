# Keel

[English](README.md) | **中文**

> 面向 AI 编码 agent 的 OpenSpec 执行纪律 —— Claude Code、Codex、OpenCode 通用。

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Node](https://img.shields.io/badge/node-%3E%3D20.19.0-brightgreen.svg)
![Targets](https://img.shields.io/badge/targets-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenCode-blue.svg)

## Keel 是做什么的

[OpenSpec](https://github.com/fission-ai/openspec) 给项目一套 spec 驱动的工作流：proposal、
design、specs、tasks，以及记录改动的 archive。Claude Code（或 Codex）提供干活的 agent。
Keel 夹在两者中间，在 agent 走完一个 OpenSpec change 的过程中盯住它别跑偏。

放任不管时，agent 容易漂移：改了任务没提到的文件、上下文重置后丢了线索、或者没有证据就把活
勾成完成。Keel 加的是一层轻量、可校验的约束来防止这些，而且它尽量复用你已有的能力，而不是另造
一套。

Keel 加的东西：

- **无状态连续性**：`keel context` 每次会话都从 OpenSpec 和 Git 重算当前任务和下一步，所以工作
  能扛住 `/clear`、compaction 和冷启动，不依赖对话记忆。
- **确定性门禁**：`keel gate task-start | task-complete | change-close` 做本地结构检查，返回
  `pass` / `fail` / `needs-review` 和真实退出码。它们只检查任务契约和证据是否齐备，不判断设计对错。
- **写入守卫（Claude）**：`task-start` 之后，`PreToolUse` hook 会拒绝任何超出任务声明改动范围的
  文件编辑。
- **预期对齐**：在 specs 和 tasks 定稿前，Keel 把隐性假设摆出来，只针对真正会改变行为的那些提问。

Keel 尽量借力原生能力，而不是重造。spec 工作流就是原生 OpenSpec；执行技能、SessionStart 连续性
hook 和写入守卫 hook 都以一个普通的 Claude Code / Codex 插件分发。`keel --init` 只往你的 repo 里
写一小块宿主面：`AGENTS.md` bootstrap 块、OpenSpec schema，以及 `/opsx:*` 命令的 Keel overlay。

## 环境要求

Node.js `>=20.19.0`（内置的 OpenSpec CLI 需要）。

## 安装

**Claude Code** —— 装插件就够了。插件就是本仓库在发布 tag 上的那棵树，和 npm 发布的 `@christang/keel`
是同一份，技能和 hook 之外还带着 `keel` CLI；安装插件时 Claude 会按锁文件装好锁定版本的 OpenSpec。
agent 运行的 `keel` 就是插件带来的这一份：

```bash
claude plugin marketplace add TanglmChris/keel
claude plugin install keel@keel-marketplace
```

项目初始化后，更新会自己到来：`keel --init --target claude`（以及 `keel --install`）会在项目的
`.claude/settings.json` 里为 `keel-marketplace` 声明自动更新，Claude 先读这个声明，而不是它默认的"关闭"。
新版本会在会话发出第一条消息后在后台下载。从 5.89.0 起，正在运行的会话在下一次 hook 调用时就用上新版；
它的技能和 agent 要在 `/reload-plugins` 或下次启动后才更新。

想一次更新整台机器——全局 CLI、Claude 插件和 Codex 插件——就运行 `keel --update`。它为每个组件输出一行：
变了什么、何时生效、还剩什么要你做；细节和各宿主对运行中会话的行为见 [docs/updating.md](docs/updating.md)。
不想自动更新，就把那一项的 `autoUpdate` 设为 `false`；项目写明的值 Keel 会保留，`keel --doctor` 会报告当前声明的是哪一个。

Anthropic 的插件目录里，Keel 以 `keel-openspec` 列出。每次发版都会把 npm 包的文件（清单改名、带图标）提交到
`claude-directory` 分支，目录跟踪这个分支。从本 marketplace 安装的插件仍叫 `keel`。

**Codex，以及你自己的终端** —— 另外装一份 CLI（同时装上捆绑的 OpenSpec CLI）：

```bash
npm install -g @christang/keel
keel --version
codex plugin add keel@<marketplace>        # Codex
```

全局装的 `keel` 在 PATH 里排在插件那份前面，所以在 Claude Code 里 agent 会用它。要么让它和插件同版本，
要么卸掉（`npm rm -g @christang/keel`）；两者版本不一致时，会话启动那一行会指出来。

> 捆绑的 OpenSpec 依赖在安装时会打印一行 opt-in 的 shell 补全提示。如果你的 npm 拦截安装脚本，
> 这行提示会被跳过，它纯属装饰，keel 照常工作。

<details>
<summary>从 GitHub 安装最新未发布版本</summary>

打包当前 `main` 并安装该 tarball（跳过 npm registry）：

**Windows（PowerShell）：**

```powershell
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
npm pack github:TanglmChris/keel --pack-destination $tmp
$pkg = Get-ChildItem $tmp -Filter "christang-keel-*.tgz" | Select-Object -First 1
npm install -g $pkg.FullName
Remove-Item -Recurse -Force $tmp
```

**Linux / macOS：**

```bash
tmp_dir="$(mktemp -d)"
npm pack github:TanglmChris/keel --pack-destination "$tmp_dir"
npm install -g "$tmp_dir"/christang-keel-*.tgz
rm -rf "$tmp_dir"
```
</details>

## 怎么用

在项目根目录，先设置一次：

```bash
keel --init                 # 默认 target：claude
keel --init --target codex  # 或 opencode
```

`keel --init` 会跑 OpenSpec 初始化/更新，并写入 Keel 的宿主面。之后每次开始或恢复工作：

```bash
keel context                # 现在该做什么，从 OpenSpec + Git 重算
keel --doctor               # 检查各部分是否就位
```

更新 OpenSpec 生成的模板正文时，运行 `keel openspec update`。更新成功后，Keel 会为仓库
中所有已安装的 target 恢复 overlay。`keel --doctor` 也会逐项报告其他已安装 target 的
overlay 状态，避免 Claude 检查正常时漏掉 Codex 的缺失。

是否使用 subagent 由模型选择，仍须遵守宿主政策。运行
`keel project --event subagent-start --change <change> --task <id>` 可生成只读 helper
brief，无须额外激活许可。加 `--subagent-mode implementation` 可生成实现委派 brief，
要求当前任务为 implementation，且有效 guard 匹配任务、指纹和 Touch；`delegation.tier`
只是可选能力元数据。主 agent 审查返回结果、独立重跑验证并负责完成判定。CLI 只生成
brief，不启动 agent，也不证明 hook 实际执行；native goal 仍须明确授权激活。

spec 相关的活走 OpenSpec 的命令（`/opsx:propose`、`/opsx:apply`、`/opsx:sync`、`/opsx:archive`），
Keel 的门禁在任务边界处运行。整个回路：

```
keel --init  →  keel context  →  /opsx:apply（选一个 task）
   →  task-start（+ 写入守卫）  →  实现并验证
   →  task-complete  →  /opsx:sync · /opsx:archive
```

### Full / Lite

**Full 模式**（上面的 OpenSpec 流程）用于新功能、接口或协议变更、跨模块，或超过约 3 文件 / 100 行
的改动。被接受的原生 `plan mode` 产物只是会话态：其中影响 scope、完成定义或执行边界的决策，必须
在实现前固化到 `proposal/design/specs/tasks`，session plan 本身不是执行权威。

**Lite 模式**用于局部小改：单点修复、小脚本、文档或补测试，不改接口、影响可局部证明；Lite 默认不
写 OpenSpec 状态。

## 这些命令，agent 是怎么用起来的

下面这些命令你几乎不用手敲。Keel 的意义在于纪律会自己跑起来：`keel --init` 把它装进 agent 的
工作流，agent 会在恰当的时刻去调用每一条命令。让这件事成立的有三样东西。

- **协议**：`keel --init` 会往你 repo 的 `AGENTS.md` 写一段 bootstrap 块（在 Claude 上由
  `CLAUDE.md` 引入）。它把 agent 要遵守的规则讲清楚：每次会话先跑 `keel context`、在任务边界处过
  门禁、只在任务声明的写入范围内改文件。这就是 agent 知道**何时**用哪条命令的来源。
- **技能**：`keel-*` 执行技能和 `/opsx:*` 命令 overlay 带着 agent 走「对齐 → apply → review →
  完成」，每一步按需调用门禁。
- **hook**：SessionStart hook 在会话打开的那一刻自动跑连续性投影；PreToolUse hook 在每次编辑时
  执行写入守卫。两者都不需要任何提示。

所以日常使用里你真正要敲的只有两条：装配时的 `keel --init`，以及想体检时的 `keel --doctor`。
下面列出的，是 agent 替你使用的「命令词汇表」。

## 验证分层

Keel 把验证分成两层，让慢测试套件不再卡住你的 push：

- **快速内环检查（fast inner-loop）** —— 秒级，在本地 pre-push 和迭代时跑，挡住明显的破坏而无需等待。
- **全量门禁（full gate）** —— 完整或慢的套件（golden 字节确定性测试、跨平台运行），交给 CI 或
  `keel gate change-close`。

任务的 `Verify` 检查保持快；慢的或穷尽的那一层归全量门禁，不放在本地 pre-push。在 `keel/config.yaml`
里声明一次你的快检命令：

```yaml
fast_check: npm test -- --fast   # 你项目的秒级检查
```

然后按需装一个仓内快 pre-push：

```bash
keel --install --with-git-hooks   # 写 .githooks/pre-push，设 core.hooksPath（仅本仓）
keel --doctor                     # 报告 fast_check、pre-push hook、core.hooksPath
keel --uninstall                  # 当 core.hooksPath 由 Keel 设置时回退
```

`--with-git-hooks` 是显式 opt-in：普通 `keel --install` 绝不碰 git config，且这个覆盖仅限本仓、可逆。

## 外部模型 CLI

会话可以把活交给外部模型 CLI 当委派对象，比如 codex、DeepSeek Harness 的 `dsh`，或你自己注册的。
调不调由模型自己判断；Keel 只提供调用接口、门控，以及大家踩过的坑。宿主自带的 subagent 不归 Keel 管，
模型自己更懂。

```bash
keel agents                      # 事实目录：可执行文件在哪、本项目是否允许
keel agents codex                # 命令模板、沙箱、数据发往哪里、带日期的坑
keel agents brief codex --mode helper --dir . --out /tmp/brief.md --change <c> --task <t>
```

`keel agents brief` 编译的就是 `keel project --event subagent-start` 给出的那份任务说明，写成文件，
再打印要跑的命令；这条命令会把 agent 的退出码写进结果旁边的 `.exit` 文件。**Keel 不启动任何进程**：命令由会话自己跑，对方交回的结果要由会话复跑每个检查后才算证据。
以下情况会被拒绝：

- 项目没允许的 agent（没写声明就一个都不允许）；
- 任务要读或要改的路径命中了禁止外发的清单；
- 在会话自己的 checkout 里做会写入的调用。宿主的写入守卫看不到外部进程，所以实现类任务，以及没有只读
  沙箱的 CLI（如 `dsh`）即使只做评审，都要用 `git worktree add` 建的独立 worktree。

```yaml
external_agents:
  allow:
    - codex
  egress_deny:
    - secrets/**: 受 NDA 约束的厂商密钥
```

事实目录只记事实：命令模板、沙箱、数据去向，以及每条都带日期和出处的坑；不写「擅长什么」，因为这种评价
常驻在会话里会左右主 agent 的判断，换个模型版本就过时。哪些活适合交出去由你自己写。工具路径属于本机事实：
`~/.keel/agents.json` 可以新增 agent 或覆盖某个字段，比如 `{"agents": {"dsh": {"executable": "/path/to/dsh"}}}`。
Keel 看不到对方在任务说明之外还读了什么，所以 `egress_deny` 防的是主动交出去的内容，管不住对方自己能打开的文件。

## 会话之间的群聊

在同一个仓库里干活的各个会话——Claude Code、Codex、无人值守的执行器，还有你——用 `keel chat` 组成一个工作群：
- 群成员可以增删维护；
- 消息可以 @ 某个角色，也可以 @all；
- 可以挂轻量待办，并关联 issue；
- 每个成员有各自的未读状态，历史全部保留。

只有被 @、分到待办或收到私聊时才会唤醒 Claude 会话，其余消息等下一次对话时再提示。消息只是另一个 agent 发来的数据，不代表授权。

Codex 自己不会在闲着时醒来，可以在它的 worktree 里运行 `keel chat wake add`：在声明了 `chat-reply` 的群里，每条找它的消息启动一轮，接着同一个会自动压缩的线程，没人找时什么都不跑（#203）。其他宿主依靠下一次对话时的提醒，不要让模型定期检查群聊。确实需要定时检查时，先用 `keel chat notice --check` 把关，每次运行都开新线程；让会话加入群聊时，也要明确告诉它不要设置定时或循环检查（#194）。

每台电脑配一个 Slack App、跑一个桥接程序，同一批群就能实时连到其他电脑上的会话和你的手机；某个角色也可以有自己的 Slack App，这样在 Slack 里能直接 @ 它、和它私聊。聊天记录同时存在孤儿分支 `keel-chat` 上，不受 Slack 保留期限制。配置方法见 [Slack 配置说明](docs/chat-slack-setup.zh-CN.md)。5.83 的 `keel mail` 命令继续可用，消息存在私聊群里。

## 命令参考

```bash
# 连续性 —— 无状态重算「现在该做什么」
keel context [--json] [--change <c> --task <t>]

# 确定性门禁 → pass | fail | needs-review
keel gate task-start    --change <c> --task <t> --json
keel gate task-complete --change <c> --task <t> [--base <git-ref>] --json
keel gate change-close  --change <c> --action sync|archive --json

# 写入守卫（Claude target）
keel guard start --change <c> --task <t> --json
keel guard status --json
keel guard clear  --json

# 一次性原生投影（只读视图，永不是权威）
keel project tasks --target claude [--change <c>] [--json]
keel project --target codex --event compaction --json

# 会话之间的群聊（接 Slack 见 docs/chat-slack-setup.zh-CN.md）
keel chat role --set <角色> [--alias <简写>]
keel chat group create <群> [--member <角色>]... | add | remove | archive | list
keel chat <群> [<消息>] [--since 2h] [--follow]     # 查看，或发言
keel chat dm <角色> <消息> | todo <群> --assignee <角色> <内容> | todos [--mine]
keel chat unread | read | notice | search <文本>
keel chat bridge add | install | status | pause <2h> | stop | start | uninstall
keel chat archive sync | pull

# 外部模型 CLI —— 事实目录，以及 Keel 编译的任务说明（Keel 不启动进程）
keel agents [name] [--json]
keel agents brief <name> --mode helper|implementation --dir <path> --out <file>

# 安装 / 维护
keel --init | --install | --check | --doctor | --uninstall  [--target <t>] [--dry-run]
keel --update [--dry-run]
keel --version | --help
```

退出码：`0` 通过 · `3` 策略失败 · `4` 缺少语义 review · `1` 输入/解析故障。

能力按可观察证据探测，不按 target 名字假定：无法验证的运行时行为报告为 `manual`，而非 `enforced`。
一个 repo 固定一个 target，后续 `--install` / `--check` / `--doctor` / `--uninstall` 都用它。

### 写入守卫

Touch 是唯一写权限来源。通过的 `keel gate task-start` 默认写入一次性守卫 manifest
（`keel guard start` 显式激活、`keel guard clear` 停止执法、`--no-guard` 退出默认激活）。守卫
激活时，`PreToolUse` hook 确定性拒绝 Touch 之外的文件编辑，并给出精确路径和恢复命令：

- manifest 记录 change/task、capsule 指纹、规范化 Touch 和权威文件哈希，存于 `guard.json`，
  fail-closed：损坏、哈希漂移、指纹不匹配或 task 已勾选时一律拒绝。
- 守卫只覆盖文件编辑工具；`Bash` 等间接写入仍受纪律约束，仓库外的临时路径直接放行。

### 一次性投影

`keel project tasks --target claude` 把选中 change 的 tasks.md 编译成只读清单视图，由当前 agent
自行决定是否手动镜像到宿主任务 UI，只读、不落盘、无同步循环。compaction 后可手动重注入：
`keel project --target codex --event compaction --json`。

## 对齐与技能纪律

- **`keel-align-expectations`**：specs/tasks 定稿前用风险触发的 deep alignment（一次一个决策、给
  推荐答案）对齐隐性假设，而不是对所有 Full change 强制问卷；先查仓库事实再问用户，接受的结论写回
  `proposal/design/specs/tasks`。
- **可插拔领域透镜**：keel 核心只保留机制，透镜内容由用户自己写在仓库的 `keel/lenses/*.md`。每份透镜
  自描述——开头一行 `Applies when:` 声明触发信号，并含一节 `Execution and review checks`。当变更
  artifacts 或 Touch 扩展名匹配某份透镜的 `Applies when:` 时，`keel-align-expectations`、
  `keel-tdd-or-test-first`、`keel-debug-failure`、`keel-review-checklist` 按需只加载匹配的那一份，
  没有匹配就不加载。`keel lenses list` 查看内置模板与已安装透镜；`keel lenses add web` 把内置模板
  （web / hardware / hardware-dsl，随包放在 `assets/lenses/`）落到 `keel/lenses/` 后自行改写，
  已存在时需 `--force` 才覆盖。
- **专门技能政策**：新增或实质扩展技能前，先研究 first-party 或其他 authoritative source 并记录
  provenance/license；用真实的 should-trigger 与近邻 `should-not-trigger` 用例验证 description，
  并至少通过一个 real task；以 `src/skills/<name>/SKILL.md` 为唯一可移植权威，target metadata 只是
  附加适配，discovery 与激活由 target-native runtime 负责。

`/opsx:sync`、`/opsx:archive` 的完成门禁由 `keel gate change-close` 加 `keel-review-checklist`
承担，不再由运行时 hook 执行（在所有 target 上能力为 `manual`）。

## 开发

无构建步骤。`src/skills/` 是可移植技能的唯一维护源，`plugins/keel/skills/` 等分发副本必须与源
字节一致（由校验强制）。

```bash
npm test          # 一条 validate_plugin.py --all 调用：baseline + 全部场景并行（--jobs N 控制并发）
node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates   # 单场景调试
node scripts/bump_version.js <patch|minor|major>                             # 一次改齐所有版本 pin
```

## 隐私

Keel 不运行服务器，自身不收集任何数据。[PRIVACY.md](PRIVACY.md) 列出它在本机存什么、什么会离开本机，
包括内置 OpenSpec CLI 的遥测及关闭方法。

## License

[MIT](LICENSE) © 2026 TanglmChris · 版本历史见 [keel/CHANGELOG.md](keel/CHANGELOG.md)。
