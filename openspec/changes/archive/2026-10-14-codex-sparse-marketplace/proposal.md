## Why

Issue #329. On 2026-10-14 `keel --update` reported `codex plugin: failed - \`codex plugin marketplace upgrade keel-marketplace\` exited 1`. Codex's reason: `git clone marketplace source timed out after 30s … fatal: early EOF`. The Keel marketplace is a plain Git source, so each refresh clones the whole repository, and through the owner's proxy a shallow clone took 44 s, past Codex's fixed 30 s limit. Codex supports sparse Git marketplaces; the plugin needs only `.agents/plugins` and `plugins/keel` (144 KB). With `sparse_paths` set, the refresh took 19–25 s when the link held, and failed with `early EOF` on some attempts, so one attempt is not enough either. The owner asked on 2026-10-14 to fix the Codex hang.

## What Changes

- `keel --update` runs `codex plugin marketplace upgrade` up to twice: a failed first attempt is retried once.
- When it still fails, the Codex `failed` line names the sparse remedy: `sparse_paths = [".agents/plugins", "plugins/keel"]` under `[marketplaces.keel-marketplace]` in the Codex config, which makes the refresh fetch only the plugin.
- The `manual` hint for a local marketplace, the README install steps (both languages), and `docs/updating.md` name the sparse form: `codex plugin marketplace add TanglmChris/keel --ref main --sparse .agents/plugins --sparse plugins/keel`.

## Capabilities

### Modified Capabilities
- `keel-native-plugin-package`: the Codex refresh is retried once, a lasting failure names the sparse remedy, and the documented Codex marketplace is sparse.

## Impact

`bin/keel.js`, `README.md`, `README.zh-CN.md`, `docs/updating.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
