## Context

Issue #305 and the owner's decision of 2026-10-12 recorded on it. Not chosen: a machine-wide setting; a reminder at session start only.

## Facts

- F1 — The owner's `~/.claude/CLAUDE.md` says to use Chinese for everything addressed to them; the agent still replied in English three times in one session on 2026-10-12, each after long English tool output.
- F2 — On Claude the chat hook script runs for UserPromptSubmit in every session (`.claude-plugin/plugin.json` → `mail-hook.js` → `keel chat hook user-prompt-submit`), and on Codex through `codex-mail-hook.js`; today it prints nothing in a worktree with no chat role.
- F3 — The protocol's only language line is "Match the user's language where practical" in `AGENTS.md`.

## Decisions

- D1 — `readOwnerLanguage(repo)` reads the scalar `owner_language`; a value matching `^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$` is the tag, anything else yields a warning `keel/config.yaml owner_language \`<v>\` is not a language tag such as zh or en; it is ignored.` and no tag.
- D2 — The rule text, from one function `ownerLanguageRule(tag)`: `Owner language: <tag> — write every message to the owner in <name>: replies, summaries, reports, and the question and options of a structured-choice prompt. Work in any language; identifiers, commands, paths, and quoted output stay as they are.` `<name>` is `Chinese (中文)` for `zh*`, `English` for `en*`, `Japanese (日本語)` for `ja*`, `Korean (한국어)` for `ko*`, else the tag. For `zh*` it adds `对负责人说话一律用中文。`
- D3 — `keel context` carries `ownerLanguage` (the tag) when declared; the session-start projection adds `- <rule>`.
- D4 — The chat hook, on `user-prompt-submit`, when the repository declares a tag, prefixes the rule to any chat notice text in `additionalContext`, and prints it alone when there is no notice — with or without a chat role. A host-run session (#300) prints nothing.
- D5 — `AGENTS.md`'s line becomes: `- When \`keel/config.yaml\` declares \`owner_language:\`, every message to the owner — replies, summaries, reports, and the question and options of a structured-choice prompt — is in that language, whatever language the work and its sources are in; identifiers, commands, paths, and quoted output stay as they are. Otherwise match the user's language where practical; understandable choices are part of the protocol.`
