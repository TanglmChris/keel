## Why

A Review `Findings` entry recording an **unresolved** finding, with a valid tracker owner, was
refused (#144):

```
Status: fail
Problem: Review Findings records a finding as resolved here, but its evidence is not usable —
it read `it`, which names neither a check nor a path.
```

The text it matched:

> … **Not resolved here:** it is a different module and would be scope expansion … Durable owner:
> https://github.com/TanglmChris/keel/issues/143

The marker scan is `/\bresolved here\s*:[ \t]*(\S*)/gi`. The `\b` sits happily at the space inside
`Not resolved here:`, so the negation was read as the marker and the next word, `it`, as its
resolution evidence.

This is a **false stop**, the shape this project treats as the expensive one when nobody is
watching: the gate refuses something correct and its diagnostic asserts a disposition the author did
not claim, so their next move is to hunt for an `M<n>` that should not exist.

It also pushes the wrong way. `Findings` is free prose by design, and "not resolved here" is the
most natural way to write what a `Durable owner:` entry means. The workaround is knowing the phrase
is booby-trapped — knowledge that lives nowhere and is acquired only by tripping. And
`## Follow-up Ownership` is explicit that "picking the marker that passes over the one that is true
files a repair as a dismissal"; this defect does the reverse, reading a dismissal as a repair and
then refusing it for lacking repair evidence.

## What Changes

- **A disposition marker counts only where it opens its clause.** The start of the value, a line
  break, or sentence-ending punctuation may precede it; a word may not. Applied to both the marker
  scan that captures resolution evidence and the one that detects a disposition is present, so the
  two cannot disagree about what a marker is.
- **The narrowing fails loudly, which is what makes it safe.** A real `Resolved here:` that no longer
  parses does not become unchecked — the finding then carries no disposition at all, and that is
  already refused. The diagnostic for it names the opening requirement, so an author whose marker
  was swallowed mid-sentence is told why rather than left guessing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-expectation-slice-evidence-gates`: a disposition marker is recognized only where it opens its
  clause, so a negated mention is not a disposition.

## Impact

- `src/core/gates.js` — the two marker patterns and the disposition diagnostic.
- `scripts/validate_plugin.py` — one new scenario.
- The change is a narrowing, so a form that parsed before may now not. It cannot pass silently: a
  finding with no recognized disposition is refused by the rule that already exists.
