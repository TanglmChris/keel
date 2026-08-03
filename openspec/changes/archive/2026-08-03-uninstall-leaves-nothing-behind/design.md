## Context

Keel installs onto two kinds of file. Files it owns — `AGENTS.md`, `CLAUDE.md`, the packaged schema — are written whole or carry a `keel:start` managed block, and the Python installer removes them on uninstall. Files OpenSpec owns — the `opsx` command surfaces and the `openspec-*` skills — receive a `keel:openspec-surface-overlay` block appended by the Node CLI after `openspec update` regenerates them.

The uninstall path only ever ran the first cleanup. `--uninstall` and `--clear` dispatch straight to the Python installer and return, and that installer has never known the overlay exists. The result is an uninstall that looks complete in the two files a user checks first and leaves Keel's instructions in eleven to fourteen files that were not Keel's to begin with.

## Goals / Non-Goals

**Goals:**
- Uninstalling removes the overlay from every surface installing writes it to, on every target.
- The removal takes the block and nothing else; the file survives, and so does every byte OpenSpec put in it.
- One surface list serves both directions, so a surface added to the install side cannot be missed by the removal side.
- `--dry-run` reports the removal it would perform rather than an empty plan for a run that writes.

**Non-Goals:**
- Restoring the OpenSpec file to its pristine upstream state. Keel appended a block; removing that block is the whole obligation. `openspec update` owns the rest of the file.
- Removing overlays a different tool's markers left behind. Only Keel's marker pair is matched.
- Changing what the overlay says, which surfaces receive it, or when it is refreshed.
- The `overlayActionLabel()` drift in the refresh summary line (see Findings ownership below). Same file, different defect, and folding it in would make this change's acceptance about two things.

## Decisions

- **F1** — reproduced at 5.22.0 on all three targets. After `keel --init` then `keel --uninstall`, the marker `keel:openspec-surface-overlay` is still present in Claude 8 of 8 surfaces, Codex 8 of 8 (4 under `.codex/skills/`, 4 under `CODEX_HOME/prompts/`), OpenCode 6 of 6. The same runs removed the `keel:start` block from `AGENTS.md` and left `CLAUDE.md` a 1-byte file. *Basis: three temporary repositories, `grep -rl` before and after each uninstall, 2026-08-03.*
- **F2** — the write path and the uninstall path never meet. `refreshOpenSpecSurfaceOverlay` is Node, called from `--init`, `--install`, and `--check`; `--clear` and `--uninstall` are one line, `runPython(INSTALL_SCRIPT, installerArgs(options, ["--uninstall"]))`, and return its status. `grep -c overlay scripts/install_to_repo.py` returns 1, and that occurrence is the module docstring. The Python side has no marker constant, no surface list, and no way to see one. *Basis: `bin/keel.js:2006`, and that grep at 5.22.0.*
- **F3** — what a reader is left with is Keel-specific and actionable. After the uninstall above, `.claude/commands/opsx/sync.md` ends with the overlay, whose surviving lines name `keel gate change-close --action sync`, `keel-review-checklist`, and "Invoke OpenSpec through `keel openspec`". All three were removed by the run that left them there. *Basis: `tail` of that file after uninstall.*
- **F4** — the published spec already asserts the missing behavior. `openspec/specs/keel-openspec-surface-overlay/spec.md` scenario "Installing projects the overlay onto the sync surface" ends "**AND THEN** uninstalling removes it from the sync surface as it does from the others". F1 shows the clause is false for sync and false for the others. *Basis: that file at 5.22.0.*
- **F5** — `--clear` and `--uninstall` are the same dispatch, and the repository already binds them jointly elsewhere: `keel-verification-layering` requires that "`keel --uninstall` and `keel --clear` MUST unset `core.hooksPath`" under one condition. Treating them together is the existing shape; making them differ would be the new decision. *Basis: `bin/keel.js:2006` and `openspec/specs/keel-verification-layering/spec.md:44`.*
- **F6** — the boundary already has a precedent in this repository. `remove_managed_block` strips the block and returns the remaining content; `plan_uninstall_managed` writes it back. The file is kept even when nothing else is in it — that is why `CLAUDE.md` survives uninstall as a 1-byte file rather than being deleted. *Basis: `scripts/install_to_repo.py:737` and `:993`, confirmed by F1's file state.*
- **F7** — `openspecOverlaySurfacesForTarget(target, repo)` is the only list of surfaces, and the count it returns is neither constant nor small: 8 for Claude, 8 for Codex, 6 for OpenCode, and it has grown twice. *Basis: reading it at 5.22.0 against F1's measured counts.*
- **F8** — the absence was recorded as deliberate, with this issue's number, in `scripts/validate_plugin.py`: "Uninstall is deliberately not asserted here. It does not strip the overlay from any surface — measured on archive as well as sync — so an assertion would be about a contract that has never existed rather than about this change." *Basis: that comment inside `validate_sync_surface_overlay_scenario`.*

- **D1** — removal lives in `bin/keel.js`, beside the write it reverses, and iterates `openspecOverlaySurfacesForTarget`. Not a port into the Python installer: the marker, the surface list, and the target rules are all Node-side, and duplicating them across the boundary is exactly the two-lists drift this project has already paid for once. *Basis: F2, F7.*
- **D2** — the match is the block plus the whitespace the install side inserted, and nothing else. The install path appends `\n\n` before the block when none is present, so removing only the marked span leaves a stray blank line. The removal regex therefore takes the newlines immediately before the block and the newline that closes it, and puts one back — a blank line elsewhere in a file Keel does not own is never touched. The file is written back, never deleted and never emptied by design. *Basis: `mergeOpenSpecSurfaceOverlay`'s separator, F6.*
- **D3** — `--clear` behaves as `--uninstall` here. *Basis: F5.*
- **D4** — `--dry-run` names each surface it would clean and writes nothing. `--check` already carries a comment recording that a Node-side step invisible to the installer's plan makes a dry run under-report a run that writes; the uninstall dry run has the same shape and is fixed at the same time rather than filed. *Basis: `bin/keel.js`, the `--check` overlay comment.*
- **D5** — a surface with no overlay, or no file at all, is counted and is not an error, symmetric with the refresh side's `current` and `missing`. So a second uninstall reports `removed=0` and succeeds, and a repository that never had an overlay is not a failure. *Basis: `refreshOpenSpecSurfaceOverlay`'s counters.*
- **D6** — the scenario asserts the overlay is present on every expected surface *before* uninstalling. Without it, a run in which the surface list resolved to nothing, or the paths were wrong, is indistinguishable from a run in which removal worked — both report "no marker found". *Precedent applied: `an-assertion-that-never-failed-proves-nothing` — a check that passes because two things agree, or because something is absent, needs a positive control. Without the precedent this would have been a question about how much the scenario should assert before the act.*
- **D7** — content preservation is asserted byte-for-byte, not by the marker's absence. The assertion compares the whole file after uninstall against the bytes that preceded the overlay before it. A removal that took the marker and half the OpenSpec file passes a marker check and fails this one. *Basis: the Goals — the risk here is over-removal from a file Keel does not own, and only a whole-file comparison measures it.*

## Hidden Knowledge / Assumptions

- **A1** — removing the block from `CODEX_HOME/prompts/opsx-*.md` is in bounds even though those files sit outside the repository. Install writes them there through the same shared list; the removal is strictly narrower than the write, taking only the marked span and leaving the file. *Basis: F1's Codex measurement — 4 of the 8 Codex surfaces are those prompts. Owner: this change.*
- **A2** — a surface holds at most one overlay block, because the install side replaces the first match rather than appending a second. The strip loops regardless, so a file that somehow carries two is left with neither rather than with one. *Basis: `mergeOpenSpecSurfaceOverlay`'s single-match replace. Owner: this change — the loop makes the assumption cost nothing if it is wrong.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- The removal edits files OpenSpec owns. That is unavoidable — it is where the block was written — and is bounded by D2 and measured by D7.
- The strip is regex-driven over the same marker pair the merge already uses. A user who hand-edited the end marker out of a surface keeps the orphaned start marker; the alternative, matching a start marker to end-of-file, would delete OpenSpec content on a file Keel damaged nothing in. The conservative failure is to leave text behind, not to remove more.
- Cleaning the separator makes uninstall's output differ by one blank line from a hand-deletion of the block. This is stated in the spec so a later reader meets it as intent.

## Open Questions

- None. The behavior is asserted by an already-published scenario (F4), the boundary is stated in the issue and matches an existing removal precedent (F6), and no gate, protocol, or interface is touched.

## Alignment

Ran `keel-align-expectations` before tasks finalized; the quick path applied. Every candidate expectation resolved against a repository fact rather than an inference: `--clear` parity by F5, the dry-run report by D4's existing `--check` comment, the file-preserving boundary by F6, and the Codex-home surfaces by A1. No `keel/lenses/` directory exists, so the domain-agnostic path applied. The declared precedent store `../decision-precedents` was consulted: `an-assertion-that-never-failed-proves-nothing` (category: acceptance, status: recorded) decided D6 in the owner's place and is cited there; `no-dependency-for-a-format-we-control` and `declarative-authorization-over-blanket-bypass` do not match a decision here.
