## Why

Issues #178 and #183 need observed Codex lifecycle behavior, a working receiving path, and an honest manual fallback. A native Codex 0.159.3 probe found that the shared hook configuration's separate `args` are ignored: the discovered command is only `node`.

## What Changes

- Give Codex an explicit hook file with complete command strings for continuity and the existing guard, without changing Claude's hooks.
- Notify Codex of unread mail at SessionStart and UserPromptSubmit using the existing mailbox notice, without consuming messages or importing Claude-only watcher fields.
- Record clean-consumer installation, a minimal Full-mode execution, native hook discovery and context delivery, trust behavior, and manual capability boundaries.
- Document hook review, version reload, role binding, and fallback steps. Group-chat notice semantics remain owned by #187; this adapter will use the existing compatibility path until that interface exists.

## Capabilities

### New Capabilities

- `keel-codex-receiving`: Codex-compatible mailbox notice hooks and their failure behavior.

### Modified Capabilities

- `keel-native-plugin-package`: explicit Codex hook discovery rather than the shared default hook file.

## Impact

Codex plugin manifest, a Codex-only hook configuration and receiver, public-interface regression checks, README, and durable runtime evidence. No new dependency, automatic host trust, mailbox migration, group-chat implementation, idle polling, or global capability promotion. #186 and Claude's #187 implementation stay outside this change.
