## Context

Issue #311 and the owner's decision of 2026-10-13 recorded on it. Not chosen: a reminder after every tool call (context cost); prompts only.

## Facts

- F1 — On 2026-10-12/13 the agent answered a host-injected "say what you're doing" nudge in English after a long run of English tool output; no UserPromptSubmit preceded it, so the 5.120.0 hook never ran.
- F2 — Claude Code's PostToolUse hooks may return `hookSpecificOutput.additionalContext`, which the model reads beside the tool result; the payload carries `session_id`.
- F3 — The Claude chat hooks are registered in the root `.claude-plugin/plugin.json` and run `plugins/keel/scripts/mail-hook.js <event>` → `keel chat hook <event>`.

## Decisions

- D1 — `post-tool-use` joins the chat hook events (`PostToolUse`), registered for Claude only, like FileChanged and SessionEnd.
- D2 — With a declared owner language and a valid `session_id`, the hook keeps `<chat root>/sessions/<session_id>.language.json` (`{ count, at }`). Each PostToolUse adds one to `count`; when `count` reaches 15 (`KEEL_LANGUAGE_EVERY_TOOLS`) or `at` is 10 minutes old (`KEEL_LANGUAGE_EVERY_MS`), it prints the rule (`ownerLanguageRule`) as `additionalContext` and resets `{ count: 0, at: now }`. A first call with no record sets `{ count: 1, at: now }` and prints nothing.
- D3 — UserPromptSubmit that states the rule resets the record to `{ count: 0, at: now }`.
- D4 — A host-run session (#300) and a repository without `owner_language:` get no output and no record; the hook never fails the tool call.
