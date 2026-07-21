# Attribute git-mv renamed paths to Touch in the completion scope check

## Why

The completion gate's scope check false-fails a legitimate `git mv` rename whose
old and new paths are both listed in Touch. `src/core/gates.js` `gitPaths()`
reads `git status --short --untracked-files=all` and strips the first three
columns off each line, but a staged rename is a single porcelain line —
`R  old -> new` — so the parse yields the one string `"old -> new"`, which
matches neither Touch entry and produces a false `outside-touch` scope failure.

Discovered while dogfooding `modernize-lens-vocabulary` task 3.1 (the
`keel-domain-profiles` → `keel-domain-lenses` capability rename): the rename was
fully inside Touch, yet `task-complete` reported it as outside-Touch. The only
workaround was to unstage the rename so git reports a delete plus an untracked
add — a real defect, since a rename entirely inside Touch must pass.

## What changes

- `gitPaths()` splits a porcelain rename entry (`old -> new`) into its two real
  paths, so the deletion of the old path and the creation of the new path are
  each attributed against Touch independently.
- Add a `keel-core-gates` scenario locking the behavior: a rename whose old and
  new paths are both in Touch attributes to both endpoints and produces no false
  `outside-touch` failure.

## Non-goals

- No version bump or release; this lands on `main` and folds into a later
  release decided separately.
- No other change to scope attribution — the guard-manifest exemption, the
  selected change's authoring-artifact exemption, and `**` glob matching are all
  unchanged. Only the parsing of a porcelain rename line changes.
