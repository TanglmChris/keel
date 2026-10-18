## Context

#345 offered skipping commit ids and code, or refusing only near-misses of a member name. The first keeps the typo rule exactly where it was meant to apply and adds no fuzzy matching.

## Facts

- F1 — `resolveMentions` (`src/core/chat/store.js`) scans `(^|[^\w@/])@([A-Za-z0-9][A-Za-z0-9/-]*)` over the whole text and throws for any token that resolves to nothing; `post`, `dm` and `todo` share it.
- F2 — `lenientMentions` (`src/core/chat/bridge.js`) uses the same pattern for Slack text and leaves unknown tokens as text (D16).

## Decisions

- D1 — `mentionText` blanks fenced blocks (```` ``` ```` to ```` ``` ````) and inline code spans with spaces of the same length before the scan, so offsets do not move; both readers use it.
- D2 — A token matching `^[0-9a-f]{7,40}$` that resolves to no member, alias, `all`, `owner` or cross-project role is skipped; one that does resolve is still a mention.
