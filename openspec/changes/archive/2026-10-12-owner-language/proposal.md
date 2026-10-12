## Why

Issue #305 (2026-10-12): the owner works in Chinese and says so in their global instructions, yet in one Keel maintenance session the agent answered them in English three times and was corrected each time. The drift comes when the context just read is mostly English — tool output, issues, OpenSpec artifacts, Keel's own output — and nothing near the reply restates the owner's language; the protocol only says "match the user's language where practical". The owner decided on 2026-10-12: declare the language per repository and remind every turn.

## What Changes

- `keel/config.yaml` accepts `owner_language: <tag>` (for example `zh`). A malformed value is reported and ignored.
- `keel context` carries `ownerLanguage`; the SessionStart and compaction projection states the rule; the chat UserPromptSubmit hook restates it on every prompt, in every worktree of the repository, role or not.
- The protocol's user-facing rule becomes binding where a language is declared: every message to the owner — replies, summaries, reports, and the question and options of a structured-choice prompt — is in that language; identifiers, commands, paths, and quoted output stay as they are; internal work may use any language.
- This repository declares `owner_language: zh`.

## Capabilities

### New Capabilities
- `keel-owner-language`: a declared language the agent addresses the owner in.

## Impact

`src/core/config.js`, `src/core/context.js`, `src/core/chat/notice.js`, `plugins/keel/scripts/session-start.js`, `plugins/keel/scripts/mail-hook.js` (comment), `keel/config.yaml`, `AGENTS.md`, `README.md`, `scripts/validate_plugin.py`, the new spec, and the changelog.
