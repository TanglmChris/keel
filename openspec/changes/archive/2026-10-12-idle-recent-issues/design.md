## Context

Issue #278, split from #241 item 3. Constraint carried from #241: continuity stays stateless — Git only, never memory or transcripts.

## Facts

- F1 — `inspect` in `src/core/worktrees.js` reads `git log --format=%s%n%b <base>..HEAD` and collects every `#<n>`, sorted numerically; `defaultBranch` resolves `origin/HEAD`, else `main`, else `master`.
- F2 — A read-only result (#246) must carry exactly one reason; idle results otherwise carry reasons the hook prints.
- F3 — The SessionStart hook prints the projection from `keel context --json`.

## Decisions

- D1 — `branchIssues(cwd, base, limit)` in `src/core/worktrees.js` returns the distinct issue numbers referenced by commits in `<base>..HEAD`, newest commit first, at most `limit`; `inspect` keeps its own sorted list from the same reader.
- D2 — On an `idle` result, `keel context` sets `recent: { issues, range }` when the list is non-empty, with `range` the `<base>..<branch>` read. It is a separate field, never a reason (F2), and never a selection.
- D3 — The projection prints `- recently referenced: #a, #b (commits in <range>; a pointer, not a selection).`
