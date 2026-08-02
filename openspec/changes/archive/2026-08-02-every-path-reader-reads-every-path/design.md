## Context

The gates check a declared path by testing whether it exists. That check is the reason a path is a valid durable owner at all — it is the one form a local, offline, model-free gate can actually verify. Extracting the path from a line of free prose is the step before it, and that step was written as an ASCII character class.

`Durable owner:` and `Findings:` are free prose by design: they hold a path and then a sentence explaining it. So the extractor cannot simply take the rest of the line; it has to find the path inside the prose. The existing implementation solved that by enumerating the characters a path may contain, which answers "where does the path end" by assuming what a path is made of.

## Goals / Non-Goals

**Goals:**
- A path that exists on disk can be named as a durable owner or as resolution evidence, whatever script it is written in.
- A path containing a space can be named, through the backtick form `Touch` already accepts.
- One extractor, read by every path reader in the gates.
- A wrong capture still fails by naming a path that does not exist, rather than passing.

**Non-Goals:**
- Widening the change-name validators. Those match an OpenSpec-generated identifier, not a path (D4).
- Widening anything in the direction #58 reports. That issue is a class too *wide*, and this change must not be cited as precedent for loosening a criterion whose problem is over-matching (D5).
- Accepting a path that does not exist. Existence remains the check; only the extraction changes.

## Decisions

- **F1** — the extractor is `/[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)+/` at `src/core/gates.js:383` and `:426`, with the same class inline at `:469` and `:473` for `keel/archive/…`. Four copies, one shape. *Basis: `grep` over `src/core/gates.js` at 5.17.0.*
- **F2** — three shapes fail, measured 2026-08-02 at 5.17.0 by running the expression directly: `notes/note-006-转岗最难的不是流程/note.md` yields `notes/note-006-`; `docs/写作/风格.md` yields no match at all; `src/has space/file.md` yields `src/has`. The first is #60's report; the second and third were found while reproducing it. *Basis: direct execution.*
- **F3** — `touchEntries` already strips backticks from a `Touch` entry (`src/core/gates.js`), so the backtick form is an existing repository convention rather than a new one this change invents. Two readers of the same authorship disagreed about how a path may be written. *Basis: `touchEntries` in `src/core/gates.js`.*
- **F4** — this is the same class as #40, fixed in `gitPaths` for the worktree reading, where a Chinese filename in `Touch` was reported as outside `Touch`. That fix did not generalize because it was a fix to one reader, not to how the repository extracts paths. *Basis: the `gitPaths` comment in `src/core/guard.js` and the `git-paths-carry-no-escaping` scenario.*
- **D1** — a path is a run of non-whitespace containing at least one `/`. Requiring the separator is what keeps the extractor from matching an ordinary word; stopping at whitespace is what keeps it from swallowing the explanatory sentence. Neither depends on which characters a filename is made of, which is the assumption that produced the defect. *Basis: F2 — every failing shape failed on character membership, not on where the path ended.*
- **D2** — a backtick-wrapped token is preferred over the bare form when present, and is taken verbatim. This is the only form that can express a path containing a space, and it is already how `Touch` is written. *Basis: F3.*
- **D3** — trailing punctuation is trimmed from a bare match, from a defined set covering both ASCII and CJK terminators. A Chinese sentence ends in `。` and a Chinese clause separates with `，`; neither is whitespace, so `\S+` swallows them. Leaving them in would replace one wrong path with another. *Basis: D1 — once the extractor stops assuming ASCII, its terminators cannot assume ASCII either.*
- **D4** — the change-name validators are untouched. `[A-Za-z0-9][A-Za-z0-9._-]*` at `context.js:199`, `gates.js:65`, and `context.js:386` matches a change identifier that OpenSpec generates as kebab-case ASCII. Widening it would accept names the tool will not produce, which is a different question from whether a path on disk can be named. *Basis: those sites validate `change`, not a filesystem path.*
- **D5** — this change is not precedent for #58. There the character class is too wide — `[0-9a-f]{7,40}` matching an eleven-digit phone number as a commit hash — and the repair is a narrowing. Recording both under one heading would license "loosen the pattern" as a general answer, when the general answer is that the implementation must match the rule, in whichever direction that lies. *Basis: #58's measurement; the two defects share a cause and have opposite fixes.*

## Hidden Knowledge / Assumptions

- **A1** — a path a user would name as an owner does not contain whitespace unless they wrapped it in backticks. Paths with spaces exist; the assumption is only that an author naming one in free prose will reach for the backtick form, which the error message names. *Basis: D2 gives the form and the message points at it. Owner: this change — the failure mode is a refusal naming a truncated path, which is loud rather than silent, and the scenario covers the space case through the backtick form.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A wider extractor can capture more prose. Bounded by the separator requirement, the whitespace stop, and the punctuation trim — and a wrong capture produces a refusal naming a non-existent path, which is exactly today's failure mode rather than a new one. The direction that would be dangerous is a wider extractor that made something *pass*; nothing here can.
- Four call sites collapse into one function, so a future defect in extraction is a defect everywhere at once. That is the intent: the reason this survived #40 is that each reader carried its own copy.

## Open Questions

None.
