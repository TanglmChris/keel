## Context

#151: a release can ship with `bump_version.js`'s TODO stub still in the changelog, because the stub
carries the line the release check reads.

## Facts

- **F1** — `version-alignment` asserts that a `Version alignment:` line exists for the version being
  released. The stub `bump_version.js` writes contains that line, so the check is satisfied by the
  placeholder and never looks at the heading above it.
- **F2** — the repository already has the vocabulary for this: `unfilledToken` in
  `src/core/task-contract.js` treats `<slot>`, `TODO`, `TBD`, and `placeholder` as unfilled, and
  `keel gate task-complete` refuses Evidence containing one. The changelog had no equivalent.
- **F3** — measured: it occurred in 5.67.0 and 5.68.0, the two releases immediately before this one,
  and in both the suite was green. The failure mode is silence, not a wrong answer.

## Decisions

- **D1** — the check is scoped to the version being released, read from `package.json`. An older
  section is history a current author cannot act on, and a rule that swept the whole file would fail
  on the archive — which is how a check gets disabled rather than fixed.
- **D2** — three shapes are refused, because the stub can survive in three ways: `TODO` in the
  version's heading, a `- TODO:` bullet inside its section, and two `## <version>` headings for that
  version. The third is what the actual defect looked like, and neither of the first two would have
  caught it alone if the author had renamed the stub's heading.
- **D3** — the refusal names the offending line verbatim. "The changelog is incomplete" sends an author
  to read a 700-line file; the line itself is one search away from the fix.
- **D4** — `bump_version.js` keeps writing the stub (F1). Removing it would mean an author who never
  wrote an entry has no section at all, and the check would then have to distinguish absent from
  unfilled — the same defect with less on screen.

## Alternatives considered

- **A1** — assert the section's length or word count. Rejected: it measures effort rather than
  presence, and a stub padded to the threshold would pass. The token is the checkable property.
- **A2** — refuse `TODO` anywhere in the changelog. Rejected by D1: the file legitimately quotes the
  token when describing the rules that refuse it, which is true of the 5.29.0 entry already in the
  file, and a check that fires on the description of itself is one an author deletes.

## Open questions

None.
