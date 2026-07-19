# Keel

[English](README.md) | **中文**

> 面向 AI 编码 agent 的 OpenSpec 执行纪律 —— Claude Code、Codex、OpenCode 通用。

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Node](https://img.shields.io/badge/node-%3E%3D20.19.0-brightgreen.svg)
![Targets](https://img.shields.io/badge/targets-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenCode-blue.svg)

Keel 在 [OpenSpec](https://github.com/fission-ai/openspec) 之上加一层轻量、确定性的执行纪律，
让编码 agent 在**稳定、可校验的边界**内完成「判断 → 设计 → 执行 → review → 交接」，
而不是中途跑偏或在会话之间丢失上下文。

Keel **无状态**：每次会话都从你的 OpenSpec artifacts 和 Git 重新推导「现在该做什么」，
绝不依赖隐藏的对话记忆、transcript 或某个存下来的「当前任务」。这让 agent 的工作可恢复、
可审计，并且能安全地在不同 runtime 之间交接。

> 这是完整中文手册。速览请看英文 [README](README.md)。

---

## 为什么用 Keel

- **确定性门禁，而不是凭感觉。** `keel gate task-start | task-complete | change-close`
  做本地、无模型的结构检查，返回 `pass` / `fail` / `needs-review` 和真实退出码。它们从不声称
  判断你的设计是否*正确*——只判断契约与证据是否齐备。
- **真正的写入守卫（Claude）。** 通过的 `task-start` 会落下一次性 manifest，插件的 `PreToolUse`
  hook 随后**确定性拒绝**任何超出任务声明 `Touch` 范围的 `Edit`/`Write`——把「请别越界」从
  祈祷变成执法。
- **无状态连续性。** `keel context` 每次都从 OpenSpec + Git 重建选中任务、下一步动作和最小读取
  列表。能扛住 compaction、`/clear` 和冷启动。`keel/HANDOFF.md` 只作为可选的、经校验的覆盖存在。
- **写代码前先对齐预期。** `keel-align-expectations` 在 specs/tasks 定稿*之前*对齐隐性假设——
  风险触发的 deep path 一次只问一个材料性决策，并把接受的答案写回 OpenSpec。
- **单任务原生目标执行。** 授权 agent 自动执行**恰好一个** OpenSpec task——带指纹化 capsule、
  硬停边界，没有隐藏调度器替你选下一个任务。
- **一套纪律，三个 runtime。** 同一协议在 Claude Code、Codex、OpenCode 上运行；执行技能与 hook
  以原生插件分发。

---

## 工作流程

```mermaid
flowchart LR
    A[keel --init] --> B[keel context]
    B --> C[proposal / design / specs / tasks]
    C --> D[keel-align-expectations]
    D --> E[/opsx:apply → 选一个 task/]
    E --> F[task-start<br/>+ 写入守卫]
    F --> G[实现 · 测试先行 · 验证]
    G --> H[keel-review-checklist]
    H --> I[task-complete]
    I --> J[/opsx:sync · /opsx:archive/]
```

OpenSpec 拥有持久 artifacts（proposal、design、specs、tasks、archive）；Keel 拥有它们周围的
*执行纪律*：模式路由、任务 capsule 契约、确定性门禁、写入守卫、连续性、review 和交接卫生。

---

## 环境要求

- **Node.js `>=20.19.0`**（内置的 OpenSpec CLI 要求此版本；更低版本可能触发 `EBADENGINE`）。

---

## 安装

Keel 有两个可安装部分：**`keel` CLI**（context、gates、guard、schema、安装）和
**`keel` 插件**（执行技能 + 运行时 hook）。

### 1. `keel` CLI

一条命令即可全局安装 CLI 与捆绑的 OpenSpec CLI：

```bash
npm install -g @christang/keel
```

验证版本，之后可用 `keel --update` 自更新：

```bash
keel --version
keel --update            # 刷新全局 CLI
keel --update --dry-run  # 先看将执行的 npm 命令
```

> 捆绑的 OpenSpec 依赖会在安装时打印一行 opt-in 的 shell 补全提示。如果你的 npm 拦截了
> 安装脚本，这行提示会被跳过——它纯属装饰，keel 照常工作。

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

### 2. `keel` 插件（技能 + hook）

执行技能（`keel-*`）和运行时 hook（SessionStart 连续性、PreToolUse 写入守卫）以原生插件分发，
**不会**被 `keel --init` 复制进你的 repo：

```bash
claude plugin install keel@<marketplace>   # Claude Code
codex plugin add keel@<marketplace>        # Codex
```

---

## 快速开始

在目标项目根目录：

```bash
keel --init                 # 默认 target：claude
keel --init --target codex
keel --init --target opencode
```

`keel --init` 会运行 OpenSpec 初始化/更新并安装 Keel 的精简宿主面。之后每次开始或恢复工作：

```bash
keel context                # 或 keel context --json
```

它返回 `ready` / `ambiguous` / `blocked` / `idle`，附带 selection、下一动作和最小读取列表。
随时检查完整就绪状态：

```bash
keel --doctor
```

### `--init` 会写入什么

`keel --init` / `--install` 只保留**精简宿主面**——不复制技能或 hook（那些来自插件）：

- `AGENTS.md` —— Keel bootstrap 块（所有 target）
- `CLAUDE.md` —— `@AGENTS.md` import 块（Claude target）
- `openspec/config.yaml` —— 设置 `schema: keel-spec-driven`
- `openspec/schemas/keel-spec-driven/` —— Keel 强化过的 OpenSpec schema
- 以及 OpenSpec 生成并叠加 Keel overlay 的 `/opsx:*` 命令面

若目标 repo 里存在旧版打包的 `keel-*` skill、`keel-adapter.js` 或 `keel-gate` hook，
`--install` 会迁移它们：与旧打包字节一致的副本被移除并提示改由原生插件提供，用户改过的副本
原样保留并给出手动迁移警告。

---

## 目标（Targets）

| target | 初始化命令 | 命令面 |
| --- | --- | --- |
| Claude Code | `keel --init` | `.claude/commands/opsx/*.md` + 插件 hook（SessionStart、PreToolUse 守卫） |
| Codex | `keel --init --target codex` | 全局 `CODEX_HOME/prompts/opsx-*.md` |
| OpenCode | `keel --init --target opencode` | 项目内 `.opencode/commands/opsx-*.md` |

一个 repo 通常固定一个 target，后续 `--install` / `--check` / `--doctor` / `--uninstall` 都用它。
能力**按可观察证据探测，不按 target 名字假定**——无法验证的运行时行为报告为 `manual`，而非 `enforced`。

---

## Full / Lite 模式

**Full 模式**——新功能、对外接口变更、跨模块、改动超过 3 文件 / 100 行、架构或协议/状态机决策，
或任何触及信号、reset、CDC、安全边界的硬件工作。Full 模式用 OpenSpec 走
proposal → design → specs → tasks → archive。

被接受的原生 `plan mode` 产物只是会话态：其中影响 scope、Acceptance、完成定义或执行边界的决策，
必须在进入实现前固化到 `proposal/design/specs/tasks`；session plan 永远不是执行权威（review
checklist 会检查这条通道）。

**Lite 模式**——仅限局部小改：单点修复、小脚本、文档或补测试，不改对外接口、不加依赖、不引入新
设计决策、影响面可局部证明。Lite 默认不写 OpenSpec 状态。

---

## 核心命令

```bash
# 连续性 —— 无状态地重算「现在该做什么」
keel context [--json] [--change <c> --task <t>]

# 确定性门禁（schemaVersion 1 → pass | fail | needs-review）
keel gate task-start    --change <c> --task <t> --json
keel gate task-complete --change <c> --task <t> [--base <git-ref>] --json
keel gate change-close  --change <c> --action sync|archive --json

# 写入守卫（Claude target）
keel guard start --change <c> --task <t> --json
keel guard status --json
keel guard clear  --json

# 一次性原生投影（视图，永不是权威）
keel project --target claude --event resume --change <c> --task <t> --json
keel project tasks [repo] --target claude [--change <c>] [--json]
keel project --target codex --event compaction --json

# 安装 / 维护
keel --init | --install | --check | --doctor | --uninstall   [--target <t>] [--dry-run]
keel --update [--dry-run]
keel --version | --help
```

退出码：`0` 通过 · `3` 确定性策略失败 · `4` 缺少语义 review · `1` 输入/解析故障。

### 写入守卫（Claude target）

Touch 是唯一写权限来源。通过的 `keel gate task-start` 默认写入一次性守卫 manifest
（`keel guard start` 显式激活、`keel guard clear` 停止执法、`--no-guard` 退出默认激活）。
守卫激活期间，插件的 `PreToolUse` hook 确定性拒绝 Touch 之外的文件编辑，并带出精确路径与恢复命令：

- manifest 记录 change/task、capsule 指纹、规范化 Touch 和权威文件哈希，存于 `guard.json`；
  失败即关闭（fail-closed）：损坏、哈希漂移、指纹不匹配或 task 已勾选时一律拒绝。
- 守卫只覆盖文件编辑工具；`Bash` 等间接写入仍属纪律约束，仓库外的临时/scratch 路径直接放行。

### 一次性原生投影

`keel project` 从当前 OpenSpec task 编译一次性视图（objective、Acceptance、Stop 边界、Read、Touch、
evidence contract），永远只是投影、不是权威，也不勾选复选框：

- `keel project tasks --target claude` 把选中 change 的 tasks.md 编译成只读清单视图，由当前 agent
  自行决定是否手动镜像到宿主任务 UI；只读、不落盘、无同步循环。
- compaction 后手动重注入：`keel project --target codex --event compaction --json`。

---

## 对齐与纪律

- **`keel-align-expectations`**：SPEC 前的隐性知识风险用 risk-triggered deep alignment（一次一个
  决策、给推荐答案），而不是对所有 Full change 强制问卷；先查仓库事实再问用户，接受的结论写回
  proposal/design/specs/tasks。v5 已退役旧的 grill 问答技能，深度对齐统一由该技能承担。
- **执行/review 阶段的领域引用**：web / hardware / hardware-dsl 三个 reference 各带一节
  `Execution and review checks`；当变更 artifacts 或 Touch 扩展名显示对应领域信号时，
  `keel-tdd-or-test-first`、`keel-debug-failure`、`keel-review-checklist` 会按需查阅——仍然只
  加载匹配的那一个。
- **Dedicated Skill Policy**：新增或实质扩展专门技能时，先研究 first-party 或其他 authoritative source
  并记录 provenance/license 影响；用真实的 `should-trigger` 与近邻 `should-not-trigger`
  提示验证 description，并至少通过一个 real task 验证程序性行为；以 `src/skills/<name>/SKILL.md`
  为唯一 portable 权威，target metadata 只是 additive adapter，discovery 与激活仍由 target-native
  runtime 负责。

`/opsx:sync`、`/opsx:archive` 的完成门禁由确定性的 `keel gate change-close` 加
`keel-review-checklist` 承担，不再由运行时 hook 执行（该门禁在所有 target 上能力为 `manual`）。

---

## 开发与校验

无构建步骤。`src/skills/` 是可移植技能的唯一维护源；`plugins/keel/skills/` 等分发副本必须与源
字节一致（由校验强制）。修改后同步副本，然后运行：

```bash
npm run validate          # baseline 校验
npm test                  # baseline + 全部场景并行（约 25s）

# 单场景调试
node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates
node scripts/run_python.js scripts/validate_plugin.py --all --jobs 4
```

`npm test` 是一条 `validate_plugin.py --all` 调用：先跑 baseline，再按内置 scenario registry
并行跑全部场景（`--jobs N` 控制并发，默认 CPU 数），fail-loud 而非 fail-fast。新增场景只需写
`validate_<name>_scenario()` 并加入 registry。

### 目录结构

```text
bin/keel.js                # 跨平台 keel CLI
src/core/                   # 无状态 Keel Core（context、gates、guard、goal、helper、projection）
src/skills/                 # 可移植技能的唯一维护源（含 keel-align-expectations/references）
plugins/keel/              # 原生插件（.claude-plugin / .codex-plugin、hooks、skills）
assets/bootstrap/AGENTS.md  # managed bootstrap 块的唯一权威源
assets/openspec/            # OpenSpec schema 资产
scripts/                    # install_to_repo.py、validate_plugin.py、run_python.js
openspec/                   # 本仓库自身的 OpenSpec 工作区
keel/                      # 项目本地 Keel 状态（CHANGELOG、archive）
```

---

## 文档

- **[English README](README.md)** —— 速览与安装。
- **[keel/CHANGELOG.md](keel/CHANGELOG.md)** —— 版本历史。

## License

[MIT](LICENSE) © 2026 TanglmChris
