## Context

Issue #194 and its session-log analysis cover the 2026-10-01 run in the `chat-playground` test repository. A Codex host automation polled the chat with a full model turn every minute in one growing thread. It exhausted the owner's quota before the session was ever mentioned.

Claude Code wakes idle sessions through `FileChanged` + `asyncRewake`, which costs nothing until something arrives. Codex gets notices only at SessionStart and UserPromptSubmit through #188's hook, and nothing wakes it while it is idle.

## Goals / Non-Goals

**Goals:**
- A host that needs a schedule can decide whether to start a model turn with a zero-cost local command.
- The documentation steers hosts and the people who start sessions away from model polling.

**Non-Goals:**
- Scheduling anything. Keel schedules nothing; that stays with the host.
- Idle wake on Codex.
- Changing what wakes a Claude session.

## Decisions

- **F1** — The automation was `kind = "heartbeat"` with `rrule = "FREQ=MINUTELY;INTERVAL=1"`, appending to the same thread. It fired 1,277 times, with a median gap of 89 seconds. The last turn read about 182,000 input tokens, and cumulative input was about 42.8 million. The quota was exhausted at 22:35, before the 22:49 mention, and 1,154 heartbeats failed afterwards. Basis: `~/.codex/sessions/2026/10/01/rollout-2026-10-01T19-55-35-….jsonl`; `~/.codex/automations/keel-lab/automation.toml`; and the analysis on #194.
- **F2** — Every heartbeat turn received keel's notice as a developer message. #188's prompt-time path therefore works on the real Codex runtime. Basis: the same session log.
- **D1** — `keel chat notice --check` prints nothing and does not advance a cursor.
  - It exits **0** when the bound role has an unread record that wakes it, under the rule in `store.wakes`: a mention by name or alias, a todo assigned to the role, or a message in its direct group.
  - It exits **1** otherwise.
  - Being outside a repository or having no bound role also exits 1. In both cases there is nothing to answer, and an error code would make every scheduler treat the check as broken.
  
  Basis: the wake rule already defines "addressed to me". The exit-code convention follows `grep -q`, so `keel chat notice --check && <start a turn>` reads naturally.
- **D2** — The documentation states:
  1. Hosts should not poll the chat with the model.
  2. A host without idle wake should rely on the prompt-time notice (F2).
  3. A schedule, when unavoidable, must be gated by `--check` and start a fresh thread or session per run, because one long thread re-reads its whole history on every turn (F1).
  4. The text that starts a chat session should say "do not set up recurring checks".
  
  Basis: #194.

## Open Questions

- **Q1** — Should `--check` also exit 0 for unread `@all` and plain messages?
  - **Resolved 2026-10-03:** the owner accepted the recommendation. `--check` follows the wake rule exactly, as D1 states, and `@all` and plain messages do not start a turn.

## Risks / Trade-offs

- `--check` costs one scan of the role's open groups, the same as `keel chat unread`. At a one-minute schedule that is negligible next to a model turn.
- A host can still ignore the documentation and poll with the model. Keel cannot prevent it; it can make the cheap path obvious.
