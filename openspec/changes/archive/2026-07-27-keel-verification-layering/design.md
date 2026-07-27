# Design — keel-verification-layering

## Context

`keel --install` (`scripts/install_to_repo.py`) writes an AGENTS managed block,
the Claude hook config into `.claude/settings.json`, and `openspec/config.yaml`;
it does not touch git hooks today. The CLI (`bin/keel.js`) parses `--install`
with `[repo] [--target] [--dry-run] [--force-template-update]` and reverts via
`--uninstall`/`--clear`. Task `Verify` is parsed in `src/core/task-contract.js`
`verification()` as one `Strategy:` entry plus ordered `M<n>: <check>` lines, with
Evidence labels mapping one-to-one to the `M<n>` labels.

## Facts

- **F1** — Keel has one runtime dependency (`@fission-ai/openspec`) and no YAML
  parser. It already hand-parses flat `key: value` front matter for
  `keel/HANDOFF.md` in `src/core/context.js`, so a flat `keel/config.yaml` needs
  no new dependency.
- **F2** — `core.hooksPath` is a per-clone local git config (stored in
  `.git/config`); pointing it at `.githooks` overrides any global hooks path
  (Codex/Husky) for that repo only, and unsetting it restores the default.
- **F3** — Git for Windows ships `sh`, so a `#!/bin/sh` `.githooks/pre-push` runs
  on Windows, Linux, and macOS alike.
- **F4** — `verification()` splits `Verify` into `Strategy:` and `M<n>:` lines via
  `^(M[1-9]\d*):\s*(.*)$`; an optional inline layer tag must parse without
  colliding with that label grammar or with Evidence's `M<n>.red`/`M<n>.green`.
- **F5** — The tasks template is single-sourced in two byte-identical copies
  (`openspec/schemas/keel-spec-driven/templates/tasks.md` and its
  `assets/…` projection); the validator fails on divergence, so both change together.

## Decisions

### D1 — One new capability owns the layering methodology and its surfaces

`keel-verification-layering` owns the fast/full split, the `fast_check`
declaration, the `--with-git-hooks` scaffold, and the doctor surface. Rationale:
these are one coherent feature; scattering them across install/portability/
diagnostics capabilities would fragment the story. The `Verify` tag is the one
piece that belongs to the existing `keel-task-capsule` contract and is a MODIFIED
requirement there.

### D2 — `fast_check` lives in `keel/config.yaml`, flat-key parsed

Projects declare the fast inner-loop command as `fast_check: <command>` in a new
`keel/config.yaml`, parsed by the same minimal flat-scalar reader style Keel uses
for HANDOFF front matter (no YAML dependency). Rationale: keeps the command
Keel-owned and future-extensible without pulling in a parser; `keel/` is Keel's
own project surface.

### D3 — `--with-git-hooks` is an explicit flag; revert is symmetric

A plain `keel --install` never touches git config. `--with-git-hooks` generates
`.githooks/pre-push` running `fast_check` and sets `core.hooksPath .githooks`,
refusing when `fast_check` is undefined (nothing to run). `keel --uninstall` and
`keel --clear` unset `core.hooksPath` only when it equals `.githooks`, leaving the
committed `.githooks/pre-push` in place. Rationale: git-config mutation is
surprising, so it stays opt-in and reversible, and Keel never clobbers a
hooksPath it did not set.

### D4 — `Verify` gains an optional `(fast)`/`(full)` layer tag, default `full`

A check may be written `M1 (fast): <check>` or `M1 (full): <check>`; an untagged
check defaults to `full`. Rationale: `full` is the conservative default (an
unmarked check belongs to the complete gate). The tag is declarative — it records
which checks the fast inner loop runs — and does not change red-green rules or
what `change-close` requires (every `M<n>` still needs evidence).

### D5 — Doctor reports the surface, never mutates it

`keel --doctor` adds a fast pre-push section reporting whether `fast_check` is
declared, whether `.githooks/pre-push` exists, and the current `core.hooksPath`.
Rationale: doctor is read-only; activation stays with `--install --with-git-hooks`.

## Risks

- Setting `core.hooksPath` overrides other hook managers repo-locally. Mitigated
  by the explicit flag, the symmetric revert, and doctor visibility. Keel's own
  repo (which uses an ECC pre-push) is never affected — the scaffold is exercised
  only in isolated validator temp repos.
- The `Verify` tag parser must stay backward compatible: existing untagged tasks
  keep compiling unchanged (default `full`), and the tag must not be mistaken for
  part of the check text or an Evidence red/green label.

## Verification

- Methodology (D1): evidence-first — the capability spec and READMEs state the
  split; a validator scenario asserts the README section.
- Config + scaffold + doctor (D2/D3/D5): regression-first through the CLI — new
  validator scenarios build isolated repos, declare `fast_check`, run
  `keel --install --with-git-hooks` (asserting the generated hook and
  `core.hooksPath`), run `--uninstall` (asserting the revert), and read
  `keel --doctor` output; red before the code exists, green after.
- Verify tag (D4): regression-first through `task-contract.js` — a validator
  scenario compiles a task whose `Verify` carries a `(fast)`/`(full)` tag and
  asserts the parsed layer, with an untagged check defaulting to `full`; red
  before the parser change, green after.
