## Why

A `Durable owner:` naming a path with a non-ASCII directory is refused, and the refusal names a path nobody wrote. Reported in #60: `notes/note-006-转岗最难的不是流程/note.md` exists and `git ls-files` finds it, but `keel gate change-close` reports

```
Problem: E4 names `notes/note-006-` as its durable owner, but no such file exists in this repository.
```

The extractor is `/[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)+/`. It stops at the first character outside ASCII, and the truncated prefix is then checked for existence and reported as missing. Measured 2026-08-02 at 5.17.0, three shapes fail: a path with a CJK segment truncates, a path whose *first* segment is CJK does not match at all, and a path containing a space truncates at the space.

This is the third instance of one defect class in this repository. #40 fixed it in `gitPaths`, where a Chinese filename declared on the first line of `Touch` was reported as outside `Touch`. #58 is its inverse — a character class too *wide*, matching a fake phone number as a commit hash. The rule was right every time; the implementation of the criterion was narrower than the rule.

For a project whose directories are named in Chinese — the reporter's note packages take their titles as directory names — the most accurate owner is unnameable, and the workaround is to name a less accurate one.

## What Changes

- Every path reader in the gates accepts the paths the filesystem accepts: any non-whitespace run containing a separator, regardless of script.
- A path may be wrapped in backticks, which additionally covers paths containing spaces. This is not a new convention — `touchEntries` already strips backticks from `Touch` entries, so `Touch` and `Durable owner:` stop disagreeing about how a path is written.
- Trailing punctuation adjacent to a path is trimmed, so `Durable owner: notes/…/note.md。` and `…note.md,` name the file rather than a sibling that does not exist. Both ASCII and CJK punctuation, because a Chinese sentence ends in `。` and the whole point is that these readers stop being ASCII-shaped.
- The four affected sites in `src/core/gates.js` — the durable-owner reader, the resolution-evidence reader, and the two `keel/archive/…` readers — read one shared extractor rather than four copies of a character class.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-core-gates`: the requirement that a durable owner or resolution path is checked for existence is narrowed to what it was protecting — that the path is real — and separated from what it accidentally required, that the path be spellable in ASCII. States that a backtick-wrapped path is accepted.

## Impact

- `src/core/gates.js`: one shared extractor replaces four inline character classes.
- `scripts/validate_plugin.py`: a scenario covering the reported shapes and the backtick form, alongside the existing `git-paths-carry-no-escaping`, which covers the same class on the worktree-reading side.
- Deliberately unchanged: the change-name patterns (`context.js:199`, `gates.js:65`, `context.js:386`). Those validate an OpenSpec-generated kebab-case identifier, not a filesystem path, and widening them would accept names OpenSpec will not produce.
- Risk: a wider extractor could capture trailing prose as part of the path. Mitigated by requiring a separator, stopping at whitespace, and trimming a defined punctuation set — and a wrong capture fails loudly by naming a path that does not exist, which is the same failure mode as today rather than a new one.
- Risk: #58 is the opposite error in the same file family, and widening here must not be read as licence to widen there. Named as a non-goal in design.
- No new dependency.
