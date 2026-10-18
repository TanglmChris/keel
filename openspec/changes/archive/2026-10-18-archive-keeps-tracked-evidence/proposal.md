## Why

Issue #352 (rtl_ppa_prj, keel 5.139.0, 2026-10-18): archiving `iecc-coupled-fifo-loop-fix` dropped 34 tracked evidence files from version control. The change directory carried its own `.gitignore` (`evidence/**`) and the evidence had been force-added. The archive moves the directory on the filesystem, so at the archived path git sees the old paths deleted and the new ones ignored, and the archive commit deleted the evidence while the files sat on disk. Nothing warned.

## What Changes

- `keel openspec archive` re-adds, with `git add -f`, each file that git tracked under the change before the move and that the archived path leaves ignored, and says how many it re-added.
- `keel gate change-close --action archive` warns, before any move, about tracked files under the change that an ignore rule matches, naming them and the archive that keeps them.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-openspec-surface-overlay`: an archive through Keel keeps the files the change tracked.

## Impact

`bin/keel.js`, `src/core/gates.js`, `scripts/validate_plugin.py`, one published spec, the changelog.
