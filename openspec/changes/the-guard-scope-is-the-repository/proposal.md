# the-guard-scope-is-the-repository

## Why

Issue #31: with a corrupt `keel/guard.json`, the write guard denies an edit to a file outside the repository. Whether a path is outside the repository is computable from the event's `cwd` and the target alone, so this is not fail-closed reasoning under uncertainty — the one fact required is known with certainty and the guard declines to use it. The practical cost is that a broken manifest blocks scratch and diagnostic work until `keel guard clear`, which is exactly what an author should not have to run to write a file the guard was never protecting.

Underneath it is a documentation gap that let the ordering drift twice. The hook's header states the passthrough unconditionally — "Paths that resolve outside the repository root are not product writes and pass through" — while `keel-touch-write-guard` never mentions it, and its own wording says a path outside the Touch list is denied, which reads as covering every path anywhere. So the behavior has no durable owner: the code comment asserts one rule, the spec implies the opposite, and the implementation currently agrees with neither in the invalid-manifest case.

This is the third ordering defect in the same function. #28 item 10 was the drift check running before the passthrough; that was fixed by moving the passthrough up one step. This is the same correction one step further up, and stating the rule in the spec is what stops it recurring.

## What Changes

- The repository boundary is stated in the spec as the guard's scope, and as taking precedence over every manifest-derived decision including the invalid-manifest denial.
- The hook resolves the target and returns for an out-of-repo path before reading or validating the manifest.
- Validation asserts the precedence directly: an out-of-repo write is allowed while the manifest is corrupt, and every in-repo path is still denied in that same state.

## Impact

- `plugins/keel/scripts/pretooluse-guard.js`
- `scripts/validate_plugin.py`
- Spec: `keel-touch-write-guard`

## Non-goals

- No change to what the guard denies inside the repository. The invalid-manifest denial, the drift denial, the completed-task denial, and the outside-Touch denial all keep their current behavior for in-repo paths.
- No change to the manifest shape, the gates, or `keel guard start`/`status`/`clear`.
