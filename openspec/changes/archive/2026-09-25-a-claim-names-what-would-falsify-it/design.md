## Context

Two clauses, one shape. `Fails with:` already demonstrates it: a declaration written inside the
check text, so it enters the contract fingerprint, enforced by requiring its literal in a named
Evidence entry, and never judged for quality. Both additions reuse that shape exactly.

## Goals / Non-Goals

**Goals:**

- A check can declare the defect it detects and the failure that injection must produce.
- A check can bind a number it states to the output that produced it.
- Both enter the fingerprint, so editing them afterwards is drift.
- Existing tasks parse and behave identically.

**Non-Goals:**

- Judging an injection or a measurement. Keel records the claim.
- Making either mandatory.
- Running the injection. Keel does not execute the mutation; the author does and records what it
  produced, which is the same standing every `M<n>` result has.
- Multi-line checks. Checks are single-line today (F2) and this change does not alter that.

## Decisions

- **F1** — `Fails with:` is parsed in `src/core/task-contract.js:161` as
  `/\bFails with:[ \t]*`([^`\n]+)`[ \t]*$/i`, end-anchored on purpose so a mid-sentence mention is
  not a declaration, with a separate `FAILURE_MARKER` catching a present-but-malformed clause rather
  than ignoring it. Basis: read at 04b731c.
- **F2** — A Verify check is one line. `fieldValues` splits the field on newlines and treats each
  line as its own entry (`src/core/task-contract.js:113`), so the report's two-line example would not
  parse today, and the clauses must sit on the same line as the check. Basis: read at 04b731c.
- **F3** — The report's own measurements: `Fails with:` caused 8 of 24 non-`none`
  `Reauthorizations` in the reporting repository, three of its predictions were wrong, and each wrong
  prediction exposed a defect in the test. Six numbers in one session were estimates or recollection
  presented as measurement, three of which reached durable artifacts; the one that was caught sat in
  a `Fails with:` clause. Basis: issue #132, with archive paths cited per row.
- **F4** — Measured in *this* repository, to know what a broad numeric rule would cost: 87 archived
  changes, **6811 inline-code spans inside Evidence, 847 containing a digit (12%)** — 541 other text
  containing a number, 170 version-like, 57 sha256, 56 bare numbers, 14 git shas. Of 256 sha256
  literals, **247 are on `Contract:` lines written by the gate** and only 9 are author-supplied, all
  of them incidental mentions rather than measurement claims. Basis: measured 2026-09-25.
- **D1** — **The clauses chain, parsed as a trailing sequence.** The parser strips one matching
  trailing clause at a time from the end of the check text until none matches. `Fails with:` keeps
  its exact current meaning whenever it stands alone or comes last, which is every task in the
  archive. Basis: F2 — the clauses share one line, so a single end-anchored slot would make them
  mutually exclusive, and the report's motivating example uses two on one check.
- **D2** — **`Detects:` takes two literals: the mutation and the failure it must produce.** The
  enforced one is the second. Keel does not run the mutation, so the mutation literal is the
  author's record of what they changed and the failure literal is the claim completion checks —
  present in a `.detects` Evidence entry for the same check. Basis: the `Fails with:`/`.red` pairing,
  unchanged in shape.
- **D3** — **`Measured:` is enforced against the check's own bare `M<n>` Evidence.** That entry is
  where the command and its output are recorded, so a literal that the output does not contain is
  either unpasted or not measured. Basis: F3's caught case worked exactly this way against `.red`.
- **D4** — **Opt-in, not universal.** The broad rule the report calls its lightest version — every
  inline-code number in Evidence must appear in a named command's output — is declined on
  measurement. F4 puts it against 847 spans in this repository, a majority of them version strings,
  counts the author computed, and quoted references that legitimately appear in no command output.
  Each would be a false stop, which this project treats as the most expensive failure shape when
  nobody is watching. **The weakness of opt-in is stated rather than hidden:** an author who invents
  a number will not volunteer to bind it. What answers that is F3 — `Fails with:` is opt-in too, and
  it still caused a third of the reporting repository's re-records, because the cost lands after the
  author has declared and is then held to it. Basis: the owner's decision, 2026-09-25, on F4.
- **D5** — **The only refusal is a malformed clause, and this narrows the report.** It proposed
  refusing `Detects:` on checks with no injectable defect, naming "shapes other than
  `(regression)`". A `(regression)` check is where an injection is worth most: it has no honest red
  by construction, and `Fails with:` is already exempt there, so injection is the only mechanism that
  can show such a check is not vacuous. Refusing it there would remove the clause from its best use.
  Keel also cannot tell an injectable defect from a non-injectable one, exactly as it cannot judge
  whether a `Fails with:` literal is a good prediction. Basis: the exemption rule in
  `keel-verification-layering`, and the `Fails with:` non-judgement this copies.

## Hidden Knowledge / Assumptions

- **A1** — A declared injection is a claim that the author ran the mutation and saw the failure. Keel
  does not run it and cannot distinguish a recorded run from a plausible-looking sentence, the same
  standing as every other `M<n>` result. Basis: Non-Goals. Consequence if wrong: a fabricated
  `.detects` passes, and what catches it is Review, not the gate — which is why the surfaces say
  Keel records the claim rather than verifying it.

## Risks / Trade-offs

- **Three clauses on one line is dense.** A check carrying all three is long and hard to read. Not
  mitigated by mechanism: no clause is mandatory, and a check needing all three is a check doing
  enough to deserve the length.
- **`Measured:` can be satisfied trivially** by declaring a literal the output obviously contains.
  Accepted, and identical to `Fails with:` — the value is in the author having to decide the literal
  before running, not in Keel grading it.
- **The parse widens.** A `Fails with:` clause followed by another clause previously read as
  malformed and refused; now it parses. The direction is toward accepting authors' intent, and no
  input that parsed before parses differently.

## Open Questions

None.
