## Facts

- F1 — `change-close` in `src/core/gates.js` pushes `missing-delta-spec` whenever `hasDeltaSpec(changePath)` finds no `specs/**/spec.md`; it never reads `.openspec.yaml`.
- F2 — OpenSpec (1.14) treats `skip_specs: true` in `.openspec.yaml` as a marker, and its archive and validate reject a marked change that carries any file under `specs/`; a marker that fails OpenSpec's metadata shape is not honored.
- F3 — The gates are local and model-free, so they read the file; they do not run `openspec status`.

## Decisions

- D1 — `declaresSkipSpecs(changePath)` reads `.openspec.yaml` and is true only for a line `skip_specs: true` (optional trailing comment); an absent file, an unreadable one, `false` and every other value are undeclared, so today's behavior is the fallback (F2: an unhonorable marker counts as undeclared).
- D2 — With the marker, `missing-delta-spec` is not raised, for both close actions. If any file exists under `specs/`, the problem `skip-specs-with-specs` is raised instead, naming the first file found (F2).
- D3 — The gate does not check OpenSpec's reading of the marker; `keel openspec archive` remains the authority and fails a marker it cannot honor.
