## Why

`validate_source_repo_bootstrap_skip_scenario` runs a real `keel --install --target claude` against the repository root. It asserts the one thing it cares about — that `AGENTS.md` is skipped — and asserts nothing about the rest, so the install's overlay refresh silently rewrites `.claude/` markers and `CLAUDE.md` as a side effect ([#26](https://github.com/TanglmChris/keel/issues/26)).

Two consequences, and the second is the worse one. `npm test` dirties the working tree after a version bump, in files unrelated to whatever the author is doing. And the marker-alignment check added in 5.3.4 is green on the `.claude/` side **because the suite writes those markers**, not because anything guarantees them — a check whose input its own process produces cannot fail. That is the defect family [#18](https://github.com/TanglmChris/keel/issues/18) opened, one step further along: not a check that does nothing, but a check that manufactures its own passing condition.

## What Changes

- The scenario builds a repository that satisfies the two signals `is_keel_source_repo` actually tests — a `package.json` named `@christang/keel` and a `plugins/keel/` directory — instead of using the real one. It keeps asserting the skip, and gains an assertion that the install left the fixture's other files alone.
- A source-level check refuses any scenario that passes `ROOT` to a mutating Keel invocation, so the class cannot return through a different scenario. Read-only invocations against `ROOT` stay legal and are the common case.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `keel-validation-runner`: the suite must not write to the repository it validates, and a check that its own process could satisfy does not count as verification.

## Impact

- `scripts/validate_plugin.py` — the only file. One scenario rebuilt on a fixture, one source-level check added.
- No product behavior changes. `keel --install` against the source repository stays a supported operation; it is the *test* that stops calling it there.
- After this, the `.claude/` overlay markers are guaranteed by `bump_version.js` and the 5.3.4 marker check alone, which is what was intended when those landed.
