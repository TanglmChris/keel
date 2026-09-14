## Context

This is a discoverability defect in a feature that already works. 5.55.0 proved the narrowing
behavior red-green and documented it in `README.md`; what it did not do is connect the feature
to the one moment an author needs it, which is the moment they are being told to re-verify.

Alignment ran the quick path: the request is complete, the reporter names the file and the
branch, and no choice here can change user-visible gate behavior — only what a message says
about a flag that already exists.

## Goals / Non-Goals

**Goals:**

- An author who has never used `--keep-evidence` learns it exists at the moment it would save
  them a re-verification, not after they have already paid for one.
- All three staleness exits say it, because an author hits whichever one their workflow
  reaches first and there is no reason for two of them to stay silent.

**Non-Goals:**

- Changing what `--keep-evidence` accepts, what it narrows, or what it verifies. See D4.
- Making the suggestion conditional on Keel having judged that some check *is* unaffected.
  See D3.
- Auditing every Keel message for a missing affordance. This change fixes the three exits that
  share one stale-evidence sentence; the general question is #135's.

## Decisions

- F1 — Three exits tell an author their evidence is stale, and none names `--keep-evidence`:
  `src/core/gates.js:430`/`:437` (the re-record warning, both branches share the sentence),
  `src/core/gates.js:143-150` (the `contract-drift` problem), and
  `src/core/context.js:128-133` (`driftSearchSet`). Basis: `grep -rn "re-verify\|previous
  contract is stale" src/ bin/`, read 2026-09-14.
- F2 — In the source, `--keep-evidence` appears only at `src/core/gates.js:307`, `:313`, and
  `:331` — its parse site and its two refusals. Basis: the grep in #134, re-run 2026-09-14.
  The reporter grepped `src/` only; it is also in `README.md:375`, which does not change the
  finding, because a reader who is mid-refusal is not reading the README.
- F3 — The existing `evidence-survives-what-did-not-change` scenario's control asserts only
  `"stale" in said(blanket)`, so the blanket branch's wording is currently unpinned and this
  change does not break it. Basis: `scripts/validate_plugin.py:26500-26512`, read 2026-09-14.
- D1 — Fix all three exits rather than only the blanket branch #134 names. Basis: the reporter
  names the context drift stop themselves ("漂移硬停同理"), and the third — `task-complete`'s
  `contract-drift` — is the strongest case of the three: it already prints `keel gate
  task-start --record`, so it names the command and omits its one relevant flag. Leaving two of
  three would reproduce the reported defect at a different exit.
- D2 — The added sentence names the condition, not just the flag: the declaration is for checks
  whose *assertions* did not move, and the reason goes in `Reauthorizations`. Basis: a bare
  `--keep-evidence M1,M3` in a refusal reads as a way to make the refusal go away. The flag's
  own contract is that Keel records the claim and does not verify it (D3 of the 5.55.0 change),
  so the sentence that introduces it has to carry the same limit, for the same reason
  `README.md` puts the limit in the same paragraph as the feature.
- D3 — The suggestion is unconditional text, not a computed hint about which checks are
  unaffected. Basis: the gate retains only the previous fingerprint and not the capsule behind
  it, so it cannot compare a check's former text to its current one — the limit #115 owns and
  the reason the flag is a declaration at all. A message that named specific checks would be
  claiming exactly the knowledge D3 of 5.55.0 says the gate does not have.
- D4 — No behavior change. Basis: `--keep-evidence` already validates its labels, already
  refuses without `--record`, and already leaves completion untouched; all three were proven
  red-green in 5.55.0. Reopening any of them would be a different change with a different
  risk, and #134 asks for none of it.
- D5 — The narrowed branch (`kept.length > 0`) does not gain the sentence. Basis: its reader
  has already used the flag, which is the population F2 shows is already served. Adding it
  there would put a suggestion to use a flag inside the output produced by using it.

## Hidden Knowledge / Assumptions

- A1 — An author who is told the flag exists at the refusal will read `README.md` for what it
  does not verify before relying on it. Basis: cannot be checked from here, which is why D2
  puts the limit in the message rather than trusting the trip to the README.

## Risks / Trade-offs

- Three messages get longer, and #135 argues in this same batch that every non-actionable line
  in an agent's context dilutes the actionable ones. The trade is accepted because this line is
  the actionable kind: it is read at a decision point, by someone who has just been told to do
  something expensive, and it names the alternative. A line that changes what the reader does
  next is the case the dilution argument is about protecting.
- An author could reach for `--keep-evidence` to silence a refusal they should have honored.
  That exposure is the flag's, not this change's — it exists today for anyone who knows the
  flag — and the answer 5.55.0 recorded still holds: the declaration is visible, attributable,
  and challenged in Review. What changes here is only that the population who can do it is no
  longer restricted to those who already found it.

## Open Questions

None.
