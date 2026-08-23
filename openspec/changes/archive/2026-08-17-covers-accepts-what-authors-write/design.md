## Context

`criticalAuthority()` (`src/core/task-contract.js`) resolves a critical-statement reference only against a `design.md` line that starts bare: `D2 — text`. Everything else — `- D2 —`, `**D2** —`, `- **D2** —` — fails `keel gate task-start` as `Unparsed` (since 5.38.0; before that, as `Missing`). Measured across the 62 archived `design.md` files in this repository: 3 bare, 45 bold, 15 bulleted. On the Covers side the same strictness inverts into fail-open: an entry opening with the identifier plus a trailing annotation (`D2 — do not widen accepted shapes`) misses `/^[DFAQ]\d+$/`, silently becomes a `legacy-task-reference`, and the design.md link is never checked — reproduced on 5.39.0 with the identifier entirely absent from `design.md` and `task-start` returning zero problems. The owner decided on issue #49 (2026-08-17) to widen acceptance: the current strictness does not enforce more, it silently checks less.

The critical statements below are written in the bare line shape on purpose: this change's own gates run under the parser as it is before the change.

## Goals / Non-Goals

**Goals:**
- Resolve `design.md` critical-statement lines in the shapes this repository's authors actually write.
- Make a Covers entry that opens with a critical-statement identifier and a dash resolve as that critical statement — or fail loudly — never silently degrade.
- Keep the `Unparsed` diagnostic accurate about what is and is not accepted.

**Non-Goals:**
- No change to `specAuthority()` (spec scenario references) or to colon-form (`E1: text`) and free-text Covers entries.
- No comparison of a Covers annotation's prose against the design.md statement text; design.md stays the single owner of the wording.
- No change to duplicate handling: a reference matching more than one line, in any mix of shapes, still fails as ambiguous.

## Decisions

D1 — `criticalAuthority()` accepts a `design.md` critical-statement line as: optional leading whitespace, optional CommonMark list bullet (`-`, `*`, or `+`) followed by whitespace, the identifier either bare or wrapped in balanced `**`, then the existing dash-and-statement tail (`\s*[—-]\s*` unchanged). Concretely the line regex becomes `^\s*(?:[-*+]\s+)?(?:\*\*D2\*\*|D2)\s*[—-]\s*(.+?)\s*$` for reference `D2`. Basis: owner decision on issue #49 (2026-08-17); the 3/45/15 shape measurement across 62 archived design.md files.

D2 — A Covers entry that opens with a critical-statement identifier followed by a dash resolves through `criticalAuthority()` using the bare identifier: match `^([DFAQ]\d+)(?=\s|—)\s*[—-]\s*.+$` in `resolveAuthority()` before the legacy fallback. The lookahead requires whitespace or an em dash immediately after the identifier so that free text like `D2-compatible` does not become a reference. Basis: parallel to the `Q<n>` opens-the-entry rule the capsule spec already states; owner decision on issue #49.

D3 — The trailing annotation in such a Covers entry is annotation only. Authority text still comes from the resolved design.md statement, and the annotation is not diffed against it. Basis: design.md is the durable owner of the statement; comparing prose would add a sync obligation with no authority gain.

D4 — The `Unparsed` message names the accepted shapes — bare, bulleted, bold, bulleted-bold, dash required — instead of "no leading `-`, `**`, or other decoration". The branch still fires for what stays unaccepted: heading lines, a colon after the identifier, mid-line mentions. Basis: 5.38.0's message describes the pre-widening boundary and goes stale with this change.

D5 — Comma-list entries stay bare-only: `D1, D2` still splits, `D1, D2 — note` stays free text because the lookahead fails at the comma. Basis: keeping the widened surface small; nothing measured needs annotated comma lists.

F1 — Reproduced on 5.39.0 (2026-08-17, real-CLI fixtures): all three of `- **D2** —` / `**D2** —` / `- D2 —` fail task-start as `Unparsed`; a Covers entry `D2 — do not widen accepted shapes` resolves as `legacy-task-reference` with exit 0 and zero problems both when design.md has a correctly-shaped D2 and when it has no D2 at all. Basis: this session's fixture runs against `node bin/keel.js`.

F2 — Of 62 archived design.md files, 3 use the bare shape (one of them authored bare specifically to satisfy the parser), 45 use `**D<n>**`, 15 use `- D<n> —`. Basis: PR #98 measurement, 2026-08-12, recorded on issue #49.

F3 — Keel's own shipped design template teaches the bulleted shape: `assets/openspec/schemas/keel-spec-driven/templates/design.md` (and its `openspec/schemas/` copy, byte-identical) shows critical statements as `- D<n> — accepted decision; Basis: …`. The template's example is a shape the parser refuses today and accepts after this change; no template edit is needed. Basis: read both copies and diffed them this session (2026-08-17).

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A live task whose Covers annotation entry used to downgrade silently will now fail when its identifier is missing from design.md. That is the decided direction — "not being checked" becomes "checked" — and archived changes are not re-gated, so only live and future tasks see it. This repository has no other live change.
- A design.md carrying the same identifier in two shapes (say bare in prose and bulleted in a list) now matches twice and fails as duplicated where it previously resolved against the single bare line. This surfaces a real ambiguity that was invisible; the fix on the author's side is deleting one of the two.
- The line regex does not see Markdown structure, so a shaped line inside a code fence matches too. That is true of the bare shape today and is unchanged in kind by this change.

## Open Questions

None.
