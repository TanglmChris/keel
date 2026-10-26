## Facts

- F1 — `src/core/task-contract.js` compiles each check as `normalizeText(match[3])`, which replaces every `\s+` with one space, and then extracts the `Fails with:`, `Detects:`, and `Measured:` literals from that text. The compiled literals therefore never hold a run of whitespace.
- F2 — `src/core/gates.js` tests `String(recorded).includes(literal)` against the raw Evidence in three places: `red-missing-declared-failure`, `injection-missing-declared-failure`, and `measurement-missing-from-evidence`.
- F3 — The fingerprint is computed over the normalized check text, so normalizing the comparison does not change what an edit to a declaration does to the fingerprint.

## Decisions

- D1 — All three comparisons collapse every run of whitespace to one space on both sides before testing containment (owner, 2026-10-26). The literal is already collapsed (F1), and the recorded Evidence is collapsed the same way. Nothing else is folded: case, punctuation, and quoting still count.
- D2 — Each of the three refusals adds that runs of whitespace are compared as one space.
- D3 — The literal keeps being extracted from the normalized check text (F1). Keeping the raw backtick text was the alternative the issue preferred. It was not taken, because a check wrapped across lines in tasks.md would then carry a line break and its indentation into the literal.
