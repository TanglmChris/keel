## Why

Issue #405. A user asked for "Markdown with embedded SVG to one Word document" as a Keel plugin capability and supplied a working prototype (`md2word`: a Python converter on python-docx, lxml, and Pillow, with a Node helper on marked and sharp). Generic Markdown-to-Word paths drop raw SVG, and without Keel the user keeps a private script that nothing discovers or updates.

The owner decided the shape on 2026-10-21 (recorded on #405): an on-demand skill in the keel plugin; third-party dependencies are not bundled and are installed, only after the user confirms, into an environment Keel manages; an existing output file is refused unless replacement is asked for; a `keel docx` command with `setup` (which lists before it installs) and `convert`, the environment in `~/.keel/docx/`. The owner also decided that no dependency is installed on this machine for this change, so the real conversion and the page-by-page rendering of a Chinese example are recorded as unverified.

## What Changes

- New skill `keel-md-docx` in the keel plugin, with the converter (`scripts/md2word.py`, `scripts/runtime.mjs`, a macOS font configuration, and the pinned dependency lists) beside its `SKILL.md`. It loads only when the user asks to export Markdown with SVG to Word.
- New `keel docx setup [--yes]`: without `--yes` it prints each package, its licence, its download size, and where it would go, and installs nothing; with `--yes` it creates a Python virtual environment and a Node package directory under `~/.keel/docx/` (or `$KEEL_HOME/docx/`) and installs the pinned packages there, never globally, and records the environment as ready only when every step succeeded.
- New `keel docx convert <input.md> [-o <output.docx>] [--template <template.docx>] [--replace]`: refuses before setup, naming the setup command; refuses an existing output without `--replace`; otherwise runs the converter in the managed environment, which writes atomically, so a failed conversion leaves any previous file untouched.
- The converter is the #405 prototype without its machine-specific launcher: the probe of a Codex runtime cache is removed, and Keel supplies the Node binary, the module directory, and on macOS the font configuration.
- The skill's provenance, licences, sizes, trigger cases, and the unverified acceptance items are recorded in `keel/archive/skill-evidence/keel-md-docx-v1.md`.

## Capabilities

### New Capabilities
- `keel-md-docx-export`: on-demand Markdown-with-SVG export to Word through a consented, Keel-managed environment.

### Modified Capabilities
- none

## Impact

New `src/core/docx.js`, `bin/keel.js` (dispatch, help, skill list), new `src/skills/keel-md-docx/` and its mirror under `plugins/keel/skills/`, new `scripts/validation/export.py`, `scripts/validation/registry.py`, `scripts/validation/hosts.py` (plugin skill list), `scripts/validation/baseline.py` (mutating commands), both READMEs, `keel/archive/skill-evidence/`, the changelog. No new package dependency.
