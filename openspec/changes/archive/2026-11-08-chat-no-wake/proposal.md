## Why

Issue #502, filed 2026-11-04 from the kaiwu token review and chosen for work by the owner on 2026-11-08 ("继续，除 175，其它都要解"). In a multi-role project a chat record wakes the addressed role's idle session through `signal/<role>`; the woken session's cache has mostly expired, so its first request rewrites the whole context. Measured over 2026-10-21 to 11-04 (Keel 5.216.0, the issue's data): 2198 turns started by a chat notice were 70.4% of the project's usage, 764 of them read and ended, and 258 cache rewrites on wake were about 18%. The sender has no way to say "this is information, read it at the next prompt": not mentioning is the only way, and a direct group wakes on every message.

The owner's answer to the issue's open question (2026-11-08): the default stays; lock and shift notices still wake. Only the sender's explicit option is added.

## What Changes

- **`keel chat post` and `keel chat dm` take `--no-wake`.** The record is delivered as always: it is in the log, `keel chat unread` lists it, the next prompt's notice counts it. It is addressed to no one for waking: `signal/<role>` and `signal/worktree/<id>` are not touched, `keel tick` does not resume an ended session for it, and `keel chat notice --check` does not report it.
- The record carries `no_wake: yes`, so every reader — this and other worktrees, `wakes()` everywhere — agrees without a second rule.
- `--no-wake` with `--ack` is refused: asking someone to acknowledge and not waking them contradict each other.
- Not changed: the default; `keel lock` and shift notices; todos; `@all`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

`src/core/chat/store.js`, `src/core/chat/cli.js`, `scripts/validation/chat.py`, `scripts/validation/registry.py`, `README.md`, `plugins/keel/commands/chat.md`, the published spec, and the changelog.
