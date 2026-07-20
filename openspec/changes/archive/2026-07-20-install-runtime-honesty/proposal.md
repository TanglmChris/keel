## Why

After `keel --init`, several surfaces tell an agent something the runtime does not deliver. This is Change 1's failure shape (surface disconnected from reality) at the **install / openspec-runtime / lifecycle** layer instead of the gate layer.

- **keel-* skills never install (issue #1 Case A).** The overlay, `keel --help`, and `keel --doctor` all reference the `keel-*` behavioral skills, but `keel --init` installs none of them. `scripts/install_to_repo.py:skill_actions` sources the five `CORE_KEEL_SKILLS` from a deliberately retired `dist/` directory (`scripts/validate_plugin.py:376` and `:1905` assert `dist/` and `npm run build` are retired; `package.json` `files` ships neither `dist/` nor `src/skills/`), so `skills_root.is_dir()` is always false and zero keel-* skills land. Confirmed empirically: this repo's own `.codex/skills/` holds only the five `openspec-*` skills, zero keel-*. The v4 architecture delivers keel-* through the plugin (`plugins/keel/skills/`, shipped via `files`), and the thin-CLI spec forbids the CLI from copying `.claude/skills/keel-*`; so the defect is not a missing CLI install but surfaces (help, doctor) that dishonestly imply CLI install plus a dead code path that would violate that spec.
- **Bare `openspec` is not callable (issue #2).** The opsx skills drive bare `openspec …`, but the openspec shim lives at keel's nested `node_modules/.bin/openspec` and is not on PATH, so the first `openspec` command is command-not-found. `keel --doctor` nonetheless reports `openspec: ok` because `findOpenSpecCommand()` resolves the internal shim (`bin/keel.js:1262-1267`) — "keel-resolvable" is reported as if "PATH-runnable."
- **archive double-applies the spec delta (issue #3).** `/opsx:sync` promotes a change's spec delta into the main specs, then `openspec archive` re-applies the same delta and aborts with `ADDED … already exists`; only `--skip-specs` completes. Both are documented paths, so a change authored via sync then archived aborts at close.
- **Guard is not cleared on archive (issue #2 addendum).** After a change is archived, its guard manifest is not cleared, leaving a `drifted` dangling guard that demands reauthorization for a task that no longer exists.

## What Changes

- **Case A (issue #1) — honest, complete skill delivery.** keel-* skills are plugin-delivered by design (they ship in `plugins/keel/skills/` via `files`), so the thin CLI must not install them. Remove the dead `skill_actions` keel-* path (it sources the retired `dist/` and would violate the thin-CLI spec), correct the false `keel --help` text that claims the CLI installs `.claude/skills/keel-*`, and make `keel --doctor` report the keel-* skill inventory as a plugin surface with explicit remediation when the plugin is absent — so `keel --init` completeness is verifiable rather than pretended.
- **issue #2 — openspec invocable + doctor honesty.** Add a `keel openspec …` passthrough (resolving keel's internal shim) and have keel's overlays direct skill-driven agents to use it in place of bare `openspec` (decided: overlay/passthrough, not PATH surgery). Downgrade doctor's `openspec: ok` to a warning when the resolved openspec is not PATH-reachable, naming the working invocation.
- **issue #2 addendum — guard lifecycle.** The archive overlay reminds the current agent to run `keel guard clear` after archiving (decided: gate stays read-only), so no `drifted` guard is left hanging; the gate still writes nothing and the guard spec's "gates never delete the manifest" invariant is preserved.
- **issue #3 — archive idempotency after sync.** Overlay the archive skill to pass `--skip-specs` when `/opsx:sync` has already promoted the delta (decided), so a change authored through `/opsx:sync` and then archived does not abort. Root idempotency stays upstream in `@fission-ai/openspec`; keel guides around it.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-skill-sourcing-and-portability`: keel-* skills are plugin-delivered; the CLI no longer claims or attempts to install them, and the documented product matches what `keel --init` plus the installed plugin actually provide.
- `keel-target-surface-diagnostics`: doctor distinguishes "keel-resolvable" from "PATH-reachable" for openspec, reports the keel-* skill inventory as a plugin surface with remediation, and the `keel --help` text matches reality.
- `keel-openspec-surface-overlay`: overlay guidance makes openspec invocable for skill-driven agents, sequences `/opsx:sync` → `archive --skip-specs`, and reminds the agent to clear the guard after archiving.

## Impact

- Code: `scripts/install_to_repo.py` (remove the dead keel-* `skill_actions` path), `bin/keel.js` (`keel openspec` passthrough per Q1; doctor openspec PATH honesty; doctor keel-* plugin-skill inventory + remediation; corrected `--help` text).
- Assets / overlay: the archive overlay text (`--skip-specs` sequencing plus the `keel guard clear` reminder); the openspec-invocation direction in overlays.
- Validator: `scripts/validate_plugin.py` gains assertions that the CLI does not install keel-* skills, that `--help`/doctor describe plugin delivery, that doctor warns when openspec is not PATH-reachable, and that the archive overlay carries the `--skip-specs` sequence and the guard-clear reminder.
- Upstream boundary: the archive delta idempotency itself lives in vendored `@fission-ai/openspec`; keel wraps or guides around it rather than patching upstream.
- Closes GitHub issue #1 Case A, issue #2 (and its guard addendum), and issue #3.
- Folds into the held, unpublished 5.2.0.

## Decisions

Resolved during alignment (2026-07-20):

- **Q1 — openspec invocation:** a `keel openspec …` passthrough directed by keel's overlays, not PATH exposure.
- **Q2 — archive idempotency:** overlay the archive skill to pass `--skip-specs` after `/opsx:sync`; the root idempotency fix stays upstream in `@fission-ai/openspec`.
- **Q3 — guard clear point:** the archive overlay reminds the agent to run `keel guard clear` after archiving; the gate stays read-only and the guard spec's "gates never delete the manifest" invariant is preserved (resolved during authoring 2026-07-20, after the立项 direction conflicted with `keel-touch-write-guard`).

## Non-goals

- Issue #1 Cases B/C/D — the sibling change `align-gate-authoring-surface`.
- Patching `@fission-ai/openspec` internals.
- Redesigning skill delivery beyond making `keel --init` install the existing `keel-*` skills.
