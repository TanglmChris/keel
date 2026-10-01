## Why

A task can cite a multi-line critical decision while its contract fingerprint covers only the opening line. Editing a continuation or nested bullet then evades drift detection. A multi-reference Covers entry can also fall through as unlinked legacy prose, falsely appearing to anchor decisions (issue #177).

## What Changes

- Fingerprint the complete cited critical statement, including owned continuation lines and nested list items, while stopping at the next peer statement, peer paragraph, or heading.
- Reject Covers entries that contain critical identifiers but cannot be resolved as a supported reference or an annotation to one opening reference; preserve the established resolved-question-as-supporting-detail case.
- Keep colon-shaped design statements explicitly unparsed, with a diagnostic naming the accepted dash shape; do not add a new colon syntax.
- **BREAKING**: Existing recorded fingerprints for tasks citing multi-line statements can move. Document the reauthorization and evidence handling path; do not silently accept an old anchor.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-task-capsule`: Covers references and contract fingerprints must bind the whole statement and refuse unlinked multi-references.
- `keel-expectation-slice-evidence-gates`: Define the extent of an accepted critical statement without broadening its opening-line syntax.

## Impact

The task contract compiler, CLI gate regression scenarios, affected OpenSpec specifications, and Keel workflow changelog change. No new dependency or host-runtime capability is required. Existing active tasks with recorded anchors may need explicit re-recording and evidence review after this release.
