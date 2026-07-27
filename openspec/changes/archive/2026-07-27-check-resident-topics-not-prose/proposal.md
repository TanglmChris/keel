## Why

The resident-block check calls its entries *topics* and matches them as *prose*.

`RESIDENT_BLOCKS[0]["required"]` is a flat list of ten substrings, and `validate_resident_blocks` tests each with `required not in managed_block`, reporting "missing required topic". So the consumer bootstrap's wording is pinned character-for-character by a check whose stated purpose is that the block still *covers* the essential topics.

This has a demonstrated cost. On 2026-07-27, adding the record-layer qualifier from 5.3.0 to the bootstrap — so a consumer stops inferring that Touch bounds every write — failed twice:

```
Keel v4.1.0 baseline validation failed:
- Bootstrap resident block missing required topic: Touch is the write boundary
skill-portability-policy source policy validation failed:
- Bootstrap resident block missing required topic: Touch is the write boundary
```

Both failures came from the same function, called by `run_baseline` and by the `skill-portability-policy` scenario. The fix that shipped had to keep the literal phrase as a substring and append to it, rather than say the thing the way it wanted to be said.

The ten entries are also not one kind. Four are commands or markers — `Keel Bootstrap`, `keel context`, `keel gate task-start`, `keel --init` — where a rename genuinely *should* fail the check. The rest are prose, where pinning the words guards nothing the byte budget is not already squeezing.

Reported as issue #15 item 1.

## What Changes

- A required entry may be a literal string **or** a pattern. Literal is for a command, a marker, or an identifier, where a rename must fail. A pattern is for prose, where the concepts must remain but the wording may move. The error names which kind was missing.
- Convert the one entry that has demonstrably blocked work — the Touch boundary statement — to a pattern requiring `Touch` and a `bound…` word in the same statement.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-validation-runner`: a required resident-block entry is matched as a topic when it is prose and as a literal when it names a command or marker.

## Impact

- The consumer bootstrap's prose can be improved without a validator edit, which matters because that block is under a byte budget and gets reworded to fit.
- Deleting a required statement still fails, and renaming a command still fails, so the check keeps what it was for.
- Honest limit: this does **not** unblock naming the record-layer exemption in the bootstrap. That was blocked by the 1024-byte budget, not by this assertion; a freer wording buys a few bytes, not the ~19 the fuller sentence needs. Issue #15's remaining half stays with the budget question.
- The other nine entries are left as they are; the mechanism and the rule are the path for whichever one bites next.
