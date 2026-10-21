## Why

Issue #441. The owner approved fixing it at once on 2026-10-21. On 2026-10-21, after #415 (5.181.0), a session started with `claude --bg -w` from the main checkout was resumed on the real host. Its chat hook still bound it to the main checkout's role and watched that role's signal, so keel-maint-2 slept through three direct messages.

A throwaway probe on Claude Code 2.1.304 measured the resume payload. Both `cwd` and `transcript_path` name the launch directory: `.../projects/-Users-...-keel/<id>.jsonl`. That file does not exist; the session keeps writing `.../projects/<worktree project>/<id>.jsonl`. #415's fix trusted `transcript_path`, and its scenario fed an assumed payload that named the worktree project.

## What Changes

- **`hookLocation` falls back to the transcript that exists.** When the payload's `transcript_path` does not exist, it looks for `<CLAUDE_CONFIG_DIR or ~/.claude>/projects/*/<session_id>.jsonl` and uses that file's project directory to find the worktree.
- **The scenario feeds the measured payload shape.** `chat-hook-follows-session-worktree` gains a case built from what the host sent.
- **The contract page records the measured resume payload.** `docs/host-contract.md` adds it.

A session already resumed with the wrong watch list needs one more resume after this ships.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`

## Impact

The change touches:
- `src/core/chat/notice.js`
- `scripts/validation/chat.py`
- `docs/host-contract.md`
- the published spec
- the changelog
