## Why

`#55` item 3 (split forward into `#92` item 1) measured that `keel guard status` and `keel guard
clear` each carry two boilerplate warning sentences (~300 chars combined) on every call,
unconditionally:

```
$ node bin/keel.js guard status | wc -c
     398
$ node bin/keel.js guard clear  | wc -c
     397
```

`openspec/specs/keel-touch-write-guard/spec.md:89` has a MUST requiring the guard command's own
result to carry the enforcement-boundary statement, specifically so a written manifest is never
read as observed enforcement (source: issue `#14`, archived change
`2026-07-27-honest-surfaces-and-owners`). That MUST does not pin exact wording — it names three
ideas the result must carry (the status describes the manifest only, enforcement is a runtime
hook Keel cannot observe, and a written manifest is not evidence a write was checked) — so the
~300-char cost is a wording choice, not a requirement.

The owner authorized (2026-08-12, on `#92`): "Shorten the wording only — the MUST … stays
satisfied (disclaimer stays in default output), the goal is reducing the ~300-char cost, not
removing or hiding it." This change implements exactly that authorization: reword, do not remove,
relocate to `--verbose`, or make first-call-only.

## What Changes

- The two standing warning sentences `guardResult` (`src/core/guard.js`) attaches to every guard
  result are reworded for brevity. Every required idea survives: the manifest is a disposable
  enforcement pointer and not durable authority (OpenSpec and Git are, and selection never
  derives from it); and separately, the reported status describes the manifest only — enforcement
  runs as a runtime hook Keel cannot observe, so a written manifest is not evidence a write was
  checked.
- Combined length drops from 344 characters to 278 (66 fewer, ~19%), measured on the literal
  strings.
- No status value, problem code, schema field, or existing behavior changes. Both warnings remain
  in every guard result (`start`, `status`, `clear`) by default — nothing moves to `--verbose` or
  becomes first-call-only, since the owner's authorization was for shortening only.
- `#92` item 2 (the `keel-align-expectations` injection-surface restructuring) is out of scope:
  the owner declined to authorize it as Full-mode work in the same decision.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-touch-write-guard`: the existing "Guard capability is reported from observed evidence"
  Requirement gains a scenario establishing that the standing warnings may be reworded for
  brevity as long as every required idea and the existing honesty guarantees survive — the
  Requirement's own text does not pin exact wording, and this scenario makes that explicit so a
  future editorial pass has the same room without reopening this decision.

## Impact

- `src/core/guard.js` — `guardResult`'s two `warnings` string literals are reworded. No change to
  the function signature, the `warnings` array shape (still two entries), or any other field.
- `scripts/validate_plugin.py` — no assertion changes needed: `validate_guard_status_is_not_
  enforcement_scenario` checks for the ideas (`enforcement`, `runtime hook`, `cannot observe`,
  `durable authority`) as substrings, not exact text, and forbids three assertive-enforcement
  phrases that this rewording does not introduce.
- No change to any other command, schema, or CLI surface.
