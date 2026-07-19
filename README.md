# Keel

**English** | [中文](README.zh-CN.md)

> OpenSpec execution discipline for AI coding agents — Claude Code, Codex, and OpenCode.

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Node](https://img.shields.io/badge/node-%3E%3D20.19.0-brightgreen.svg)
![Targets](https://img.shields.io/badge/targets-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenCode-blue.svg)

Keel wraps [OpenSpec](https://github.com/fission-ai/openspec) with a thin, deterministic
execution layer so a coding agent **plans, implements, verifies, reviews, and hands off**
work inside stable, checkable boundaries — instead of drifting mid-task or losing the
thread between sessions.

Keel is **stateless by design**: every session recomputes what to do from your OpenSpec
artifacts and Git, never from hidden chat memory, transcripts, or a saved "current task."
That makes an agent's work resumable, auditable, and safe to hand between runtimes.

---

## Why Keel

- **Deterministic gates, not vibes.** `keel gate task-start | task-complete | change-close`
  run local, model-free structural checks and return `pass` / `fail` / `needs-review` with
  real exit codes. They never claim to judge whether your design is *correct* — only whether
  the contract and evidence are present.
- **A real write guard (Claude).** A passing `task-start` drops a one-shot manifest, and a
  `PreToolUse` hook then *deterministically rejects* any `Edit`/`Write` outside the task's
  declared `Touch` scope — turning "please stay in scope" from a hope into enforcement.
- **Stateless continuity.** `keel context` reconstructs the selected task, next action, and
  minimal read list from OpenSpec + Git every time. Survives compaction, `/clear`, and cold
  starts. `keel/HANDOFF.md` exists only as an optional, validated override.
- **Expectation alignment before code.** `keel-align-expectations` aligns hidden assumptions
  *before* specs and tasks finalize — a risk-triggered deep path asks one material decision at
  a time and writes accepted answers back into OpenSpec.
- **Single-task goal execution.** Authorize the agent to autonomously drive *exactly one*
  OpenSpec task — with a fingerprinted capsule, a hard stop boundary, and no hidden scheduler
  picking the next task for you.
- **One discipline, three runtimes.** The same protocol runs on Claude Code, Codex, and
  OpenCode; execution skills and hooks ship as a native plugin.

---

## How it works

```mermaid
flowchart LR
    A[keel --init] --> B[keel context]
    B --> C[proposal / design / specs / tasks]
    C --> D[keel-align-expectations]
    D --> E[/opsx:apply → pick one task/]
    E --> F[task-start<br/>+ write guard]
    F --> G[implement · test-first · verify]
    G --> H[keel-review-checklist]
    H --> I[task-complete]
    I --> J[/opsx:sync · /opsx:archive/]
```

OpenSpec owns the durable artifacts (proposal, design, specs, tasks, archive). Keel owns the
*execution discipline* around them: mode routing, the task capsule contract, deterministic
gates, the write guard, continuity, review, and handoff hygiene.

---

## Requirements

- **Node.js `>=20.19.0`** (the bundled OpenSpec CLI requires it; older Node may hit
  `EBADENGINE`).

---

## Install

Keel has two installable pieces: the **`keel` CLI** (context, gates, guard, schema,
install) and the **`keel` plugin** (execution skills + runtime hooks).

### 1. The `keel` CLI

One command installs the CLI and the bundled OpenSpec CLI globally:

```bash
npm install -g @christang/keel
```

Verify, and self-update later:

```bash
keel --version
keel --update            # refresh the global CLI
```

> The bundled OpenSpec dependency prints an opt-in shell-completion tip during
> install. If your npm blocks install scripts that tip is skipped — it is purely
> cosmetic and `keel` works either way.

<details>
<summary>Install the latest unreleased build from GitHub</summary>

Pack the current `main` and install the tarball (skips the npm registry):

**Windows (PowerShell):**

```powershell
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $tmp | Out-Null
npm pack github:TanglmChris/keel --pack-destination $tmp
$pkg = Get-ChildItem $tmp -Filter "christang-keel-*.tgz" | Select-Object -First 1
npm install -g $pkg.FullName
Remove-Item -Recurse -Force $tmp
```

**Linux / macOS:**

```bash
tmp_dir="$(mktemp -d)"
npm pack github:TanglmChris/keel --pack-destination "$tmp_dir"
npm install -g "$tmp_dir"/christang-keel-*.tgz
rm -rf "$tmp_dir"
```
</details>

### 2. The `keel` plugin (skills + hooks)

Execution skills (`keel-*`) and the runtime hooks (SessionStart continuity, the PreToolUse
write guard) ship as a native plugin — they are **not** copied into your repo by `keel --init`:

```bash
claude plugin install keel@<marketplace>   # Claude Code
codex plugin add keel@<marketplace>        # Codex
```

---

## Quick start

From your target project's root:

```bash
keel --init                 # default target: claude
keel --init --target codex
keel --init --target opencode
```

`keel --init` runs OpenSpec init/update and installs Keel's thin host surface. Then, every
time you start or resume work:

```bash
keel context                # or: keel context --json
```

It returns `ready` / `ambiguous` / `blocked` / `idle` with the selection, next action, and a
minimal read list. Check full readiness anytime:

```bash
keel --doctor
```

### What `--init` writes

`keel --init` / `--install` keeps a **thin host surface** — it does not copy skills or hooks
(those come from the plugin):

- `AGENTS.md` — Keel bootstrap block (all targets)
- `CLAUDE.md` — `@AGENTS.md` import block (Claude target)
- `openspec/config.yaml` — sets `schema: keel-spec-driven`
- `openspec/schemas/keel-spec-driven/` — the Keel-hardened OpenSpec schema
- plus the OpenSpec command surface (`/opsx:*`) with the Keel authoring/apply/archive overlay

---

## Targets

| Target | Init command | Command surface |
| --- | --- | --- |
| Claude Code | `keel --init` | `.claude/commands/opsx/*.md` + plugin hooks (SessionStart, PreToolUse guard) |
| Codex | `keel --init --target codex` | global `CODEX_HOME/prompts/opsx-*.md` |
| OpenCode | `keel --init --target opencode` | project-local `.opencode/commands/opsx-*.md` |

Pick one target per repo and use it for every subsequent `--install` / `--check` / `--doctor`
/ `--uninstall`. Capabilities are **probed, not assumed by target name** — unverified runtime
behavior is reported as `manual`, not `enforced`.

---

## Full vs Lite mode

**Full mode** — for new features, external interface changes, cross-module work, changes over
3 files / 100 lines, architecture or protocol/state-machine decisions, or any hardware work
touching signals, reset, CDC, or security boundaries. Full mode uses OpenSpec for
proposal → design → specs → tasks → archive.

**Lite mode** — local fixes, small scripts, docs, or test additions only: no interface change,
no new dependency, no new design decision, locally provable impact. Lite does not write
OpenSpec state by default.

---

## Core commands

```bash
# Continuity — recompute what to do (stateless)
keel context [--json] [--change <c> --task <t>]

# Deterministic gates (schemaVersion 1 → pass | fail | needs-review)
keel gate task-start    --change <c> --task <t> --json
keel gate task-complete --change <c> --task <t> [--base <git-ref>] --json
keel gate change-close  --change <c> --action sync|archive --json

# Write guard (Claude target)
keel guard start --change <c> --task <t> --json
keel guard status --json
keel guard clear  --json

# Install / maintenance
keel --init | --install | --check | --doctor | --uninstall   [--target <t>] [--dry-run]
keel --update [--dry-run]
keel --version | --help
```

Exit codes: `0` pass · `3` deterministic policy failure · `4` missing semantic review · `1`
input/parse failure.

---

## Development

No build step. `src/skills/` is the single source of truth for portable skills; distribution
copies under `plugins/keel/skills/` must stay byte-identical (enforced by validation). After
editing, sync copies and run:

```bash
npm run validate          # baseline validation
npm test                  # baseline + all scenarios in parallel (~25s)

# single scenario
node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates
```

### Repository layout

```text
bin/keel.js                # cross-platform keel CLI
src/core/                   # stateless Keel Core (context, gates, guard, goal, helper, projection)
src/skills/                 # canonical portable skills (+ keel-align-expectations/references)
plugins/keel/              # native plugin (.claude-plugin / .codex-plugin, hooks, skills)
assets/bootstrap/AGENTS.md  # canonical managed bootstrap block
assets/openspec/            # OpenSpec schema assets
scripts/                    # install_to_repo.py, validate_plugin.py, run_python.js
openspec/                   # this repo's own OpenSpec workspace
keel/                      # project-local Keel state (CHANGELOG, archive)
```

---

## Documentation

- **[中文完整手册 (Chinese full manual)](README.zh-CN.md)** — exhaustive command and workflow reference.
- **[keel/CHANGELOG.md](keel/CHANGELOG.md)** — version history.

## License

[MIT](LICENSE) © 2026 TanglmChris
