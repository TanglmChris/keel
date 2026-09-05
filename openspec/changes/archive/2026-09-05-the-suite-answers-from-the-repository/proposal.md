## Why

Two answers this repository gives about itself depend on the machine that produced them rather than on the repository.

**The validator looks for `openspec` only on `PATH`.** `run_openspec()` resolves it with `shutil.which("openspec")`, but openspec is this package's own declared dependency and lands in `node_modules/.bin/`, which a Python subprocess does not inherit. On a checkout that has only run `npm install`, `--all` reports `validation --all failed for: compact-task-authoring`, and that scenario alone prints `compact-task-authoring could not resolve the schema through OpenSpec` — while `node_modules/.bin/openspec schema which keel-spec-driven` resolves it perfectly. So a missing `PATH` entry is reported as a failure of the thing being probed, and the reader is sent to a schema that has nothing wrong with it. Reproduced on this repository, 2026-09-05. Issue #105.

That scenario's own condition is the second half: `if which is None or which.returncode != 0` guards two distinct failures behind one message, so "the CLI was not found" and "the CLI ran and refused" print the same sentence. `assertion-shape-count` exists in this suite to catch exactly that shape and does not read scenario internals.

**The published tarball depends on who packs it.** `files` includes `scripts/`, there is no `.npmignore`, and a declared `files` array means `.gitignore` no longer filters inside an included directory — while `__pycache__` is not on npm's default exclusion list. Measured on one commit: a clean checkout packs 41 files; the same commit after anyone has run the Python in `scripts/` packs 43, the extra two being `scripts/__pycache__/*.cpython-310.pyc`. The published 5.44.0 was the 41-file build and is unaffected, but which build gets published is decided by the publisher's working tree. Issue #110.

## What Changes

- `run_openspec()` resolves the declared dependency at `<repo>/node_modules/.bin/openspec` before falling back to `PATH`, so a checkout that ran `npm install` runs these scenarios instead of failing or skipping them.
- `compact-task-authoring` splits its two failures: a CLI it could not find reports the skip contract (exit `3`) and names where it looked; a CLI that ran and refused fails and prints what it said.
- `package.json`'s `files` gains negated entries excluding `__pycache__` and `*.pyc`. Measured: a root `.npmignore` carrying those patterns is **not consulted at all** once `files` is declared and still packs 42; negated `files` entries pack 41, as does a `.npmignore` placed inside `scripts/`. The negated entries sit beside the inventory they qualify and cover every included directory rather than one, so this is where the exclusion goes.
- A new check asserts every file in `npm pack --dry-run` is tracked by Git, so the tarball is decided by the repository rather than by the machine.

## Capabilities

### Modified Capabilities
- `keel-validation-runner`: the "The full run is parallel, deterministic, and fail-loud" requirement defines the skip contract for an absent external runtime. It gains the distinction between an external runtime and this package's own declared dependency — which is resolved from the package before `PATH` — and the rule that a probe which cannot find its tool never reports that as a failure of the thing it was probing.

### New Capabilities
- `keel-release-artifact`: what the published package contains is determined by the repository's tracked contents, not by the state of the machine that packs it, and a check enforces that.

## Impact

- Affected files: `scripts/validate_plugin.py` (`run_openspec`, the `compact-task-authoring` branch, two new scenarios) and `package.json`'s `files` array.
- No production code changes; `bin/`, `src/core/`, and the shipped assets are untouched.
- Direction: a scenario that failed on a clean checkout now runs; a diagnostic that named the wrong cause now names the right one; and the packed file set stops depending on the publisher's working tree.
- No new dependency, no CLI surface change, no change to what is installed into a target repository.
