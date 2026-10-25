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
勾成完成。Keel 加的是一层轻量、可校验的约束来防止这些，而且它建立在你已有的工具之上，而不是
替换它们。

Keel 加的东西：

- **无状态连续性**：`keel context` 每次会话都从 OpenSpec 和 Git 重算当前任务和下一步，所以工作
  能扛住 `/clear`、compaction 和冷启动，不依赖对话记忆。
- **确定性门禁**：`keel gate task-start | task-complete | change-close` 做本地结构检查，返回
  `pass` / `fail` / `needs-review`，并带真实的进程退出状态。它们只检查任务契约和证据是否齐备，不判断设计对错。
- **写入守卫（Claude）**：`task-start` 之后，`PreToolUse` hook 会拒绝任何超出任务声明改动范围的
  文件编辑。声明了 `push:<branch glob>` 时，它还会拒绝推到其他分支的 `git push`，有没有 task 都一样。
- **预期对齐**：在 specs 和 tasks 定稿前，Keel 把隐性假设摆出来，只针对真正会改变行为的那些提问。

Keel 尽量借力原生能力，而不是重造。spec 工作流就是原生 OpenSpec；执行技能、SessionStart 连续性
hook 和写入守卫 hook 都以一个普通的 Claude Code / Codex 插件分发。除了运行 OpenSpec 自己的 init，
`keel --init` 还往你的 repo 里写一小块宿主面：`AGENTS.md` bootstrap 块、OpenSpec schema、
OpenSpec 工作流 skill 上的 overlay，以及在 Claude 上写入 `.claude/settings.json` 的插件自动更新条目。

## 环境要求

Node.js `>=20.19.0`（内置的 OpenSpec CLI 需要）。

## 安装

**Claude Code** —— 装插件就够了。插件就是发布版本的 npm 包 `@christang/keel`，和 `keel` CLI 来自同一个包，
所以技能和 hook 之外还带着 CLI；安装插件时 Claude 会按锁文件装好锁定版本的 OpenSpec（#337）。
agent 运行的 `keel` 命令用的就是插件带来的这一份：

```bash
claude plugin marketplace add TanglmChris/keel
claude plugin install keel@keel-marketplace
```

插件用你的 npm 客户端获取；只有 marketplace 清单 `.claude-plugin/marketplace.json` 从 GitHub 读取。
如果某台机器 clone GitHub 失败（SSH host key、代理等），可以改为用 `url` 类型的 marketplace 来源、通过 HTTPS 读取清单：

```bash
claude plugin marketplace add https://raw.githubusercontent.com/TanglmChris/keel/main/.claude-plugin/marketplace.json
```

或者在 `~/.claude/settings.json` 里声明：

```json
"extraKnownMarketplaces": {
  "keel-marketplace": {
    "source": {
      "source": "url",
      "url": "https://raw.githubusercontent.com/TanglmChris/keel/main/.claude-plugin/marketplace.json"
    }
  }
}
```

Claude Code 目前还不支持从 npm 包加载 marketplace（其参考文档把这种来源列为尚未实现），所以清单本身还不能也从 npm 来。

项目设置好之后，更新会自己到来：`keel --init --target claude`（以及 `keel --install`）会在项目的
`.claude/settings.json` 里为 `keel-marketplace` 声明自动更新，Claude 会先读这个声明，再考虑它自己默认的"关闭"。
新版本会在会话发出第一条消息后在后台下载。从 5.89.0 起，正在运行的会话的 hook 在下一次调用时就用上新版；
它的技能要在 `/reload-plugins` 之后或下次启动时才跟上。

想一次更新整台机器——全局 CLI、Claude 插件和 Codex 插件——就运行 `keel --update`。它为每个组件输出一行：
变了什么、何时生效、还剩什么要你做；细节以及各宿主对运行中会话的处理见 [docs/updating.md](docs/updating.md)。
不想自动更新，就把那一项的 `autoUpdate` 设为 `false`；项目写明的值 Keel 会保留，`keel --doctor` 会报告当前声明的是哪一个。

Anthropic 的插件目录里，Keel 以 `keel-openspec` 列出。每次发版都会把 npm 包的文件（清单改名、加上图标）提交到
`claude-directory` 分支，目录跟踪的就是这个分支。从本 marketplace 安装的插件仍叫 `keel`。

**Codex，以及你自己的终端** —— 另外装一份 CLI（同时装上捆绑的 OpenSpec CLI）：

```bash
npm install -g @christang/keel
keel --version
codex plugin marketplace add TanglmChris/keel --ref main --sparse .agents/plugins --sparse plugins/keel
codex plugin add keel@keel-marketplace     # Codex
```

`--sparse` 路径让 Codex 只拉插件本身，而不是整个仓库；网络慢时，整仓克隆可能超过 Codex 的 30 秒上限。

在 Codex 上，用 CLI 里的 `/hooks` 审阅当前的 hook 定义；安装本身不会授予 hook 信任。运行中的 Codex
会话在下一次 hook 调用时就用上更新后的插件，而改动了 hook 定义的版本需要再审阅一次。
用 `keel mail role --set codex-maint` 绑定一个邮箱角色；受信任的 hook 会在会话启动和下一次用户输入时
提示未读邮件，但不会把它标为已读。如果收件 hook 不可用，就显式使用 `keel mail list` 和 `keel mail read`。
Codex 闲着时不会自己醒来；在它的 worktree 里运行 `keel chat wake add`，有找它的消息到达时就会启动一轮（#203）。
原生的写入守卫执行仍未经验证。
版本、运行时证据、局限以及干净消费方上的 Full 模式检查，见 [Codex 验收记录](docs/codex-validation.md)。

全局装的 `keel` 在 PATH 里排在插件那份前面，所以在 Claude Code 里 agent 会运行它。要么让它和插件同版本，
要么卸掉（`npm rm -g @christang/keel`）；两者版本不一致时，会话启动那一行会指出来。

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

要刷新 OpenSpec 生成的模板，运行 `keel openspec update`。更新成功后，Keel 会为仓库
中所有已安装的 target 恢复 overlay。`keel --doctor` 也会报告其他已安装 target 的
overlay 状态，所以 Claude 一侧正常不会掩盖 Codex overlay 的缺失。

用不用 subagent 由模型自己决定，subagent 与主 agent 同等对待：门禁、`Touch` 写入守卫
和证据规则适用于执行该步骤的任何一方。Keel 在 subagent 动手前不要求 brief、额外激活或另一个
agent 复跑，也不引导模型去用或不用它（#414）。

spec 相关的活走 OpenSpec 的工作流 skill（`openspec-propose`、`openspec-apply-change`、`openspec-sync-specs`、
`openspec-archive-change`）；Keel 只生成 skill，不生成 OpenSpec 斜杠命令（#406）。Keel 自己的命令和可以手动调用的技能列在
[docs/commands.zh-CN.md](docs/commands.zh-CN.md)。Keel 的门禁在任务边界处运行。整个回路：

```
keel --init  →  keel context  →  openspec-apply-change（按顺序做 task）
   →  task-start（+ 写入守卫）  →  实现并验证
   →  task-complete  →  openspec-sync-specs · openspec-archive-change
```

在 Claude target 上，session-start hook 还会把这个状态展示给**你**，而不只是给 agent——在你输入任何内容
之前，显示一行：

```
Keel: add-user-auth#2.1 — next: task-start. Disposable projection; OpenSpec and Git are the authority.
```

设置 `KEEL_SESSION_PANEL=1` 可改为画成带 Keel 标志的边框面板。它默认关闭，打开后只改变呈现方式——
两种形式里的状态和下一条命令完全相同。

宿主的 hook 没有报告的 compaction 之后，可以用 `keel project --target <t> --event compaction --json` 手动重新投影同样的状态。

写入守卫是一份一次性 manifest：`keel/guard.json`。在 Claude 上，通过的 `task-start` 会写入它（`--no-guard` 退出）；
`keel guard start` 显式写入，`keel guard clear` 删除。它记录 change 与 task、capsule 指纹、规范化后的 `Touch`
和权威文件的哈希，并且失败即关闭：Keel 读不了的 manifest 会拒绝编辑，而不是放行。守卫检查文件编辑工具；
`Bash` 命令造成的写入不检查，只有声明了 `push:` 范围时会检查 `git push`。

### 常设授权

对于没有授权依据的仓库操作，Keel 会先问；下次会话还会再问，因为对话里给的许可熬不过上下文重置。
改为在 `keel/config.yaml` 里一次性声明：

```yaml
authorize:          # accepted names: commit, push, push:<branch glob>[@<role>], release, archive, continuation, issue:<owner>/<repo>[@<role>], protocol-refresh, chat-reply:<group>[@<role>], issue-close:<owner>/<repo>[@<role>], cleanup:scratch[@<role>], push-protected:<branch glob>[@<role>], shift-restore, self-shift
  - commit
  - push
```

没有自己写 `Autonomy boundary:` 的 task 会继承这份声明，编译出的 capsule 会把 `keel/config.yaml`
标为该条目的来源，这样继承来的授权永远不会被误当成 task 自己做的决定。自己写了边界的 task 保留自己的边界。

下文的序数按名字计，不按上面注释里的写法计：`push` 和 `push:<branch glob>` 是同一个名字，所以词汇共 13 个名字，
`continuation` 是第五个。

`continuation`（第五个名字）会被接受，但什么都不改变。在你批准过 `tasks.md` 的同一个 change 里，
从一个已持久完成的 task 转到下一个未勾选的 task，默认就不需要确认（#414）。下一个 task 照样通过
`keel gate task-start` 启动、记录自己的 fingerprint；每个门禁、证据要求、语义 Review 和写入守卫都照常运行；
有自身触发条件的停止——阻塞、fingerprint 漂移、超出范围的需要、未解决的问题——照样停下。继续做下去不授权任何
仓库操作，也不调度任何东西。在词汇表早于这个词的旧版 Keel 上，这一条目无法识别，整份声明在改正之前不授权
任何东西——失败即关闭，绝不会悄悄放行。

`issue:<owner>/<repo>`（第六个名字）要写明它能触及的资源，不写就被拒绝；`chat-reply:<group>`（第八个）、
`issue-close:<owner>/<repo>` 和 `cleanup:scratch`（第九、第十个），以及 `push-protected:<branch glob>`（第十一个）
也同样要写。其余名字作用于声明所在的 checkout，所以天然被限定在你声明它的那个仓库里。开 issue 用的凭据却不是：
`gh` 是账号级的，一个裸的 `issue` 能触及你账号能碰到的每个仓库——悄无声息地成为文件里范围最大的条目，比 `push`
还大。写明仓库，授权的大小就和它字面说的一致。Keel 把这个范围带到 `keel --doctor` 和编译出的 capsule 里，
**但不强制执行**：它不调用任何 tracker 客户端，也观察不到它，正如它从不替你提交一样。关闭 issue 是另一个名字，
`issue-close:<owner>/<repo>`（#257）：由自动化 token 完成的合并不会触发 `Closes #<n>`，所以做完工作的会话要
自己关闭 issue，并附一条评论写明解决它的 pull request。Keel 以同样方式携带这个范围，同样不强制执行。

`push:<branch glob>` 把 `push` 收窄到会话可以推送的分支（#257）——例如在只有协调者推 `main` 的仓库里写
`push:claude/*` 和 `push:worktree-*`。每个 glob 一条；`*` 在一个 `/` 段内匹配，`**` 跨段匹配。和其他所有
范围不同，这一个是强制执行的：只要声明了任何 `push:` glob，Claude 写入守卫就会检查每个 `Bash` 调用里跑的
`git push`，有没有 task 都一样；推到其他分支的，或者看不出目标的——`--all`、`--mirror`、`--tags`、shell 变量、
没有配置推送目的地——一律拒绝，并提示改用 `git push origin <branch>`。同时带上附注 tag 的推送——`--follow-tags`，
或 git config 里设了 `push.followTags`——算作 tag 推送（#327）：没有哪个 `push:` glob 允许它，所以会被拒绝并
提示 `--no-follow-tags`；除非它推送的每个分支都是 `push-protected`，那样就像任何受保护推送一样被询问。裸的
`push` 保持原来的含义，而把它和 `push:` glob 一起声明会被拒绝，因为它会悄悄放宽 glob。Codex 没有这样的 hook，
所以在那里这个范围只被携带，不被强制执行。

`push-protected:<branch glob>`（可带 `@<role>`）指定一个既不允许也不拒绝、而是要询问的分支（#280）：推到它时
Claude 写入守卫返回 `ask`，于是 Claude Code 请你确认这一条命令，下一次推送还会再问——Keel 不存储任何批准。
`push-protected:main@iecc-pm` 只让绑定到 `iecc-pm` 的会话得到询问；其他会话一律拒绝。无法保证会询问的权限模式
`bypassPermissions` 或 `dontAsk` 也被拒绝。声明它本身就会打开推送检查，而在它旁边写裸的 `push` 会被拒绝。

每个带范围的条目——`push:`、`issue:`、`issue-close:`、`cleanup:`、`chat-reply:` 和 `push-protected:`——都可以
以 `@<role>` 结尾，或用角色模式如 `@kaiwu-design-*`，其中 `*` 匹配任意一串角色字符（#378）。这样的条目只作用于
chat 角色与之匹配的会话。会话在 capsule、`keel context`、`keel --doctor` 和它的 chat-reply 群里读到属于自己
角色的授权，`keel --doctor` 还会为每个已绑定角色列出作用于它的带范围条目。推送时，Claude 写入守卫只通过会话自己
角色的条目放行分支，对另一个角色的条目所覆盖的分支则拒绝并写明那个角色。只要声明了任何推送条目，这个检查对每个
会话都保持开启，所以没有被任何条目点名的角色是受限的，而不是不受限。tracker、chat 和 scratchpad 范围仍然只被
携带、不被强制执行：角色只决定由哪个会话读到它们。

`shift-restore`（#319）涵盖 Claude 桌面应用上因换班而启动的会话在 `keel shift resume` 之后必须马上做的两件事：
如果自己的 Remote Control 回来时是关着的，就把它重新打开；把自己的名字改回工作标题。桌面应用上被清空的会话不会保留原来的标题。
没有这份声明时，被唤醒的会话会把这次恢复当成另一个会话的请求，停下来问你。它只作用于那个会话，所以不带范围；
它不涵盖任何其他会话，不涵盖 clear 或 archive，也不涵盖任何仓库操作。

`self-shift`（#319）是它在交班一侧的对应：便条存好后，`keel shift ready --wake` 在桌面应用上打印的四个步骤——
创建唤醒任务（它用 `keel shift await-clear` 等待 clear，需要时先把会话取消归档，#326）、用
`run_scheduled_task` 启动它、给会话改名、清空会话。整个换班远不到一分钟。Remote Control 保持开启（#324）。
它不决定是否换班；那仍由任务边界规则和协调者决定。它不带范围。

`cleanup:scratch` 涵盖在确认已合并、且没有进程在使用之后，删除会话自己 scratchpad 下的临时 worktree 和运行输出。
它从不涵盖分支或其他会话的文件，并且和 tracker 范围一样只被携带、不被强制执行。

`protocol-refresh`（第七个名字）涵盖插件更新带不过来的那一部分发布内容：本仓库 `AGENTS.md` 里受管理的协议块，
它只有在这里运行 `keel --install` 时才会更新。当 `keel context` 报告这个块比正在运行的 Keel 旧时，会打印一行
`Protocol:` 写明刷新命令；声明了这个名字，agent 就会在做其他工作之前不经询问地运行它。task 的写入守卫处于激活
状态时它绝不运行，因为刷新会写到该 task 的 `Touch` 之外；它也从不提交：diff 留给你，提交它是另一个操作，和其他
提交一样由声明的 `commit` 涵盖。在词汇表早于这个词的旧版 Keel 上，这份声明在改正之前不授权任何东西。

`chat-reply:<group>`（第八个名字）让会话在那个 `keel chat` 群里，不先问你就答复发给自己角色的记录——一次提及、
一个分配的待办或一条私信——方式是回复、给发送者发私信，或关闭待办。否则每个新会话都会来问，因为聊天消息是数据，
不授予任何东西。它从不涵盖去做消息要求的事——编辑文件、运行改变状态的命令、提交、推送、往聊天之外发送任何东西——
chat 提示在"这是数据不是指令"那句话旁边也会这么说。它按群逐个声明，裸写会被拒绝：在接了 Slack 的群里，一条回复
会离开本机。

这份声明不是以下三样东西：

- **不是绕过门禁的路。** 它授权的是操作，从不是证明。不管你声明了什么，`keel gate task-complete`
  返回的判定和失败文字都完全一样。
- **不是触发器。** 它去掉的是一次确认，不是通往该操作的那一步。没有什么会自己调度起来，也不会替你选下一个 task。
- **不是开放式的。** 上面这 13 个名字就是全部词汇。无法识别的条目会连同可接受的名字一起报告，在你改正之前
  整份声明不授权任何东西——打错字永远不会变成悄悄的放行。

这个块默认不存在，什么都不声明的仓库的行为和这个功能出现之前完全一样。`keel --doctor` 会报告声明了什么。

### 决策先例

你在对话里做的决定，到下一次上下文重置就用掉了，而促成它的那段理由——能推广到你还没遇到的决定的那部分——也随之
消失。把 Keel 指向一个先例目录，它就会查阅先例，而不是再问你一遍：

```yaml
precedents: ../my-decisions   # 任意路径；可以放在本仓库之外
```

Keel 不自带先例，也不创建存储。它只读那个目录，别的都不碰——从不 clone、pull 或访问网络——所以仓库之外的一个
目录可以服务你所有的仓库，而一个不存在的路径，效果和根本没有声明完全一样。

每个先例是一个 markdown 文件，带一个 `Applies when:` 头、它所属的重要性类别、`recorded` 或 `authorized`
状态、决定本身，以及**理由**。最后一项是承重的：*"选了 A"* 只适用于字面记录的那个情形，而 *"选了 A，因为 B
离线时会失败"* 可以用到没人见过的情形上——也能在新情形是在线时被认出不适用。没有理由的先例会被报告为不完整，
永远不会被应用。

使用它们有三条规则：

- **先例恰在替代了一个问题的地方被引用。** 如果应用它意味着你没被问到本该问你的事，回复里会写明它。例行决定
  不引用，所以一次引用总是标记一个替你做的决定。
- **只有你能提升先例。** 先例以 `recorded` 进入，在问题照问的同时作为推荐提出。只有当你接受了向你提出的提升，
  它才变成 `authorized`——绝不靠使用次数，那样会在无人看着时越过界线。
- **先例回答的是重复出现的问题；它从不重新归类。** 它可以在自己的类别内缩短一个决定，但不能把一个决定移出
  必须问你的那些类别，先例积累得再多，也不会让某个类别不再重要。

和常设授权一样，先例为决定提供依据，从不替代证明：门禁、证据、review 和写入守卫都不受存储里任何东西的影响。
会话启动那一行只报告存储的规模和新旧——先例正文只在真正要做决定时才加载。

### 无人值守运行

一个循环最后需要的，是*开始*的许可。声明哪些 issue 可以不经询问就开工：

```yaml
triage:             # 两种来源任一都可准入；不写则什么都不准入
  labels:           # issue 带的标签
    - auto
  issues:           # issue 编号，声明在这里而不是 issue 上
    - 62
```

直接写在 `triage:` 下的裸列表仍表示标签，所以在第二种来源出现之前写的声明，含义完全不变。

```bash
gh issue view 42 --json labels,number \
  --jq '"--labels \([.labels[].name]|join(",")) --issue \(.number)"' \
  | xargs keel triage
```

**Keel 从不获取 issue。** 你把 `gh` 返回的内容传进去，评估保持本地、离线、确定——正是这些性质让 Keel 的其他
每个回答值得信任。`--labels` / `--issue` 至少要给一个；两个都不给，等于要求它去获取。Keel 无法完整读懂的
`triage:` 块什么都不准入，并写明出错的条目——准入能读懂的那一半，就等于准入了你打错字那一条旁边的条目。

**两种来源的单位都是一个 issue。** 一个人贴标签或敲编号，都是针对某一个具体的 issue，所以这套策略准入的是你
一个一个挑选出来的集合——而不是去猜哪些 issue 看起来简单，那恰恰是不该自动化的判断。

它们的区别在于**你的决定记在哪里**，这也是两者都存在的原因：

- **标签**把它记在 issue 上。在 issue 来自别人的仓库里，这意味着一个运维开关落在了你让报告者用来分类的词汇里，
  提交 issue 的人看得见也改得了。Keel 也无法确认是人贴的标签；如果你的自动化能给 issue 打标签，这个来源比
  看上去更宽。
- **issue 编号**把它记在你自己的文件里。报告者看不到它，只有提交者能改，它会出现在 diff 里，而且你可以撤销
  一条而不动其他条目。

**准入只回答"可以开始吗"，之后的事一概不管。** 对齐照样上报每一个重要选择，每个门禁照样运行，写入守卫照样约束。
具体来说：

- 无人值守运行**可以** triage、编写、实现、验证、在 `authorize:` 允许的地方推送，并**开 pull request**。
- 它**不可以合并**。合并是未经审阅的决定变成你项目历史的那一刻，Keel 里没有任何声明能授权合并。
- 准入来自这份声明，**从不来自先例**，不管存储里积累了多少 triage 历史——一个 issue 是否变成工作，是一个
  要由你明确委托的决定。

**Keel 不调度任何东西。** `/loop`、cron 和 CI 触发器属于你的运行时；Keel 负责的是让每一步都能有依据地做出
决定。唯一的例外是 `keel shift ready --wake`：一个一次性的等待者，在那个角色的下一个会话启动后写下一条唤醒记录，
然后退出——一个给自己换班的会话，没有别人来启动它。而一次在真正的决定处停下的运行，正是按设计结束的——
别为了让它不再停下而放宽策略。

### 谁来合并

Keel 从不让 agent 合并——无人值守运行开出 pull request 就停下。仓库仍然可以按自己的规则在没有人的情况下合并：
在必需状态检查之后的 GitHub 自动合并，或者一个合并已通过内容的 workflow job。Keel 自己的仓库用的是后者——
`.github/workflows/publish.yml` 里的 `land` job 在负责人的 pull request 的 head commit 通过 `full-gate` 之后
合并它，然后在同一次运行里发布并发版，不用任何存储的 secret。如果你的仓库会自己合并，就写明：

```yaml
merge: repository:full-gate
```

这样 `keel context` 会报告默认分支在 `full-gate` 通过时合并，并且**合并前没有人审阅**。不写的话，读你协议的人
会以为每个改动都有人看过，因为协议里关于合并只说了一句：agent 不可以合并。

`merge: human` 表达的是相反的意思。裸的 `repository` 会被拒绝——"没人审阅"只有写明了是什么取代了审阅者才算
诚实。它不是一项许可：`authorize:` 没有 `merge` 条目，也不该有。Keel 只读这份声明，从不读 GitHub，所以它无法
确认你的仓库真的那样合并；它报告的是你声明的内容。

### Full 与 Lite

**Full 模式**（上面的 OpenSpec 流程）用于新功能、接口或协议变更、跨模块工作，或超过约 3 个文件 / 100 行的改动。
**Lite 模式**用于局部修复、小脚本、文档，或不改接口、影响可局部证明的测试；Lite 不写 OpenSpec 状态。这条规则
写在 `keel --init` 安装的块里，因为路由是一次会话的第一个决定，而一条只能从这份 README 找到的规则，只有已经
主动去找的 agent 才找得到。

体量门槛是风险的代理指标，不是风险本身，有些仓库恰好相反：一份只追加的记录，其 schema 改动只是一个字段的 diff，
却可能是项目里风险最高的改动；而横跨二十个文件的机械改名，风险却最低。把这条经验法则判断错的路径声明出来，
每条附上它为什么判断错：

```yaml
full_mode_paths:
  - results/experiments.jsonl: 只追加；一个字段的 diff 无法回退
```

`keel context` 会报告声明了什么，这样例外会在做决定时出现，`keel --doctor` 则报告这份声明的健康状况。这里刻意
**没有反方向的键**：那个文件里的每一项声明都只去掉一次确认、从不去掉门禁，而一个把工作挡在流程*之外*的条目
会是第一个破坏这一点的。Keel 也不对任何路由决定设门禁——路由决定的是 change 是否存在，所以门禁没有可以绑定的
对象；Keel 做的是确保 agent 做决定时，规则和你的例外都摆在它面前。

被接受的原生 plan mode 计划只是会话态。其中影响 scope、完成定义或执行边界的决定，要在实现之前写进
proposal/design/specs/tasks；会话里的计划本身从来不是执行权威。

### agent 加载多少指导

Keel 的技能承载两类内容，它们的价值朝相反方向变化。*怎么做*——如何拆分 task、按什么顺序做事——执行者越强，
就越不重要。*让自己可被证伪*——先红后绿、检查预言的失败字面量、fingerprint、`Durable owner:` 引用是否真的
存在——反而越重要，因为强执行者产出的是自信的工作，而这些正是能反驳它的检查。

所以技能中按步骤指导的那一半放在它旁边的 `guidance.md` 里，仓库可以声明自己不需要那一半：

```yaml
executor_tier: high
```

默认是 `standard`，会读指导；缺失或拼错的声明也会读，所以一个没配置的仓库最坏也只是多付一次读取的代价。
`keel context` 和 `keel --doctor` 会报告这个等级。

**等级只影响指导，别的一概不动**——没有哪个门禁、准则、证据要求或 Review 随它变化。这不是这份 README 里的承诺：
指导文件会被检查，确保其中不含 Keel 用来陈述准则的任何词，所以等级永远只能跳过一个什么都不决定的文件。跳过
什么由声明决定、而不由 agent 自己判断，这是有意的——"我需要这份帮助吗？"恰恰是弱执行者最容易判断错的问题，
而它回答的还是关于它自己的问题。

目前只有一个技能带指导文件：`tdd-or-test-first`，一张按"什么会让 Acceptance 不成立"来挑选 Verify 策略的
表，附带正确和错误的选择，以及每种证据形式何时划算（#389）。其余四个技能几乎全是准则，拆开它们只会把必须
留下的那一半挪走。

## 这些命令，agent 是怎么用起来的

下面这些命令你几乎不用手敲。Keel 的意义在于纪律会自己跑起来：`keel --init` 把它装进 agent 自己的
工作流，agent 会在恰当的时刻去调用每一条命令。让这件事成立的有三样东西。

- **协议**：`keel --init` 会往你 repo 的 `AGENTS.md` 写一段 bootstrap 块（在 Claude 上由
  `CLAUDE.md` 引入）。它写明 agent 要遵守的规则：每次会话先跑 `keel context`、把工作路由到 Full 或 Lite、
  在任务边界处过门禁、只在任务声明的写入范围内改文件。这就是 agent 知道**何时**运行什么的来源。
- **技能**：`keel-*` 执行技能和 OpenSpec 工作流 skill 上的 overlay 带着 agent 走「对齐 → apply → review →
  完成」，每一步调用门禁。新增或实质扩展的技能，要从 authoritative source 研究并记录出处与许可证，
  用真实的 should-trigger 与 should-not-trigger 用例检验其 description，并至少通过一个 real task。
  `src/skills/<name>/SKILL.md` 是唯一可移植权威，target metadata 只是附加，发现与激活由 target-native 运行时负责。
- **hook**：SessionStart hook 在会话打开的那一刻自动跑连续性投影；PreToolUse hook 在每次编辑时
  执行写入守卫。两者都不需要任何提示。

所以日常使用里你要运行的只有两条：想检查接线时运行 `keel --doctor`，以及每当它告诉你仓库落后于安装版本时运行
`keel --install`——协议版本存在你的 `AGENTS.md` 里，更新软件包并不会让它跟着动。下面的一切，都是 agent 替你
使用的词汇。

### 当正确答案是"什么都没变"

重构、搬移、声称数字不变的流程升级——这类改动正确的证据是*零差异*，而先红后绿没有表达它的形状。报告这个问题的
仓库里，有个 task 的 `tasks.md` 好几次写着"这个没有诚实的红"，还为了凑形状重新记录了两次契约。准则本身是对的；
只是它没有地方安放。

```
- Verify:
  - Strategy: equivalence
  - Base: origin/main
  - Fields: wns, tns, cell_count
  - M1: node compare.js --base --head reports every field equal
```

`equivalence` 不欠红。它的准则是 base 和 head 在你点名的字段上一致，这比先红后绿*更强*——它还能抓住顺带改动了
某个结果的改动。门禁检查的是这种形状看似完整、实际什么都没比较的每一种情况：缺少 `Base:` 或 `Fields:`、字段集
为空、ref 解析不到任何东西，以及 `Base:` 解析到 HEAD。

它不是逃避先红后绿的出口。一个声明 `equivalence` 的 task，如果覆盖的是它所在 change *新增*的场景，就会被拒绝，
除非有一个兄弟 task 以先红后绿策略覆盖同一条目——新的行为不是不变的行为，一个 task 无法同时证明两者。

而且 Evidence 不必再复述输出：

```
- M1: artifact openspec/changes/<change>/evidence/compare.json sha256:9f2c…
```

门禁检查文件存在且摘要匹配，并拒绝 change 自身目录之外的路径，因为归档会移动那个目录，指针就会断掉。Keel 对
字节做哈希，不读里面的任何内容——声明仍然是你的，摘要换来的是：审阅者打开的文件，就是你指的那个文件。

## 验证分层

Keel 把验证分成两层，让慢测试套件永远不会卡住你的 push：

- **快速内环检查（fast inner-loop）** —— 秒级，在本地 pre-push 和迭代时跑，无需等待就能挡住明显的破坏。
- **全量门禁（full gate）** —— 完整或慢的套件（golden 字节确定性测试、跨平台运行），在 CI 或
  `keel gate change-close` 时跑。

任务的 `Verify` 检查保持快；慢的或穷尽的那一层归全量门禁，不放在本地 pre-push。在 `keel/config.yaml`
——也就是存放常设授权的同一个文件——里声明你的快检命令：

```yaml
fast_check: npm test -- --fast   # 你项目的秒级检查
```

然后按需启用仓内的快 pre-push：

```bash
keel --install --with-git-hooks   # 写 .githooks/pre-push，设 core.hooksPath（仅本仓）
keel --doctor                     # 报告 fast_check、pre-push hook、core.hooksPath
keel --uninstall                  # 当 core.hooksPath 由 Keel 设置时回退
```

`--with-git-hooks` 需要显式开启：普通的 `keel --install` 绝不碰 git config，且这个覆盖仅限本仓、可逆。

## 声明一次红证明了什么

先红后绿的纪律要求你写一个在实现出现之前就失败的检查，`keel gate task-complete` 会拒绝缺少 `M<n>.red`
Evidence 的 task。它以前查不到的是红*为什么*失败——因为夹具是空的而失败，或者因为 `PATH` 从没清理过而失败，
形状上都无可挑剔。

检查可以在末尾声明它的红必须呈现的失败：

```
- M1: `npm test -- --scenario widget` asserts the widget renders. Fails with: `widget is undefined`
```

完成时就要求检查的 `.red` Evidence 里出现那个字面量：

```
- M1.red: fail, for the right reason. The scenario reported `widget is undefined`.
```

这个子句位于检查文本之内，所以也在契约 fingerprint 之内。这正是关键：签名不能在观察到红之后再补上或改写而不
挪动锚点，这就是预言与转录的区别。Keel 不判断签名好不好——你可以声明一个任何失败都会打印的字符串——它只保证
是你先写下的，并且 review 看得见。

这个子句是可选的；不带它的检查行为与以前完全一样。在不可能有红的检查上声明——标了 `(regression)` 的检查，或者
任何红绿集合之外策略下的检查——会让 `task-start` 指名失败，而不是待在契约里什么也不做。没有给出字面量的
`Fails with:` 标记也一样。如果只是想在检查里*提到*这个标记而不是声明它，把它放进行内代码。

#### 红可以是诚实的，检查却依然免疫

签名预言的是**缺失**功能的红。它对**坏掉**的功能的红一无所知，而两者可能毫不相干。一个断言两个工具输出一致的
一致性检查，有真实的红、正确的签名、真实的绿——却在一个 1000 倍的单位错误下依然保持绿色，而那正是它存在的意义，
原因是它的容差带着一个默认的绝对下限。发现这种问题的唯一办法，是把缺陷放进去看着。

`Detects:` 声明的就是这种注入——变异，以及它必须产生的失败：

```
- M1: `pytest tests/test_fmax.py` asserts synth fmax == sta fmax. Fails with: `AttributeError` Detects: `sed -i s/0.0005/0.5/ run_sta.py` -> `assert 5e-16 == 5e-13`
```

完成时要求检查的 `.detects` Evidence 里出现第二个字面量。子句可以串联，所以一个检查可以同时带两者——上面的例子
是一个检查、一行。

**Keel 不运行变异，也不评判它。** 它记录这个声明，并把它放在 review 看得见的地方，与其他每个检查结果的地位相同。
你可以声明一个任何检查都能抓住的注入；这个子句换来的是：你在运行之前就做了决定，而事后修改它会挪动 fingerprint。

`(regression)` 检查**可以**声明一个，而且那是最合适的地方：这类检查从构造上就没有诚实的红，所以注入是唯一能
证明它不是空转的东西。

#### 一个数字可以自称是测量值

`Basis:`、Evidence 正文和 `Findings` 都是自由文本，其中的数字无论是测出来的、估出来的还是记出来的，读起来都一样。
`Measured:` 把一个数字绑定到它背后的输出：

```
- M1: `node bench.js` reports the fanout load. Measured: `1799.9`
```

完成时要求那个字面量出现在该检查自己的 `M<n>` Evidence 里——也就是记录命令及其输出的那一条。它需要主动开启，
而且刻意不做成管所有数字的规则：拿这个仓库的归档来量，那样的规则会波及 847 个行内代码片段，大多是版本字符串、
计数和不出现在任何命令输出里的引用，每一个都会是一次误停。

## 领域透镜

Keel 的核心是纯流程；它不带任何领域知识，也不带任何自己的决定。除了上面的先例存储，Keel 按需加载的另一个由用户
编写的面是领域指导，它住在你在仓库 `keel/lenses/*.md` 下编写的
**透镜（lens）** 里。每份透镜自描述：开头一行 `Applies when:` 写明触发它的信号（文件扩展名、artifact 形态），
并带一节 `Execution and review checks`。当一个 change 的 artifacts 或 Touch 匹配某份透镜时，对齐、测试、调试
和 review 技能会在下结论前读它——没有匹配时什么都不加载。也没有规则阻止技能去读它判断相关的另一份透镜。
Keel 保持领域无关；知识归你所有、由你编辑。

三份透镜以需要主动选用的模板形式随包提供（`web`、`hardware`、`hardware-dsl`），放在 `assets/lenses/` 下。
它们永远不会被自动安装：

```bash
keel lenses list            # 内置模板 + keel/lenses/ 里已安装的透镜
keel lenses add web         # 把 web 模板复制到 keel/lenses/web.md，然后自行编辑
keel lenses add web --force # 覆盖已有的透镜
```

## 覆盖声明拿什么来核对

`## Expectation Coverage` 用三种方式之一关闭每条预期，每一种都会被检查。`Durable owner:` 必须指向一个存在的
路径，或一个已经承载了其内容的 `https://…` 引用。`Discard reason:` 必须给出理由。而**引用了预期标识符的**
`Covered by:`，会与它所指 task 的 `Covers:` 进行比对：

```
- E3: the records land in different flow generations (F4, D3). Covered by: 1.1
```

`keel gate change-close` 检查 task 1.1 的 `Covers:` 是否真的写了 `F4` 和 `D3`。没写时，拒绝信息会说明这一点，
并说出那个标识符*在*哪里——本 change 中哪个 task 的 `Covers:` 含有它，或者没有任何 task 含有它。

**引用标识符是可选的。** 一条不引用任何标识符的条目不会被拒绝，也不会被报告为有缺陷；很多预期本就是散文
（"文档和技能跟随上述行为变更"），为了满足解析器给它们编号，比不编号更糟。检查要你兑现的，是你自己选择做出的
声明。为了不让一次通过被理解得超出它的实际含义，关闭时会报告比对了多少条目、多少条没有比对。

## 重新记录契约

在工作开始后修改 task 的契约会挪动它的 fingerprint，Keel 会报告旧契约下产出的证据已经过时。有时这太宽了——
给某个检查加一个分类标签并没有动它的断言，为此重跑一个三分钟的实验毫无收益。那就直说：

```bash
keel gate task-start --change <c> --task <t> --record --keep-evidence M1,M3
```

这样报告只会列出仍然过时的检查，列出你声明不受影响的那些，并说明这种收窄来自你的声明。**Keel 不验证这个声明**——
锚点保存的是之前的 fingerprint，而不是它背后的 capsule，所以它无法把检查以前的文本和现在的文本作比较。把你的
理由写在 task 的 `Reauthorizations` 行里，审阅者可以在那里提出异议。完成的要求没有任何改变：每个检查仍需要
自己的 Evidence。

当 Git 能说清变了什么时，漂移信息就会直接说出来（#342）。锚点会在摘要旁记录 Keel 版本——
`- Contract: keel-task-capsule/v1 sha256:<hex> (keel <version>)`——漂移时，Keel 会用正在运行的编译器，从记录
该锚点的那个 commit 编译 task 的源。如果那个 commit 能复现锚点，信息就会列出自那以后变化了的 capsule 字段。
如果不能复现，但锚点来自另一个 Keel 版本、且那个 commit 编译出的正是今天的 fingerprint，那么原因是编译器变了：
用 `task-start --record` 重新记录，证据照样成立，无需 `--keep-evidence` 声明。其他情况下不作任何断言。一个已勾选
的 task，如果自记录 commit 以来唯一的变化是继承自 `keel/config.yaml` 的常设授权，就不会让 `change-close` 失败；
它会在一条警告里被点名。

## 暂停一个 change

一个你有意停下的 change——在等仓库之外的某件事，或者只是眼下不是优先项——可以就地写明，写在它自己的
`openspec/changes/<name>/.openspec.yaml` 里：

```yaml
schema: keel-spec-driven
created: 2026-09-05
keel:
  status: paused
  reason: waiting on the competition brief; the priority is knowledge that needs no tooling
  since: 2026-09-05
```

这样 `keel context` 在推断下一步做什么时会跳过它，并说明跳过了哪个 change、为什么——一次你看不见的跳过，比它
所取代的错误推荐更糟。如果所有活跃的 change 都暂停了，`context` 会如实报告并附上各自的原因，而不是报告什么都
不存在。

这只改变 Keel *推荐*什么。门禁、写入守卫和完成，行为都和没有它时完全一样，`keel context --change <paused>`
仍然会选中它——你是点名要它的。Keel 从不自己暂停一个 change。

## 归其他 worktree 所有的 change

当多个会话共用一个仓库、各自在自己的 worktree 里时，别处正在进行的 change 不决定你这个会话的状态（#241）。
`keel context` 只在属于本 worktree 的 change 上做推断，其余的作为背景列出：`Change X (blocked) belongs to worktree Y on
branch B; it does not set this session's status.` 一个 change 属于别处，是指它的 `.openspec.yaml` 把另一个 chat
角色写为所有者，

```yaml
keel:
  owner: verify
```

或者在没写所有者时，另一个 worktree 的分支有超出默认分支、触及它的 commit，而你的分支没有。只看已提交的历史；
未提交的文件从不起决定作用。
`keel context --change <name>` 仍然可以按名字选中任何 change。

没有选中任何东西时，`keel context` 和会话提示还会指出这个分支最近在做什么（#278）：它超出默认分支的 commit 所引用
的最多五个 issue，最新的在前——`recently referenced: #162, #182`。这是从 Git 读出来的，不选中任何东西。

一个从不拥有 change 的会话——review、验证、协调者——可以按它的 chat 角色声明为只读（#246）：

```yaml
read_only_roles:
  - review
```

在绑定到列出角色的 worktree 里，`keel context` 只报告一行 `idle` 并写明角色，不列任何候选；SessionStart 和
compaction 后的提示会说没有选中 change，而不是让会话去挑一个。`keel context --change` 和 `keel/HANDOFF.md`
照常可用。

## 外部模型 CLI

会话可以把活交给外部模型 CLI 当委派对象——codex、DeepSeek Harness 的 `dsh`，或你自己注册的。调不调由模型
自己选择；Keel 负责的是接口、门禁，以及别人已经踩过的坑。宿主自带的 subagent 不在其中：模型自己更懂它们。

```bash
keel agents                      # 事实目录：每个可执行文件解析到哪里、本项目是否允许
keel agents codex                # 命令模板、沙箱、数据发往哪里、带日期的坑
keel agents brief codex --mode helper --dir . --out /tmp/brief.md --change <c> --task <t>
```

`keel agents brief` 从选中任务的 capsule 编译出一份任务说明，写成文件，再打印要运行的命令；这条命令会把 agent
的退出状态写进结果旁边的 `.exit` 文件。**Keel 不启动任何东西**；命令由会话自己运行，任何结果在算作证据之前，
会话都要复跑每个检查。以下情况会被拒绝：

- 项目没有允许的 agent——没有声明时，一个都不允许；
- 项目声明了不得外发的 Read 或 Touch 路径；
- 在会话自己的 checkout 里做会写入的运行。宿主的写入守卫看不到外部进程，所以实现（以及 CLI 没有只读沙箱的
  helper，比如 `dsh`）需要用 `git worktree add` 另建一个。

```yaml
external_agents:
  allow:
    - codex
  egress_deny:
    - secrets/**: 受 NDA 约束的厂商密钥
```

事实目录只记事实——命令模板、沙箱、数据去向，以及每条都带日期和出处的坑——从不写某个 agent 擅长什么，因为常驻
在会话里的评价会左右它，而且换个模型就过时。哪些活适合交给外部 agent，由你自己写。工具路径属于本机事实：
`~/.keel/agents.json` 可以新增 agent 或覆盖某个字段，比如
`{"agents": {"dsh": {"executable": "/path/to/dsh"}}}`。Keel 看不到 agent 在任务说明之外还读了什么，所以
`egress_deny` 防的是交出去的内容，而不是它自己能打开的文件。

## 共享资源租约

会话通过有期限的租约在各 worktree 之间协调共享资源。其他持有者会被拒绝并记为等待者；持有者释放租约，或有人发现租约已过期时，
等待者会收到私信通知。租约对 Git 或文件系统不做任何强制。换班检查会报告本 worktree 仍持有的租约。见
[docs/resource-lock.md](docs/resource-lock.md)。

## worktree 总览

`keel worktrees [--repo <path>] [--issues <file>] [--json]` 列出每个 worktree 的分支或游离 HEAD、上游及
ahead/behind 计数、最后一次 commit、脏路径数、绑定的 chat 角色及在线状态，以及引用的 issue。被锁定、可清理和
已缺失的 worktree 也会显示。它读取本地状态，不写仓库，也不写 chat 存储，而且从不 fetch：ahead/behind 以最后一次
fetch 为准。issue 引用来自默认分支（origin 的 HEAD，否则本地 `main`，再否则 `master`）之外的 commit 标题和正文，
文本输出会写明用的是哪个默认分支。

用 `--issues issues.json` 显式传入 issue 时间，内容是一个 JSON 数组，例如
`[{"number":12,"updatedAt":"2026-10-05T08:00:00Z"}]`（即
`gh issue list --json number,updatedAt` 的格式）。无法读取或格式错误的文件会被拒绝（exit 1），并写明文件名。
JSON 输出包含 `defaultBranch` 和 `worktrees`；每个 worktree 的 `issues` 仍是一个排好序的编号数组。带 `--issues`
时，`issueUpdates` 会加上 `{number, updatedAt}` 条目，没有时间的记为 null。默认分支未知时，不推断 issue 范围。

## 会话之间的群聊

在同一个仓库里干活的各个会话——Claude Code 会话、Codex 会话、无人值守的执行器，还有你——用 `keel chat` 共享一个工作群。群有维护中的成员名单，一条消息可以 `@` 某个角色或 `@all`，轻量待办可以关联 issue。一条记录可以取代同一作者之前的记录（`--supersedes <id>`），被取代的那条随即从所有人的未读里消失；未读按新到旧排列。用 `--ack` 发出的记录会请它所指向的角色确认，方式是 `keel chat ack <id>` 或回复；`keel chat show <id>` 和 `keel chat acks` 会列出谁已确认、谁只读过、谁还没读。`keel chat summary --since <time>` 汇总你能读的群里发生了什么变化——按发送者列出消息数、开出的待办及其是否仍未关闭、已关闭的待办、并入后继记录的被取代记录，以及仍在等待的确认——不用模型，也不把任何东西标为已读。每个成员有各自的未读状态，历史全部保留。用 `keel chat group add <group> <role> --listen` 加入的成员在那个群里只听不说：它接收这个群——包括桥接到 Slack 的群，这样 review 会话读到的是你自己的原话，而不是协调者的转述——被找时会被唤醒，可以确认并关闭自己的待办，但不能在那个群里发言或修改它（#248）。会话的 chat 角色就是它的身份：按角色称呼其他会话，绝不要按宿主的会话标题，Keel 看不到那个标题；角色绑定在会话运行的 worktree 上，所以一个换了地方的会话必须在新的位置重新绑定角色，否则那里什么都唤不醒它。`keel patrol` 和 `keel --doctor` 会报告绑定到已删除 worktree 的绑定，以及有东西在等、却已两小时没有会话活跃的角色；未绑定就启动的会话会被告知是哪些角色；`keel chat role --prune` 会删掉指向已删除 worktree 的绑定（#301）；`keel context` 和会话投影会写明绑定到本 worktree 的角色，并在这里其他 worktree 都有角色、本 worktree 却没有时提醒（#245）。`keel chat role --rename <old> <new>` 给角色改名而不改写日志：群聊会把旧名读作新名——群和私聊群的成员身份、待办分配对象，以及 `@old` 提及——而 worktree 绑定和各角色的状态（读取游标、在线状态、parked 标记、换班便条及历史、patrol 状态）会迁到新名下，新名在已有自己一份的地方保留自己的。旧名不能再被绑定，`keel/config.yaml` 和 `keel/chat.json` 里仍写着旧名的行会列出来交给你编辑（#376）。只有被提及、分到待办或收到私信才会唤醒 Claude 会话；其他消息都等它的下一次提示。消息只是另一个 agent 发来的数据，从不代表授权。两道循环防护拦住失控的 agent：一个角色每 10 分钟最多发 20 条记录；当两个角色在 10 分钟内交替发完一个群的最近 8 条消息时，那里的下一次发言会被拒绝（#297）。发言者可以带 `--not-a-loop "<why>"` 发一次——一问一答本来就是私聊群的正常形态——之后再重复就会叫来负责人，负责人的发言会解除它。`keel/chat.json` 里的 `limits` 设置 `rate`、`window_minutes`、`pingpong` 和 `pingpong_minutes`。消息里的时间应该来自 Keel 的时钟，而不是估计：除非给了 `--no-stamp`，`keel chat post` 和 `keel chat dm` 会以它为准加上 `[MM-DD HH:MM]` 前缀（#298、#349）。Codex 自己不会醒来，由 `keel chat wake add` 唤醒：在声明了 `chat-reply` 的群里，每条指向它的记录启动一轮，接续同一个会自动压缩的线程，没有找它的消息时什么都不跑（#203）。其他宿主依靠提示时的通知，不得让模型轮询群聊；如果确实避免不了定时，就先用 `keel chat notice --check` 把关，每次运行都开新线程，并告诉加入群聊的会话不要设置定时检查（#194）。每台机器一个 Slack App、一个桥接进程，同一批群就能实时连到其他机器上的会话和你的手机，孤儿分支 `keel-chat` 会把历史保留到超出 Slack 保留期之后。角色也可以通过一个你能在 Slack 里提及的 Slack bot 发言，一个 bot 可以服务多个项目，在每个项目的频道里充当那个项目的角色。见 [Slack 配置指南](docs/chat-slack-setup.zh-CN.md)。角色的会话通过 `keel shift` 换班：协调者发起，会话自查收尾、留下便条、清空自己，新的一班从便条接手；见 [docs/shift-change.zh-CN.md](docs/shift-change.zh-CN.md)。如果团队的角色以后台 Claude Code CLI 会话运行、没有桌面应用，就改用 `keel tick` 来唤醒、巡查和换班；见 [docs/cli-team.zh-CN.md](docs/cli-team.zh-CN.md)。5.83 的 `keel mail` 命令在私聊群上继续可用。

## 协调者巡查

一个协调会话安静下来，等它的每个人都会卡住（#260）。角色记下自己在等什么，由宿主按计划运行的巡查在条件成立时
告诉它：

```bash
keel chat wait soc --commit eb340a7 rerun R007 when the fix lands   # 或：--issue 42 --closed
git fetch && gh issue list --json number,title,state,labels,updatedAt > /tmp/issues.json
keel patrol --issues /tmp/issues.json        # 以协调者的角色运行
```

`keel patrol` 把条件已经成立的每条等待——远端出现某个 commit、某个 issue 已关闭——标为已满足，并给等待的角色发
一条私信，把它唤醒。它列出每个角色的在线状态、最近活动和未关闭的待办，并标出闲置超过 `--idle`（默认 `30m`）的
角色。它不 fetch、不调度、不调用模型，没有新情况时什么都不写；这时它以 0 退出，当协调者有事要处理——一个风险，
或它自己的等待已满足——时以 2 退出，只记录了东西或通知了其他角色时以 3 退出，出错时以 1 退出，所以一个廉价的
调度器——cron、`/loop`、CI——可以只在 2 时唤醒模型（#350）。`keel chat waits` 列出仍在等待的事项。

按小时运行的巡查应该报告变化而不是状态，否则它每小时都会为一张故意搁置的便条唤醒协调者（#295）。
`keel patrol --since-last` 为每个角色保存一份快照——换班状态、远端默认分支的末端、主 checkout 的未提交路径、
每个角色的闲置情况和未关闭待办，以及协调者收到的、未读超过 `--idle` 的指向它的记录——只为与上一次运行不同的
内容打印 `changed:` 行；第一次运行记录基线。它每次运行都写入快照，有变化时以 3 退出，只有风险变化时才以 2 退出。
加上 `--notify`，协调者会收到一条来自 `keel-patrol` 的私信，唤醒它的会话，内容只包含风险（#307）：共享 checkout
在一次干净的运行之后出现了未提交路径、宿主用 `--disk-free-gb` 报告的剩余磁盘降到 `--disk-min-gb`（默认 20）
以下，以及一个角色连续两次催促都没有回应。换班状态变化和新 commit 只打印，不发送。每次运行都会往 chat 存储里的
`patrol/log/<role>.log` 追加一行，所以一次静默的运行也能审计。
宿主还可以用 `--quota <percent>` 传入每周配额的已用百分比：`--quota-alerts`（默认 `90,95,99`）里的每个阈值
在每个配额周期内成为一次风险，数字下降即开始新周期；达到 `--quota-quiet-at`（默认 90）或以上时，`--nudge`
什么都不发，因为每次催促都会唤醒一个大会话。

`keel patrol --nudge` 更进一步，自己去催每个闲置的角色，用一条来自 `keel-patrol`、会唤醒其会话的私信（#307）：
当指向它的记录等待时间超过 `--idle` 时（最多每两小时一次）；当分配给它的一个待办被关闭时，告诉它在这个任务边界
换班——如果还有另一个待办分给它，就用 `keel shift ready --wake`，否则用普通的 `ready` 等协调者——因为换班跟在
完成的任务之后，而宿主会在一个任务之内做 compaction（#313）；以及当它用 `ready --wake` 留下的便条一直没被
恢复时。不带 `--wake` 留下的便条——协调者搁置某个角色——不会被打扰，Keel 自己的消息也从不算作等待。

带上 `--issues` 时，巡查还会分派 issue 更新（#242）：`keel/config.yaml` 里的 `issue_roles:` 把一个标签映射到
一个角色，每个角色会为带着它标签的 issue 的每次更新收到一条私信——这样一个标为 `role:verify` 的交接无需第二条
消息就能到达 `verify`。一个键也可以是用 ` + ` 连起来的一组标签（#433），只匹配同时带着这些标签的 issue，这样
结构相同的几个团队就能共用能力标签。当一条匹配路由的标签是另一条的子集时，只有标签更多的那条的角色收到更新；
加了引号的键仍是单个标签。

```yaml
issue_roles:
  role:verify: verify
  design: design-iecc
  design + dmc_rmw: design-rmw
```

在会话内创建的宿主计划任务会随该会话结束，所以换班或重启就会丢掉它。声明由哪个角色巡查、多久一次，那个角色的
新会话——以及它的 `keel shift resume`——
就会被提醒重新创建它（#260）；Keel 本身仍然不调度任何东西：

```yaml
patrol:
  role: iecc-pm
  every: 30m
```

一个团队一个协调者的仓库可以列出多个（#434），每一项带同样的键，再加上 `scope: group:<name>`。带范围的协调者
只催促该聊天群的成员、只把 issue 分派给他们、也只报告他们的情况；不带范围的协调者负责不在任何范围里的角色，
同时在两个群里的角色两边都管，但同一窗口内只会被催一次。远端分支头、共享 checkout、绑定漂移、磁盘和配额由不带
范围的协调者报告，全部都带范围时由列在第一个的报告。每个角色收到自己的提醒，`keel patrol task` 渲染调用所在
worktree 的角色的任务（或 `--role <role>` 指定的），`keel tick` 在各自到期时分别运行：

```yaml
patrol:
  - role: pm-iecc
    every: 60m
    scope: group:iecc
  - role: pm-rmw
    every: 60m
    scope: group:rmw
```

更好的做法是把巡查完全放到协调者的会话之外，作为一个运行在小模型上的宿主计划任务，这样它能熬过协调者清空自己
（#295）。加上 `host_task: <id>`（愿意的话再加 `model: <id>`，Keel 只是原样传递，从不替你选择），然后运行
`keel patrol task`：它打印出这个任务——id、由 `every:` 生成的 cron、模型，以及一份按路径针对协调者 worktree 运行
`keel patrol --since-last --notify` 的自包含提示。Keel 什么都不创建；由会话的模型用宿主自己的计划任务工具安装它，
因为计划由宿主自己保存。声明了 `host_task:` 后，提醒只会请你确认这个任务仍处于启用状态。请在一个文件夹未绑定任何
角色的会话里创建这个任务：宿主任务会在创建它的那个文件夹里开始运行。如果某次运行还是在某个角色的 worktree 里启动
了，Keel 会凭它的第一条提示（`<scheduled-task …`）认出它，随即恢复那个角色的在线状态并忽略这个会话，所以它既不会
把角色标为离线，也不会触发 `keel shift ready --wake`（#300）。

没有桌面应用时，`keel tick` 就是执行器：一个不用模型的步骤，由 launchd 每隔几分钟调用一次，一旦过了巡查建议的
下一次运行时间，就运行巡查。声明 `runner: tick`，再加上 `cadence: adaptive` 让巡查根据所见来选择下一次运行时间；
`keel tick task` 会打印 launchd 任务。见 [docs/cli-team.zh-CN.md](docs/cli-team.zh-CN.md)。

tick 还会把以前由宿主任务传的数字交给巡查（#456）。它测量每个巡查 worktree 所在文件系统的剩余磁盘空间，对照
`disk_min_gb:`（默认 20）。它从 `quota_file:` 指定的文件里读取周配额百分比，前提是这个文件在 6 小时内写过。Keel
不会为了配额去执行任何命令；可以由 status line 来写这个文件，因为只有 status line 能拿到 `rate_limits`。文件过期，
或者根本没有声明时，tick 只说一次。两项都可以声明在任意一个 `patrol:` 项上，由负责全仓库风险的协调者报告。

```bash
# 在 ~/.claude/statusline-command.sh 里，把 JSON 读进 $input 之后
echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' > ~/.claude/keel-quota.txt
```

## 负责人的语言

agent 读到的大多是英文——工具输出、issue、spec、Keel 自己的输出——回答你时也会滑向英文。声明你希望被使用的语言，这条规则就会在写回复的地方被重申：在 `keel context`、会话启动提示，以及每个 worktree 里每次提示时的 chat hook 中（#305）——在 Claude 上，还会在每 15 次工具调用或连续 10 分钟的工具调用之后重申，因为回合中途写的状态更新并不跟在某次提示之后（#311）。agent 仍可以用任何语言工作；标识符、命令、路径和引用的输出保持原样。

```yaml
owner_language: zh
```

## 命令参考

```bash
# 连续性 —— 无状态重算「现在该做什么」
keel context [--json] [--change <c> --task <t>]
keel context --clear-handoff                       # 删除 keel/HANDOFF.md
keel project --target <t> --event startup|resume|compaction|worktree [--expected-owner <owner>] --json
keel capabilities [--target <t>] [--json]          # 各 target 的自动化经验证能做什么

# 确定性门禁 → pass | fail | needs-review
keel gate task-start    --change <c> --task <t> [--record] [--keep-evidence M1,M3] [--no-guard] --json
keel gate task-complete --change <c> --task <t> [--base <git-ref>] --json
keel gate change-close  --change <c> --action sync|archive [--base <git-ref>] --json

# 写入守卫（Claude target）
keel guard start --change <c> --task <t> [--force] --json
keel guard status --json
keel guard clear  --json

# 领域透镜 —— keel/lenses/ 里由用户编写的指导
# （另一个由用户编写的面是先例存储，见上文）
keel lenses list
keel lenses add <name> [--force]

# 会话之间的群聊（接 Slack 见 docs/chat-slack-setup.zh-CN.md）
keel chat role --set <role> [--alias <a>] | --rename <old> <new>
keel chat group create <g> [--member <r>]... | add | remove | archive | list
keel chat <g> [<text>] [--since 2h] [--follow]     # 查看，或发言
keel chat dm <role> <text> | todo <g> --assignee <r> <text> | todos [--mine]
keel chat unread | read | notice | search <text>
keel chat bridge add | install | status | pause <2h> | stop | start | uninstall
keel chat wake now <role>                          # 恢复某个角色已结束的 CLI 会话
keel chat archive sync | pull
keel mail role | send | list | read                # 5.83 的邮箱；在私聊群上可用

# 换班、共享资源租约、worktree 总览
keel shift request | check | ready [--wake] | start | resume | status
keel lock acquire | release | list                 # 见 docs/resource-lock.md
keel worktrees [--repo <path>] [--issues <file>] [--json]

# 无人值守 triage —— 这个 issue 能否不经询问就开工？
# Keel 从不获取 issue；传入 gh 返回的内容。两个参数至少给一个。
keel triage [--labels <l1,l2>] [--issue <n>] [--json]

# 协调者巡查，以及宿主调度器调用的无模型步骤（docs/cli-team.zh-CN.md）
keel patrol [--issues <file>] [--idle <dur>] [--since-last] [--notify] [--nudge] [--json]
keel tick [--json] | keel tick task                # 执行一步；打印 launchd 任务

# 外部模型 CLI —— 事实目录，以及 Keel 编译的任务说明（Keel 不启动任何东西）
keel agents [name] [--json]
keel agents brief <name> --mode helper|implementation --dir <path> --out <file>

# 本角色已合入的任务分支：列出分支和 sha；不 fetch，也不删除
keel branches [repo] [--role <role>] [--json]

# 安装 / 维护
keel --init    [--target <t>] [--dry-run] [--force-template-update]
keel --install [--target <t>] [--dry-run] [--force-template-update] [--with-git-hooks]
keel --check | --doctor  [--target <t>]
keel --uninstall | --clear  [--target <t>] [--dry-run]   # --clear 是同一种移除
keel --update [--dry-run] [--source <npm package or git spec>] [--adopt]   # --adopt：让空闲的后台会话重启到新插件上
keel --version | --help

# OpenSpec，通过 Keel 捆绑的 CLI 运行
keel openspec <args>
```

命令接受仓库路径，可以是位置参数，也可以是 `--repo <path>`；具体用哪种见 `keel --help`。
每组命令都会打印自己的完整子命令列表：`keel chat help`、`keel mail help`、`keel shift --help`、
`keel lock --help`、`keel patrol --help` 和 `keel agents --help`。

退出码：`0` 通过 · `1` 输入错误 · `2` 用法错误（未知 flag，或命令拒绝的 flag） · `3` 策略失败 · `4` 缺少语义 review。`keel patrol` 用 `2` 和 `3` 表示它发现了什么；见「协调者巡查」。

target 是探测出来的，不按名字假定：无法验证的运行时行为报告为 `manual`，而非 `enforced`。一个 repo 固定选一个
target，后续每次 `--install` / `--check` / `--doctor` / `--uninstall` 都用它。

## 开发

无构建步骤。`src/skills/` 是可移植技能的唯一维护源；`plugins/keel/skills/` 下的分发副本必须与之字节一致
（由校验强制）。

```bash
npm test                  # 一次 validate_plugin.py --all：baseline + 全部场景并行（--jobs N 控制并发），最后一行是 evidence: 证据分类
node scripts/run_python.js scripts/validate_plugin.py --evidence           # 哪些场景是确定性的、哪些对着替身宿主跑；--markdown 给发布说明用
node scripts/run_python.js scripts/validate_plugin.py --scenario <name>   # 单个场景
node scripts/run_python.js scripts/validate_plugin.py --group <module>    # 一个模块的场景，例如 --group chat
node scripts/bump_version.js <patch|minor|major>   # 一次改齐所有版本 pin
```

场景按职责放在 `scripts/validation/` 下的模块里（`contract`、`install`、`hosts`、`guard`、`chat`、
`shift`、`docs`、`selfcheck`）；`registry.py` 是唯一的有序注册表，`common.py` 放它们共用的辅助代码。

## 隐私

Keel 不运行服务器，自身不收集任何数据。[PRIVACY.md](PRIVACY.md) 列出它在你本机存什么、什么会离开本机，
包括内置 OpenSpec CLI 的遥测及关闭方法。

## License

[MIT](LICENSE) © 2026 TanglmChris。**[English 版](README.md)** 含有相同的章节。
