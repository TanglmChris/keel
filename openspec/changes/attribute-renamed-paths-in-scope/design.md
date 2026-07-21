# Design — attribute-renamed-paths-in-scope

## Context

`task-complete` compares changed paths to the task's Touch list. Changed paths
come from two sources unioned in `gates.js`: `git diff --name-only <base> --`
and `gitPaths()` (the dirty working tree). `gitPaths()` runs
`git status --short --untracked-files=all` and takes `line.slice(3).trim()` per
line.

## Facts

- **F1** — `git status --short` reports a staged rename as one line,
  `R  <old> -> <new>` (and a copy as `C  <old> -> <new>`). Every other status
  line carries a single path.
- **F2** — `gitPaths().map(line => line.slice(3).trim())` therefore emits the
  literal `"<old> -> <new>"` for a rename, which `pathAllowed` cannot match
  against a Touch entry, yielding a false `outside-touch` failure even when both
  endpoints are in Touch.
- **F3** — The sibling source `git diff --name-only` never uses the `-> ` form,
  so the defect is isolated to the porcelain parse in `gitPaths()`.

## Decisions

### D1 — Split a rename entry into both endpoints, not just the new path

`gitPaths()` splits on the `" -> "` separator and emits both the old and new
paths. Rationale: a rename is a deletion of the old path plus a creation of the
new path, and both are real changes the scope check must attribute. Emitting only
the new path would let a rename that moves a file *out of* Touch (old in Touch,
new outside — or vice versa) escape attribution. Emitting both preserves the
gate's guarantee that every changed path is checked against Touch.

## Risks

- Low. The split only affects lines containing `" -> "`, which for
  `git status --short` are exactly renames and copies; ordinary paths are
  unaffected. Paths with a literal `" -> "` substring would require shell-special
  characters git would quote, and are out of scope for this gate's inputs.

## Verification

Regression-first through the public `keel gate task-complete` interface: a new
`keel-core-gates` scenario builds a git repo, authors a task whose Touch lists a
file's old and new paths, `git mv`s the file, and asserts `task-complete --base`
attributes both paths inside Touch (green) where the pre-fix parse reported
`outside-touch` (red).
