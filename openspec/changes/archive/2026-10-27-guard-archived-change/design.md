## Facts

- F1 — The hook (`plugins/keel/scripts/pretooluse-guard.js`) denies every write as a stale manifest once `openspec/changes/<change>` is gone; `keel guard status` (`src/core/guard.js`) reports `drifted` with `stale-manifest`. Both decide by the change directory (#56).
- F2 — #56 kept the denial because "failing closed is what stops archiving a change from silently disabling the guard": archiving a change whose task is still open must not lift the guard.
- F3 — `openspec archive` moves the directory to `openspec/changes/archive/<YYYY-MM-DD>-<change>/`, keeping `tasks.md`.
- F4 — A live change whose guarded task is checked complete already denies product writes and names `keel guard clear` (the `taskIsChecked` branch); that is unchanged.
- F5 — `keel guard status` exits 0 for `started`, `active`, `absent`, and `cleared`.

## Decisions

- D1 — When the change directory is gone, the hook and `keel guard status` both look for `openspec/changes/archive/<YYYY-MM-DD>-<change>/tasks.md`, taking the lexically last match, and read the guarded task's checkbox there with the same pattern `taskIsChecked` uses. Checked means the task finished and its change was archived; the manifest then authorizes and forbids nothing.
- D2 — In that case the hook returns no decision for the write. `keel guard status` returns status `archived` with problem code `task-archived`, naming the archived directory, saying the manifest enforces nothing, and naming `keel guard clear`; it exits 0, beside `absent` and `cleared`.
- D3 — With no archived copy, or with the guarded task unchecked in it, both surfaces keep the stale-manifest refusal unchanged, which keeps F2.
- D4 — Not taken: clearing the manifest from `keel gate change-close --action archive` (the protocol keeps gates other than `task-start` from writing project state), and allowing `openspec/changes/` writes under any stale manifest. `keel context` still defers a protocol refresh while `keel/guard.json` exists; the next `task-start` replaces the manifest.
