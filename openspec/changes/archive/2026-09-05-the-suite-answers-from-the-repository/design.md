## Context

`run_openspec()` is the suite's one entry to the OpenSpec CLI, used by four scenarios. It was written when openspec was assumed to be a tool the host provides. It is not: `package.json` declares `@fission-ai/openspec` as a dependency, and `npm install` puts an executable at `node_modules/.bin/openspec`. npm scripts see that directory on `PATH`; a Python subprocess started by `node scripts/run_python.js` does not.

Two scenarios already treat an absent openspec as a skip (exit `3`); `compact-task-authoring` treats it as a failure. Neither behaviour is right for a declared dependency, because the dependency is present after `npm install` — the question was never "is this host equipped" but "did anyone look in the right place".

The packaging half is a different subject with the same shape. `npm pack` decides the tarball from `files`, `.npmignore`, and npm's built-in exclusions. `.gitignore` is consulted only when there is no `files` array and no `.npmignore`, so this repository's `__pycache__/` and `*.pyc` entries do not reach the packer.

## Goals / Non-Goals

**Goals:**
- Make these scenarios run on any checkout that installed the dependencies.
- Make a probe that cannot find its tool say so, instead of reporting the subject as broken.
- Make the packed file set a function of the repository.

**Non-Goals:**
- Adding openspec to `PATH` for the suite, or requiring a global install. The dependency is declared; resolving it is the fix.
- Changing the skip contract for a genuinely external runtime. Codex and OpenCode probes keep it.
- Any change to production code or to what `keel --install` writes.

## Decisions

F1 — On a checkout that has run only `npm install`, with no global openspec, `node scripts/run_python.js scripts/validate_plugin.py --all` reports `validation --all failed for: compact-task-authoring`; the scenario alone prints `compact-task-authoring could not resolve the schema through OpenSpec.`; and `node_modules/.bin/openspec schema which keel-spec-driven --json` resolves the schema with `"source": "project"`. Prefixing `PATH` with `node_modules/.bin` makes the whole run green. Basis: reproduced on this repository, 2026-09-05, against 5.44.0.

F2 — `scripts/validate_plugin.py`'s `compact-task-authoring` branch reads `if which is None or which.returncode != 0`, one condition over two distinct failures. `assertion-shape-count` bounds this shape across the suite but counts assertion sites, not scenario control flow, so it did not see this one. Basis: source read, 2026-09-05.

F3 — Packing the same commit twice: a clean checkout yields 41 files; after any run of the Python in `scripts/`, 43, the difference being `scripts/__pycache__/install_to_repo.cpython-310.pyc` and `validate_plugin.cpython-310.pyc`. `npm view @christang/keel@5.44.0` shows the published build was the 41-file one, and every file in it matches `main` byte for byte. Basis: `npm pack --dry-run --json` before and after, plus a file-by-file hash comparison of the published tarball, 2026-09-05.

D1 — `run_openspec()` resolves `<ROOT>/node_modules/.bin/openspec` first and falls back to `shutil.which`. Basis: F1. The declared dependency is the version this repository is tested against; a global install that happens to be on `PATH` is a different version answering for it, which is the weaker of the two.

D2 — The two failures in `compact-task-authoring` are split. An unresolvable CLI reports the skip contract, exit `3`, and names the locations it searched; a CLI that ran and refused fails and prints its output. Basis: F2 and `keel-review-checklist`'s rule that a failure message must name the actual cause. After D1 the skip path should be unreachable on any installed checkout, which is why it must say where it looked — a skip nobody can explain is worse than a failure.

D3 — The skip contract is extended in wording, not in scope: it already covers "an external runtime it probes is absent", and a declared dependency that is somehow absent is the same observable state. What changes is that the runner resolves the dependency first, so the skip stops standing in for a lookup that was never done. Basis: the existing requirement already forbids skipping for anything but an absent runtime, and this keeps that.

F4 — Measured on this repository with `scripts/__pycache__/probe.pyc` present, 2026-09-05: a root `.npmignore` carrying `__pycache__/` and `*.pyc` packs **42** files — it is not consulted at all for a directory named by `files`. A `.npmignore` placed inside `scripts/` packs 41, and negated entries in `files` (`!**/__pycache__`, `!**/*.pyc`) pack 41. Basis: `npm pack --dry-run --json` under each of the three arrangements.

D4 — The exclusion is expressed as negated entries in `package.json`'s `files`, not as an `.npmignore`. Basis: F4. A root `.npmignore` does not run, which is the arrangement that looks right and silently does nothing; a directory-local one runs but guards only the directory it sits in, so residue appearing anywhere else would ship. Negated entries sit beside the inventory they qualify and cover every included directory at once. This reverses the reading in issue #110, which assumed an `.npmignore` would take over from `.gitignore` — it would, for a package with no `files` array.

D5 — The check asserts that every packed file is tracked by Git, not that the packed set equals a computed list. Basis: this is the invariant the issue is about — the tarball is decided by the repository — and it cannot false-positive on npm's own always-include rules, since `package.json` and `README.md` are tracked. A recomputed expected list would have to reimplement npm's inclusion order and would drift from it.

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **`.npmignore` replaces `.gitignore` wholesale.** Anything the packer was excluding via `.gitignore` and is not restated is newly included. The entries are few and are restated; the new check is also the guard, since anything newly included would be untracked or would not be.
- **Preferring the local dependency hides a global mismatch.** A host whose global openspec differs from the declared one will now be ignored by these scenarios. That is the intent: the declared version is the one this repository is tested against.
- **The pack check runs `npm pack --dry-run`,** which is slower than the assertions around it and needs npm present. npm is already required to run the suite at all.

## Open Questions

None.
