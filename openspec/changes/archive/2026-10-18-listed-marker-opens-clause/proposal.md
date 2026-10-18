## Why

Issue #362 (rtl_ppa_prj, keel 5.143.0, 2026-10-18): `keel gate task-complete` refused a Review `Findings` written as a sub-list — `- Findings:` followed by `  - Resolved here: M1`, or by a repo path that exists — as `finding-owner`, while the same text on the label's own line passed. The refusal told the author to write exactly what they had written. The marker opening rule (#144) accepts the start of the value, a line break, or sentence-ending punctuation before a marker; a sub-list item puts `- ` between the line break and the marker, so the marker read as a mid-sentence mention.

## What Changes

- A list bullet (`-`, `*` or `+` and a space) that begins a line opens a clause, so a disposition written as a sub-list item is read exactly as one on the label's line.
- The refusal that explains the opening rule names a list item among the openings.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: a marker at the head of a list item opens its clause.

## Impact

`src/core/gates.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
