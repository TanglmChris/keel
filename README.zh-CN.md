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

两部分：`keel` CLI 和 `keel` 插件。

**CLI** —— 一条命令（同时装上捆绑的 OpenSpec CLI）：

```bash
npm install -g @christang/keel
keel --version
```

**插件** —— 执行技能和运行时 hook：

```bash
claude plugin install keel@<marketplace>   # Claude Code
codex plugin add keel@<marketplace>        # Codex
```

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
- **领域引用**：web / hardware / hardware-dsl 三份 reference 各含一节 `Execution and review checks`；
  当变更 artifacts 或 Touch 扩展名显示对应领域信号时，`keel-tdd-or-test-first`、`keel-debug-failure`、
  `keel-review-checklist` 按需只加载匹配的那一份。
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

## License

[MIT](LICENSE) © 2026 TanglmChris · 版本历史见 [keel/CHANGELOG.md](keel/CHANGELOG.md)。
