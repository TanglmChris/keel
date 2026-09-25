## Why

`node scripts/bump_version.js minor` writes a stub section into `keel/CHANGELOG.md`:

```
## 5.68.0 - TODO: summarize this release

- TODO: describe the change.
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 5.68.0; …
```

The convention is to fill that section in. Writing the release entry *above* it instead leaves an orphan
stub, and nothing catches it (#151): `version-alignment` looks for an alignment line for the version
being released, finds the **stub's**, and passes. `npm test` was green with the file in that state.

It happened twice in a row, in 5.67.0 and 5.68.0, and was found by eye while grepping the changelog for
something unrelated — three commits after the first one shipped.

Two properties make it worth a check rather than a habit:

- **The placeholder is what satisfies the check.** The stub carries the `Version alignment:` line the
  scenario reads, so the section that describes nothing is the section that passes. That is the shape
  this suite refuses everywhere else; `keel gate task-complete` already refuses `TODO` in Evidence
  through `unfilledToken`, and the changelog has no equivalent.
- **It reaches the reader.** `## 5.68.0 - TODO: summarize this release` is published, above a second
  section for the same version. A consumer sees two 5.68.0 headings, one saying the release was never
  described.

## What Changes

- **`version-alignment` refuses a changelog whose released version is not described**: a `TODO` in that
  version's heading, a `- TODO:` bullet under it, or two `## <version>` headings for the same version.
  Each names the line it found.
- The refusal is scoped to **the version being released**. An older section is history; rewriting the
  rule to sweep the whole file would fail on the archive for reasons no current author can act on.

## Capabilities

### Modified Capabilities

- `keel-validation-runner`: the release check reads whether the release describes itself, not only
  whether its version markers agree.

## Impact

- `scripts/validate_plugin.py` — the assertion.
- `keel/CHANGELOG.md` — the entry for this release.
- **Not adopted**: having `bump_version.js` stop writing a stub. The stub is what carries the alignment
  line the check reads, so removing it would let an author who forgot the entry entirely pass with no
  section at all — the same defect with nothing on screen.
