## Why

Issue #359: on 2026-10-18, after both the 5.139.0 and the 5.143.0 releases, `keel --update` on the owner's machine (Claude Code 2.1.302, proxy `127.0.0.1:7890`) reported `claude plugin: failed - \`claude plugin marketplace update keel-marketplace\` exited 1`; the same command run directly right after passed, and a second `keel --update` read `current`. The Codex refresh already retries once (#329); the Claude refresh does not, so about every other release leaves the Claude plugin a version behind until a manual rerun. The failing run's cause was not captured either, because a failed host step names only its exit status.

## What Changes

- `claude plugin marketplace update` is retried once when it fails, as the Codex refresh is; when the retry fails too, the Claude line reads `failed` and says it failed twice.
- A host step that exits nonzero names, beside its exit status, the last line it wrote to stderr, so the cause is visible on the first failure.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: the Claude marketplace refresh is retried once, and a failed host step names its last stderr line.

## Impact

`bin/keel.js`, `scripts/validate_plugin.py`, `docs/updating.md`, one published spec, the changelog.
