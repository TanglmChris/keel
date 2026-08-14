## Context

`criticalAuthority(repo, change, reference)` in `src/core/task-contract.js` resolves a Covers reference such as `D2` against `design.md`. It requires the reference to sit at the very start of a line, followed by `—` or `-`, e.g. `D2 — Keep one shared parser.` (this exact shape is itself what every `D<n>`/`F<n>`/`A<n>` line in this repository's own `design.md` files uses, including this one). When the regex finds zero matches, today's code reports `Missing Covers critical statement: <ref>.` regardless of whether the identifier is absent from the file entirely or present in some other shape, such as a bulleted/bold line (`- **D2** — text`).

F1 — Reproduced against the current tree (2026-08-12, keel 5.37.0): a fixture `design.md` containing `- **D2** — Keep one shared parser. Basis: fixture authority.` and a `tasks.md` Covers entry of bare `D2` fails `node bin/keel.js gate task-start` with `Missing Covers critical statement: D2.`, even though D2 is present in the file. Command: `node bin/keel.js gate task-start --change demo --task 1.1 --json --no-guard` against that fixture; output problem `{"code":"unresolved-covers","message":"Missing Covers critical statement: D2."}`.

F2 — The other two diagnostics issue #49 reported in the same family are already fixed in the current tree, confirmed by direct reproduction rather than by reading the issue: the Review Findings message now opens with the imperative (`name a path after \`Durable owner:\`...`) instead of burying it after a long enumeration, and an unfenced HTML fragment in an Evidence value now produces `Evidence carries the unfilled slot \`<div class="domlgd">\`, so it is not concrete. ... fence it in inline code when it is literal text` instead of the old bare `Evidence must be concrete` plus a spurious `Commands must define at least one M<n>` companion error. Only the `Missing`/critical-statement case (F1) still reproduces.

## Goals / Non-Goals

**Goals:**
- When a `D<n>`/`F<n>`/`A<n>`/`Q<n>` Covers reference resolves to zero exact-shape matches, tell the author whether the identifier is textually absent from `design.md` (`Missing`) or present but not in the required line shape (`Unparsed`), and in the latter case state the shape.

**Non-Goals:**
- Widening what line shapes `criticalAuthority()` accepts as a resolved critical statement. The fix is diagnostic wording for an already-existing zero-match branch, not a parser change to accept more inputs.
- Touching `specAuthority()` (the capability/requirement/scenario Covers branch) or any other diagnostic. Issue #49's other two sub-issues are already resolved (F2) and are out of scope here.

## Decisions

D1 — The zero-match branch in `criticalAuthority()` runs a second, looser check — `\b<ref>\b` against the raw `design.md` content — only when the strict shape regex found nothing. If the loose check also finds nothing, the message stays `Missing Covers critical statement: <ref>.`. If the loose check finds the token, the message becomes `Unparsed Covers critical statement: <ref>. Write it starting the line as \`<ref> — one-line statement\` (no leading \`-\`, \`**\`, or other decoration) so it can be resolved.` Basis: this mirrors how the `Invalidates` and `Expectation Coverage` diagnostics already state the required literal shape in-message (issue #49's own comparison), and a whole-word check is cheap and needs no new dependency.

D2 — The loose check runs only inside the existing zero-match branch (`matches.length !== 1` path was already being evaluated; this only refines the `matches.length === 0` half of it). The `matches.length > 1` (`Duplicated`) branch and the file-does-not-exist branch (line ~681, `design.md` missing entirely) are unchanged: a missing file has nothing to loosely search, and a duplicate is already resolved with a clear message. Basis: keeps the change to exactly the one ambiguous outcome named in the proposal.

D3 — `reference` reaching this function has already passed `/^[DFAQ]\d+$/.test(reference)` (line 673), so it is guaranteed to be a bare letter-plus-digits token with no regex metacharacters; the loose check embeds it directly in a `\b...\b` pattern with no escaping needed. Basis: existing guard at the top of the function, read directly.

## Hidden Knowledge / Assumptions

None.

## Risks / Trade-offs

- A whole-word `\b<ref>\b` scan can find the identifier used in unrelated prose (e.g. a sentence that mentions "D2" for some other reason) and call that `Unparsed` rather than `Missing`. This trades a small chance of a slightly-off diagnostic label for the common case the issue reports — the identifier genuinely present but in the wrong shape — and either way the author is pointed at the same file and line-shape requirement, so the actionable guidance is correct even when the label is generous.

## Open Questions

None.
