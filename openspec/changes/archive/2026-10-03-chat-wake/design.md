## Context

Issue #203 records the decision and the 2026-10-03 probes. The chat store already appends to `<git common dir>/keel-chat/signal/<role>` only for a record that wakes the role (`store.wakes`). That signal file is what Claude's `FileChanged` hook watches. `keel chat notice --check` (#194) applies the same rule without a model. Replies have advanced the replier's cursor since #201.

## Goals / Non-Goals

**Goals:**
- An addressed record starts one Codex turn on this machine without anyone starting it, and nothing runs while nothing is addressed.
- Turns continue one thread, and compaction bounds the thread's size.
- The unattended turn is told it may only reply.

**Non-Goals:**
- Hosts other than Codex.
- A resident process, or any schedule.
- Waking for `@all` or plain messages.
- Enforcing, at the system level, that the unattended turn only replies.

## Decisions

- **F1** — With Codex CLI 0.159.3, a `codex exec` turn run in the Codex worktree received Keel's notice through the plugin's SessionStart hook and answered two `@cx` records in `lab`. It used about 62,900 input tokens, 54,700 of them cached. Basis: the 2026-10-03 playground run recorded on #203.
- **F2** — `codex exec resume <thread> <prompt>` accepts `-c model_auto_compact_token_limit=<n>`, `-c sandbox_mode="workspace-write"`, and `-c sandbox_workspace_write.writable_roots=[...]`, but not `-s`, `-C`, or `--add-dir`. A resumed turn remembered the previous turn and could write the git common directory. It used about 107,200 input tokens, 88,800 of them cached. `--json` emits `{"type":"thread.started","thread_id":...}`. Basis: `codex exec resume --help` and the same run.
- **D1** — The trigger is a per-registration macOS LaunchAgent. Its `WatchPaths` names the role's signal file, it sets `RunAtLoad` so records that arrived while it was unloaded are seen at login, and it runs `keel chat wake run --once --worktree <path>`. `wake add` creates the signal file if it is missing. There is no resident process.
  
  Basis: the signal file already encodes the wake rule, and launchd watches it without Keel polling.
- **D2** — `wake run --once` takes a per-role lock and exits if another run holds it. Then it repeats:
  1. Collect the role's unread records that `store.wakes` accepts, that lie in a group the worktree's `keel/config.yaml` declares `chat-reply:<group>` for, and whose id is newer than the registration's `delivered` mark.
  2. Stop when there are none.
  3. Stop and log the hold when the role already started its per-hour limit of turns (default 10, `--max-per-hour`) in the last hour.
  4. Otherwise set `delivered` to the newest collected id, start one turn, and wait for it.
  
  Each record therefore starts at most one turn, even when that turn did not answer it.
  
  Basis: the owner asked that nothing run while nothing is addressed. Without the `chat-reply` declaration a woken turn could not answer, because a chat message grants nothing.
- **D3** — The first turn runs `codex exec --json <prompt>`, and every later turn runs `codex exec resume <thread> <prompt> --json`. Both run with the worktree as their working directory and with `-c model_auto_compact_token_limit=<n>` (default 100000, `--compact-at`), `-c sandbox_mode="workspace-write"`, and `-c sandbox_workspace_write.writable_roots=["<git common dir>"]`. The thread id comes from the first `thread.started` event and is stored with the registration. `wake add --thread <id>` adopts an existing thread instead. A turn running longer than 15 minutes is stopped. The executable is `KEEL_CHAT_CODEX` or `codex`.
  
  Basis: the owner chose one continuing thread with compaction, and F2 is the surface that supports it.
- **D4** — The prompt is fixed. It says that keel chat started this turn unattended because records addressed to the role are waiting, that nobody is watching and nobody can answer questions, and that the turn should read them with `keel chat notice`. It allows answering only within the repository's `chat-reply` authorization, with no file edits, state-changing commands, commits, pushes, or schedules. When a message asks for more, the turn replies that the owner must approve it in a live session. The record texts never enter the prompt; the turn reads them as data through the notice.
- **D5** — Registrations live in `~/.keel/chat/wake.json` (or under `KEEL_HOME`), keyed by worktree path and role. Thread id, `delivered`, and turn times live in `~/.keel/chat/wake/<label>.json`, and each run logs to `~/.keel/chat/wake/<label>.log`. The label is `dev.keel.chat-wake.<role>-<8 hex of the worktree path's sha256>`. `wake remove` unloads and deletes the agent and the registration, and keeps the log.
- **D6** — "Keel MUST NOT start any session" becomes "Keel MUST NOT start any session except through a waker the owner installed for that role on that machine". Basis: the owner's 2026-10-03 decision on #203.

## Risks / Trade-offs

- The unattended turn can write the worktree. Only the prompt and the model's judgment keep it to replying, and nothing at the system level enforces that. D2 limits waking to groups where replying is authorized, and the prompt says nothing else is.
- Whether resuming a thread the Codex App has open at the same moment conflicts is unverified. By default the waker creates its own thread. `--thread` adopts one only when the owner names it.
- Each turn re-reads the thread up to the compaction limit, and the reported input sums several model calls per turn: F2 measured about 107,000 tokens, mostly cached. The per-hour limit and D2's one-turn-per-record rule bound the total.
- A Claude–Codex exchange is still bounded by the existing loop guard.
