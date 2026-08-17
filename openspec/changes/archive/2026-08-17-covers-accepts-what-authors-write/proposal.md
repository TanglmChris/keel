## Why

`criticalAuthority()` in `src/core/task-contract.js` resolves a `D<n>`/`F<n>`/`A<n>`/`Q<n>` critical statement only when its `design.md` line starts bare — `D2 — text`, no bullet, no bold. Measured across all 62 archived `design.md` files in this repository (PR #98, 2026-08-12): 3 use that bare shape, 45 write `**D<n>**`, 15 write `- D<n> —`. The one shape the parser requires is the one authors do not write. Worse, the strictness is fail-open on the Covers side: a Covers entry that opens with the identifier and carries a trailing annotation (`D2 — do not widen accepted shapes`) stops matching `/^[DFAQ]\d+$/`, silently downgrades to `legacy-task-reference`, and the link to `design.md` is never checked — `task-start` passes with zero problems even when the identifier does not exist in `design.md` at all. Reproduced against the current tree (2026-08-17, 5.39.0). The owner decided on issue #49 (2026-08-17): widen acceptance, because the current state silently skips the check for the shapes authors actually write.

## What Changes

- `criticalAuthority()` accepts a `design.md` critical-statement line in the shapes authors write: an optional list bullet (`-`, `*`, or `+`), an identifier optionally wrapped in `**`, then the dash and statement. Bare `D2 — text` still resolves unchanged. A reference matching more than one line — in any mix of shapes — still fails as duplicated.
- A Covers entry that opens with a critical-statement identifier followed by a dash and trailing text (`D2 — annotation`) resolves as that critical statement — the same opens-the-entry reading `Q<n>` references already get — instead of silently degrading to an unlinked `legacy-task-reference`. When the identifier then fails to resolve against `design.md`, `task-start` fails instead of passing silently. Colon-form entries (`E1: text`) and free-text references are unchanged.
- The `Unparsed Covers critical statement` message names the newly accepted shapes instead of saying "no leading `-`, `**`, or other decoration"; the branch still fires for shapes that remain unaccepted (heading lines, colon after the identifier, mid-line mentions).

## Capabilities

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the "Unresolved critical-statement Covers references distinguish missing from unparsed" requirement's scenarios name bullet/bold wrapping as the mis-shaped example; those shapes now resolve, so its scenarios move to shapes that stay unaccepted, and a new requirement states the accepted shapes.
- `keel-task-capsule`: the "Covers resolves durable authority and Acceptance" requirement gains the rule that an entry opening with a critical-statement identifier followed by a dash resolves as that critical statement rather than degrading into an unlinked free-text reference.

## Impact

- Affected code: `src/core/task-contract.js` (`criticalAuthority`, `resolveAuthority`).
- Affected tests: `scripts/validate_plugin.py` — the `unparsed-covers-critical-statement` scenario's mis-shaped fixture (`- **D2** — …`) becomes a resolving shape and must move to a still-unaccepted one; new scenarios for the widened design.md shapes and the Covers annotation entry.
- Gate-acceptance change, owner-decided (issue #49, 2026-08-17): references that previously failed as `Unparsed` now resolve, and Covers annotation entries that previously passed unchecked now fail when their identifier is missing. Direction is stricter enforcement — "not being checked" becomes "checked". No new dependency, no schema change.
