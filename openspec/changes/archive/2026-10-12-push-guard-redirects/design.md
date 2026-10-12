## Context

Issue #286.

## Facts

- F1 — `shellSegments` in `plugins/keel/scripts/pretooluse-guard.js` splits words on whitespace and segments on `;`, newline, `&`, `|`, `(`, `)`, honouring quotes; it has no notion of redirection, so `2>&1` yields the word `2>` and a segment boundary at `&`.

## Decisions

- D1 — Outside quotes, `<` or `>` starts a redirection: a word made only of digits immediately before it is its file descriptor and is dropped; a second `>` or `<`, or `&` followed by digits or `-`, belongs to the operator; otherwise the next word is its target and is dropped. `&>` and `&>>` are redirections too, not a segment boundary. Heredoc `<<` keeps its existing handling.
