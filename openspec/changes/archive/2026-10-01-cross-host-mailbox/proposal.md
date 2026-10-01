## Why

The same project often has a Claude Code session and a Codex session working side by side in separate worktrees — one on RTL, one on verification — and they need to pass conclusions to each other. Today the user copies and pastes. Writing directly into the other host's session thread was tried on 2026-10-01 and fails on host-internal storage formats, writer locks, versions, and an absent receiver, and works in one direction only (issue #180). Hosts should exchange plain Markdown files instead, and each host should decide for itself how to receive them.

## What Changes

- A host-neutral mailbox under the repository's git common directory, shared by every worktree of the repository and never versioned. A message is one Markdown file with `from`, `to`, `created`, `subject`, optional `reply_to` and `refs`, written atomically. Addresses are user-chosen role names bound to a worktree.
- `keel mail role | send | list | read` on the CLI, usable from any host's shell. Reading moves a message to `done/`; a reply is a new message carrying `reply_to`.
- Claude Code receives through plugin hooks: SessionStart and UserPromptSubmit announce unread mail, and a FileChanged hook with `asyncRewake` wakes an idle session when mail arrives. Each notice says the message is data from another agent, not a user instruction, and grants no authorization.
- No gate: unread mail never blocks a task, commit, or change.
- Codex's receiving side is left to Codex's own development; Codex sessions can already send and read through the CLI.

## Capabilities

### New Capabilities

- `keel-cross-host-mailbox`: mailbox location, message format, role addressing, CLI operations, and how a host is notified.

### Modified Capabilities

- `keel-native-plugin-package`: the Claude root manifest carries the Codex-shared hooks plus Claude-only mailbox hooks, instead of exactly the shared set.

## Impact

New `src/core/mail.js`, a `mail` entry in `bin/keel.js`, a new plugin script `plugins/keel/scripts/mail-hook.js`, the root Claude manifest's hooks, validation scenarios, the resident protocol's hook statement, and the specs above. `plugins/keel/hooks/hooks.json` — which Codex also loads — is unchanged. No new dependency.
