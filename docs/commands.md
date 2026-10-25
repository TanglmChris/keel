# Keel's slash commands and skills

**English** | [中文](commands.zh-CN.md)

What a person can type in a Claude Code session with the Keel plugin installed, and what each one runs. Every entry is namespaced by the plugin: `/keel:<name>`.

## Commands

Each command orders the steps of one `keel` CLI flow; the CLI does the work and the gates decide.

| Command | Runs | Use it to |
|---|---|---|
| `/keel:context` | `keel context` | see the status, the selected task, the next action, and whether the Keel and protocol versions agree |
| `/keel:start [change] [task]` | `keel gate task-start` | start a task: compile its capsule, record the fingerprint, arm the write guard |
| `/keel:done [change] [task]` | `keel gate task-complete` | complete a task: record evidence, run the review checklist, then the gate |
| `/keel:chat` | `keel chat unread` | read this role's unread chat and act on what is addressed to it |
| `/keel:shift` | `keel shift check`, `keel shift ready --wake` | change this session's shift: check loose ends, write the note, arm the wake |

These five are Claude Code commands. Codex plugins carry skills and no commands, so on Codex run the `keel` CLI flow directly.

## Skills you can invoke

| Skill | Use it to |
|---|---|
| `/keel:align-expectations [change or request]` | align requirements, hidden expectations, acceptance, and decision authority before specs and tasks finalize |
| `/keel:handoff [create, validate, or clear]` | write, check, or clear the optional `keel/HANDOFF.md` pointer when the next step cannot be inferred |

## Skills only the model invokes

These do not appear in the slash menu. The protocol has the model run them at fixed points: `debug-failure` when a task's command or check fails, `review-checklist` at completion gates, and `tdd-or-test-first` before a task's implementation when it needs tests or evidence first. On Codex they read as `keel:<name>`.

## Retired

- `keel docx` and the Markdown-to-Word skill were retired in 5.202.0 (#464): exporting documents is not part of Keel.
- The skills were named `keel-<name>` before 5.202.0. A repository's protocol block names them the old way until its next `keel --init`, which `keel context` asks for when the block is older than the running Keel.
- OpenSpec's own `/opsx:*` commands are not generated (#406); `keel --init` removes ones a repository still holds. Its workflows are the `openspec-*` skills.
