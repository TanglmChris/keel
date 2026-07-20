## Why

After `keel --init`, several surfaces tell an agent something the runtime does not deliver. This is Change 1's failure shape (surface disconnected from reality) at the **install / openspec-runtime / lifecycle** layer instead of the gate layer.

- **keel-* skills never install (issue #1 Case A).** The overlay, `keel --help`, and `keel --doctor` all reference the `keel-*` behavioral skills, but `keel --init` installs none of them. `scripts/install_to_repo.py:skill_actions` sources the five `CORE_KEEL_SKILLS` from a deliberately retired `dist/` directory (`scripts/validate_plugin.py:376` and `:1905` assert `dist/` and `npm run build` are retired; `package.json` `files` ships neither `dist/` nor `src/skills/`), so `skills_root.is_dir()` is always false and zero keel-* skills land. Confirmed empirically: this repo's own `.codex/skills/` holds only the five `openspec-*` skills, zero keel-*.
- **Bare `openspec` is not callable (issue #2).** The opsx skills drive bare `openspec …`, but the openspec shim lives at keel's nested `node_modules/.bin/openspec` and is not on PATH, so the first `openspec` command is command-not-found. `keel --doctor` nonetheless reports `openspec: ok` because `findOpenSpecCommand()` resolves the internal shim (`bin/keel.js:1262-1267`) — "keel-resolvable" is reported as if "PATH-runnable."
- **archive double-applies the spec delta (issue #3).** `/opsx:sync` promotes a change's spec delta into the main specs, then `openspec archive` re-applies the same delta and aborts with `ADDED … already exists`; only `--skip-specs` completes. Both are documented paths, so a change authored via sync then archived aborts at close.
- **Guard is not cleared on archive (issue #2 addendum).** After a change is archived, its guard manifest is not cleared, leaving a `drifted` dangling guard that demands reauthorization for a task that no longer exists.

## What Changes

- **Case A (issue #1) — keel-* skills actually install.** Repoint `skill_actions` to a shipped source (the git-tracked `plugins/keel/skills/`, or add `src/skills/` to `files`) and drop the dead `dist/` dependency; ensure that source ships via `files`. Once the keel-* skills land, the overlay / help / doctor references become true; correct the `keel --help` skill-prefix wording if it still misstates the location.
- **issue #2 — openspec invocable + doctor honesty.** Add a `keel openspec …` passthrough (resolving keel's internal shim) and have keel's overlays direct skill-driven agents to use it in place of bare `openspec` (decided: overlay/passthrough, not PATH surgery). Downgrade doctor's `openspec: ok` to a warning when the resolved openspec is not PATH-reachable, naming the working invocation.
- **issue #2 addendum — guard lifecycle.** Auto-clear the change's guard manifest on the change-close archive action (decided), so no `drifted` guard is left hanging.
- **issue #3 — archive idempotency after sync.** Overlay the archive skill to pass `--skip-specs` when `/opsx:sync` has already promoted the delta (decided), so a change authored through `/opsx:sync` and then archived does not abort. Root idempotency stays upstream in `@fission-ai/openspec`; keel guides around it.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-skill-sourcing-and-portability`: the `keel-*` skills install from a shipped source; the documented install product matches what `keel --init` actually lays down.
- `keel-target-surface-diagnostics`: doctor distinguishes "keel-resolvable" from "PATH-reachable" for openspec and reports the skill install truthfully; the `keel --help` prefix matches reality.
- `keel-openspec-surface-overlay`: overlay guidance makes openspec invocable for skill-driven agents and sequences `/opsx:sync` → `archive --skip-specs`.
- `keel-touch-write-guard`: the guard manifest auto-clears on change-close / archive rather than lingering as `drifted`.

## Impact

- Code: `scripts/install_to_repo.py` (skill_actions source; retire the dead `dist/` path), `package.json` (`files` ships the keel-* skill source), `bin/keel.js` (doctor openspec honesty; optional `keel openspec` passthrough per Q1; guard-clear wiring; help prefix).
- Assets / overlay: the archive (and possibly sync) overlay text; `keel --help` wording.
- Validator: `scripts/validate_plugin.py` gains assertions that keel-* skills install for each target, that doctor warns when openspec is not PATH-reachable, and that the guard clears on archive.
- Upstream boundary: the archive delta idempotency itself lives in vendored `@fission-ai/openspec`; keel wraps or guides around it rather than patching upstream.
- Closes GitHub issue #1 Case A, issue #2 (and its guard addendum), and issue #3.
- Folds into the held, unpublished 5.2.0.

## Decisions

Resolved during alignment (2026-07-20):

- **Q1 — openspec invocation:** a `keel openspec …` passthrough directed by keel's overlays, not PATH exposure.
- **Q2 — archive idempotency:** overlay the archive skill to pass `--skip-specs` after `/opsx:sync`; the root idempotency fix stays upstream in `@fission-ai/openspec`.
- **Q3 — guard clear point:** the change-close archive action clears the guard manifest.

## Non-goals

- Issue #1 Cases B/C/D — the sibling change `align-gate-authoring-surface`.
- Patching `@fission-ai/openspec` internals.
- Redesigning skill delivery beyond making `keel --init` install the existing `keel-*` skills.
