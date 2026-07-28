## Context

`scripts/validate_plugin.py:445` asserts that `dist`, `plugin.json`, `src/adapters`, and `src/hooks` have been removed from the repository. Several helpers written before that retirement still resolve their roots underneath `dist/` or `src/assets/`. Because `Path.rglob()` on a missing directory yields nothing without error, and because the affected helper returns `[]` when its root is absent, the resulting assertions execute zero comparisons and report success.

The consequential one is `packaged_openspec_schema_install_paths()`. Its six callers assert that `keel --install` writes the packaged OpenSpec schema into a consumer repository, that `--uninstall` plans and performs its removal, and that `--clear` leaves nothing behind. `keel-openspec-surface-overlay` requires that install behavior, so a specified requirement currently has no executing verification.

## Goals / Non-Goals

**Goals:**
- The six packaged-schema assertions execute against real files.
- The same failure mode — a derived path set collapsing to empty — fails loudly wherever it can recur.
- The repository no longer references retired distribution paths.

**Non-Goals:**
- Fixing any product defect the restored assertions expose. That is a separate authorization (see A1).
- Re-litigating `#15`'s resident-block budget, or `#17`.
- Changing installer behavior, CLI surface, gate semantics, or the scenario registry's contract.

## Decisions

- **F1** — `dist/` and `src/assets/` do not exist and are asserted not to exist. Basis: `scripts/validate_plugin.py:445` retirement list; `ls` on 2026-07-28 confirms both absent. This removes the "packaging-time only, so skip with exit 3" branch the issue originally floated: there is nothing to skip for.
- **F2** — The installer's real source root is `assets/openspec/schemas/keel-spec-driven/`, mapped into consumer repos at `openspec/schemas/keel-spec-driven/`. Basis: `scripts/install_to_repo.py:352-365`, `OPENSPEC_ASSET_ROOT = assets/openspec`. Five files: `schema.yaml` plus four templates.
- **F3** — `run_keel_hook` (`scripts/validate_plugin.py:2465`) has zero callers. Basis: grep for `run_keel_hook(` returns only the definition.
- **D1** — Repoint the helper at the F2 root and **raise** when the root is missing, rather than returning `[]`. Basis: `install_to_repo.py:352` already raises `ValueError` on exactly this condition. The same fact must not be fatal in the installer and silent in the validator; the asymmetry is the defect, not the wrong path string. Repointing alone would fix today's symptom and leave the silence in place.
- **D2** — Delete rather than repoint the `compact-task-authoring` projection loop. Basis: what it intended to assert (repo-local copy equals packaged copy) is already asserted byte-for-byte by `invalidation-authoring-surface`, added in 5.3.3. Repointing it would duplicate a working check; keeping it as-is preserves a check that has never compared anything.
- **D3** — Delete `run_keel_hook`; **repoint** rather than delete the two `if base.exists()` package-hygiene loops. Basis: F3 for the helper. The hygiene loops assert that no live `keel/TASK.md` placeholder and no `keel/backlog/*` asset ships; that intent is still valid, and the roots that actually ship are declared by `package.json`'s `files` (`bin/`, `scripts/`, `src/core/`, `assets/`, `plugins/`). Deriving the roots from `files` makes the check track what is really packaged instead of a hardcoded tree that can retire again. Their vacuity could not hide a regression — they are negative assertions — so this is intent preservation, not coverage restoration.
- **D4** — Collapse `validate_openspec_schema`'s `(("source", source_root), ("dist", dist_root))` loop, where `dist_root = source_root`. Basis: it checks one directory twice and labels one pass `dist`, implying a second copy that does not exist.
- **D5** — The new scenario asserts on the helper's **behavior**, not on a file listing: an empty derived set is a failure, and a missing root raises. Basis: pinning the current five filenames would make the check a maintenance tax that fails on every legitimate template addition, while the defect being locked out is emptiness, not a particular count.

## Hidden Knowledge / Assumptions

- **A1** — The six restored assertions may fail on first execution, which would mean a real product defect hid behind the vacuity. Basis: they have provably never run. Resolve by: the implementing task records the first-run outcome as evidence. If any assertion fails, the task hard-stops and reports; fixing installer behavior is outside Touch and requires explicit reauthorization. The change is not blocked on the outcome — restoring the check is correct either way.
- **A2** — `native-plugin-install-matrix` (one of the four restored scenarios) skips with exit `3` when the `codex`/`claude` CLIs are absent. Basis: `keel-validation-runner`'s skip convention. On this host both are present, so its restored assertion does execute; on a bare CI runner it legitimately does not. The other three scenarios have no runtime dependency and execute everywhere.

## Coupled Iteration Contract

Not required; no coupled artifacts.

## Risks / Trade-offs

- **Raising instead of returning `[]` makes the helper fatal at import-adjacent call time.** Accepted: every caller is inside a scenario that already fails loudly, and the raise carries the missing path. The alternative — returning `[]` with a warning — reproduces the reviewed defect in quieter form.
- **Deleting rather than repointing loses one nominal check** (`compact-task-authoring`'s projection). Accepted per D2: it never compared anything, and `invalidation-authoring-surface` already asserts the pair it meant to.
- **A restored assertion could fail for a fixture reason rather than a product reason.** Handled by A1's stop-and-report boundary; the evidence records which.

## Open Questions

None.
