# Keel

**English** | [中文](README.zh-CN.md)

> OpenSpec execution discipline for AI coding agents — Claude Code, Codex, and OpenCode.

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Node](https://img.shields.io/badge/node-%3E%3D20.19.0-brightgreen.svg)
![Targets](https://img.shields.io/badge/targets-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenCode-blue.svg)

## What Keel is for

[OpenSpec](https://github.com/fission-ai/openspec) gives a project a spec-driven
workflow: proposal, design, specs, tasks, and an archive of what changed. Claude Code
(or Codex) gives you the agent that does the work. Keel sits between them and keeps the
agent on track while it works through an OpenSpec change.

Left alone, an agent tends to drift: it edits files the task never mentioned, loses the
thread after a context reset, or checks work off without proof. Keel adds a thin, checkable
layer that prevents that, and it does so by building on tools you already have instead of
replacing them.

What Keel adds:

- **Stateless continuity.** `keel context` recomputes the current task and next step from
  OpenSpec and Git every session, so work survives `/clear`, compaction, and cold starts
  without depending on chat memory.
- **Deterministic gates.** `keel gate task-start | task-complete | change-close` run local
  structural checks and return `pass` / `fail` / `needs-review` with real exit codes. They
  check that the task contract and evidence are present; they do not judge whether the design
  is correct.
- **A write guard (Claude).** After `task-start`, a `PreToolUse` hook rejects any edit
  outside the files the task declared it would touch.
- **Expectation alignment.** Before specs and tasks are finalized, Keel surfaces hidden
  assumptions and asks about the ones that actually change behavior.

Keel leans on native capabilities rather than reinventing them. The spec workflow is plain
OpenSpec. The execution skills, the SessionStart continuity hook, and the write-guard hook
ship as an ordinary Claude Code / Codex plugin. `keel --init` writes only a small host
surface into your repo: an `AGENTS.md` bootstrap block, the OpenSpec schema, and the
`/opsx:*` command overlay.

## Requirements

Node.js `>=20.19.0` (the bundled OpenSpec CLI needs it).

## Install

Two pieces: the `keel` CLI and the `keel` plugin.

**CLI** — one command (also installs the bundled OpenSpec CLI):

```bash
npm install -g @christang/keel
keel --version
```

**Plugin** — the execution skills and runtime hooks:

```bash
claude plugin install keel@<marketplace>   # Claude Code
codex plugin add keel@<marketplace>        # Codex
```

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

## Use

In your project's root, set it up once:

```bash
keel --init                 # default target: claude
keel --init --target codex  # or: opencode
```

`keel --init` runs OpenSpec init/update and writes Keel's host surface. Then, every time you
start or resume work:

```bash
keel context                # what to do now, recomputed from OpenSpec + Git
keel --doctor               # check everything is wired up
```

Do the spec work through OpenSpec's commands (`/opsx:propose`, `/opsx:apply`, `/opsx:sync`,
`/opsx:archive`). Keel's gates run at the task boundaries. The whole loop:

```
keel --init  →  keel context  →  /opsx:apply (pick one task)
   →  task-start (+ write guard)  →  implement & verify
   →  task-complete  →  /opsx:sync · /opsx:archive
```

On the Claude target, the session-start hook also shows that state to **you**, not only to the
agent — one line, before you type anything:

```
Keel: add-user-auth#2.1 — next: task-start. Disposable projection; OpenSpec and Git are the authority.
```

Set `KEEL_SESSION_PANEL=1` to draw it as a framed panel with the Keel mark instead. It is off by
default, and turning it on changes nothing but the presentation — the same status and the same
next command are in both forms.

### Standing authorization

Keel asks before a repository action it has no authority for, and it asks again next session,
because a permission granted in conversation does not survive a context reset. Declare it once in
`keel/config.yaml` instead:

```yaml
authorize:          # accepted names: commit, push, release, archive
  - commit
  - push
```

A task that authors no `Autonomy boundary:` inherits the declaration, and the compiled capsule
names `keel/config.yaml` as that entry's source so an inherited authorization is never mistaken
for one the task decided. A task that authors its own boundary keeps it.

Three things the declaration is not:

- **Not a way past a gate.** It authorizes the action, never the proof. `keel gate task-complete`
  returns exactly the same verdict, and the same failure text, whether or not you declared
  anything.
- **Not a trigger.** It removes a confirmation, not the step that reaches the action. Nothing
  schedules itself, and no next task is selected for you.
- **Not open-ended.** The four names above are the whole vocabulary. An unrecognized entry is
  reported with the accepted names and the declaration authorizes nothing until you fix it — a
  typo never becomes a silent grant.

The block is absent by default, and a repository that declares nothing behaves exactly as it did
before this feature existed. `keel --doctor` reports what is declared.

### Full vs Lite

Use **Full mode** (the OpenSpec flow above) for new features, interface or protocol changes,
cross-module work, or anything over ~3 files / 100 lines. Use **Lite mode** for local fixes,
small scripts, docs, or tests with no interface change and locally provable impact; Lite does
not write OpenSpec state.

## How the agent uses these

You rarely type the commands below. The point of Keel is that the discipline runs itself:
`keel --init` installs it into the agent's own workflow, and the agent reaches for each
command at the right moment. Three things make that happen.

- **The protocol.** `keel --init` writes a bootstrap block into your repo's `AGENTS.md`
  (imported by `CLAUDE.md` on Claude). It states the rules the agent follows: open every
  session with `keel context`, pass the gates at task boundaries, and stay inside the task's
  declared write scope. That is how the agent knows *when* to run what.
- **The skills.** The `keel-*` execution skills and the `/opsx:*` command overlays walk the
  agent through align → apply → review → complete, invoking the gates at each step.
- **The hooks.** A SessionStart hook runs the continuity projection the moment a session
  opens; a PreToolUse hook enforces the write guard on every edit. Neither needs prompting.

So in day-to-day use you run two commands: `keel --init` once, and `keel --doctor` when you
want to check the wiring. Everything below is the vocabulary the agent uses on your behalf.

## Verification layering

Keel splits verification into two layers so a slow suite never blocks your push:

- **Fast inner-loop check** — seconds, run at a local pre-push and during iteration. It catches
  obvious breakage without waiting.
- **Full gate** — the complete or slow suite (golden byte-determinism tests, cross-platform runs),
  run at CI or at `keel gate change-close`.

A task's `Verify` checks stay fast; the slow or exhaustive layer belongs to the full gate, not the
local pre-push. Declare your fast check in `keel/config.yaml`, the same file that holds your
standing authorization:

```yaml
fast_check: npm test -- --fast   # your project's seconds-scale check
```

Then opt into a repo-local fast pre-push:

```bash
keel --install --with-git-hooks   # writes .githooks/pre-push, sets core.hooksPath (this repo only)
keel --doctor                     # reports fast_check, the pre-push hook, and core.hooksPath
keel --uninstall                  # reverts core.hooksPath when Keel set it
```

`--with-git-hooks` is opt-in: a plain `keel --install` never touches git config, and the override
is repo-local and reversible.

## Domain lenses

Keel's core is pure process; it ships no domain knowledge of its own. Domain guidance lives in
**lenses** you author under `keel/lenses/*.md` in your repo. Each lens is self-describing: it
opens with an `Applies when:` line stating the signals that trigger it (file extensions, artifact
shapes) and carries an `Execution and review checks` section. When a change's artifacts or Touch
match a lens, the alignment, test, debug, and review skills load only that one lens — and nothing
when none match. Keel stays domain-agnostic; the knowledge is yours to own and edit.

Three lenses ship as opt-in templates (`web`, `hardware`, `hardware-dsl`) under `assets/lenses/`.
They are never installed automatically:

```bash
keel lenses list            # shipped templates + lenses installed in keel/lenses/
keel lenses add web         # copy the web template into keel/lenses/web.md, then edit it
keel lenses add web --force # overwrite an existing lens
```

## Commands

```bash
# Continuity — recompute what to do (stateless)
keel context [--json] [--change <c> --task <t>]

# Deterministic gates → pass | fail | needs-review
keel gate task-start    --change <c> --task <t> --json
keel gate task-complete --change <c> --task <t> [--base <git-ref>] --json
keel gate change-close  --change <c> --action sync|archive --json

# Write guard (Claude target)
keel guard start --change <c> --task <t> --json
keel guard status --json
keel guard clear  --json

# Domain lenses — user-authored guidance in keel/lenses/
keel lenses list
keel lenses add <name> [--force]

# Install / maintenance
keel --init | --install | --check | --doctor | --uninstall  [--target <t>] [--dry-run]
keel --update [--dry-run]
keel --version | --help
```

Exit codes: `0` pass · `3` policy failure · `4` missing semantic review · `1` input error.

Targets are probed, not assumed by name: unverified runtime behavior is reported as `manual`,
not `enforced`. Pick one target per repo and use it for every `--install` / `--check` /
`--doctor` / `--uninstall`.

## Development

No build step. `src/skills/` is the single source of truth for portable skills; the
distribution copies under `plugins/keel/skills/` must stay byte-identical (enforced by
validation).

```bash
npm test                  # baseline + all scenarios in parallel
node scripts/bump_version.js <patch|minor|major>   # bump every version pin at once
```

## License

[MIT](LICENSE) © 2026 TanglmChris. See the **[中文完整手册](README.zh-CN.md)** for the full
command and workflow reference.
