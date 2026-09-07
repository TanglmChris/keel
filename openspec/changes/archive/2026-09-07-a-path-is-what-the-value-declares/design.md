## Context

`declaredPath()` is the one extractor every gate reader of a declared path uses. Its rule came from issue #60, where the defect was the opposite: a character class too narrow to hold non-ASCII directory names. The repair stated the principle that still holds — what a path is *made of* is the filesystem's business — and settled the other half as "what ends a path is whitespace". 5.45.0 added the separator-free filename form for repository-root files (issue #107) without touching either half.

The consumer corpus is the first body of evidence large enough to test the second half. It is also written in Chinese, where the assumption fails: a sentence supplies no whitespace, so a path is followed immediately by its terminator.

## Goals / Non-Goals

**Goals:**
- Return the path the author declared, in prose that has no spaces and in prose that cites other files.
- Keep every extraction that is correct today.

**Non-Goals:**
- Restricting which characters a path may hold. #60's rule stands; this is about where the run ends and which candidate is the declaration.
- Changing which readers name a missing path, or the filename form added in 5.45.0.
- Parsing the prose around the value. The rule is positional, not semantic.

## Decisions

F1 — Measured across `chip_sec_flow_v2`, `my_xhs`, `dasauto`, and `rtl_ppa_prj`, 2026-09-06 against 5.46.0: 624 path-shaped `Durable owner:`/`Resolved here:` values; 34 extract something other than the declared path — 14 by swallowing the sentence, 20 by returning a backticked citation instead of the declaration. 590 are unchanged by the rule below. Basis: the real `declaredPath()` lifted from `src/core/gates.js` and run over every such line.

F2 — The two halves fail differently. A swallowed sentence yields a path that cannot exist, so the gate refuses and names something the author never wrote. A citation that outranks the declaration yields a path that usually *does* exist, so the gate accepts — checking a file the author did not declare. Basis: the samples in F1, among them `docs/operations/packaging.md` returned where the author declared `scripts/build_dist.py`.

F3 — `chip_sec_flow_v2` runs Keel 5.14.0 and `my_xhs` runs 5.20.0, both older than the release that introduced the whitespace-run rule, so neither repository sees either defect today. Basis: their `keel:start` markers and this repository's changelog. The defects are upgrade-surfaced, which is why a corpus this size had accumulated them unnoticed.

D1 — The declaration is what the value opens with. A backticked path at the start of the value (after leading whitespace) wins; otherwise the first bare run wins; a backticked span elsewhere is used only when neither produced anything. Basis: F2. `Findings` is free prose in which citing a file after naming the owner is ordinary, and the current order lets the citation win silently. The third step keeps `Durable owner: 见 `docs/a b.md`` working, which is the only way to declare a path containing whitespace when the value does not begin with it.

D2 — A bare run ends at whitespace or at a CJK sentence terminator: `。，、；：！？（）【】《》「」〈〉""''`. Basis: F1's first half. In a script that does not separate words with spaces, the terminator is what ends the path; treating it as an ordinary character is the same error as #40 and #60, made about the boundary instead of the alphabet.

D3 — ASCII punctuation keeps its current treatment: allowed inside the run, stripped from its end. Basis: `a.b/c-d.e`, `f(1)/g`, and `x_1.py` are paths, and ASCII prose does supply the whitespace that ends them. The asymmetry is not an inconsistency; it follows from whether the writing system separates words.

D4 — The terminator set excludes CJK characters that are not punctuation. Basis: #60's own example, `notes/note-006-转岗最难的不是流程/note.md`, must keep resolving — and it does, since the rule adds terminators rather than narrowing the alphabet.

D5 — A backticked capture whose segments are all empty is not a path. Two adjacent inline code spans put a separator between them — `` `networkx`/`PyYAML` `` closes one span and opens the next — and a capture spanning that gap is the single character `/`. Basis: measured twice in the consumer corpus after D1 and D2 were in place, each reported as a file that does not exist. The check is on the capture rather than on the pattern, because the pattern that excludes it also excludes a path whose first segment is empty, which is a different question.

## Hidden Knowledge / Assumptions

A1 — The CJK terminator set is assumed to be the punctuation an author writes immediately after a path in Chinese prose. It is drawn from the corpus and from `DECLARED_PATH_TRAILING`, which already lists most of them for the trailing case. A terminator outside the set leaves that declaration extracting as it does today — the current behaviour, not a new failure. Basis: F1's 14 instances all terminate with a character in the set. Owner: https://github.com/TanglmChris/keel/issues/113.

A2 — A value that declares no path at all but contains a separator inside ordinary prose — `协议/端口标注`, `(M2/M3)` — still yields a path-shaped run, and the gate reports it as a file that does not exist. Two such values remain in the consumer corpus after this change, down from 15. Telling a CJK word pair from a two-segment path needs semantics the gate does not have, so this is left as it is rather than guessed at. Basis: the post-change re-measurement over the same 624 declarations. Owner: https://github.com/TanglmChris/keel/issues/113.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **A path whose directory name genuinely contains CJK punctuation is now truncated.** `notes/第一章。总论/x.md` would extract as `notes/第一章`. No such path exists in the corpus, and the alternative is the measured 14 that swallow whole sentences.
- **The reordering changes which of two present paths is returned.** That is the point, and the direction is toward the declaration; but a value that named its owner in a trailing backtick span while a bare path appeared earlier in the same value would now take the earlier one. The corpus holds no such value, and the rule is stated positionally so an author can predict it.
- Both halves are contained in one function that every reader shares, so there is no possibility of repairing one reader and leaving the others — the failure mode #60 recorded.

## Open Questions

None.
