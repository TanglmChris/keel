## Why

Keel writes a `keel:openspec-surface-overlay` block into files OpenSpec owns — the `opsx` command surfaces and the `openspec-*` skills. `keel --uninstall` does not take it back out.

What is left behind is not inert. The block's whole content is Keel: it tells the agent to run `keel gate change-close --action sync`, to run `keel-review-checklist`, to invoke OpenSpec through `keel openspec`, and to read standing authorization from `keel/config.yaml`. After an uninstall, none of those exist. A user who tried Keel on an existing OpenSpec repository and removed it is left with `/opsx:sync` instructions pointing at a command that was just deleted, in a file that was never Keel's.

Reproduced 2026-08-03 at 5.22.0 on all three targets. Every surface keeps its overlay: Claude 8 of 8, Codex 8 of 8 (four in `.codex/skills/`, four in `CODEX_HOME/prompts/`), OpenCode 6 of 6. In the same run the `keel:start` managed block *is* removed from `AGENTS.md` and `CLAUDE.md`, so the uninstall looks clean everywhere a reader is likely to check.

The published spec already says this should not happen. `keel-openspec-surface-overlay` carries the scenario line "uninstalling removes it from the sync surface as it does from the others" — a claim nothing implements, and whose "as it does from the others" was never true of the others either.

## What Changes

`keel --uninstall` and `keel --clear` remove the overlay block from every surface `keel --init` / `keel --install` project it onto, driven by the same surface list, and leave the file itself and every other byte in it alone.

- The removal is a Node-side step in `bin/keel.js`, beside the write it reverses. The uninstall path runs through the Python installer, which has no overlay knowledge at all — one occurrence of the word "overlay" in that file, in its module docstring.
- `--dry-run` names each surface it would clean and writes nothing, which is the same gap `--check` already had to close for the refresh step.
- A surface with no overlay, or no file, is counted and not an error, so a second uninstall is a no-op rather than a failure.

**No gate, no protocol, and no interface changes.** `--uninstall` already edits these two categories of file; this makes it finish the second one.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-openspec-surface-overlay`: gains the requirement that uninstalling removes the overlay from every surface installing projects it onto, bounded to the block, with the file preserved.

## Impact

- `bin/keel.js`: one strip helper, one removal function symmetric with `refreshOpenSpecSurfaceOverlay`, and the uninstall/clear dispatch calling it after the installer returns.
- `scripts/validate_plugin.py`: one scenario across all three targets, and one stale comment corrected — it currently records the absence as deliberate and points at this issue.
- Risk is the removal reaching past its block into a file Keel does not own. It is bounded by matching the block plus only the separator the install side inserted, and by an assertion that compares the whole file after uninstall against the bytes that preceded the overlay before it.
- No new dependency. No protocol, timing, ordering, permission, or security boundary changes.
