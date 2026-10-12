## Why

Issue #311 (2026-10-13): 5.120.0 restates the owner's language on every prompt the owner submits, but a reply the agent writes mid-turn — a status update the host asks for after a long run of tools — gets no reminder, and in the Keel maintenance session it drifted into English again and the owner had to correct it. Owner decision, 2026-10-13: restate the rule after tool calls, rate-limited.

## What Changes

- A Claude PostToolUse chat hook restates the declared owner language as `additionalContext` once 15 tool calls or 10 minutes have passed since it was last stated in that session, whichever comes first.
- A restatement on UserPromptSubmit resets the count.
- A host-run session gets nothing, and nothing happens without `owner_language:`.

## Capabilities

### Modified Capabilities
- `keel-owner-language`: the rule is also restated after runs of tool calls.

## Impact

`src/core/chat/notice.js`, `plugins/keel/scripts/mail-hook.js`, `.claude-plugin/plugin.json`, `README.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
