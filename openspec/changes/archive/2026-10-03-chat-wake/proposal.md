## Why

Claude Code wakes an idle session for a mention through `FileChanged` and `asyncRewake`, which costs nothing until something arrives. Codex has no such surface (#188, `docs/codex-validation.md`): it sees the chat only at SessionStart and when the user writes to it. The one attempt to compensate, a minutely model heartbeat, exhausted the owner's quota (#194).

On 2026-10-03 the owner tested Codex in the `chat-playground` repository. A `codex exec` turn in the Codex worktree received the notice through Keel's plugin hook and answered both `@cx` records. A `codex exec resume <thread>` turn, with an auto-compaction limit and the git common directory as an extra writable root, remembered the previous turn and answered again (#203). The owner chose to build a waker that starts a turn only when something is addressed to the role, continuing one thread and keeping its length in check by compaction.

## What Changes

- **`keel chat wake`**, a per-machine, owner-installed waker for a role whose host cannot wake itself. Codex is the only host it supports.
  - `wake add` in a worktree registers the bound role for this machine and installs a macOS LaunchAgent that watches the role's signal file. Keel writes that file only for a mention, an assigned todo, or a direct message, so nothing runs while nothing is addressed.
  - Each trigger runs `wake run --once`. It starts one Codex turn when the role has an addressed unread record, in a group the worktree declares `chat-reply:<group>` for, that no earlier turn was given. The first turn creates the thread, and later turns resume it with `model_auto_compact_token_limit`.
  - One turn at a time per role, a per-hour limit, and a fixed unattended prompt that allows replying and nothing else.
  - `wake status` reports each registration, its thread, its last turn, and whether the limit is holding it. `wake remove` uninstalls it.
  - Registrations, thread ids, and logs stay under `~/.keel/chat/` on this machine and never enter a repository.
- **The requirement that Keel never starts a session** gains its one exception: a waker the owner installed for that role on that machine.
- **Documentation**: the Slack setup guide (both languages), `docs/codex-validation.md`, and both READMEs describe the waker as the way to wake Codex. The warning against polling with the model stays.

## Capabilities

### Modified Capabilities

- `keel-cross-host-mailbox`: adds the waker requirement and narrows "Keel MUST NOT start any session" to exclude an owner-installed waker.

## Impact

New `src/core/chat/wake.js`, plus `src/core/chat/cli.js`, `scripts/validate_plugin.py`, `docs/chat-slack-setup.md`, `docs/chat-slack-setup.zh-CN.md`, `docs/codex-validation.md`, `README.md`, `README.zh-CN.md`, and `keel/CHANGELOG.md`. There is no new dependency. The waker runs only after `wake add`, which the owner runs.
