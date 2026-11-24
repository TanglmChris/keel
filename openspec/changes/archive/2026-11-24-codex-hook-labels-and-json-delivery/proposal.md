## Why

Keel #543 needs distinct native hook labels for review. #559 reported hook failures. A separate reproducible failure candidate is premature process exit while emitting hook JSON.

## What Changes

Name each Codex hook with the native status label field. Preserve complete human, model and guard output when a host consumes the pipe slowly. Document native evidence collection and the review required for changed hook definitions.

## Capabilities

### New Capabilities

- `keel-codex-hook-runtime`: stable native labels and complete delivery of hook responses.
