## Why

Two gate refusals in `src/core/gates.js` report a cause the author does not have, and the repair available to them is to change the notation rather than the content. Both were found by hitting them while doing ordinary work in this repository.

**A repo-root file cannot be named as an owner or as resolution evidence.** `declaredPath()` locates a path by finding a run of non-whitespace *containing a path separator*, so a file at the repository root has none and is not seen as a path at all. `Durable owner: README.md` and `Resolved here: AGENTS.md` are refused with `it names neither a check nor a path` — for a path whose file exists. Nine files sit at this repository's root today, `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, and `package.json` among them, and every one of them is a legitimate owner. The workaround is to write `./AGENTS.md`, which is a concession to the extractor rather than a repair. Issue #107.

**A quoted phrase in `## Invalidates` cannot wrap.** The check is `/"[^"\n]{3,}"/`, so an entry whose quotation runs past the end of a line is reported as `names where to look but not what to look for` — when it named exactly that. Five entries across three changes hit this in one session, each fixed by shortening the quote to one line. The corpus looks clean for a misleading reason: 42 of this repository's 194 archived `## Invalidates` entries span more than one line, and **zero** carry a quotation that wraps — the shape is absent because the gate refuses it, not because authors do not write it. `Findings` in the same file is already read as wrapping by design. Issue #108.

## What Changes

- `declaredPath()` accepts a single token that names a file when the token has a filename shape — a trailing extension of letters — in addition to the separator form it already accepts. Existence is still what decides: a root file that exists is accepted, one that does not is refused **by name** rather than as unrecognized, which is strictly more informative than today.
- A value with no path shape at all is still `unrecognized`. `Durable owner: pending` must not become "the file `pending` does not exist", and a version string like `5.44.0` must not read as a filename.
- The `## Invalidates` quoted-phrase check reads the entry body across lines. The entry's bounds are already set by the section parser, so a quotation cannot run past its own entry.

## Capabilities

### Modified Capabilities
- `keel-core-gates`: the "A declared path is extracted by where it ends, not by what it is made of" requirement states that a path is located by a run containing a separator, which is the sentence that excludes every root file. It gains the filename form and the boundary that keeps a non-path value unrecognized.
- `keel-expectation-slice-evidence-gates`: the "Task Authoring Gate covers statements the change invalidates" requirement requires a searchable phrase without saying how the phrase may be laid out; it gains the rule that the phrase is read across the entry's lines, matching how `Findings` is already read.

## Impact

- Affected code: `src/core/gates.js` — `declaredPath()` and the `invalidation-phrase` check.
- Affected tests: `scripts/validate_plugin.py` — new scenarios for both, asserted through the real CLI.
- Direction is **looser**, in the one place each was refusing correct work. Both are bounded: existence still decides every path, and a non-path value is still refused.
- No new dependency, no schema change, no CLI surface change.
