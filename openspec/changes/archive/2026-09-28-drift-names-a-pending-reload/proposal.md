## Why

Issue #172. On 2026-09-28 the host had already auto-updated the Keel plugin to 5.78.0, but a session that had loaded 5.77.0 kept printing the SessionStart drift line after `/clear`, because `/clear` does not reload hooks. That line named `claude plugin update`, which had already happened. It also told the reader to align the global CLI with `npm i -g @christang/keel@5.77.0`, which is a downgrade to the stale loaded plugin. The only remedy the state needed was `/reload-plugins`.

## What Changes

- **The drift line recognizes an update the host already installed.** On Claude the host records each installed plugin in `installed_plugins.json`, four directories above a cached plugin's package root. When that record names another install of this same plugin at a different version, the line says the host has already installed it and names `/reload-plugins` or the next session start as the whole remedy. It does not name `claude plugin update`.
- **The PATH copy is judged against the installed version.** When a pending install is known and the PATH `keel` matches it, the shadow sentence is omitted, because the reload removes the shadow. When it does not match, the align command names the installed version instead of the loaded one.
- **Nothing else moves.** An absent, unreadable, or unrecognized record keeps today's wording byte for byte, so Codex and any other layout are unaffected. The check stays local and offline, and runs nothing.

## Capabilities

### Modified Capabilities

- `keel-native-runtime-projection`: the drift report distinguishes an update that still needs installing from one that only needs a reload.

## Impact

- `plugins/keel/scripts/session-start.js`, `scripts/validate_plugin.py`.
- Reads one more host file, locally, with every failure falling back to the current wording.
