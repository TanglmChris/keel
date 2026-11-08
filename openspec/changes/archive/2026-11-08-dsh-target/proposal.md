## Why

Issue #504 (Keel 5.216.0, DSH 0.2.0-rc.2; probed again on 2026-11-08 against DSH 0.2.2-rc.1): the owner runs Keel and DSH (DeepSeek Harness) side by side, and `keel --init --target dsh`, `keel capabilities --target dsh` and `keel project --target dsh` all answer `invalid target: dsh`. The owner approved stage S1 of the design posted on #504 on 2026-11-08 and chose that DSH share Codex's files rather than get its own.

## What Changes

- **`dsh` becomes an accepted `--target`** for `--init`, `--install`, `--check`, `--doctor`, `--clear`, `--uninstall`, `keel capabilities` and `keel project`.
- **DSH uses Codex's repository surface, not one of its own.** DSH reads the repository `AGENTS.md` and `.agents/skills`, which are the files the Codex target writes. `--target dsh` therefore writes, checks and removes exactly what `--target codex` does; no `.dsh/` copy is made.
- **Capabilities and projection name the host.** `keel capabilities --target dsh` and `keel project --target dsh --event …` report target `dsh`, all six behaviors `manual`, and evidence that says what was probed: DSH's factory profiles carry no session-start, resume or compaction hook, so the entry is the `AGENTS.md` bootstrap (run `keel context` first), the same level as OpenCode.
- **`keel --doctor --target dsh` adds a DSH block**: whether a `dsh` binary is on PATH and its version (a missing one is reported, not failed), the absence of a hook surface, and that the surface is shared with Codex.
- **`--uninstall`/`--clear --target dsh` say the files are shared** with Codex, because Keel cannot tell from the files which host a repository's `.agents/` surface was installed for.
- Not in this change, on purpose: a DSH bundle (`dsh plugin add`), a command surface, and hooks. They wait for the spike on #504.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-target-surface-diagnostics`

## Impact

`bin/keel.js`, `src/core/capabilities.js`, `src/core/projection.js`, `scripts/validation/dsh.py`, `scripts/validation/registry.py`, `README.md`, `README.zh-CN.md`, the published spec, and the changelog.
