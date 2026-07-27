# Keel verification layering: fast inner-loop vs full gate, with an opt-in fast pre-push

## Why

Generic pre-push hooks (Codex/ECC, Husky, …) commonly run a project's *full*
test suite. On projects with a slow suite — golden byte-determinism tests that
run 40–60 minutes serially, for example — every `git push` is blocked for a long
time. The hook itself is not Keel's, but Keel owns the spec-driven verification
workflow and installs project protocol/host files, so Keel is positioned to give
its projects a convention that avoids the trap. Reported as GitHub issue #5.

The methodology Keel already implies — fast red-green inner loop, full evidence at
`change-close` — has no explicit split between what belongs at a local pre-push
and what belongs at CI / the full gate, and the task capsule's `Verify` checks
carry no layer marker to express it. Projects also have nowhere to declare the
one fast check Keel could wire into a repo-local pre-push.

## What changes

- **Methodology (spec + docs).** A `keel-verification-layering` capability states
  the split: a *fast inner-loop* check (seconds, local pre-push) versus the *full
  gate* (CI or `keel gate change-close`). The READMEs document it.
- **Fast-check declaration (`keel/config.yaml`).** Projects declare their fast
  inner-loop command in a new `keel/config.yaml` (`fast_check: <command>`), read
  by Keel's existing minimal flat-key parser — no new dependency. `keel --install`
  scaffolds a commented template.
- **Opt-in fast pre-push (`keel --install --with-git-hooks`).** Behind an explicit
  flag, `keel --install` generates `.githooks/pre-push` (a `#!/bin/sh` script that
  runs `fast_check`) and sets `git config core.hooksPath .githooks` (per-clone,
  repo-local, reversible). It refuses when `fast_check` is undefined. `keel
  --uninstall`/`--clear` unsets `core.hooksPath` when it points at `.githooks`.
- **Diagnostics.** `keel --doctor` reports the fast pre-push surface: whether
  `fast_check` is declared, whether `.githooks/pre-push` exists, and the current
  `core.hooksPath`.
- **Verify layer tag (`keel-task-capsule`).** A task capsule `Verify` check may
  carry an optional `(fast)` / `(full)` layer tag; untagged defaults to `full`.
  The tag is declarative metadata (which checks belong to the fast inner loop);
  `change-close` still requires evidence for every `M<n>`.

## Non-goals

- Keel does not own or run the project's test content — the project authors its
  own `fast_check` command; Keel only wires and reports it.
- No implicit `core.hooksPath` mutation: the flag is required, so a plain
  `keel --install` never touches git config or global hooks.
- No CI-provider configuration is generated; the full/slow layer staying in CI is
  the project's own pipeline.
- The `Verify` layer tag does not change what `change-close` requires (all `M<n>`
  evidence); it does not gate completion on the fast/full split.
- No version bump or release; this lands on `main` and folds into a later release
  decided separately.
