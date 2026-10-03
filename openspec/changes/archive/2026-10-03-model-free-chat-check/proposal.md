## Why

On 2026-10-01 a Codex session in the `chat-playground` test repository was asked to check the group chat before answering. It created a host automation that ran a full model turn every minute in the same thread. The first heartbeat ran at 20:00; by 23:21 the next day it had fired 1,277 times.

Each turn's context kept growing, until a single turn read about 182,000 input tokens. Cumulative input reached about 42.8 million tokens. The owner's Codex quota ran out at 22:35 on 10-01, before anyone had even mentioned the session, and the remaining 1,154 heartbeats failed (issue #194, with the session-log analysis in its comments).

Codex was in fact receiving keel's notices through #188's hook the whole time. What was missing was a way for a host that cannot wake on its own to ask "is anything addressed to me?" without paying for a model turn. Nothing in Keel's documentation warned against model polling either.

## What Changes

- **`keel chat notice --check`:** a model-free check for schedulers.
  - It prints nothing.
  - It exits 0 when the bound role has an unread record addressed to it, using the same rule that wakes a Claude session (a mention, an assigned todo, or a direct message).
  - It exits 1 otherwise, including when there is no repository or no role.
  - It advances no cursor and costs one file scan.
  - A scheduler runs it first and starts a model turn only on exit 0.
- **Documentation for the setup guide (both languages), `docs/codex-validation.md`, and the README chat section:**
  - Hosts should not poll the chat with the model.
  - The prompt-time notice is the recommended path for hosts without idle wake.
  - If a schedule is unavoidable, gate it with `--check`, and start a fresh thread per run instead of appending to one long session.
  - Prompts that start a chat session should say "do not set up recurring checks".

## Capabilities

### Modified Capabilities

- `keel-cross-host-mailbox`: the host-neutral notice requirement gains the model-free `--check` form.

## Impact

`src/core/chat/cli.js`, `src/core/chat/notice.js`, `scripts/validate_plugin.py`, `docs/chat-slack-setup.md`, `docs/chat-slack-setup.zh-CN.md`, `docs/codex-validation.md`, `README.md`, `README.zh-CN.md`, and `keel/CHANGELOG.md`. No new dependency, and no change for hosts that do not use it.
