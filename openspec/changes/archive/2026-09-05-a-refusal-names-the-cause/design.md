## Context

`declaredPath()` is the one extractor every gate reader of a declared path uses — `Durable owner:`, `Resolved here:`, and the `keel/archive/…` reference inside `Findings`. It was last repaired for issue #60, where the defect was the opposite direction: a character class too narrow to hold non-ASCII directory names. That repair established the right rule — what ends a path is whitespace, what a path is made of is the filesystem's business — and fixed the separator requirement in place while doing so.

The `## Invalidates` phrase check sits a few hundred lines away in the same file. Its entry bounds come from the section parser, which already treats an entry as running until the next `I<n>`; only the phrase test assumes one line.

## Goals / Non-Goals

**Goals:**
- Let an author name a file that exists, wherever it sits.
- Let an author lay out a quoted phrase the way the entry needs.
- Keep every refusal that is currently correct.

**Non-Goals:**
- Widening what counts as an owner. Existence still decides; this changes what is *seen* as a path, not what passes.
- Touching the backtick form, the trailing-punctuation trim, or the `Findings` artifact fallbacks.
- Making a bare word a path. `Durable owner: pending` stays unrecognized.

## Decisions

F1 — Nine files sit at this repository's root: `.gitattributes`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`, `README.zh-CN.md`, `package-lock.json`, `package.json`. None can be named as a durable owner or as resolution evidence today, because `declaredPath()` requires a separator. Basis: directory listing plus the extractor read, 2026-09-05 against 5.44.0.

F2 — Reproduced against 5.44.0 while completing `an-owner-outlives-the-change`'s release task: `Resolved here: AGENTS.md` failed `keel gate task-complete` with `it names neither a check nor a path`, and `Resolved here: ./AGENTS.md` passed. Basis: the gate output recorded in that change's own Review, `openspec/changes/archive/2026-09-05-an-owner-outlives-the-change/tasks.md`.

F3 — 42 of this repository's 194 archived `## Invalidates` entries span more than one line, and **zero** carry a quotation that wraps across lines. Basis: scripted count over `openspec/changes/archive/**/tasks.md` using the gate's own entry-splitting pattern. The absence is the workaround, not the behaviour: five entries in one session were refused and then shortened to fit, across `quoted-text-is-not-a-claim` (I2, I5), `an-owner-outlives-the-change` (I3, I4), and `the-spec-names-the-managed-set` (I4).

D1 — `declaredPath()` gains a filename form: a single non-whitespace token, after the trailing-punctuation trim, ending in a dot and one to eight letters or digits that begin with a letter. Basis: F1 and F2. The existing separator form is tried first and is unchanged, so no path that resolves today resolves differently.

D2 — The extension must begin with a letter. Basis: this is what keeps `5.44.0` — a version, which authors do write in prose beside an owner — from reading as a file named `44` with extension `0`. A shape that could swallow a version number would trade the refusal being fixed for a stranger one.

D3 — A token with no separator and no filename shape stays `unrecognized`, and the refusal keeps saying so. Basis: issue #107 names this explicitly. `Durable owner: pending` reported as "the file `pending` does not exist" would send the author to create a file, which is worse than the message they get now.

D4 — Existence still decides. A root file that does not exist is refused as `missing` and named, rather than as unrecognized. Basis: that is what the existing requirement already promises for every other path, and the whole reason the path form is the one a gate can check.

D5 — The `## Invalidates` phrase test drops `\n` from its character class rather than normalizing the body. Basis: the entry's bounds are already set by the section parser's lookahead, so a quotation cannot reach past its own entry; normalizing would introduce a second reading of the same text for no gain.

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **A filename-shaped word in prose is now extracted.** A `Durable owner:` whose value reads `see gates.js for context` would extract `gates.js`, find no such file at the root, and be refused by name instead of as unrecognized. Both refuse; the new message is the more specific of the two, and it points at the thing the author actually wrote.
- **The wrapped-quote check accepts a run-on quotation inside one entry.** An entry with a single unbalanced quote followed by a later one now matches. The bound is the entry, and the phrase's content is the author's judgment rather than the gate's — the requirement already says so.
- Both changes are loosening, so nothing that passes today starts failing. Rollback is a revert of one file.

## Open Questions

None.
