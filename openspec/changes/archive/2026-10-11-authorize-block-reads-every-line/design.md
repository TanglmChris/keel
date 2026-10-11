## Context

Issue #275.

## Facts

- F1 — `configList` in `src/core/config.js` matches items with `^\s+-\s*(\S+)\s*$` and ends the block at the first line that does not match; `readStandingAuthorization` is its only caller.
- F2 — `readPushGlobs` in `plugins/keel/scripts/pretooluse-guard.js` matches `^\s+-\s*push:(\S+)\s*$`, so `- push:claude/*  # note` is not read as a glob.
- F3 — An unrecognized entry already voids the whole declaration and is named with the accepted forms (keel-standing-authorization, "An unrecognized action name is reported, not granted").

## Decisions

- D1 — In the block, a line at column zero ends it; an indented comment or blank line is skipped; every other indented line is an entry. A list item contributes its text after `- `; a line that is not a list item contributes its trimmed text. Both go through the existing classification, so the refusal path is F3's.
- D2 — A trailing comment is ` #` (whitespace, then `#`) to the end of the line, as YAML reads it, and is stripped before the entry is read, in both readers.
