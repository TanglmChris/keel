## Why

Issue #168, a regression from 5.74.0. `keel --init` runs `openspec init --force` and `openspec update --force` with the OpenSpec Keel resolves. Since 5.74.0 the published `npm-shrinkwrap.json` pins that OpenSpec to 1.6.0 for every install. Consumers had been resolving `^1.4.1` to the newest 1.x, 1.13.2. On 2026-09-27, `keel --init` in such a repository (`rtl_ppa_prj`) rewrote ten OpenSpec skill and command files with 1.6.0 templates and deleted about 1000 lines. Doctor still said `openspec: ok`. The agent there restored the files by hand.

The owner asked for the fix in Keel and for the affected repository to be repaired through what `keel --doctor` tells it, not by editing it from here. That repository has two problems doctor does not name today:
- templates newer than Keel's OpenSpec, which the next `--init` would downgrade;
- a plugin auto-update declaration in a `.claude/settings.json` that Git does not track, so only that checkout declares it.

Moving Keel itself to OpenSpec 1.13.x is #169. It changes the Codex surface layout and is a separate change.

## What Changes

- **`keel --init` never downgrades OpenSpec surfaces.** Before its OpenSpec rewrite, it reads the highest `generatedBy` among the repository's OpenSpec skills. If that version is newer than the OpenSpec it would run, it skips `openspec init --force` and `openspec update --force`, still runs the Keel installer and the overlay refresh, and says which version wrote the surfaces and which one it declined to run.
- **Doctor names the OpenSpec that wrote the surfaces.** A new `OpenSpec surfaces` line compares the newest `generatedBy` with the OpenSpec Keel runs. It is `ok` when Keel's is the same or newer. It is `warning` when the surfaces are newer, stating that `keel --init` will leave them alone and that `keel --install` refreshes the protocol without touching them.
- **Doctor names an untracked auto-update declaration.** When `.claude/settings.json` declares `autoUpdate: true` but Git does not track the file, the `plugin auto-update` line is a `warning` that names `git add .claude/settings.json`.

## Capabilities

### Modified Capabilities

- `keel-openspec-surface-overlay`: project init never replaces OpenSpec surfaces with an older OpenSpec's.
- `keel-target-surface-diagnostics`: doctor reports which OpenSpec wrote the surfaces, and an auto-update declaration only one checkout carries.

## Impact

- `bin/keel.js`, `scripts/validate_plugin.py`.
- A repository whose surfaces are newer than Keel's OpenSpec keeps them through `keel --init`. Until #169 lands, a brand-new repository still starts on 1.6.0 templates.
