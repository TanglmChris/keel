## Context

`Findings` is free prose in a repository whose subject is the protocol, so the marker vocabulary
appears inside it constantly. 5.42.0 already established that a **quoted** marker is a quotation
rather than a disposition. A **negated** one is the same class of mistake and was not covered.

## Goals / Non-Goals

**Goals:**

- `Not resolved here:` and its kin are not dispositions.
- A real marker opening a clause still parses, including after a line break in wrapped prose.
- A marker swallowed by the narrowing is refused with a diagnostic naming why.

**Non-Goals:**

- Detecting negation semantically. The rule is positional, like every other rule here.
- Changing what resolution evidence must be, or any of the three dispositions' meanings.

## Decisions

- **F1** — The pattern is `/\bresolved here\s*:[ \t]*(\S*)/gi` at `src/core/gates.js:675`, with a
  sibling presence pattern `DISPOSITION_MARKER` at `:718` covering `resolved here`,
  `durable owner`, and `discard reason|rationale`. `\b` matches at the space in `Not resolved
  here:`. Basis: read at fe2b341, and reproduced against this session's own task 1.3.
- **F2** — The comment above the capture already records that the block "used to be one line and
  may now wrap across several", and that every rule downstream reads positionally. So the opening
  rule has to admit a line break, not only the start of the value. Basis: read at fe2b341.
- **D1** — **A marker opens its clause when it is preceded by the start of the value, a line break,
  or sentence-ending punctuation.** Expressed as a lookbehind, so the existing captures keep reading
  from the same offsets — F2 records that downstream rules are positional, and a rule that shortened
  the text would move what they read. Basis: the failing case is `Not ` immediately before the
  marker, and a word before a marker makes it part of that sentence rather than the head of a clause.
- **D2** — **The same rule applies to both patterns.** If only the capture narrowed, `Not resolved
  here:` would still count as a disposition being *present* while supplying no evidence, which is a
  worse state than either — the finding would be accepted as disposed with nothing behind it. Basis:
  the two patterns answer halves of one question.
- **D3** — **The narrowing is allowed to refuse a real marker, because it cannot do so silently.** A
  `Resolved here:` written mid-sentence stops being recognized; the finding then carries no
  disposition, which the existing rule already refuses. What this change owes is that the refusal
  says why, so the author is not told "carry a disposition" about a sentence that visibly carries
  one. Basis: the alternative — accepting a marker anywhere — is the defect.

## Hidden Knowledge / Assumptions

- **A1** — Sentence-ending punctuation is approximated by a character class rather than parsed. A
  marker after a closing parenthesis or a quotation mark would not be recognized. Basis: not
  measured; no such form exists in this repository's archive. Consequence if wrong: the author gets
  D3's loud refusal naming the requirement, which is recoverable in one edit.

## Risks / Trade-offs

- **A narrowing can surprise.** Mitigated only by D3: the failure is loud and names the rule. There
  is no silent path.
- **The rule is positional, so a determined sentence can still defeat it** — "the finding is not
  Resolved here: M1" opens no clause and will be refused, while "Resolved here: M1 is not what
  happened" parses. Accepted: Keel does not read English, and the shape it can check is where the
  marker sits.

## Open Questions

None.
