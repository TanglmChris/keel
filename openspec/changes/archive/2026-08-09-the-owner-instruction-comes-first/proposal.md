## Why

`#49` (section 2) measured that the `finding-owner` diagnostic — produced by `keel gate
task-complete` when a Review `Findings` value carries no recognized disposition — states its
one actionable instruction ("Name a path after `Durable owner:` so it reads as the owner
rather than a file the finding mentions") as its *last* sentence, after a three-way enumeration
of accepted forms (`Resolved here:`, `Durable owner:`, `Discard reason:`/`Discard rationale:`).
An author who has genuinely forgotten to name a path — the reported failure mode — reads the
enumeration first and the instruction last, when the instruction is the only sentence that
tells them what to do.

Confirmed still current at 5.33.0 (`src/core/gates.js:863-877`): the imperative sentence is
still the message's closing sentence, unchanged since it was first reported.

Two prior unattended runs on this issue (2026-08-02, 2026-08-04/PR #83) each independently
declined to move it: not because moving it is a material decision, but because both rounds were
mid-diff on an unrelated behavior fix and judged that editing this string in the same diff would
mix a message edit with a behavior change and make neither easy to review. The 2026-08-04 comment
states the rationale directly: "跨行既然不再是这个检查的失败方式，那句话最误导的成因已经消失；剩下的是文案偏好" (now that
line-wrapping is no longer this check's failure mode, the most misleading cause behind that
sentence is gone; what remains is a wording preference) — and closes with "留给你" (left for you).
Section 1 of the same issue (bare `D<n>` Covers references reported `Missing`) is a separate,
still-unresolved material decision escalated twice to the owner; this change does not touch it.

This change is that isolated diff: reorder one message's sentences, in a change with no other
behavior edit, so the review is exactly the pure wording change the prior runs deferred.

## What Changes

- `finding-owner`'s message states its actionable instruction — name a path after
  `Durable owner:` — immediately after its opening sentence, before enumerating the three
  accepted disposition forms, instead of after them.
- No word in the message is added, removed, or reworded; only its position moves. The three
  disposition forms, `DURABLE_OWNER_FORMS`, every other diagnostic code and message, and what
  `task-complete` accepts or refuses are all unchanged.
- The existing `core-gates` validation scenario gains order assertions so a future edit cannot
  silently move the instruction back to the end.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: the `finding-owner` diagnostic's existing requirement ("A finding resolved
  in its own task is recorded as resolved") gains a sentence-order constraint and a scenario
  proving it, alongside its unchanged content requirements.

## Impact

- `src/core/gates.js` — one message string's sentence order, inside the existing
  `finding-owner` branch of `taskComplete`'s review checks. No function signature, code path, or
  accepted/refused verdict changes.
- `scripts/validate_plugin.py` — the existing `core-gates` scenario gains three single-cause
  order assertions on the same `finding_owner_message` it already captures.
- Output text of the `finding-owner` diagnostic only. No change to `task-start`, `task-complete`
  exit codes, or any other diagnostic.
