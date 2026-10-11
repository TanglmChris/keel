## Context

Issue #271.

## Facts

- F1 — `UNFILLED_TOKEN` in `src/core/task-contract.js` is `/(<[^>]+>|\bTODO\b|\bTBD\b|\bplaceholder\b)/i`; the `i` flag applies to all four alternatives. `isConcrete` and `unfilledToken` both read it, after stripping inline code, so every concreteness judgement — required fields, `M<n>` checks, Evidence, Reauthorizations, the evidence-first `Reason` — shares it.
- F2 — The `non-concrete-verify` message in the same file says "Angle brackets, TODO, TBD, and the word placeholder all read as unfilled, including inside prose."
- F3 — `openspec/specs/keel-core-gates/spec.md` lists the set as "`<slot>`/`TODO`/`TBD`/`placeholder`" in the Reauthorizations requirement; no published requirement states the set itself or its case.
- F4 — `keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md` records the decision that inline code exempts every form, and that a bare token in prose stays non-concrete. It does not address case.

## Decisions

- D1 — The marker words read as unfilled only in capitals: `TODO`, `TBD`, `PLACEHOLDER`. Capitals are the form people use to mark something unfinished; lowercase and mixed case are words. `PLACEHOLDER` is kept in capitals so the three words follow one rule rather than dropping one of them.
- D2 — Angle-bracket slots are unchanged: `<…>` with any content outside inline code stays unfilled, including the prose numeric-range case the published scenario already names.
- D3 — The change only narrows: nothing judged concrete before becomes non-concrete.
