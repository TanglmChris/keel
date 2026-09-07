## Context

`Review Findings` carries three dispositions, each introduced by a marker. The gate finds them by scanning the whole field, which is correct — a finding may need several paragraphs and the marker can be anywhere in them. What the scan does not do is distinguish a marker from a quotation of one.

## Goals / Non-Goals

**Goals:**

- A marker quoted in inline code is not a disposition.
- One quoted mention cannot eclipse the real dispositions beside it.
- An author told their evidence is unusable can see what the gate read.

**Non-Goals:**

- Widening what `Resolved here:` accepts after the marker. See D4.
- Changing `Durable owner:`, `Discard reason:`, or the path and tracker vocabularies.
- Extending the treatment to fenced code blocks: `Findings` is a field value on one logical block and holds no fences.

## Decisions

- F1 — Probed against the real gate, 2026-09-07. A Findings block whose prose mentions the marker inside inline code and then records `Durable owner: https://github.com/x/y/issues/1` returns `fail` with `finding-resolution-evidence`; the same block recording `Resolved here: M1` returns the same failure. Both pass once the quoted mention is removed.
- F2 — `RESOLVED_HERE` is a global match and the caller breaks at the first claim it cannot resolve, so the quoted mention is evaluated *before* the real disposition and the real one is never reached. Basis: `src/core/gates.js`, read 2026-09-07.
- F3 — The rule already exists in this repository. `withoutInlineCode()` in `src/core/task-contract.js` blanks inline code before the unfilled-slot scan, established in 5.42.0 as "an inline-code span holds quoted material rather than an assertion". It is not used by the finding dispositions. Basis: read 2026-09-07.
- F4 — Across six repositories, 388 real `Resolved here:` dispositions were written in `Findings`. The form authors use is prose, then the marker, then the evidence, and it passes today: `one thing, fixed in this task. Resolved here: M1` and `Resolved here: M1, which asserts it.` both return `pass`. Basis: corpus survey plus six gate probes, 2026-09-07.
- D1 — Blank inline-code spans before the Findings scan, preserving length. Basis: the existing rules read positionally — `Durable owner:` captures to end of line, `Resolved here:` captures the next token — so a strip that shortens the text would move what they read. Replacing each span with an equal run of spaces removes the marker and leaves every other offset where it was.
- D2 — Blank for *finding* purposes only, and keep the original text for anything reported back. Basis: a diagnostic that quoted the blanked text would show the author a sentence with holes in it.
- D3 — Apply it to all four markers rather than only the one that fired. Basis: they are one vocabulary read from one field, and fixing the one observed would leave the same defect behind two markers nobody has quoted yet.
- D4 — Do not widen `Resolved here:`. Basis: F4. The original report treated the narrow capture as the defect, and the corpus does not support it — the form that fails is the marker used as a sentence clause, which is an authoring slip the diagnostic can name rather than a rule the gate should relax. 5.36.0's comment records what a wider capture costs: a block recording one fix and one tracker-owned follow-up was refused because the follow-up's URL was read as the fix's evidence.
- D5 — Name the token that was read in the refusal. Basis: the current message says the evidence "names neither a check nor a path", which is what the author believes they did name. Showing the token turns an argument into an observation.

## Hidden Knowledge / Assumptions

- A1 — A marker written inside a code span is never intended as a disposition. Basis: a disposition is a field prefix, and inline code marks quoted material — the whole convention 5.42.0 established. If an author ever wants a real disposition inside backticks there is no way to express it after this change, which is the same trade the unfilled-slot scan already makes. Durable owner: https://github.com/TanglmChris/keel/issues/114

## Risks / Trade-offs

- A finding whose only disposition is quoted now reports the generic owner refusal instead of the resolution one. That is the correct message — the block has no disposition — and it is what the block would have reported had the quotation never been there.
- Blanking is one more transformation between what an author wrote and what the gate read. Mitigated by D2: nothing reported back comes from the blanked text.

## Open Questions

None.
