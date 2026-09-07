## Why

A contract fingerprint hard-stop says only that the value moved:

```
Task contract fingerprint drift for <change>#1.1: recorded sha256:261ffe8c49…, current sha256:10e527cc3f….
```

Two sha-256 values and nothing to search. The author is holding a `tasks.md` they have been writing Evidence into all session and a change directory of several files, and the message distinguishes none of them.

It produced a wrong record in this repository. The 5.42.0 archive states the anchor moved because of "an edit inside the Review, which the compiled capsule covers". A controlled experiment against the real gates measures the opposite: editing Review `Findings` leaves the fingerprint unchanged, while editing the text of a `design.md` statement the task's `Covers` cites changes it. The real cause was an edit made in the same step to a cited statement, and which one is no longer recoverable — the change was committed as one squashed commit. The correction is appended to that record and the mechanism is issue #115.

The capsule already knows the answer. Every authority entry it compiled carries the `source` it was resolved from — `openspec/changes/<change>/design.md`, the task block in `tasks.md`, a published spec — so the set of files whose *text* can move this fingerprint is available at the moment the drift is reported, and is not being reported.

## What Changes

- The drift message names the authority sources the capsule resolved text from, so the author has a search set instead of a directory.
- It states what the fingerprint does not cover — Evidence, Review, and the checkbox — because the failure this fixes was believing that it did.
- Both fingerprints keep their place in the message; nothing is removed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-stateless-continuity`: a reported drift names where the authority it covers was read from.

## Impact

- `src/core/context.js` — the drift message.
- `scripts/validate_plugin.py` — one new scenario.
- No change to what the fingerprint covers, to when drift is reported, or to what a drift blocks. The hard stop is unchanged; only what it tells the reader is.
- Risk: naming the sources invites the author to look only there. That is the correct search set — those are the files whose text the fingerprint covers — and the message says what is outside it rather than leaving the reader to assume.
