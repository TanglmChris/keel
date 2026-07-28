## Context

The overlay refresh is a Node-side step that runs after the Python installer. `keel --check` invokes only the installer, twice, so the Node step is structurally outside its plan. The `dryRun` branch inside `refreshOpenSpecSurfaceOverlay` exists but is reachable only from `--install --dry-run` and `--init`, and it never reads a file — it prints one line per known surface.

## Goals / Non-Goals

**Goals:**
- Every write a real run would perform appears in the corresponding dry-run.
- No write that would not happen appears in a dry-run.
- The two dry-run entry points agree with each other and with the real run.

**Non-Goals:**
- Changing what `keel --install` writes.
- Moving the overlay refresh into the Python installer's action plan. That would unify the two halves, but it relocates working product code to fix a reporting defect; reporting is what is broken.

## Decisions

- **F1** — `--check` never calls `refreshOpenSpecSurfaceOverlay`. It runs `INSTALL_SCRIPT` for status and again with `dryRun: true` for the plan. Basis: `bin/keel.js` `action === "check"`, which returns the second `runPython` directly.
- **F2** — The dry-run branch returns before reading any surface and prints one `would refresh` line per surface. Basis: `refreshOpenSpecSurfaceOverlay`'s `options.dryRun` block, which loops `surfaces` and returns zeroed counts. Reproduced: one stale marker out of six, six `would refresh` lines.
- **F3** — The real run's three-way classification is cheap and pure: read the file, compute `mergeOpenSpecSurfaceOverlay`, compare. Nothing about it needs to write. Basis: the non-dry-run loop in the same function.
- **D1** — Make the dry-run compute F3's classification rather than list surfaces. Basis: the two paths then share one definition of "would change", so they cannot disagree; today they are separate pieces of code that happen to be about the same thing.
- **D2** — Report the dry-run in the same `refreshed=/current=/missing=` shape as the real run, with a `would ` prefix on the per-file lines. Basis: a reader comparing plan to outcome should be comparing like with like; different shapes invite the reader to assume they measure different things.
- **D3** — Have `--check` call the overlay dry-run after the installer plan. Basis: F1 — this is the whole of the reported defect, and it is one call.

## Hidden Knowledge / Assumptions

- **A1** — `--check` refuses `--dry-run` as an explicit flag but is itself a dry run; passing `dryRun: true` internally is consistent with what it already does for the installer plan. Basis: the same action already constructs `{ ...options, dryRun: true }`.

## Risks / Trade-offs

- **`keel --check` output grows** when overlays are stale. Accepted: that output is the missing information, and when nothing is stale the summary line reports `current=N` rather than listing files.
- **Computing the merge during a dry run costs a read per surface.** Six small files; the real run already does it.

## Open Questions

None.
