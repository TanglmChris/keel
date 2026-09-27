## Why

Issue #164, change 2 of 3. Since 5.74.0 the Claude plugin *is* the published package, so one plugin update brings the CLI too. The update still does not happen by itself. Claude Code auto-updates plugins only from marketplaces that have auto-update turned on, and that is on by default only for Anthropic's official marketplaces: "off for every other marketplace", and a marketplace author cannot change the default. Each user would have to find the `/plugin` → Marketplaces toggle. The owner decided (#164, option (i)) that a release should go live without the user doing anything beyond, at most, `/reload-plugins`.

Claude reads a marketplace's auto-update setting first from `autoUpdate` on its `extraKnownMarketplaces` entry in any settings file. A project's committed `.claude/settings.json` is such a file, and `keel --init --target claude` already writes the project's Claude surface.

## What Changes

- **Init and install declare auto-update.** On the Claude target, `keel --init` and `keel --install` merge the following into `.claude/settings.json`:

  ```json
  "extraKnownMarketplaces": {
    "keel-marketplace": {
      "source": { "source": "github", "repo": "TanglmChris/keel" },
      "autoUpdate": true
    }
  }
  ```

  Every other key in the file is kept. An existing `keel-marketplace` entry keeps its own `source`, and a stated `autoUpdate` is never overwritten: a project that wrote `false` has decided. Re-running changes nothing.
- **Uninstall removes only what Keel wrote.** The entry is removed when it is exactly the one Keel writes, and left alone otherwise.
- **Doctor reports it.** A `plugin auto-update` line reports one of three states: declared on, declared off by the project, or not declared, with the command that declares it.
- Codex and OpenCode targets write nothing new.

## Capabilities

### Modified Capabilities

- `keel-native-plugin-package`: project setup declares Claude plugin auto-update for the Keel marketplace.

## Impact

- `scripts/install_to_repo.py`, `bin/keel.js` (doctor), `scripts/validate_plugin.py`, `README.md`, `README.zh-CN.md`.
- A project's `.claude/settings.json` gains an `extraKnownMarketplaces` entry on its next `keel --install`. Collaborators who trust the folder are offered the Keel marketplace. Updates then arrive in the background after a session's first message, and apply after `/reload-plugins` or at the next start.
- Keel cannot observe whether the host honored the setting: the host's `marketplace list --json` reports no auto-update state. Doctor reports the declaration, not the behavior.
