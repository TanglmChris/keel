## Context

The scenario's intent is sound: proving that `keel --install` skips `AGENTS.md` in Keel's own repository requires running it against something the installer classifies as Keel's own repository. The mistake was reaching for the real one when a fixture would do, and then asserting only the property under test rather than the absence of other writes.

## Goals / Non-Goals

**Goals:**
- `npm test` leaves the working tree byte-identical.
- The 5.3.4 marker check is green because the markers are right, not because the suite wrote them.
- The class is refused at source level, not just fixed at one call site.

**Non-Goals:**
- Changing `keel --install`. Installing into the source repository is a supported operation and is how `.codex/` was refreshed by hand twice.
- Making the whole suite provably read-only. Scenarios legitimately read `ROOT`; only mutating invocations against it are refused.
- Reworking the overlay refresh's position outside the dry-run plan (F3).

## Decisions

- **F1** — `is_keel_source_repo` requires exactly two signals: `package.json` with `name` equal to the Keel package name, and a `plugins/keel/` directory. Basis: `scripts/install_to_repo.py:454-468`, whose docstring says both are required so a vendoring project is not misclassified. A fixture therefore costs three lines.
- **F2** — The scenario is the only place a mutating Keel command is aimed at `ROOT`. Basis: `grep` for `run_keel(ROOT` and `run_install(ROOT` returns one mutating call site among many read-only ones (`--help`, `--version`, `--doctor`, `gate …`).
- **F3** — The overlay refresh runs outside the dry-run action plan: with a stale marker, `keel --check` prints an empty plan while `keel --install` reports `refreshed=1`. Basis: reproduced by rolling one marker back. This is why the side effect was invisible to anyone reading the plan.
- **D1** — Fix the scenario with a fixture rather than by snapshotting and restoring `ROOT`. Basis: restore-after-write still writes, so it would leave the same window open for a parallel scenario and would keep the marker check passing for the wrong reason during the run.
- **D2** — Add a source-level refusal keyed on the *invocation*, listing which Keel subcommands mutate, rather than banning `ROOT` outright. Basis: most `ROOT` invocations are read-only and legitimate; a blanket ban would be rewritten into a workaround the first time someone needed `--version`.
- **D3** — Also assert, inside the scenario, that the install wrote nothing to the fixture beyond what it announced. Basis: the original defect was not the wrong repository so much as the missing assertion; moving to a fixture without adding the assertion would leave the same blind spot in a safer place.

## Hidden Knowledge / Assumptions

- **A1** — A fixture satisfying F1 exercises the same `collect_actions` branch as the real repository, so the skip being asserted is the same skip. Basis: the branch is a direct `is_keel_source_repo(repo)` test with no other repository-shape input.

## Risks / Trade-offs

- **A fixture can drift from what the real source repository looks like.** Mitigated by F1: the classifier reads two signals, and the fixture provides exactly those, so drift would have to be a change to the classifier — which would fail this scenario rather than pass it silently.
- **The mutating-command list must be maintained.** Accepted, and preferable to the alternatives: an under-inclusive list fails open for one command, while banning `ROOT` outright fails closed for dozens of legitimate reads.

## Open Questions

None.
