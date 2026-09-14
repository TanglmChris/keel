## Why

5.55.0 shipped `keel gate task-start --record --keep-evidence M1,M3`: the one way an author
can say a contract change did not touch a check, so the stale-evidence report stops saying
*all of it*. Issue #134 measured its use in a consumer repository — **67 task capsules, used
once** — and found why:

```
$ grep -rn 'keepEvidence\|keep-evidence' src/
src/core/gates.js:307   const declaredKeep = Array.isArray(options.keepEvidence)
src/core/gates.js:313      "keep-evidence-without-record",
src/core/gates.js:331      "keep-evidence-unknown-check",
```

It is named in its own two error paths and nowhere else in the source. Only an author
**already using it** is ever told it exists. Everyone else lands in the blanket branch and
reads *execution evidence produced under the previous contract is stale* — and, acting on
that sentence in good faith, re-runs everything. In that repository one re-verification is a
**median 256 s**; the reporter paid it twice in one session, once for a contract change that
was a single literal inside a `Fails with:` clause with no causal path to the check they
re-ran.

The comment directly above that branch already describes the defect:

> What it can stop doing is saying "all of it" to an author who can see that one check's
> assertion did not change — because an author acting on that sentence in good faith re-runs
> everything, and issue #112 measured four such re-verifications in one session

5.55.0 built the way out and left it unsigned.

## What Changes

- Every exit that tells an author their execution evidence is stale also names the declaration
  that narrows it. There are three, and today none of them does:
  - `task-start --record`'s blanket stale-evidence warning (`src/core/gates.js`) — the one
    #134 names.
  - `task-complete`'s `contract-drift` refusal (`src/core/gates.js`), which already names
    `keel gate task-start --record` — the exact command the flag belongs to — and stops there.
  - the context drift hard-stop's reauthorization sentence (`src/core/context.js`), which
    already says to re-run `task-start` and record the new anchor.
- The sentence is conditional in the same way the flag is: it points at a declaration the
  author makes only for checks whose assertions did not move, and says the reason belongs in
  `Reauthorizations`.
- **Nothing about the flag itself changes** — not what it accepts, not what it narrows, not
  that Keel records the claim without verifying it. This change is what the surfaces say, not
  what the gate does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-core-gates`: a report of stale evidence names the declaration that narrows it — at the
  blanket re-record warning and at the `task-complete` drift refusal.
- `keel-stateless-continuity`: the reported drift's reauthorization sentence names it too.

## Impact

- `src/core/gates.js` — two message strings.
- `src/core/context.js` — one message string.
- `scripts/validate_plugin.py` — the existing `evidence-survives-what-did-not-change`
  scenario's control currently asserts only that the word `stale` appears, so it does not pin
  the blanket wording; it gains the assertion, and the two drift exits gain theirs.
- **What this does not change**: which evidence is stale, what the fingerprint covers, when
  drift blocks, or what completion requires. A message that names a flag is not a gate that
  accepts one, and the flag still refuses an undeclared label and still refuses to appear
  without `--record`.
